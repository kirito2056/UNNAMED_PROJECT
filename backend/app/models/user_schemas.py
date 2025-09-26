"""
User-related Pydantic Schemas
사용자 관련 요청/응답 스키마 정의
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """사용자 기본 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    full_name: Optional[str] = Field(None, max_length=100, description="전체 이름")


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str = Field(..., min_length=8, description="패스워드")
    
    @validator('username')
    def validate_username(cls, v):
        """사용자명 검증"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('사용자명은 영문, 숫자, 언더스코어, 하이픈만 사용 가능합니다')
        return v.lower()
    
    @validator('email')
    def validate_email(cls, v):
        """이메일 검증"""
        return v.lower()


class UserUpdate(BaseModel):
    """사용자 정보 업데이트 스키마"""
    email: Optional[EmailStr] = Field(None, description="이메일 주소")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="사용자명")
    full_name: Optional[str] = Field(None, max_length=100, description="전체 이름")
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if not v.replace('_', '').replace('-', '').isalnum():
                raise ValueError('사용자명은 영문, 숫자, 언더스코어, 하이픈만 사용 가능합니다')
            return v.lower()
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v is not None:
            return v.lower()
        return v


class PasswordChange(BaseModel):
    """패스워드 변경 스키마"""
    old_password: str = Field(..., description="기존 패스워드")
    new_password: str = Field(..., min_length=8, description="새 패스워드")


class UserProfileBase(BaseModel):
    """사용자 프로필 기본 스키마"""
    bio: Optional[str] = Field(None, max_length=500, description="자기소개")
    avatar_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    timezone: Optional[str] = Field("UTC", description="시간대")
    language: Optional[str] = Field("ko", description="언어 설정")


class UserProfileUpdate(UserProfileBase):
    """사용자 프로필 업데이트 스키마"""
    preferences: Optional[Dict[str, Any]] = Field(None, description="사용자 선호도 설정")
    settings: Optional[Dict[str, Any]] = Field(None, description="앱 설정")


class UserProfileResponse(UserProfileBase):
    """사용자 프로필 응답 스키마"""
    id: UUID
    user_id: UUID
    preferences: Dict[str, Any]
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """사용자 정보 응답 스키마"""
    id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    profile: Optional[UserProfileResponse] = None
    
    class Config:
        from_attributes = True


class UserPublicResponse(BaseModel):
    """공개 사용자 정보 응답 스키마 (민감정보 제외)"""
    id: UUID
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# 인증 관련 스키마
class LoginRequest(BaseModel):
    """로그인 요청 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., description="패스워드")
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower()


class TokenResponse(BaseModel):
    """토큰 응답 스키마"""
    access_token: str = Field(..., description="액세스 토큰")
    refresh_token: str = Field(..., description="리프레시 토큰")
    token_type: str = Field("bearer", description="토큰 타입")
    expires_in: int = Field(..., description="토큰 만료 시간(초)")


class TokenRefreshRequest(BaseModel):
    """토큰 갱신 요청 스키마"""
    refresh_token: str = Field(..., description="리프레시 토큰")


class RegisterRequest(UserCreate):
    """회원가입 요청 스키마"""
    confirm_password: str = Field(..., description="패스워드 확인")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('패스워드가 일치하지 않습니다')
        return v


class RegisterResponse(BaseModel):
    """회원가입 응답 스키마"""
    user: UserResponse
    message: str = Field(default="회원가입이 완료되었습니다. 이메일 인증을 진행해주세요.")


# 이메일 인증 관련
class EmailVerificationRequest(BaseModel):
    """이메일 인증 요청 스키마"""
    token: str = Field(..., description="이메일 인증 토큰")


class PasswordResetRequest(BaseModel):
    """패스워드 재설정 요청 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower()


class PasswordResetConfirm(BaseModel):
    """패스워드 재설정 확인 스키마"""
    token: str = Field(..., description="패스워드 재설정 토큰")
    new_password: str = Field(..., min_length=8, description="새 패스워드")
    confirm_password: str = Field(..., description="패스워드 확인")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('패스워드가 일치하지 않습니다')
        return v
