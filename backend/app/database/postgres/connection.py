"""
PostgreSQL Database Connection
PostgreSQL 데이터베이스 연결 관리
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy 비동기 엔진 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 개발 모드에서 SQL 쿼리 로깅
    pool_pre_ping=True,   # 연결 상태 확인
    pool_recycle=300,     # 5분마다 연결 재생성
)

# 비동기 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 베이스 클래스"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    데이터베이스 세션 의존성
    FastAPI 의존성 주입에서 사용
    
    Yields:
        AsyncSession: 비동기 데이터베이스 세션
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    데이터베이스 초기화
    테이블 생성 및 초기 데이터 설정
    """
    try:
        async with engine.begin() as conn:
            # 모든 테이블 생성 (실제로는 Alembic 마이그레이션 사용 권장)
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_db() -> None:
    """
    데이터베이스 연결 종료
    애플리케이션 종료 시 호출
    """
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# 데이터베이스 상태 확인
async def check_db_health() -> bool:
    """
    데이터베이스 연결 상태 확인
    
    Returns:
        bool: 연결 상태 (True: 정상, False: 오류)
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
