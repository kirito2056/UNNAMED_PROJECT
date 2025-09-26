from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Import routers
from app.api.endpoints import communication, auth
from app.database.postgres.connection import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 데이터베이스 초기화
    await init_db()
    yield
    # 종료 시 데이터베이스 연결 해제
    await close_db()

# Create FastAPI app instance
# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="Friend-like AI Assistant",
    description="A personalized AI assistant with real-time communication and user authentication",
    version="0.1.0",
    lifespan=lifespan
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

# Include routers
# 라우터 포함
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    communication.router,
    prefix="/api",
    tags=["Real-time Communication"]
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