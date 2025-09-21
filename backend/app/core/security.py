"""
Security utilities for authentication and authorization
인증 및 권한 관리를 위한 보안 유틸리티
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings


# 패스워드 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰 생성
    
    Args:
        data: 토큰에 포함할 데이터 (주로 user_id, email 등)
        expires_delta: 토큰 만료 시간 (기본값: 30분)
        
    Returns:
        str: JWT 토큰 문자열
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 리프레시 토큰 생성
    
    Args:
        data: 토큰에 포함할 데이터
        expires_delta: 토큰 만료 시간 (기본값: 7일)
        
    Returns:
        str: JWT 리프레시 토큰 문자열
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    JWT 토큰 검증 및 디코딩
    
    Args:
        token: JWT 토큰 문자열
        token_type: 토큰 타입 ("access" 또는 "refresh")
        
    Returns:
        dict: 토큰 페이로드 (검증 실패 시 None)
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # 토큰 타입 확인
        if payload.get("type") != token_type:
            return None
            
        return payload
    except JWTError:
        return None


def get_password_hash(password: str) -> str:
    """
    패스워드 해싱
    
    Args:
        password: 평문 패스워드
        
    Returns:
        str: 해싱된 패스워드
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    패스워드 검증
    
    Args:
        plain_password: 평문 패스워드
        hashed_password: 해싱된 패스워드
        
    Returns:
        bool: 패스워드 일치 여부
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> bool:
    """
    패스워드 강도 검증
    
    Args:
        password: 검증할 패스워드
        
    Returns:
        bool: 패스워드 강도 충족 여부
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False
    
    # 추가 검증 로직 (대소문자, 숫자, 특수문자 등)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    return has_upper and has_lower and has_digit


# 예외 정의
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="인증 정보를 확인할 수 없습니다",
    headers={"WWW-Authenticate": "Bearer"},
)

inactive_user_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="비활성화된 사용자입니다"
)

invalid_token_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="유효하지 않은 토큰입니다",
    headers={"WWW-Authenticate": "Bearer"},
)
