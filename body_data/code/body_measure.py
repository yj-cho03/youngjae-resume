import json
import math

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_point(data, idx):
    for item in data:
        if item["id"] == idx:
            return item
    raise ValueError(f"id {idx} 좌표를 찾을 수 없습니다.")

def distance_2d(p1, p2):
    return math.sqrt((p1["x"] - p2["x"]) ** 2 + (p1["y"] - p2["y"]) ** 2)

def midpoint(p1, p2):
    return {
        "x": (p1["x"] + p2["x"]) / 2,
        "y": (p1["y"] + p2["y"]) / 2
    }

front = load_json("front.json")
side = load_json("side.json")

# front 좌표
p11 = get_point(front, 11)  # right shoulder
p12 = get_point(front, 12)  # left shoulder
p13 = get_point(front, 13)  # right elbow
p14 = get_point(front, 14)  # left elbow
p15 = get_point(front, 15)  # right wrist
p16 = get_point(front, 16)  # left wrist
p23 = get_point(front, 23)  # right hip
p24 = get_point(front, 24)  # left hip
p25 = get_point(front, 25)  # right knee
p26 = get_point(front, 26)  # left knee
p27 = get_point(front, 27)  # right ankle
p28 = get_point(front, 28)  # left ankle

# 1. 어깨 넓이
shoulder_width = distance_2d(p11, p12)

# 2. 허리 넓이 (골반 기준)
waist_width = distance_2d(p23, p24)

# 3. 팔 길이 (양팔 평균)
right_arm_length = distance_2d(p11, p13) + distance_2d(p13, p15)
left_arm_length = distance_2d(p12, p14) + distance_2d(p14, p16)
arm_length = (right_arm_length + left_arm_length) / 2

# 4. 상체 길이 (어깨 중심 ~ 골반 중심)
shoulder_center = midpoint(p11, p12)
hip_center = midpoint(p23, p24)
upper_body_length = distance_2d(shoulder_center, hip_center)

# 5. 하체 길이 (골반 중심 ~ 발목 중심)
ankle_center = midpoint(p27, p28)
lower_body_length = distance_2d(hip_center, ankle_center)

# 참고용: 다리 길이 평균
right_leg_length = distance_2d(p23, p25) + distance_2d(p25, p27)
left_leg_length = distance_2d(p24, p26) + distance_2d(p26, p28)
leg_length_avg = (right_leg_length + left_leg_length) / 2

# 6. 비율 계산
upper_lower_ratio = upper_body_length / lower_body_length if lower_body_length != 0 else 0
shoulder_waist_ratio = shoulder_width / waist_width if waist_width != 0 else 0

# 결과 데이터 생성
result = {
    "shoulder_width": shoulder_width,
    "waist_width": waist_width,
    "arm_length": arm_length,
    "upper_body_length": upper_body_length,
    "lower_body_length": lower_body_length,
    "leg_length_avg": leg_length_avg,
    "upper_lower_ratio": upper_lower_ratio,
    "shoulder_waist_ratio": shoulder_waist_ratio,
    "source_files": {
        "front": "front.json",
        "side": "side.json"
    }
}

# 결과 출력
print("=== 체형 분석 결과 ===")
print(f"어깨 넓이: {shoulder_width:.4f}")
print(f"허리 넓이: {waist_width:.4f}")
print(f"팔 길이: {arm_length:.4f}")
print(f"상체 길이: {upper_body_length:.4f}")
print(f"하체 길이: {lower_body_length:.4f}")
print(f"다리 길이 평균: {leg_length_avg:.4f}")
print(f"상하체 비율: {upper_lower_ratio:.4f}")
print(f"어깨/허리 비율: {shoulder_waist_ratio:.4f}")

# 결과 JSON 저장
with open("body_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("body_result.json 생성 완료")