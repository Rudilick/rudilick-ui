from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage
from google.oauth2 import service_account
from pydantic import BaseModel
from datetime import datetime
import os
import json
import librosa
from typing import List

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.rudilick.com", "https://rudilick.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GCS 설정 (🔧 키 JSON 직접 삽입)
credentials_info = {
  "type": "service_account",
  "project_id": "centered-sol-460814-n5",
  "private_key_id": "31dc31e91134129d17a20ce4b9ec03bf35340e30",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCb6BA/JpnyAi6o\n5N2gdR+daeaYE9EcROW9ZI7qQwVzDFd+I2TinExWBljTvophbm3lDxCR9Ih03gN9\nmpu/TDT8f/aK/tqT0FIyn2hMKjitp0HSopwxb/zHd7AEsFQUOgK7fX8Az9UoEXFa\n19Y4+BXVVbV/ZxdX/0hOtX3x66FO0tsIZynJor7SPNzGQrPy6XoKrOjxwMQsHa4d\nTrLYhprcCZPsIp/UVNHYhKkK1ksq7KUCeds4a1eDDGcEMPiK8ow/0vCqcHQbVzQ5\naupbwj43gfcQaYwzVlweyvjZEtm5R+FpiV4s4NMahXBCZRCoZ/RHkwoOZQB5RHJM\n4rWwFev7AgMBAAECggEAByjJcjTyFdBu1xena8JlIMPnsG0cialKSX+wJmbMfcN/\n0w2KCPP3d23UL2kNDrtU9ZNTBfjOOVummmJ6q3ay6jNwHWLlo6sJ00RJtFGuB59q\nIOORu51yZLCE1zpHqiQd0wFIzz88ARqH8418y2HtEr5cVszjoAlbhy3DalQRNL7c\nnNglv3pYVGV31YzJshndo3svjRXiUkJyTq/p5QKXA425JFKj8KIVgTgzzdAC3OMy\nYmK5C4aXk3OkGPSiXcmTp4z2odQOdyGAaU6bMKfIsdJJWLbYltSUFQXbmsIT0c/l\nWUoOZJf8YlVpDBrLQSX1cuZKR+ER4IM8WSkEoPp+xQKBgQDbmw0WM1FoHqpJdRY7\ntjSb8BwQ7V5G7EYuvk2WpONok2qhs7QsK4rsdGjFQTKcEM2SrwiV61lZCIx/mWQt\n8T17cSnswRSpj3RMcJjjA9n/cMsfyAq58L7ZGz8wIFZ/hoV9TevQq3+GG3YriIOW\njjmgL847a/izlUi7b/csAiOyLwKBgQC1voX2L9mriD/qjHPx7jrSrPnPXC0emn9H\n0B7gJy1LtKHHeM0FQ/xeqpv+fxi3kxPHCY4n4+torVlzbJvv8z3wQmwYDAGOTiH6\nDAT7dGflfh0dtzE+Z2kIIV22CkvvBu7dpgXIfAgHLJYa35PeOjtgpt5agfvd1SFI\nKTvbK8mr9QKBgQDPbN6pj4NfA0f45l0/vVRnzh3UZ0BbYSTRVfLXTZt21XcskR6n\nceFggnvLhU+WVdC2shk78faMwCRlCa+0LV7TUAo3lBA+MD+7S8c89hBc1F8n/70R\n8DFzw+alQIYzIg7IUmdgy/xB4YJ2kBUqieAoS79SJSPeDC2Mza77pHGvBQKBgFHT\nH3kBfhyuUSiGZ8Uqnq0vV6E2PNIkeN2aI+yDdu84ugWWq6eNPlhYs7bW/gfYXfUk\npi3rfZc5RKak5WgYuXAsV4JUFXc+UinDs5KKjCRUrUMtsSwJXs5cR1aoOBu7oVuF\nXeEvhmXEeyhKNMa+rPEM79sL3pu3Uy6r8djxU/DpAoGAFFOVSzwcENizdFjv92K3\n6Hx7JhLScNRMFae6isklTke7aDHoCyLmDGu1VayFvYHpSrWseljHdQGnKBAZHFFC\nLyICuaUaaK7Q2AveOeMY4PL3ANrZahpkXAe+Z9kmI5DjU0hjg+jHj+G6gsL3VE/z\nFjOA9o9whnMRs/4LOHhiiaw=\n-----END PRIVATE KEY-----\n",
  "client_email": "gcs-uploader@centered-sol-460814-n5.iam.gserviceaccount.com",
  "client_id": "111659134961989373118",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/gcs-uploader%40centered-sol-460814-n5.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
credentials = service_account.Credentials.from_service_account_info(credentials_info)
client = storage.Client(credentials=credentials)
bucket = client.bucket(GCS_BUCKET_NAME)

# 모델 정의
class FileRequest(BaseModel):
    filename: str

# 업로드
@app.post("/upload-wav/")
async def upload_wav(file: UploadFile = File(...)):
    print("📥 파일 업로드 요청 수신됨")
    blob_name = file.filename  # ⬅️ 파일명을 그대로 사용!
    blob = bucket.blob(blob_name)
    contents = await file.read()
    blob.upload_from_string(contents, content_type="audio/wav")
    return {
        "message": "파일이 GCS에 업로드되었습니다.",
        "filename": blob_name,
        "url": f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{blob_name}"
    }

# 전사
@app.post("/transcribe-beat/")
async def transcribe_beat(request: FileRequest):
    try:
        blob = bucket.blob(request.filename)
        local_path = f"temp/{request.filename}"
        os.makedirs("temp", exist_ok=True)
        blob.download_to_filename(local_path)

        # 전사 함수
        def transcribe_with_beat_quantization(wav_path: str, divisions: List[int] = [3, 4, 6]) -> dict:
            y, sr = librosa.load(wav_path, sr=None)
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            grid_times = []
            for i in range(len(beat_times) - 1):
                start = beat_times[i]
                end = beat_times[i + 1]
                for div in divisions:
                    interval = (end - start) / div
                    grid_times.extend([round(start + interval * j, 3) for j in range(div)])
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
            onset_times = librosa.frames_to_time(onset_frames, sr=sr)
            result = []
            for onset in onset_times:
                closest = min(grid_times, key=lambda g: abs(g - onset))
                result.append({
                    "quantized_time": round(closest, 3),
                    "raw_time": round(float(onset), 3)
                })
            return {
                "tempo": round(float(tempo), 2),
                "beats": len(beat_times),
                "notes": result
            }

        return transcribe_with_beat_quantization(local_path)

    except Exception as e:
        return {"error": str(e)}