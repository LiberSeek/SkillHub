#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TTS_SCRIPT = SCRIPT_DIR / "voicebox_tts.sh"


@dataclass
class Segment:
    index: int
    text: str
    audio_file: str
    duration: float
    start: float
    end: float


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=True)


def ffprobe_duration(path: Path) -> float:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    return float(result.stdout.strip())


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        parts = text.split("\n---\n", 1)
        if len(parts) == 2:
            return parts[1]
    return text


def extract_script_text(script_file: Path) -> str:
    text = strip_frontmatter(script_file.read_text(encoding="utf-8"))
    lines = text.splitlines()
    mode = "include"
    pieces: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        nonlocal paragraph
        if paragraph:
            pieces.append(" ".join(x.strip() for x in paragraph if x.strip()))
            paragraph = []

    for raw in lines:
        line = raw.strip()
        if not line:
            flush()
            continue
        if line.startswith("#"):
            flush()
            heading = line.lstrip("#").strip()
            if any(token in heading for token in ("质检", "参考", "附录")):
                break
            if "标题" in heading and "口播" not in heading:
                mode = "skip"
            elif any(token in heading for token in ("口播稿", "正文", "内容", "脚本", "文稿")):
                mode = "include"
            continue
        if mode == "skip":
            continue
        if re.match(r"^L\d+\b", line):
            continue
        paragraph.append(line)

    flush()
    cleaned = "\n\n".join(piece for piece in pieces if piece)
    if not cleaned:
        raise RuntimeError(f"Could not extract usable narration text from {script_file}")
    return cleaned


def split_segments(text: str, mode: str) -> list[str]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    if mode == "paragraph":
        return blocks

    segments: list[str] = []
    for block in blocks:
        parts = re.split(r"(?<=[。！？!?])\s*", block)
        for part in parts:
            part = part.strip()
            if part:
                segments.append(part)
    return segments


def ensure_duration_attr(index_html: Path, duration_seconds: float) -> None:
    html = index_html.read_text(encoding="utf-8")
    replacement = f'data-duration="{duration_seconds:.3f}"'
    updated, count = re.subn(r'data-duration="[^"]+"', replacement, html, count=1)
    if count != 1:
        raise RuntimeError(f"Could not update data-duration in {index_html}")
    index_html.write_text(updated, encoding="utf-8")


def write_concat_list(paths: Iterable[Path], output: Path) -> None:
    lines = []
    for path in paths:
        escaped = path.as_posix().replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def synthesize_segments(
    tts_script: Path,
    profile_id: str,
    segments: list[str],
    chunk_dir: Path,
    language: str,
    engine: str,
    model_size: str,
    personality: bool,
    instruct: str | None,
    seed: int | None,
) -> list[Path]:
    chunk_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []

    for idx, text in enumerate(segments, start=1):
        out = chunk_dir / f"{idx:03d}.wav"
        cmd = [
            str(tts_script),
            "--profile-id",
            profile_id,
            "--text",
            text,
            "--output",
            str(out),
            "--language",
            language,
            "--engine",
            engine,
            "--model-size",
            model_size,
        ]
        if personality:
            cmd.append("--personality")
        if instruct:
            cmd.extend(["--instruct", instruct])
        if seed is not None:
            cmd.extend(["--seed", str(seed + idx - 1)])
        run(cmd)
        files.append(out)

    return files


def concat_audio(chunk_files: list[Path], gap_ms: int, work_dir: Path, output_wav: Path) -> list[Path]:
    if not chunk_files:
        raise RuntimeError("No audio chunks to concatenate")

    if gap_ms <= 0 or len(chunk_files) == 1:
        concat_inputs = chunk_files
    else:
        silence = work_dir / "silence.wav"
        run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=24000:cl=mono",
                "-t",
                f"{gap_ms / 1000:.3f}",
                str(silence),
            ]
        )
        concat_inputs = []
        for idx, chunk in enumerate(chunk_files):
            concat_inputs.append(chunk)
            if idx != len(chunk_files) - 1:
                concat_inputs.append(silence)

    concat_list = work_dir / "concat.txt"
    write_concat_list(concat_inputs, concat_list)
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c:a",
            "pcm_s16le",
            str(output_wav),
        ]
    )
    return concat_inputs


def build_segment_manifest(chunk_files: list[Path], texts: list[str], gap_ms: int) -> list[Segment]:
    segments: list[Segment] = []
    cursor = 0.0
    gap_sec = gap_ms / 1000.0
    for idx, (chunk, text) in enumerate(zip(chunk_files, texts, strict=True), start=1):
        duration = ffprobe_duration(chunk)
        start = cursor
        end = start + duration
        segments.append(
            Segment(
                index=idx,
                text=text,
                audio_file=str(chunk),
                duration=round(duration, 3),
                start=round(start, 3),
                end=round(end, 3),
            )
        )
        cursor = end + gap_sec
    return segments


def render_silent_video(hyperframes_dir: Path, output_video: Path, quality: str) -> None:
    run(
        [
            "npx",
            "-y",
            "hyperframes",
            "render",
            ".",
            "-o",
            str(output_video),
            "-q",
            quality,
        ],
        cwd=hyperframes_dir,
    )


