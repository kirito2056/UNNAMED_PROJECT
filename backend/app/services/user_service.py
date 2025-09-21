"""
User Service
사용자 관리를 위한 비즈니스 로직
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.database.postgres.models import User, UserProfile
from app.core.security import get_password_hash, verify_password, validate_password_strength
from app.models.user_schemas import UserCreate, UserUpdate, UserProfileUpdate


class UserService:
    """사용자 관리 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        새 사용자 생성
        
        Args:
            user_data: 사용자 생성 데이터
            
        Returns:
            User: 생성된 사용자 객체
            
        Raises:
            ValueError: 이메일 중복, 패스워드 강도 부족 등
        """
        # 이메일 중복 확인
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("이미 등록된 이메일입니다")
        
        # 사용자명 중복 확인
        existing_username = await self.get_user_by_username(user_data.username)
        if existing_username:
            raise ValueError("이미 사용 중인 사용자명입니다")
        
        # 패스워드 강도 검증
        if not validate_password_strength(user_data.password):
            raise ValueError(
                f"패스워드는 최소 8자 이상이고, 대문자, 소문자, 숫자를 포함해야 합니다"
            )
        
        # 패스워드 해싱
        hashed_password = get_password_hash(user_data.password)
        
        # 사용자 생성
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=True,
            is_verified=False  # 이메일 인증 필요
        )
        
        self.db.add(db_user)
        await self.db.flush()  # ID 생성을 위해 flush
        
        # 기본 프로필 생성
        db_profile = UserProfile(
            user_id=db_user.id,
            preferences={},
            settings={
                "theme": "light",
                "language": "ko",
                "notifications": True
            },
            timezone="Asia/Seoul",
            language="ko"
        )
        
        self.db.add(db_profile)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        return db_user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        사용자 인증 (로그인)
        
        Args:
            email: 이메일
            password: 패스워드
            
        Returns:
            Optional[User]: 인증된 사용자 또는 None
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # 마지막 로그인 시간 업데이트
        await self.update_last_login(user.id)
        
        return user
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """ID로 사용자 조회"""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """사용자명으로 사용자 조회"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """
        사용자 정보 업데이트
        
        Args:
            user_id: 사용자 ID
            user_data: 업데이트할 데이터
            
        Returns:
            Optional[User]: 업데이트된 사용자 또는 None
        """
        # 기존 사용자 조회
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        update_data = {}
        
        # 이메일 변경 시 중복 확인
        if user_data.email and user_data.email != user.email:
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                raise ValueError("이미 등록된 이메일입니다")
            update_data["email"] = user_data.email
            update_data["is_verified"] = False  # 이메일 변경 시 재인증 필요
        
        # 사용자명 변경 시 중복 확인
        if user_data.username and user_data.username != user.username:
            existing_username = await self.get_user_by_username(user_data.username)
            if existing_username:
                raise ValueError("이미 사용 중인 사용자명입니다")
            update_data["username"] = user_data.username
        
        if user_data.full_name is not None:
            update_data["full_name"] = user_data.full_name
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await self.db.execute(
                update(User).where(User.id == user_id).values(**update_data)
            )
            await self.db.commit()
            
            # 업데이트된 사용자 정보 반환
            return await self.get_user_by_id(user_id)
        
        return user
    
    async def update_password(self, user_id: UUID, old_password: str, new_password: str) -> bool:
        """
        패스워드 변경
        
        Args:
            user_id: 사용자 ID
            old_password: 기존 패스워드
            new_password: 새 패스워드
            
        Returns:
            bool: 변경 성공 여부
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # 기존 패스워드 확인
        if not verify_password(old_password, user.hashed_password):
            raise ValueError("기존 패스워드가 일치하지 않습니다")
        
        # 새 패스워드 강도 검증
        if not validate_password_strength(new_password):
            raise ValueError(
                "패스워드는 최소 8자 이상이고, 대문자, 소문자, 숫자를 포함해야 합니다"
            )
        
        # 패스워드 해싱 및 업데이트
        hashed_password = get_password_hash(new_password)
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(hashed_password=hashed_password, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        
        return True
    
    async def update_last_login(self, user_id: UUID) -> None:
        """마지막 로그인 시간 업데이트"""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.utcnow())
        )
        await self.db.commit()
    
    async def deactivate_user(self, user_id: UUID) -> bool:
        """사용자 비활성화"""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        return True
    
    async def activate_user(self, user_id: UUID) -> bool:
        """사용자 활성화"""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=True, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        return True
    
    async def verify_email(self, user_id: UUID) -> bool:
        """이메일 인증 완료 처리"""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_verified=True, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        return True
    
    async def update_profile(self, user_id: UUID, profile_data: UserProfileUpdate) -> Optional[UserProfile]:
        """
        사용자 프로필 업데이트
        
        Args:
            user_id: 사용자 ID
            profile_data: 프로필 업데이트 데이터
            
        Returns:
            Optional[UserProfile]: 업데이트된 프로필 또는 None
        """
        # 기존 프로필 조회
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            return None
        
        update_data = {}
        
        if profile_data.bio is not None:
            update_data["bio"] = profile_data.bio
        
        if profile_data.avatar_url is not None:
            update_data["avatar_url"] = profile_data.avatar_url
        
        if profile_data.timezone is not None:
            update_data["timezone"] = profile_data.timezone
        
        if profile_data.language is not None:
            update_data["language"] = profile_data.language
        
        if profile_data.preferences is not None:
            update_data["preferences"] = profile_data.preferences
        
        if profile_data.settings is not None:
            update_data["settings"] = profile_data.settings
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await self.db.execute(
                update(UserProfile)
                .where(UserProfile.user_id == user_id)
                .values(**update_data)
            )
            await self.db.commit()
        
        # 업데이트된 프로필 반환
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()


def get_user_service(db: AsyncSession = None) -> UserService:
    """UserService 인스턴스 반환 (의존성 주입용)"""
    return UserService(db)
