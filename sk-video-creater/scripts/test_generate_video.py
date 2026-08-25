#!/usr/bin/env python3
"""Offline integration tests for generate_video.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).with_name("generate_video.py")
VIDEO_BYTES = b"mock-mp4-data"


class MockVideoHandler(BaseHTTPRequestHandler):
    provider = ""
    port = 0
    submitted: dict[str, Any] = {}
    headers_seen: dict[str, str] = {}

    def log_message(self, format: str, *args: Any) -> None:
        return

    def send_json(self, value: dict[str, Any]) -> None:
        body = json.dumps(value).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        size = int(self.headers.get("Content-Length", "0"))
        type(self).submitted = json.loads(self.rfile.read(size))
        type(self).headers_seen = dict(self.headers)
        if self.provider in {"happyhorse", "wan"}:
            self.send_json({"output": {"task_id": "hh-1", "task_status": "PENDING"}})
        elif self.provider == "seedance":
            self.send_json({"id": "seed-1", "status": "queued"})
        else:
            self.send_json({"request_id": "grok-1", "status": "pending"})

    def do_GET(self) -> None:
        if self.path == "/result.mp4":
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(VIDEO_BYTES)))
            self.end_headers()
            self.wfile.write(VIDEO_BYTES)
            return
        video_url = f"http://127.0.0.1:{self.port}/result.mp4"
        if self.provider in {"happyhorse", "wan"}:
            self.send_json({"output": {"task_id": "hh-1", "task_status": "SUCCEEDED", "video_url": video_url}})
        elif self.provider == "seedance":
            self.send_json({"id": "seed-1", "status": "succeeded", "content": {"video_url": video_url}})
        else:
            self.send_json({"request_id": "grok-1", "status": "done", "video": {"url": video_url}})


class VideoCliTests(unittest.TestCase):
    def dry_run(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments, "--dry-run"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    def run_provider(self, provider: str) -> tuple[dict[str, Any], dict[str, str]]:
        handler = type(f"{provider.title()}Handler", (MockVideoHandler,), {"provider": provider})
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        handler.port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tempdir:
                command = [
                    sys.executable,
                    str(SCRIPT),
                    "--provider",
                    provider,
                    "--base-url",
                    f"http://127.0.0.1:{handler.port}",
                    "--api-key",
                    "test-key",
                    "--prompt",
                    "A cinematic test",
                    "--duration",
                    "5",
                    "--ratio",
                    "16:9",
                    "--resolution",
                    "720p",
                    "--poll-interval",
                    "0.01",
                    "--outdir",
                    tempdir,
                    "--no-download",
                ]
                result = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(result.stdout.strip().startswith("http://127.0.0.1:"))
                return handler.submitted, {key.lower(): value for key, value in handler.headers_seen.items()}
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_happyhorse_flow(self) -> None:
        payload, headers = self.run_provider("happyhorse")
        self.assertEqual(payload["model"], "happyhorse-1.1-t2v")
        self.assertEqual(payload["parameters"]["resolution"], "720P")
        self.assertEqual(headers.get("x-dashscope-async"), "enable")

    def test_wan_flow(self) -> None:
        payload, headers = self.run_provider("wan")
        self.assertEqual(payload["model"], "wan3.0-video")
        self.assertEqual(payload["parameters"]["resolution"], "720P")
        self.assertEqual(headers.get("x-dashscope-async"), "enable")

    def test_wan_gateway_supports_adaptive_ratio_and_api_direct(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--provider", "wan",
                "--base-url", "https://api-direct.boft.ai/v1",
                "--model", "wan3.0-video-prime",
                "--prompt", "A gateway test",
                "--duration", "5",
                "--ratio", "adaptive",
                "--resolution", "480p",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        preview = json.loads(result.stdout)
        self.assertEqual(preview["create_endpoint"], "https://api-direct.boft.ai/v1/videos/generations")
        self.assertEqual(preview["query_endpoint_template"], "https://api-direct.boft.ai/v1/videos/generations/{task_id}")
        self.assertEqual(preview["body"]["model"], "wan3.0-video-prime")
        self.assertEqual(preview["body"]["aspect_ratio"], "adaptive")
        self.assertEqual(preview["body"]["resolution"], "480p")

    def test_wan_gateway_accepts_full_create_endpoint_and_media_image(self) -> None:
        result = subprocess.run(
            [
                sys.executable, str(SCRIPT),
                "--provider", "wan",
                "--base-url", "https://api.boft.ai/v1/videos/generations",
                "--prompt", "A gateway image test",
                "--image", "https://example.com/first.png",
                "--duration", "30",
                "--ratio", "adaptive",
                "--resolution", "480p",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        preview = json.loads(result.stdout)
        self.assertEqual(preview["create_endpoint"], "https://api.boft.ai/v1/videos/generations")
        self.assertEqual(preview["query_endpoint_template"], "https://api.boft.ai/v1/videos/generations/{task_id}")
        self.assertEqual(preview["body"]["media"], [{"type": "first_frame", "url": "https://example.com/first.png"}])

    def test_wan_gateway_supports_first_and_last_frames(self) -> None:
        result = self.dry_run(
            "--provider", "wan", "--base-url", "https://api.boft.ai", "--mode", "kf2v",
            "--first-frame", "https://example.com/start.png", "--last-frame", "https://example.com/end.png",
            "--prompt", "A controlled transition", "--duration", "5", "--resolution", "720p",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        preview = json.loads(result.stdout)
        self.assertEqual(
            preview["body"]["media"],
            [
                {"type": "first_frame", "url": "https://example.com/start.png"},
                {"type": "last_frame", "url": "https://example.com/end.png"},
            ],
        )

    def test_wan_gateway_supports_video_edit_media(self) -> None:
        result = self.dry_run(
            "--provider", "wan", "--base-url", "https://api.boft.ai", "--mode", "videoedit",
            "--video", "https://example.com/input.mp4", "--reference", "https://example.com/coat.png",
            "--prompt", "Replace the coat and preserve motion", "--duration", "5",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        preview = json.loads(result.stdout)
        self.assertEqual(preview["body"]["model"], "wan3.0-video")
        self.assertEqual(preview["body"]["media"][0]["type"], "video")
        self.assertEqual(preview["body"]["media"][1]["type"], "reference_image")

    def test_happyhorse_reference_mode_selects_r2v(self) -> None:
        result = self.dry_run(
            "--provider", "happyhorse", "--base-url", "https://dashscope.aliyuncs.com", "--mode", "r2v",
            "--reference", "https://example.com/person.png", "--prompt", "character1 waves",
            "--duration", "5", "--ratio", "16:9", "--resolution", "720p",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        preview = json.loads(result.stdout)
        self.assertEqual(preview["body"]["model"], "happyhorse-1.1-r2v")
        self.assertEqual(preview["body"]["input"]["media"], [{"type": "reference_image", "url": "https://example.com/person.png"}])

    def test_happyhorse_video_edit_selects_model(self) -> None:
        result = self.dry_run(
            "--provider", "happyhorse", "--base-url", "https://dashscope.aliyuncs.com", "--mode", "videoedit",
            "--video", "https://example.com/input.mp4", "--reference", "https://example.com/coat.png",
            "--prompt", "Replace the jacket while preserving motion",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        preview = json.loads(result.stdout)
        self.assertEqual(preview["body"]["model"], "happyhorse-1.0-video-edit")
        self.assertEqual(preview["body"]["input"]["media"][0]["type"], "video")

    def test_happyhorse_i2v_native_omits_ratio(self) -> None:
        result = self.dry_run(
            "--provider", "happyhorse", "--base-url", "https://dashscope.aliyuncs.com", "--mode", "i2v",
            "--first-frame", "https://example.com/frame.png", "--prompt", "A slow push in",
            "--duration", "5", "--ratio", "16:9", "--resolution", "720p",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        preview = json.loads(result.stdout)
        self.assertNotIn("ratio", preview["body"]["parameters"])

    def test_happyhorse_rejects_keyframe_mode(self) -> None:
        result = self.dry_run(
            "--provider", "happyhorse", "--mode", "kf2v", "--first-frame", "https://example.com/start.png",
            "--last-frame", "https://example.com/end.png", "--prompt", "A transition", "--duration", "5",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not support first+last-frame", result.stderr)

    def test_wan_keyframe_allows_variable_duration(self) -> None:
        result = self.dry_run(
            "--provider", "wan", "--mode", "kf2v", "--first-frame", "https://example.com/start.png",
            "--last-frame", "https://example.com/end.png", "--prompt", "A transition", "--duration", "8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        preview = json.loads(result.stdout)
        self.assertEqual(preview["body"]["duration"], 8)

    def test_happyhorse_model_suffix_routes_and_validates_media(self) -> None:
        result = self.dry_run(
            "--provider", "happyhorse", "--model", "happyhorse-1.1-r2v",
            "--prompt", "A reference performance",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("r2v requires", result.stderr)

        result = self.dry_run(
            "--provider", "happyhorse", "--model", "happyhorse-1.1-i2v",
            "--prompt", "An image performance",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("i2v requires", result.stderr)

    def test_happyhorse_r2v_mode_wins_over_first_frame(self) -> None:
        result = self.dry_run(
            "--provider", "happyhorse", "--base-url", "https://dashscope.aliyuncs.com", "--mode", "r2v",
            "--first-frame", "https://example.com/first.png",
            "--reference", "https://example.com/character.png",
            "--prompt", "character1 waves",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        preview = json.loads(result.stdout)
        self.assertEqual(preview["body"]["model"], "happyhorse-1.1-r2v")
        self.assertEqual(preview["body"]["input"]["media"][0]["type"], "reference_image")

    def test_ratio_validation_is_provider_specific(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--provider", "grok-video", "--prompt", "A test", "--ratio", "adaptive", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not support adaptive", result.stderr)

    def test_happyhorse_compatible_gateway_flow(self) -> None:
        class GatewayHandler(MockVideoHandler):
            provider = "happyhorse-gateway"

            def do_POST(self) -> None:
                size = int(self.headers.get("Content-Length", "0"))
                type(self).submitted = json.loads(self.rfile.read(size))
                self.send_json({"data": {"id": "gw-1", "status": "queued"}})

            def do_GET(self) -> None:
                if self.path == "/v1/videos/generations/gw-1":
                    video_url = f"http://127.0.0.1:{self.port}/result.mp4"
                    self.send_json({"data": {"id": "gw-1", "status": "completed", "result": {"video_url": video_url}}})
                    return
                super().do_GET()

        server = ThreadingHTTPServer(("127.0.0.1", 0), GatewayHandler)
        GatewayHandler.port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tempdir:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "--provider", "happyhorse",
                        "--base-url", f"http://127.0.0.1:{GatewayHandler.port}/v1",
                        "--api-key", "test-key",
                        "--prompt", "A gateway test",
                        "--duration", "5",
                        "--ratio", "16:9",
                        "--resolution", "720p",
                        "--poll-interval", "0.01",
                        "--outdir", tempdir,
                        "--no-download",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(result.stdout.strip().startswith("http://127.0.0.1:"))
                self.assertEqual(GatewayHandler.submitted["model"], "happyhorse-1.1-t2v")
                self.assertEqual(GatewayHandler.submitted["aspect_ratio"], "16:9")
                self.assertEqual(GatewayHandler.submitted["resolution"], "720p")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_seedance_flow(self) -> None:
        payload, headers = self.run_provider("seedance")
        self.assertEqual(payload["model"], "doubao-seedance-2-0-260128")
        self.assertEqual(payload["content"][0]["type"], "text")
        self.assertEqual(payload["resolution"], "720p")
        self.assertNotIn("x-dashscope-async", headers)

    def test_grok_video_flow(self) -> None:
        payload, _ = self.run_provider("grok-video")
        self.assertEqual(payload["aspect_ratio"], "16:9")
        self.assertEqual(payload["model"], "grok-imagine-video-1.5")

    def test_grok_duration_validation(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--provider",
                "grok-video",
                "--prompt",
                "A test",
                "--duration",
                "16",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("between 1 and 15 seconds", result.stderr)

    def test_download_rejects_private_result_url(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("generate_video", SCRIPT)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaisesRegex(RuntimeError, "private or reserved"):
                module.download_video("http://127.0.0.1/result.mp4", Path(tempdir), "wan", "task-1", 1)


if __name__ == "__main__":
    unittest.main()
