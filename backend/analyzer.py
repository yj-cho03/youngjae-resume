import json
import math
from pathlib import Path
from typing import Any

import cv2
import mediapipe as mp
import numpy as np

import os
import sys
import mediapipe as mp

print("[ANALYZER DEBUG] PYTHON =", sys.executable)
print("[ANALYZER DEBUG] MEDIAPIPE =", mp.__file__)
_analyzer_p = os.path.join(
    os.path.dirname(mp.__file__),
    "modules",
    "pose_landmark",
    "pose_landmark_cpu.binarypb",
)
print("[ANALYZER DEBUG] BINARYPB =", _analyzer_p)
print("[ANALYZER DEBUG] EXISTS =", os.path.exists(_analyzer_p))

mp_pose = mp.solutions.pose

POSE_INDEX = {
    "LEFT_SHOULDER": 11,
    "RIGHT_SHOULDER": 12,
    "LEFT_ELBOW": 13,
    "RIGHT_ELBOW": 14,
    "LEFT_WRIST": 15,
    "RIGHT_WRIST": 16,
    "LEFT_HIP": 23,
    "RIGHT_HIP": 24,
    "LEFT_KNEE": 25,
    "RIGHT_KNEE": 26,
    "LEFT_ANKLE": 27,
    "RIGHT_ANKLE": 28,
}


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_pose(image_path: str) -> list[dict[str, float | int]]:
    p = Path(image_path)
    print(f"[DEBUG] file exists: {p.exists()}, path: {p}")

    if not p.exists():
        raise FileNotFoundError(f"이미지 파일이 존재하지 않습니다: {image_path}")

    file_size = p.stat().st_size
    print(f"[DEBUG] file size: {file_size}")

    if file_size == 0:
        raise ValueError(f"이미지 파일 크기가 0입니다: {image_path}")

    # Windows / OneDrive / 한글 경로 대응
    file_bytes = np.fromfile(str(p), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    print(f"[DEBUG] cv2.imdecode is None: {image is None}")

    if image is None:
        raise FileNotFoundError(f"이미지를 읽을 수 없습니다: {image_path}")

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        enable_segmentation=False,
        min_detection_confidence=0.5,
    ) as pose:
        result = pose.process(image_rgb)

    if not result.pose_landmarks:
        raise ValueError(f"포즈를 인식하지 못했습니다: {image_path}")

    landmarks: list[dict[str, float | int]] = []
    for idx, lm in enumerate(result.pose_landmarks.landmark):
        landmarks.append(
            {
                "id": idx,
                "x": float(lm.x),
                "y": float(lm.y),
                "z": float(lm.z),
                "visibility": float(lm.visibility),
            }
        )

    return landmarks


def get_lm(landmarks: list[dict[str, Any]], idx: int) -> dict[str, float]:
    lm = landmarks[idx]
    return {
        "x": float(lm["x"]),
        "y": float(lm["y"]),
        "z": float(lm["z"]),
        "visibility": float(lm["visibility"]),
    }


def distance(p1: dict[str, float], p2: dict[str, float]) -> float:
    return math.sqrt(
        (p1["x"] - p2["x"]) ** 2
        + (p1["y"] - p2["y"]) ** 2
        + (p1["z"] - p2["z"]) ** 2
    )


def midpoint(p1: dict[str, float], p2: dict[str, float]) -> dict[str, float]:
    return {
        "x": (p1["x"] + p2["x"]) / 2,
        "y": (p1["y"] + p2["y"]) / 2,
        "z": (p1["z"] + p2["z"]) / 2,
        "visibility": (p1["visibility"] + p2["visibility"]) / 2,
    }


def calculate_body(front_landmarks: list[dict[str, Any]]) -> dict[str, Any]:
    ls = get_lm(front_landmarks, POSE_INDEX["LEFT_SHOULDER"])
    rs = get_lm(front_landmarks, POSE_INDEX["RIGHT_SHOULDER"])
    lh = get_lm(front_landmarks, POSE_INDEX["LEFT_HIP"])
    rh = get_lm(front_landmarks, POSE_INDEX["RIGHT_HIP"])
    le = get_lm(front_landmarks, POSE_INDEX["LEFT_ELBOW"])
    lw = get_lm(front_landmarks, POSE_INDEX["LEFT_WRIST"])
    lk = get_lm(front_landmarks, POSE_INDEX["LEFT_KNEE"])
    la = get_lm(front_landmarks, POSE_INDEX["LEFT_ANKLE"])

    shoulder_center = midpoint(ls, rs)
    hip_center = midpoint(lh, rh)

    # 허리 landmark가 따로 없으므로 중간점으로 근사
    left_waist = midpoint(ls, lh)
    right_waist = midpoint(rs, rh)

    shoulder_width = distance(ls, rs)
    waist_width = distance(left_waist, right_waist)
    hip_width = distance(lh, rh)
    arm_length = distance(ls, le) + distance(le, lw)
    upper_body_length = distance(shoulder_center, hip_center)
    lower_body_length = distance(hip_center, midpoint(lk, la))

    upper_lower_ratio = upper_body_length / lower_body_length if lower_body_length > 0 else 0.0
    shoulder_waist_ratio = shoulder_width / waist_width if waist_width > 0 else 0.0

    if shoulder_waist_ratio >= 1.15:
        body_type = "상체형"
    elif shoulder_waist_ratio <= 0.95:
        body_type = "하체형"
    else:
        body_type = "균형형"

    return {
        "lengths": {
            "shoulder_width": shoulder_width,
            "waist_width": waist_width,
            "hip_width": hip_width,
            "arm_length": arm_length,
            "upper_body_length": upper_body_length,
            "lower_body_length": lower_body_length,
        },
        "ratios": {
            "upper_lower_ratio": upper_lower_ratio,
            "shoulder_waist_ratio": shoulder_waist_ratio,
        },
        "body_type": body_type,
    }


def run_analysis(front_path: Path, side_path: Path, json_dir: Path) -> dict[str, Any]:
    print("[DEBUG] run_analysis start")
    print(f"[DEBUG] front_path: {front_path}")
    print(f"[DEBUG] side_path: {side_path}")
    print(f"[DEBUG] json_dir: {json_dir}")

    json_dir.mkdir(parents=True, exist_ok=True)

    front_landmarks = extract_pose(str(front_path))
    side_landmarks = extract_pose(str(side_path))

    front_json = json_dir / "front.json"
    side_json = json_dir / "side.json"
    result_json = json_dir / "body_result.json"

    save_json(front_json, front_landmarks)
    save_json(side_json, side_landmarks)

    result = calculate_body(front_landmarks)
    result["paths"] = {
        "front_json_path": str(front_json),
        "side_json_path": str(side_json),
        "result_json_path": str(result_json),
    }

    save_json(result_json, result)

    print("[DEBUG] run_analysis complete")
    return result