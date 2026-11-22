import tempfile
import unittest
from pathlib import Path
from audio_editing_claim_audit.audit import audit, claims, evidence, GENERIC
from audio_editing_claim_audit.phrases import AUDIOEDITING, NOAUDIOEDITING

class AuditTests(unittest.TestCase):
    def test_phrases(self):
        self.assertEqual((len(set(AUDIOEDITING)), len(set(NOAUDIOEDITING)), len(GENERIC)), (50, 24, 24))
        for phrase in AUDIOEDITING:
            with self.subTest(phrase=phrase): self.assertEqual(claims(phrase), (True, False))
        for phrase in NOAUDIOEDITING:
            with self.subTest(phrase=phrase): self.assertEqual(claims(phrase), (False, True))
        self.assertEqual(claims('```\nedit audio\n```\n\n`edit audio`'), (True, False))
    def test_routes(self):
        samples = ['from pydub import AudioSegment as A\ns=A.from_file()\ns.fade_in()', 'import pydub as p\np.AudioSegment()[1:]', 'from pydub import AudioSegment\nwith AudioSegment() as s: x=s[0]', 'from pydub.silence import split_on_silence as f\nf()', 'import librosa as l\nl.effects.trim()', 'from librosa.effects import pitch_shift as p\np()', 'import sox\nt=sox.Transformer()\nt.tempo()', 'from ffmpeg import filter_ as f\nf(x="volume")', 'x.filter(1, "atrim")', 'from x import edit_audio as e\ne()']
        samples += ['import x\nx.'+n+'()' for n in GENERIC]
        for s in samples:
            with self.subTest(source=s): self.assertTrue(evidence(s))
        for n in ('fade','fade_in','fade_out','apply_gain','reverse','get_sample_slice','remove_dc_offset'):
            with self.subTest(method=n): self.assertTrue(evidence('from pydub import AudioSegment\ns=AudioSegment()\ns.'+n+'()'))
        for n in ('trim','fade','gain','tempo','vol'):
            with self.subTest(method=n): self.assertTrue(evidence('import sox\ns=sox.Transformer()\ns.'+n+'()'))
        for n in ('trim','time_stretch','pitch_shift','split'):
            with self.subTest(method=n): self.assertTrue(evidence('import librosa\nlibrosa.effects.'+n+'()'))
        for n in ('atrim','afade','atempo','loudnorm','volume'):
            with self.subTest(filter=n): self.assertTrue(evidence('x.filter_(name="'+n+'")'))
    def test_non_evidence(self):
        samples=['from pydub import AudioSegment\ns=AudioSegment()', 'x.fade_in()', 'x[1:]', 'import sox\ns=sox.Transformer()', 'import sox\nsox.Transformer().build()', 'import sox\nsox.Transformer().preview()', 'import sox\nsox.Combiner().trim()', 'filter("atrim")', 'x.filter("amix")', 'x.filter("amerge")', 'x.filter("concat")', 'x.filter("trim")', 'x.filter(name=v)', 'import librosa\nlibrosa.load()', 'import moviepy\nmoviepy.concatenate_audioclips()', 'moviepy.CompositeVideoClip()', 'subprocess.run("ffmpeg -af atrim")', 'numpy.array([1])+1', 'volumedetect()', 'x.rms()', 'x.dBFS', 'x.separate_audio()', 'x.generate_audio()', 'x.recognize_speech()', 'x.denoise()', 'edit_audio()', 'def edit_audio(): pass\nx.edit_audio()', 'import librosa\nlibrosa=1\nlibrosa.effects.trim()', 'import sox\nsox.Transformer()\ndef trim(): pass\nx.trim()']
        samples += ['from pydub import AudioSegment\ns=AudioSegment()\ns.'+n+'()' for n in ('append','overlay','export','set_frame_rate','set_channels','set_sample_width','split_to_mono')]
        samples += ['import pydub\npydub.silence.'+n+'()' for n in ('detect_silence','detect_nonsilent','detect_leading_silence')]
        samples += ['import librosa\nlibrosa.effects.'+n+'()' for n in ('remix','hpss','harmonic','percussive')]
        for s in samples:
            with self.subTest(source=s): self.assertFalse(evidence(s))
    def test_findings(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'README.md').write_text('edit audio')
            self.assertEqual(audit(p)[0]['severity'], 'HIGH')
            (p/'tests').mkdir(); (p/'tests/test_x.py').write_text('x.edit_audio()')
            self.assertEqual(audit(p)[0]['severity'], 'MEDIUM')
            (p/'x.py').write_text('x.edit_audio()')
            self.assertEqual(audit(p), [])
            (p/'README.md').write_text('does not edit audio')
            self.assertEqual(audit(p)[0]['severity'], 'HIGH')
    def test_scope(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'README.md').write_text('edit audio'); (p/'a.py').write_text('from pydub import AudioSegment\nAudioSegment()'); (p/'b.py').write_text('x.fade()')
            self.assertEqual(audit(p)[0]['severity'], 'HIGH')
            (p/'docs').mkdir(); (p/'docs/a.py').write_text('x.edit_audio()')
            self.assertEqual(audit(p)[0]['severity'], 'HIGH')
            self.assertEqual(audit(p, ['README.md']), [])
    def test_self_audit(self):
        self.assertEqual(audit(Path(__file__).resolve().parents[1]), [])
