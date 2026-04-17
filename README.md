# 개인 이력서 - 조영재

## 프로젝트명
AI 기반 체형 분석 의류 추천 시스템

## 프로젝트 설명
사용자의 전신 이미지를 촬영하고 MediaPipe를 활용하여 신체 관절 좌표를 추출한 뒤,
신체 길이 및 비율을 계산하여 체형을 분석하는 시스템을 구현하였다.

## 담당 역할
- Raspberry Pi 카메라 촬영 기능 구현
- OpenCV + MediaPipe Pose 기반 관절 좌표 추출
- JSON 데이터 생성 (front.json, side.json)
- 신체 길이 및 비율 계산
- body_result.json 생성
- 전체 데이터 처리 자동화

## 폴더 구조 설명
- backend: 서버 및 분석 코드
- raspberry_pi: 촬영 및 전송 코드
- body_data: 좌표 추출 및 비율 계산 코드

## 사용 기술
- Python
- OpenCV
- MediaPipe
- Raspberry Pi
- JSON
