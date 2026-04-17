import argparse
import pathlib
import subprocess
import sys
import time

import requests


def capture_image(output_path: pathlib.Path) -> None:
    cmd = [
        "rpicam-still",
        "-o",
        str(output_path),
        "--nopreview",
        "-t",
        "1000",
        "--width",
        "1280",
        "--height",
        "720",
    ]
    subprocess.run(cmd, check=True)


def send_image(server_url: str, session_id: str, image_type: str, image_path: pathlib.Path) -> None:
    with image_path.open("rb") as f:
        files = {"file": (image_path.name, f, "image/jpeg")}
        data = {
            "session_id": session_id,
            "image_type": image_type,
        }
        response = requests.post(
            f"{server_url}/upload-image",
            data=data,
            files=files,
            timeout=60,
        )
        response.raise_for_status()
        print(f"[서버 응답 - {image_type}] {response.json()}")


def capture_and_send(
    server_url: str,
    session_id: str,
    image_type: str,
    output_dir: pathlib.Path,
) -> None:
    output_path = output_dir / f"{image_type}.jpg"

    print(f"\n[1] {image_type} 사진 촬영 중...")
    capture_image(output_path)
    print(f"[2] {image_type} 사진 저장 완료: {output_path}")

    print(f"[3] {image_type} 서버로 전송 중...")
    send_image(server_url, session_id, image_type, output_path)
    print(f"[완료] {image_type} 전송 완료")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", required=True, help="예: http://192.168.0.10:8000")
    parser.add_argument("--session", required=True, help="예: test200")
    parser.add_argument("--output-dir", default="captures", help="사진 저장 폴더")
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="front 촬영 후 side 촬영까지 대기 시간(초)",
    )
    args = parser.parse_args()

    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("===================================")
    print("PCRS 라즈베리파이 자동 촬영/전송 시작")
    print(f"서버 주소: {args.server}")
    print(f"세션 ID : {args.session}")
    print("===================================")

    # 1) 정면 촬영 및 전송
    print("\n정면(front) 촬영을 시작합니다.")
    print("카메라 앞에서 정면 자세를 잡아주세요.")
    time.sleep(2)
    capture_and_send(args.server, args.session, "front", output_dir)

    # 2) 측면 촬영 안내
    print(f"\n{args.delay}초 후 측면(side) 촬영을 시작합니다.")
    print("옆으로 돌아서 측면 자세를 잡아주세요.")
    for i in range(args.delay, 0, -1):
        print(f"{i}...")
        time.sleep(1)

    # 3) 측면 촬영 및 전송
    capture_and_send(args.server, args.session, "side", output_dir)

    print("\n===================================")
    print("front / side 촬영 및 전송이 모두 완료되었습니다.")
    print("서버에서 자동 분석이 실행됩니다.")
    print("===================================")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)