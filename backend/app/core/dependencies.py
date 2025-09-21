"""
Authentication Dependencies
FastAPI 의존성 주입을 위한 인증 관련 함수들
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, WebSocket, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import verify_token, credentials_exception, inactive_user_exception
from app.database.postgres.connection import get_db
from app.database.postgres.models import User


# HTTP Bearer 토큰 스키마
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    현재 인증된 사용자 정보 반환
    JWT 토큰을 검증하고 사용자 정보를 데이터베이스에서 조회
    
    Args:
        credentials: HTTP Bearer 토큰
        db: 데이터베이스 세션
        
    Returns:
        User: 현재 사용자 객체
        
    Raises:
        HTTPException: 토큰이 유효하지 않거나 사용자를 찾을 수 없는 경우
    """
    # JWT 토큰 검증
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    # 토큰에서 사용자 ID 추출
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # 데이터베이스에서 사용자 조회
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    현재 활성화된 사용자 정보 반환
    비활성화된 사용자의 경우 예외 발생
    
    Args:
        current_user: 현재 사용자 (get_current_user에서 주입)
        
    Returns:
        User: 활성화된 사용자 객체
        
    Raises:
        HTTPException: 사용자가 비활성화된 경우
    """
    if not current_user.is_active:
        raise inactive_user_exception
    
    return current_user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    선택적 사용자 인증 (토큰이 없어도 None 반환)
    공개 API에서 사용자가 로그인했으면 추가 정보 제공하는 경우 사용
    
    Args:
        credentials: HTTP Bearer 토큰 (선택적)
        db: 데이터베이스 세션
        
    Returns:
        Optional[User]: 사용자 객체 또는 None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_current_user_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    WebSocket 연결을 위한 사용자 인증
    쿼리 파라미터로 토큰을 받아서 인증
    
    Args:
        websocket: WebSocket 연결 객체
        token: JWT 토큰 (쿼리 파라미터)
        db: 데이터베이스 세션
        
    Returns:
        Optional[User]: 인증된 사용자 또는 None
    """
    if not token:
        return None
    
    # JWT 토큰 검증
    payload = verify_token(token)
    if payload is None:
        return None
    
    # 토큰에서 사용자 ID 추출
    user_id: str = payload.get("sub")
    if user_id is None:
        return None
    
    # 데이터베이스에서 사용자 조회
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user and user.is_active:
            return user
    except Exception:
        pass
    
    return None


# 타입 별칭 정의 (편의성을 위해)
CurrentUser = Annotated[User, Depends(get_current_active_user)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]
