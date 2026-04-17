import json
import traceback
import sys
import os
import mediapipe as mp

print("[DEBUG] PYTHON =", sys.executable)
print("[DEBUG] MEDIAPIPE =", mp.__file__)
p = os.path.join(
    os.path.dirname(mp.__file__),
    "modules",
    "pose_landmark",
    "pose_landmark_cpu.binarypb",
)
print("[DEBUG] BINARYPB =", p)
print("[DEBUG] EXISTS =", os.path.exists(p))
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from analyzer import run_analysis

app = FastAPI(
    title="PCRS Body Analysis API",
    description="정면(front) / 측면(side) 이미지를 업로드하면 체형 분석 결과를 반환합니다.",
    version="0.1.0",
)

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
JSON_DIR = BASE_DIR / "data" / "json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
def root():
    return {"message": "PCRS FastAPI server is running"}


@app.post("/upload-image", summary="이미지 업로드", description="정면(front) 또는 측면(side) 이미지를 업로드합니다.")
async def upload_image(
    session_id: str = Form(...),
    image_type: str = Form(...),
    file: UploadFile = File(...),
):
    try:
        print(f"[DEBUG] upload start: session_id={session_id}, image_type={image_type}, filename={file.filename}")

        if image_type not in {"front", "side"}:
            raise HTTPException(status_code=400, detail="image_type은 front 또는 side 여야 합니다.")

        session_upload_dir = UPLOAD_DIR / session_id
        session_upload_dir.mkdir(parents=True, exist_ok=True)

        save_path = session_upload_dir / f"{image_type}.jpg"

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="업로드된 파일이 비어 있습니다.")

        save_path.write_bytes(content)
        print(f"[DEBUG] saved file: {save_path}, size={save_path.stat().st_size}")

        front_path = session_upload_dir / "front.jpg"
        side_path = session_upload_dir / "side.jpg"

        print(f"[DEBUG] front exists: {front_path.exists()}")
        print(f"[DEBUG] side exists: {side_path.exists()}")

        if front_path.exists() and side_path.exists():
            session_json_dir = JSON_DIR / session_id
            session_json_dir.mkdir(parents=True, exist_ok=True)

            try:
                result = run_analysis(front_path, side_path, session_json_dir)
            except Exception as e:
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")

            return JSONResponse(
                {
                    "status": "analysis_complete",
                    "session_id": session_id,
                    "result": result,
                }
            )

        return JSONResponse(
            {
                "status": "uploaded",
                "session_id": session_id,
                "message": f"{image_type}.jpg 업로드 완료. 나머지 이미지 업로드 대기 중",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@app.get("/result/{session_id}", summary="분석 결과 조회")
def get_result(session_id: str):
    result_path = JSON_DIR / session_id / "body_result.json"

    if not result_path.exists():
        raise HTTPException(status_code=404, detail="분석 결과가 없습니다.")

    try:
        with result_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"결과 파일 읽기 실패: {str(e)}")

    return JSONResponse(
        {
            "status": "success",
            "session_id": session_id,
            "result": data,
        }
    )