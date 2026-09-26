#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
from pathlib import Path


def run(cmd, *, input_text=None):
    print('+', ' '.join(map(str, cmd)))
    subprocess.run(
        [str(x) for x in cmd],
        input=input_text.encode('utf-8') if input_text is not None else None,
        check=True,
    )


def probe_duration(path: Path) -> float:
    out = subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', str(path)
    ], text=True).strip()
    return float(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segments', default='demo/segments.json')
    ap.add_argument('--captures', default='demo/captures')
    ap.add_argument('--work', default='demo/render')
    ap.add_argument('--output', default='DEMOS/exerx-eye-v10-piper-hq-demo.mp4')
    ap.add_argument('--piper', required=True)
    ap.add_argument('--model', required=True)
    ap.add_argument('--config', required=True)
    args = ap.parse_args()

    for tool in ('ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            raise SystemExit(f'Missing required tool: {tool}')

    piper = Path(args.piper)
    model = Path(args.model)
    config = Path(args.config)
    captures = Path(args.captures)
    work = Path(args.work)
    audio_dir = work / 'audio'
    clip_dir = work / 'clips'
    audio_dir.mkdir(parents=True, exist_ok=True)
    clip_dir.mkdir(parents=True, exist_ok=True)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    segments = json.loads(Path(args.segments).read_text(encoding='utf-8'))
    concat_lines = []

    for idx, seg in enumerate(segments, 1):
        image = captures / seg['image']
        if not image.exists():
            raise SystemExit(f'Missing capture: {image}')

        wav = audio_dir / f'{idx:02d}.wav'
        run([
            piper,
            '--model', model,
            '--config', config,
            '--output_file', wav,
        ], input_text=seg['text'])

        spoken = probe_duration(wav)
        duration = max(4.0, spoken + 0.65)
        frames = max(120, math.ceil(duration * 30))
        fade_out_start = max(0.0, duration - 0.35)
        clip = clip_dir / f'{idx:02d}.mp4'

        # Subtle slow push-in plus short fades. Voice is normalized and resampled to 48 kHz.
        vf = (
            "scale=2048:1152:force_original_aspect_ratio=increase,"
            "crop=2048:1152,"
            f"zoompan=z='min(zoom+0.00010,1.035)':x='(iw-iw/zoom)/2':"
            f"y='(ih-ih/zoom)/2':d={frames}:s=1920x1080:fps=30,"
            "fade=t=in:st=0:d=0.25,"
            f"fade=t=out:st={fade_out_start:.3f}:d=0.35,"
            "format=yuv420p"
        )
        af = (
            "highpass=f=70,lowpass=f=14500,"
            "loudnorm=I=-16:TP=-1.5:LRA=11,"
            "aresample=48000,apad"
        )
        run([
            'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
            '-loop', '1', '-i', image,
            '-i', wav,
            '-filter_complex', f'[0:v]{vf}[v];[1:a]{af}[a]',
            '-map', '[v]', '-map', '[a]',
            '-t', f'{duration:.3f}',
            '-r', '30',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
            '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
            '-movflags', '+faststart',
            clip,
        ])
        concat_lines.append(f"file '{clip.resolve()}'")

    concat_file = work / 'concat.txt'
    concat_file.write_text('\n'.join(concat_lines) + '\n', encoding='utf-8')
    run([
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-f', 'concat', '-safe', '0', '-i', concat_file,
        '-c', 'copy', '-movflags', '+faststart', output,
    ])

    # Validate final media.
    info = subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,r_frame_rate,codec_name',
        '-of', 'json', str(output)
    ], text=True)
    parsed = json.loads(info)['streams'][0]
    if (parsed.get('width'), parsed.get('height')) != (1920, 1080):
        raise SystemExit(f"Unexpected output size: {parsed.get('width')}x{parsed.get('height')}")
    print(f'Created {output} ({output.stat().st_size / 1024 / 1024:.1f} MiB)')


if __name__ == '__main__':
    main()
