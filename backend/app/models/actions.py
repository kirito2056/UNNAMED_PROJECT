"""
Action Block Models
AI 어시스턴트의 응답을 위한 액션 블록 데이터 모델 정의
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from enum import Enum


class ActionType(str, Enum):
    """액션 블록 타입 정의"""
    TEXT = "text"
    MUSIC = "music"
    SCHEDULE = "schedule"
    REMINDER = "reminder"
    SEARCH = "search"
    WEATHER = "weather"
    NEWS = "news"
    CALL = "call"
    MESSAGE = "message"
    EMAIL = "email"
    NOTE = "note"
    TIMER = "timer"
    ALARM = "alarm"
    CALCULATE = "calculate"


class BaseAction(BaseModel):
    """기본 액션 블록 모델"""
    type: ActionType
    title: str = Field(..., description="액션 제목")
    description: Optional[str] = Field(None, description="액션 설명")
    timestamp: datetime = Field(default_factory=datetime.now, description="생성 시간")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")


class TextAction(BaseAction):
    """텍스트 응답 액션"""
    type: Literal[ActionType.TEXT] = ActionType.TEXT
    content: str = Field(..., description="텍스트 내용")
    is_streaming: bool = Field(False, description="스트리밍 응답 여부")


class MusicAction(BaseAction):
    """음악 재생 액션"""
    type: Literal[ActionType.MUSIC] = ActionType.MUSIC
    song_title: str = Field(..., description="곡 제목")
    artist: Optional[str] = Field(None, description="아티스트")
    album: Optional[str] = Field(None, description="앨범")
    duration: Optional[int] = Field(None, description="재생 시간(초)")
    url: Optional[str] = Field(None, description="음악 스트리밍 URL")
    thumbnail: Optional[str] = Field(None, description="앨범 커버 이미지 URL")


class ScheduleAction(BaseAction):
    """일정 관리 액션"""
    type: Literal[ActionType.SCHEDULE] = ActionType.SCHEDULE
    event_title: str = Field(..., description="일정 제목")
    start_time: datetime = Field(..., description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")
    location: Optional[str] = Field(None, description="장소")
    attendees: List[str] = Field(default_factory=list, description="참석자 목록")
    reminder_minutes: Optional[int] = Field(None, description="알림 시간(분 전)")


class ReminderAction(BaseAction):
    """리마인더 액션"""
    type: Literal[ActionType.REMINDER] = ActionType.REMINDER
    reminder_text: str = Field(..., description="리마인더 내용")
    remind_at: datetime = Field(..., description="알림 시간")
    is_recurring: bool = Field(False, description="반복 여부")
    recurrence_pattern: Optional[str] = Field(None, description="반복 패턴")


class SearchAction(BaseAction):
    """검색 액션"""
    type: Literal[ActionType.SEARCH] = ActionType.SEARCH
    query: str = Field(..., description="검색 쿼리")
    search_type: str = Field("web", description="검색 타입 (web, images, videos 등)")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="검색 결과")


class WeatherAction(BaseAction):
    """날씨 정보 액션"""
    type: Literal[ActionType.WEATHER] = ActionType.WEATHER
    location: str = Field(..., description="위치")
    current_temp: Optional[float] = Field(None, description="현재 온도")
    condition: Optional[str] = Field(None, description="날씨 상태")
    humidity: Optional[int] = Field(None, description="습도 (%)")
    wind_speed: Optional[float] = Field(None, description="풍속")
    forecast: List[Dict[str, Any]] = Field(default_factory=list, description="예보 정보")


class TimerAction(BaseAction):
    """타이머 액션"""
    type: Literal[ActionType.TIMER] = ActionType.TIMER
    duration_seconds: int = Field(..., description="타이머 시간(초)")
    timer_name: Optional[str] = Field(None, description="타이머 이름")
    is_active: bool = Field(True, description="타이머 활성 여부")


class CalculateAction(BaseAction):
    """계산 액션"""
    type: Literal[ActionType.CALCULATE] = ActionType.CALCULATE
    expression: str = Field(..., description="계산식")
    result: str = Field(..., description="계산 결과")


# 메시지 모델들
class UserMessage(BaseModel):
    """사용자 메시지 모델"""
    content: str = Field(..., description="메시지 내용")
    message_type: Literal["text", "voice", "image"] = Field("text", description="메시지 타입")
    timestamp: datetime = Field(default_factory=datetime.now, description="전송 시간")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    session_id: Optional[str] = Field(None, description="세션 ID")


class AIResponse(BaseModel):
    """AI 응답 모델"""
    message_id: str = Field(..., description="메시지 고유 ID")
    response_text: str = Field(..., description="AI 응답 텍스트")
    actions: List[BaseAction] = Field(default_factory=list, description="실행할 액션 블록들")
    confidence_score: Optional[float] = Field(None, description="응답 신뢰도 (0-1)")
    processing_time_ms: Optional[int] = Field(None, description="처리 시간(밀리초)")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")


class WebSocketMessage(BaseModel):
    """WebSocket 메시지 모델"""
    type: Literal["user_message", "ai_response", "system", "error", "typing"] = Field(..., description="메시지 타입")
    data: Dict[str, Any] = Field(..., description="메시지 데이터")
    timestamp: datetime = Field(default_factory=datetime.now, description="메시지 시간")
    connection_id: Optional[str] = Field(None, description="연결 ID")


# 유니온 타입으로 모든 액션 타입 정의
ActionBlock = (
    TextAction | MusicAction | ScheduleAction | ReminderAction |
    SearchAction | WeatherAction | TimerAction | CalculateAction
)