def mux_audio(silent_video: Path, audio_file: Path, output_video: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(audio_file),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(output_video),
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a HyperFrames video from narration audio first, then render against measured duration.")
    parser.add_argument("--hyperframes-dir", required=True, help="Directory containing index.html and hyperframes.json")
    parser.add_argument("--script-file", help="Markdown or text file used to generate narration audio")
    parser.add_argument("--audio-input", help="Existing wav/mp3 narration file; skips TTS generation")
    parser.add_argument("--profile-id", help="VoiceBox profile id, required when using --script-file without --audio-input")
    parser.add_argument("--segment-mode", choices=["paragraph", "sentence"], default="paragraph")
    parser.add_argument("--gap-ms", type=int, default=220, help="Silence gap inserted between synthesized chunks")
    parser.add_argument("--tail-pad-sec", type=float, default=0.0, help="Extra seconds appended to video duration after narration ends")
    parser.add_argument("--lead-pad-sec", type=float, default=0.0, help="Extra seconds added before narration for video timing")
    parser.add_argument("--tts-script", default=str(DEFAULT_TTS_SCRIPT))
    parser.add_argument("--language", default="zh")
    parser.add_argument("--engine", default="qwen")
    parser.add_argument("--model-size", default="1.7B")
    parser.add_argument("--personality", action="store_true")
    parser.add_argument("--instruct")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--quality", default="standard", choices=["draft", "standard", "high"])
    parser.add_argument("--assembled-audio-output", help="Final assembled narration wav path")
    parser.add_argument("--silent-video-output", help="Rendered silent mp4 path")
    parser.add_argument("--final-video-output", help="Final mp4 path with muxed audio")
    parser.add_argument("--manifest-output", help="JSON manifest for chunk timings and outputs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    hyperframes_dir = Path(args.hyperframes_dir).expanduser().resolve()
    index_html = hyperframes_dir / "index.html"
    if not index_html.exists():
        raise RuntimeError(f"Missing HyperFrames index.html: {index_html}")

    work_dir = hyperframes_dir / "build" / "voice-driven"
    chunk_dir = work_dir / "chunks"
    work_dir.mkdir(parents=True, exist_ok=True)

    assembled_audio = Path(args.assembled_audio_output).expanduser().resolve() if args.assembled_audio_output else hyperframes_dir / "assets" / "voiceover-final.wav"
    silent_video = Path(args.silent_video_output).expanduser().resolve() if args.silent_video_output else hyperframes_dir / "exports" / "voice-driven-silent.mp4"
    final_video = Path(args.final_video_output).expanduser().resolve() if args.final_video_output else hyperframes_dir / "exports" / "voice-driven.mp4"
    manifest_output = Path(args.manifest_output).expanduser().resolve() if args.manifest_output else work_dir / "build-manifest.json"

    assembled_audio.parent.mkdir(parents=True, exist_ok=True)
    silent_video.parent.mkdir(parents=True, exist_ok=True)
    final_video.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.parent.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, object] = {
        "hyperframes_dir": str(hyperframes_dir),
        "index_html": str(index_html),
        "assembled_audio": str(assembled_audio),
        "silent_video": str(silent_video),
        "final_video": str(final_video),
    }

    if args.audio_input:
        audio_input = Path(args.audio_input).expanduser().resolve()
        if not audio_input.exists():
            raise RuntimeError(f"Audio input not found: {audio_input}")
        if audio_input != assembled_audio:
            run(["ffmpeg", "-y", "-i", str(audio_input), str(assembled_audio)])
        manifest["audio_source"] = str(audio_input)
        manifest["segments"] = []
    else:
        if not args.script_file or not args.profile_id:
            raise RuntimeError("Using TTS requires both --script-file and --profile-id")
        script_file = Path(args.script_file).expanduser().resolve()
        if not script_file.exists():
            raise RuntimeError(f"Script file not found: {script_file}")
        script_text = extract_script_text(script_file)
        segments = split_segments(script_text, args.segment_mode)
        chunk_files = synthesize_segments(
            tts_script=Path(args.tts_script).expanduser().resolve(),
            profile_id=args.profile_id,
            segments=segments,
            chunk_dir=chunk_dir,
            language=args.language,
            engine=args.engine,
            model_size=args.model_size,
            personality=args.personality,
            instruct=args.instruct,
            seed=args.seed,
        )
        concat_audio(chunk_files, args.gap_ms, work_dir, assembled_audio)
        manifest["script_file"] = str(script_file)
        manifest["segment_mode"] = args.segment_mode
        manifest["segments"] = [asdict(item) for item in build_segment_manifest(chunk_files, segments, args.gap_ms)]

    audio_duration = ffprobe_duration(assembled_audio)
    target_duration = args.lead_pad_sec + audio_duration + args.tail_pad_sec
    ensure_duration_attr(index_html, target_duration)
    render_silent_video(hyperframes_dir, silent_video, args.quality)
    mux_audio(silent_video, assembled_audio, final_video)

    manifest["audio_duration"] = round(audio_duration, 3)
    manifest["lead_pad_sec"] = args.lead_pad_sec
    manifest["tail_pad_sec"] = args.tail_pad_sec
    manifest["video_duration_target"] = round(target_duration, 3)
    manifest_output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "final_video": str(final_video), "audio_duration": round(audio_duration, 3), "video_duration_target": round(target_duration, 3)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
