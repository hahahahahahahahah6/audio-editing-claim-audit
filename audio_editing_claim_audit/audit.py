"""Offline documentation and Python source inspection."""
import ast
import os
import re
from pathlib import Path
from .phrases import AUDIOEDITING, NOAUDIOEDITING

GENERIC = set('trim_audio trims_audio trimming_audio cut_audio cuts_audio cutting_audio edit_audio edits_audio editing_audio fade_audio fades_audio fading_audio fade_in_audio fade_out_audio normalize_audio normalizes_audio normalizing_audio split_audio splits_audio splitting_audio change_audio_speed speed_up_audio slow_down_audio audio_editor'.split())
LOADS = set('from_file from_mp3 from_flv from_ogg from_wav from_raw silent empty'.split())
EDITS = set('fade fade_in fade_out apply_gain reverse get_sample_slice remove_dc_offset'.split())
EFFECTS = set('trim fade gain tempo vol'.split())
LIBROSA = set('trim time_stretch pitch_shift split'.split())
FILTERS = set('atrim afade atempo loudnorm volume'.split())

def normalize(text):
    return ' '.join(text.lower().replace("n't", ' not').replace('-', ' ').split())

def _pattern(phrases):
    return re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(x) for x in sorted(phrases, key=lambda x: (-len(x), x))) + r')(?!\w)')

YES = _pattern(AUDIOEDITING)
NO = _pattern(NOAUDIOEDITING)

def claims(text):
    lines = []
    fence = None
    for line in text.splitlines():
        m = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip():
                fence = None
            continue
        if m:
            fence = m.group(1)
            continue
        lines.append(line)
    positive = negative = False
    for paragraph in re.split(r'\n\s*\n', '\n'.join(lines)):
        paragraph = normalize(paragraph)
        negative |= bool(NO.search(paragraph))
        positive |= bool(YES.search(NO.sub(' ', paragraph)))
    return positive, negative

def evidence(source):
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return False
    nodes = list(ast.walk(tree))
    imports = {}
    definitions = set()
    rebound = set()
    for n in nodes:
        if isinstance(n, ast.Import):
            for a in n.names:
                imports[a.asname or a.name.split('.')[0]] = a.name if a.asname else a.name.split('.')[0]
        elif isinstance(n, ast.ImportFrom) and n.module:
            for a in n.names:
                if a.name != '*':
                    imports[a.asname or a.name] = n.module + '.' + a.name
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions.add(n.name)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            rebound.add(n.id)
    def root(node):
        while isinstance(node, ast.Attribute):
            node = node.value
        return node.id if isinstance(node, ast.Name) else None
    def resolved(name):
        return imports.get(name, '') if name not in definitions and name not in rebound else ''
    def valid_attr(f):
        r = root(f)
        return f.attr not in definitions and not (r in imports and (r in rebound or r in definitions))
    def matches(f, target, attr, roots):
        if isinstance(f, ast.Name):
            return resolved(f.id) == target and attr not in definitions
        return isinstance(f, ast.Attribute) and f.attr == attr and valid_attr(f) and resolved(root(f)) in roots
    def segment(call):
        if not isinstance(call, ast.Call): return False
        f = call.func
        if matches(f, 'pydub.AudioSegment', 'AudioSegment', {'pydub'}): return True
        return isinstance(f, ast.Attribute) and f.attr in LOADS and valid_attr(f) and resolved(root(f)) in {'pydub', 'pydub.AudioSegment'}
    calls = [n for n in nodes if isinstance(n, ast.Call)]
    seg = any(segment(c) for c in calls)
    transformer = any(matches(c.func, 'sox.Transformer', 'Transformer', {'sox'}) for c in calls)
    bound = set()
    for n in nodes:
        if isinstance(n, (ast.Assign, ast.AnnAssign)) and segment(n.value):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            bound.update(t.id for t in targets if isinstance(t, ast.Name))
        elif isinstance(n, (ast.With, ast.AsyncWith)):
            for item in n.items:
                if segment(item.context_expr) and isinstance(item.optional_vars, ast.Name): bound.add(item.optional_vars.id)
    sliced = any(isinstance(n, ast.Subscript) and ((isinstance(n.value, ast.Name) and n.value.id in bound) or segment(n.value)) for n in nodes)
    if seg and (sliced or any(isinstance(c.func, ast.Attribute) and c.func.attr in EDITS and valid_attr(c.func) for c in calls)): return True
    if transformer and any(isinstance(c.func, ast.Attribute) and c.func.attr in EFFECTS and valid_attr(c.func) for c in calls): return True
    for c in calls:
        f = c.func
        if matches(f, 'pydub.silence.split_on_silence', 'split_on_silence', {'pydub', 'pydub.silence'}): return True
        if any(matches(f, 'librosa.effects.' + name, name, {'librosa', 'librosa.effects'}) for name in LIBROSA): return True
        if isinstance(f, ast.Attribute) and f.attr in GENERIC and valid_attr(f): return True
        if isinstance(f, ast.Name) and resolved(f.id).rsplit('.', 1)[-1] in GENERIC and resolved(f.id).rsplit('.', 1)[-1] not in definitions: return True
        is_filter = (isinstance(f, ast.Attribute) and f.attr in {'filter', 'filter_'} and valid_attr(f)) or (isinstance(f, ast.Name) and resolved(f.id) in {'ffmpeg.filter', 'ffmpeg.filter_'} and resolved(f.id).split('.')[-1] not in definitions)
        if is_filter and any(isinstance(a, ast.Constant) and isinstance(a.value, str) and a.value in FILTERS for a in list(c.args) + [k.value for k in c.keywords]): return True
    return False

def audit(path, ignore=()):
    root = Path(path)
    if not root.is_dir() or root.is_symlink(): raise OSError('root is not a readable directory')
    positive = negative = production = test = False
    ignores = tuple(str(x).replace('\\', '/').strip('/') for x in ignore)
    def ignored(rel): return any(rel == x or rel.startswith(x + '/') for x in ignores if x)
    def onerror(error): raise error
    for base, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
        dirs[:] = sorted(d for d in dirs if not (Path(base)/d).is_symlink() and not ignored((Path(base)/d).relative_to(root).as_posix()))
        for name in sorted(files):
            file = Path(base)/name
            rel = file.relative_to(root)
            if file.is_symlink() or ignored(rel.as_posix()): continue
            parts = rel.parts
            if (rel.as_posix() == 'README.md' or ('docs' in parts and file.suffix == '.md')):
                p, n = claims(file.read_text(encoding='utf-8'))
                positive |= p; negative |= n
            if file.suffix != '.py' or any(x in parts for x in ('fixtures', 'docs', 'examples')): continue
            is_test = 'tests' in parts or name.startswith('test_') or name.endswith('_test.py')
            if evidence(file.read_text(encoding='utf-8')):
                if is_test: test = True
                else: production = True
    findings = []
    if positive and not production:
        findings.append({'id': 'documented-audio-editing-claim-false', 'severity': 'MEDIUM' if test else 'HIGH'})
    if negative and production:
        findings.append({'id': 'documented-no-audio-editing-claim-false', 'severity': 'HIGH'})
    return findings
