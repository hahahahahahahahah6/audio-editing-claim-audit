# Documentation claim auditor

This offline static auditor compares documented capability claims with Python source evidence. It never executes inspected code.

## Usage

```sh
PIP_NO_CACHE_DIR=1 python3 -m pip install .
audio-editing-claim-audit audit . --json
python3 -m audio_editing_claim_audit audit . --verbose
```

The path defaults to the current directory. Repeat `--ignore PREFIX` to exclude paths. Use `--fail-on medium` to include test-only findings. Exit status is 0 for PASS, 2 for findings at the chosen threshold, and 1 for usage or I/O errors. Use `--version` to show the version.

Finding identifiers:

```text
documented-audio-editing-claim-false
documented-no-audio-editing-claim-false
```

## Differentiation

Other families cover combining existing tracks into a simultaneous output, synthesising sound from content or models, splitting a mix into stems, transcribing speech, turning text into speech, removing noise, composing music, turning sound into notation, and editing video. This audit covers single-track transforms.

Other excluded families cover spreadsheet reading and generation, word-document reading and generation, presentation reading and generation, PDF extraction, generation, merging, splitting, encryption, rotation, form-filling, watermarking, redaction, compression and annotation, table extraction, OCR, document extraction, e-signature, payment processing, screen recording, video generation, QR code generation, barcode generation and barcode scanning.

## Limitations

- This phrase may refer to silence or a test fixture:

  ```text
  trim audio
  ```

- This phrase may refer to a fixture or a video soundtrack:

  ```text
  cut audio
  ```

- This phrase may refer to metadata:

  ```text
  edit audio
  ```

- This phrase may refer to a roadmap:

  ```text
  audio editing
  ```

- This phrase may refer to a person or hardware:

  ```text
  audio editor
  ```

- This phrase may refer to a crossfade:

  ```text
  fade audio
  ```

- This phrase may refer to a volume reading:

  ```text
  normalize audio
  ```

- This phrase may refer to source separation:

  ```text
  split audio
  ```

- This phrase may refer to playback speed:

  ```text
  change audio speed
  ```
- The segment pair accepts a method on an unrelated object.
- The segment pair does not trace data flow.
- A slice of an unbound list is missed.
- The transformer and effect must occur in one module.
- The transformer pair does not trace data flow.
- A filter graph counts even if it never runs.
- The alternate filter method is accepted.
- A filter name held in a variable is missed.
- A sound-trimming filter on video can also count for the video family.
- A bare import is not evidence.
- Roadmap, changelog and TODO prose still counts.
- Denials outside the list are not recognised.
- Documents outside the root README and docs directories are ignored.
- Evidence split across modules is missed.
- Local definitions shadow route names, including wrappers.
- Dead code counts.
- Subprocess calls invoking external tools are not evidence.
- Mixing alone is not evidence.
- Source separation alone is not evidence.
- Sound generation alone is not evidence.
- Speech recognition alone is not evidence.
- Noise suppression alone is not evidence.
- A locally defined generic name is shadowed.
- Successive alias chains can be missed.
- Only exact phrases are matched.
- Implementations in other languages are invisible.
- Runtime-only routes are invisible.
- A mixing filter is not evidence.
- A channel merge filter is not evidence.
- A video trim filter is not evidence.
- An append call is not evidence.
- Sequential clip concatenation is not evidence.
- A sequential filter is not evidence.
- An overlay call is not evidence.
- An export call alone is not evidence.
- Silence detection alone is not evidence.
- Playback alone is not evidence.
- A segment load alone is not evidence.
- An edit method alone is not evidence.
- A transformer construction alone is not evidence.
- A transformer build alone is not evidence.
- A transformer preview alone is not evidence.
- A combiner construction is not evidence.
- A format change alone is not evidence.
- A channel split alone is not evidence.
- A volume reading alone is not evidence.
- Array arithmetic alone is not evidence.
- Static matching does not establish correctness.
