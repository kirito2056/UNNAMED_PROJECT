"""
Application Configuration
애플리케이션 설정 관리
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # API Configuration / API 설정
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Database Configuration / 데이터베이스 설정
    POSTGRES_DB: str = "friend_ai"
    POSTGRES_USER: str = "friend_ai_user"
    POSTGRES_PASSWORD: str = "friend_ai_password"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """데이터베이스 URL 자동 생성"""
        if isinstance(v, str):
            return v
        return (
            f"postgresql+asyncpg://"
            f"{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_HOST')}:"
            f"{values.get('POSTGRES_PORT')}/"
            f"{values.get('POSTGRES_DB')}"
        )
    
    # JWT Configuration / JWT 설정
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security Configuration / 보안 설정
    PASSWORD_MIN_LENGTH: int = 8
    BCRYPT_ROUNDS: int = 12
    
    # CORS Configuration / CORS 설정
    ALLOWED_ORIGINS: List[str] = ["*"]  # 개발용, 프로덕션에서는 특정 도메인만 허용
    
    # Milvus Configuration (향후 사용) / Milvus 설정
    MILVUS_HOST: str = "milvus"
    MILVUS_PORT: int = 19530
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 전역 설정 인스턴스
settings = Settings()


def get_settings() -> Settings:
    """설정 인스턴스 반환 (의존성 주입용)"""
    return settings
