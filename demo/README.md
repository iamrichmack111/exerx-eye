# ExerxEye HQ Piper Demo

`demo/build_demo.sh` creates a narrated 1920×1080, 30 fps H.264/AAC product demo.

It uses Piper `en_US-ryan-high`, captures the real Flask UI with Playwright, generates each narration segment separately, normalizes the voice, synchronizes each screen to its spoken segment, and writes:

`DEMOS/exerx-eye-v10-piper-hq-demo.mp4`

## Local build

```bash
bash demo/build_demo.sh
```

The first run downloads Piper and the high-quality Ryan model into `.demo-cache/`. Those large runtime files are not committed.

## GitHub Actions

Run the **HQ Piper Demo** workflow from Actions. The resulting MP4 is uploaded as a workflow artifact and attached to the latest GitHub Release (or the release tag supplied at dispatch time).
