from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Create FastAPI app instance
# FastAPI 앱 인스턴스 생성
app = FastAPI(
    version="0.1.0",
)

# Add CORS middleware
# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

class HealthCheckResponse(BaseModel):
    """Health check response model. / 상태 확인 응답 모델"""
    status: str = "ok"


@app.get("/", tags=["Root"], summary="Welcome message")
def read_root():
    """
    Root endpoint that returns a welcome message.
    시작을 알리는 루트 엔드포인트입니다.
    """
    return {"message": "Welcome to your personalized AI assistant!"}


@app.get(
    "/health",
    tags=["Health Check"],
    summary="Perform a Health Check",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
)
def perform_health_check():
    """
    Performs a health check and returns the status of the API.
    API의 상태를 확인하고 상태를 반환합니다.
    """
    return HealthCheckResponse(status="ok")