import cv2
import mediapipe as mp
import json

mp_pose = mp.solutions.pose

def extract_pose(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"이미지를 읽을 수 없습니다: {image_path}")

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    pose = mp_pose.Pose(static_image_mode=True, model_complexity=1)
    results = pose.process(image_rgb)
    pose.close()

    if not results.pose_landmarks:
        raise RuntimeError(f"포즈를 찾지 못했습니다: {image_path}")

    landmarks = []
    for i, lm in enumerate(results.pose_landmarks.landmark):
        landmarks.append({
            "id": i,
            "x": lm.x,
            "y": lm.y,
            "z": lm.z,
            "visibility": lm.visibility
        })

    return landmarks

front = extract_pose("front.jpg")
side = extract_pose("side.jpg")

with open("front.json", "w", encoding="utf-8") as f:
    json.dump(front, f, indent=2, ensure_ascii=False)

with open("side.json", "w", encoding="utf-8") as f:
    json.dump(side, f, indent=2, ensure_ascii=False)

print("front.json / side.json 생성 완료")