#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


FONT_ENV = "CONTENT_PRODUCER_FONT"
DEFAULT_FONT_CANDIDATES = [
    os.environ.get(FONT_ENV, ""),
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]


def resolve_default_font() -> Path:
    for candidate in DEFAULT_FONT_CANDIDATES:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    return Path("/System/Library/Fonts/Hiragino Sans GB.ttc")


DEFAULT_FONT = resolve_default_font()


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, text=True)


def ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    return float(result.stdout.strip())


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if current and (bbox[2] - bbox[0]) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [text]


def prepare_scene_image(
    scene: dict,
    output_path: Path,
    width: int,
    height: int,
    font_path: Path,
) -> Path:
    image = Path(scene["image"]).expanduser().resolve()
    subtitle = scene.get("subtitle", "").strip()

    with Image.open(image) as src:
        src = src.convert("RGBA")
        scale = max(width / src.width, height / src.height)
        resized = src.resize(
            (round(src.width * scale), round(src.height * scale)),
            Image.Resampling.LANCZOS,
        )

        left = max(0, (resized.width - width) // 2)
        top = max(0, (resized.height - height) // 2)
        canvas = resized.crop((left, top, left + width, top + height))

    if subtitle:
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        font = ImageFont.truetype(str(font_path), 42)
        text_left = 80
        text_top = height - 260
        text_width = width - 160
        lines = wrap_text(draw, subtitle, font, text_width)
        line_height = 54
        box_height = max(190, 70 + line_height * len(lines))
        box_top = height - box_height - 60

        draw.rounded_rectangle(
            (40, box_top, width - 40, box_top + box_height),
            radius=28,
            fill=(0, 0, 0, 122),
        )

        y = box_top + 42
        for line in lines:
            draw.text((text_left, y), line, font=font, fill=(255, 255, 255, 255))
            y += line_height

        canvas = Image.alpha_composite(canvas, overlay)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, quality=95)
    return output_path


def build_scene_clip(
    scene: dict,
    rendered_image_path: Path,
    output_path: Path,
    fps: int,
) -> None:
    duration = float(scene["duration"])
    motion = scene.get("motion", "slow_push")

    if motion == "slow_push":
        zoom_expr = "min(zoom+0.00045,1.10)"
    elif motion == "slow_pull":
        zoom_expr = "if(lte(on,1),1.10,max(1.0,zoom-0.00045))"
    else:
        zoom_expr = "1.0"

    frames = max(1, round(duration * fps))

    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(rendered_image_path),
            "-vf",
            f"zoompan=z='{zoom_expr}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}",
            "-t",
            f"{duration:.3f}",
            "-r",
            str(fps),
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "libx264",
            str(output_path),
        ]
    )


def concat_clips(clip_paths: list[Path], concat_file: Path, output_video: Path) -> None:
    lines = [f"file '{clip.resolve().as_posix()}'" for clip in clip_paths]
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(output_video),
        ]
    )


def mux_audio(video: Path, audio: Path, output_video: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-i",
            str(audio),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(output_video),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a short-form video from still images and a scene manifest.")
    parser.add_argument("--manifest", required=True, help="Path to manifest JSON")
    parser.add_argument("--output", required=True, help="Output MP4 path")
    parser.add_argument("--workdir", help="Optional work directory for clips")
    parser.add_argument("--font", default=str(DEFAULT_FONT), help="Font file used for subtitles")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    width = int(data.get("width", 1080))
    height = int(data.get("height", 1920))
    fps = int(data.get("fps", 30))
    scenes = data["scenes"]
    audio_path = Path(data["audio"]).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    font_path = Path(args.font).expanduser().resolve()

    workdir = (
        Path(args.workdir).expanduser().resolve()
        if args.workdir
        else output_path.parent / "build" / "image-driven"
    )
    clips_dir = workdir / "clips"
    frames_dir = workdir / "frames"
    if workdir.exists():
        shutil.rmtree(workdir)
    clips_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    audio_duration = ffprobe_duration(audio_path)
    scenes_duration = sum(float(scene["duration"]) for scene in scenes)
    if abs(audio_duration - scenes_duration) > 0.5:
        raise RuntimeError(
            f"Scene durations ({scenes_duration:.3f}s) do not match audio duration ({audio_duration:.3f}s)."
        )

    clip_paths: list[Path] = []
    for idx, scene in enumerate(scenes, start=1):
        frame_path = frames_dir / f"{idx:02d}.jpg"
        prepare_scene_image(scene, frame_path, width, height, font_path)
        clip_path = clips_dir / f"{idx:02d}.mp4"
        build_scene_clip(scene, frame_path, clip_path, fps)
        clip_paths.append(clip_path)

    silent_video = workdir / "silent.mp4"
    concat_file = workdir / "concat.txt"
    concat_clips(clip_paths, concat_file, silent_video)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mux_audio(silent_video, audio_path, output_path)

    print(
        json.dumps(
            {
                "ok": True,
                "output": str(output_path),
                "audio_duration": round(audio_duration, 3),
                "scene_count": len(scenes),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
