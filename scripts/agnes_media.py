#!/usr/bin/env python3
"""
AGNES Media Generation Script
支持图片和视频生成
"""
import os
import sys
import json
import argparse
import time
import requests
from pathlib import Path

# 从环境变量或本地 .env 文件读取 API Key，避免硬编码泄露
def _load_api_key() -> str:
    """从环境变量 AGNES_API_KEY 或脚本目录下的 .env 文件读取 API Key。"""
    # 1. 优先读环境变量
    key = os.environ.get("AGNES_API_KEY", "").strip()
    if key:
        return key

    # 2. 回退到脚本同级的 .env 文件（格式：AGNES_API_KEY=sk-xxx）
    script_dir = Path(__file__).resolve().parent
    env_file = script_dir / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == "AGNES_API_KEY" and v.strip():
                return v.strip()

    raise SystemExit(
        "未找到 AGNES API Key。请设置环境变量 AGNES_API_KEY，"
        "或在 scripts/.env 文件中写入 AGNES_API_KEY=sk-xxx"
    )

API_KEY = _load_api_key()
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

def make_request(method: str, url: str, data: dict = None, params: dict = None) -> dict:
    """Make HTTP request to AGNES API (bypass system proxy)."""
    session = requests.Session()
    session.trust_env = False

    if method == "GET":
        response = session.get(url, headers=HEADERS, params=params)
    elif method == "POST":
        response = session.post(url, headers=HEADERS, json=data)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

    if response.status_code != 200:
        return {"error": response.text, "status_code": response.status_code}
    return response.json()

def generate_image(prompt: str, model: str = "agnes-image-2.5-flash",
                   size: str = "1024x1024", n: int = 1, output_dir: str = ".") -> dict:
    """Generate image using AGNES API."""
    data = {
        "model": model,
        "prompt": prompt,
        "n": n,
        "size": size,
    }
    result = make_request("POST", "https://api.agnes-ai.cn/v1/images/generations", data=data)

    if "error" in result:
        return result

    images = result.get("data", [])
    saved_paths = []

    for img in images:
        img_url = img.get("url")
        if img_url:
            try:
                output_path = Path(output_dir) / f"agnes_image_{len(saved_paths)+1}.png"
                session = requests.Session()
                session.trust_env = False
                resp = session.get(img_url, timeout=120)
                if resp.status_code == 200:
                    output_path.write_bytes(resp.content)
                    saved_paths.append(str(output_path))
            except Exception as e:
                print(f"Failed to save image: {e}", file=sys.stderr)

    return {"status": "success", "images": saved_paths, "raw": result}

def generate_video(prompt: str, model: str = "agnes-video-v2.0",
                   width: int = None, height: int = None,
                   num_frames: int = None, frame_rate: int = None,
                   max_wait: int = 180, output_dir: str = ".") -> dict:
    """Generate video using AGNES API.

    注意：实测该接口会拒绝 width/height/num_frames/frame_rate 等字段
    （返回 "xxx is a forbidden field"），因此默认全部省略，只发送 model + prompt。
    """
    # 创建任务：只传接口接受的字段，避免 forbidden field 报错
    data = {
        "model": model,
        "prompt": prompt,
    }
    result = make_request("POST", "https://api.agnes-ai.cn/v1/videos", data=data)

    if "error" in result:
        return result

    task_id = result.get("task_id") or result.get("id")
    video_id = result.get("video_id") or task_id

    print(f"Task submitted: {task_id}", file=sys.stderr)
    print(f"Waiting for video generation...", file=sys.stderr)

    # 轮询等待
    start_time = time.time()
    while time.time() - start_time < max_wait:
        time.sleep(5)
        status_result = make_request("GET", "https://api.agnes-ai.cn/agnesapi",
                                     params={"video_id": video_id})

        if "error" in status_result:
            return status_result

        status = status_result.get("status", "")
        progress = status_result.get("progress", 0)
        print(f"Status: {status}, Progress: {progress}%", file=sys.stderr)

        if status == "completed":
            metadata = status_result.get("metadata", {})
            video_url = metadata.get("url")
            if video_url:
                try:
                    output_path = Path(output_dir) / "agnes_video.mp4"
                    session = requests.Session()
                    session.trust_env = False
                    resp = session.get(video_url, timeout=120)
                    if resp.status_code == 200:
                        output_path.write_bytes(resp.content)
                        print(f"Video saved to: {output_path}", file=sys.stderr)
                        return {"status": "success", "video_url": video_url,
                                "task_id": task_id, "video_path": str(output_path)}
                except Exception as e:
                    return {"error": f"Download failed: {e}", "status_code": 0}
            break
        elif status == "failed":
            return {"error": "Video generation failed", "status": "failed"}

    return {"error": "Timeout waiting for video generation", "status": "timeout"}

def main():
    parser = argparse.ArgumentParser(description="AGNES Media Generation Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Image command
    img_parser = subparsers.add_parser("image", help="Generate image")
    img_parser.add_argument("prompt", help="Image description")
    img_parser.add_argument("--model", "-m", default="agnes-image-2.5-flash")
    img_parser.add_argument("--size", "-s", default="1024x1024")
    img_parser.add_argument("--n", "-n", type=int, default=1)
    img_parser.add_argument("--output-dir", "-o", default=".")

    # Video command
    vid_parser = subparsers.add_parser("video", help="Generate video")
    vid_parser.add_argument("prompt", help="Video description")
    vid_parser.add_argument("--model", "-m", default="agnes-video-v2.0")
    # 以下参数当前接口不接受（forbidden field），保留但不默认发送
    vid_parser.add_argument("--width", "-W", type=int, default=None)
    vid_parser.add_argument("--height", "-H", type=int, default=None)
    vid_parser.add_argument("--frames", "-f", type=int, default=None)
    vid_parser.add_argument("--fps", type=int, default=None)
    vid_parser.add_argument("--max-wait", type=int, default=180)
    vid_parser.add_argument("--output-dir", "-o", default=".")

    args = parser.parse_args()

    if args.command == "image":
        result = generate_image(
            prompt=args.prompt,
            model=args.model,
            size=args.size,
            n=args.n,
            output_dir=args.output_dir
        )
        print(json.dumps(result, indent=2))
    elif args.command == "video":
        result = generate_video(
            prompt=args.prompt,
            model=args.model,
            width=args.width,
            height=args.height,
            num_frames=args.frames,
            frame_rate=args.fps,
            max_wait=args.max_wait,
            output_dir=args.output_dir
        )
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()