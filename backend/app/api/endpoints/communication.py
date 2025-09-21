"""
Real-time Communication Endpoints
WebSocket 및 SSE를 통한 실시간 통신 엔드포인트 구현
"""

import json
import logging
import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.status import HTTP_404_NOT_FOUND

from app.models.actions import (
    UserMessage, AIResponse, WebSocketMessage, ActionBlock,
    TextAction, MusicAction, ScheduleAction, ActionType
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 간단한 연결 관리자 (실제 프로덕션에서는 Redis 등 사용)
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> connection_id
    
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> str:
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        
        if user_id:
            self.user_sessions[user_id] = connection_id
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")
        return connection_id
    
    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            # user_sessions에서도 제거
            user_to_remove = None
            for user_id, conn_id in self.user_sessions.items():
                if conn_id == connection_id:
                    user_to_remove = user_id
                    break
            if user_to_remove:
                del self.user_sessions[user_to_remove]
            
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: dict, connection_id: str) -> bool:
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(
                    json.dumps(message, ensure_ascii=False, default=str)
                )
                return True
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                self.disconnect(connection_id)
                return False
        return False
    
    async def send_to_user(self, message: dict, user_id: str) -> bool:
        if user_id in self.user_sessions:
            connection_id = self.user_sessions[user_id]
            return await self.send_personal_message(message, connection_id)
        return False

# 전역 연결 관리자
manager = ConnectionManager()

# Mock AI 응답 생성기 (실제로는 LLM 서비스 연동)
async def generate_ai_response(user_message: UserMessage) -> AIResponse:
    """사용자 메시지에 대한 AI 응답 생성 (Mock)"""
    
    # 간단한 키워드 기반 응답 생성
    content = user_message.content.lower()
    actions = []
    response_text = ""
    
    if "음악" in content or "노래" in content:
        response_text = "음악을 틀어드릴게요!"
        actions.append(MusicAction(
            title="음악 재생",
            description="요청하신 음악을 재생합니다",
            song_title="좋은 음악",
            artist="AI 아티스트",
            duration=180,
            url="https://example.com/music/sample.mp3"
        ))
    
    elif "일정" in content or "스케줄" in content:
        response_text = "일정을 확인하고 등록해드릴게요!"
        actions.append(ScheduleAction(
            title="일정 등록",
            description="새로운 일정을 등록합니다",
            event_title="새로운 일정",
            start_time=datetime.now(),
            location="회의실 A"
        ))
    
    elif "안녕" in content or "hello" in content.lower():
        response_text = "안녕하세요! 저는 당신의 AI 어시스턴트입니다. 무엇을 도와드릴까요?"
        actions.append(TextAction(
            title="인사 응답",
            description="사용자에게 인사를 전합니다",
            content=response_text
        ))
    
    else:
        response_text = f"'{user_message.content}'에 대해 이해했습니다. 더 구체적으로 말씀해 주시면 도움을 드릴 수 있습니다."
        actions.append(TextAction(
            title="일반 응답",
            description="사용자 메시지에 대한 일반적인 응답",
            content=response_text
        ))
    
    # 약간의 처리 시간 시뮬레이션
    await asyncio.sleep(0.5)
    
    return AIResponse(
        message_id=str(uuid.uuid4()),
        response_text=response_text,
        actions=actions,
        confidence_score=0.85,
        processing_time_ms=500
    )


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: Optional[str] = None):
    """
    WebSocket 엔드포인트 - 실시간 AI 어시스턴트 통신
    
    사용법:
    - WebSocket 연결: ws://localhost:8000/api/ws/{user_id}
    - 메시지 형식: {"type": "user_message", "data": {"content": "안녕하세요", "message_type": "text"}}
    """
    connection_id = await manager.connect(websocket, user_id)
    
    try:
        # 연결 확인 메시지 전송
        welcome_message = WebSocketMessage(
            type="system",
            data={
                "message": f"AI 어시스턴트에 연결되었습니다. (ID: {connection_id})",
                "connection_id": connection_id,
                "user_id": user_id
            }
        )
        await manager.send_personal_message(welcome_message.model_dump(), connection_id)
        
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                ws_message = WebSocketMessage(**message_data)
                
                if ws_message.type == "user_message":
                    # 사용자 메시지 처리
                    user_msg = UserMessage(**ws_message.data)
                    user_msg.user_id = user_id
                    
                    logger.info(f"Received message from {user_id}: {user_msg.content}")
                    
                    # 타이핑 인디케이터 전송
                    typing_message = WebSocketMessage(
                        type="typing",
                        data={"is_typing": True, "message": "AI가 응답을 생성 중입니다..."}
                    )
                    await manager.send_personal_message(typing_message.model_dump(), connection_id)
                    
                    # AI 응답 생성
                    ai_response = await generate_ai_response(user_msg)
                    
                    # 타이핑 종료
                    typing_message.data["is_typing"] = False
                    await manager.send_personal_message(typing_message.model_dump(), connection_id)
                    
                    # AI 응답 전송
                    response_message = WebSocketMessage(
                        type="ai_response",
                        data=ai_response.model_dump()
                    )
                    await manager.send_personal_message(response_message.model_dump(), connection_id)
                    
                elif ws_message.type == "system":
                    # 시스템 메시지 처리 (예: 연결 상태 확인)
                    if ws_message.data.get("action") == "ping":
                        pong_message = WebSocketMessage(
                            type="system",
                            data={"action": "pong", "timestamp": datetime.now().isoformat()}
                        )
                        await manager.send_personal_message(pong_message.model_dump(), connection_id)
                
            except json.JSONDecodeError:
                error_message = WebSocketMessage(
                    type="error",
                    data={"error": "잘못된 JSON 형식입니다", "received_data": data}
                )
                await manager.send_personal_message(error_message.model_dump(), connection_id)
            
            except Exception as e:
                error_message = WebSocketMessage(
                    type="error",
                    data={"error": f"메시지 처리 중 오류 발생: {str(e)}"}
                )
                await manager.send_personal_message(error_message.model_dump(), connection_id)
                logger.error(f"Error processing message: {e}")
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"WebSocket client {connection_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection_id)


@router.get("/sse/{user_id}")
async def sse_endpoint(request: Request, user_id: str):
    """
    Server-Sent Events 엔드포인트 - 일방향 실시간 스트리밍
    
    사용법:
    - GET 요청: http://localhost:8000/api/sse/{user_id}
    - EventSource 연결하여 실시간 이벤트 수신
    """
    
    async def event_generator():
        """SSE 이벤트 생성기"""
        try:
            # 연결 확인 이벤트
            yield f"data: {json.dumps({'type': 'connected', 'user_id': user_id, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 주기적으로 상태 업데이트 전송 (예시)
            counter = 0
            while True:
                # 클라이언트 연결 상태 확인
                if await request.is_disconnected():
                    break
                
                # 샘플 데이터 전송
                counter += 1
                event_data = {
                    "type": "status_update",
                    "data": {
                        "message": f"실시간 업데이트 #{counter}",
                        "timestamp": datetime.now().isoformat(),
                        "user_id": user_id
                    }
                }
                
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                
                # 5초마다 업데이트
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"SSE error for user {user_id}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )


@router.get("/connections/status")
async def get_connection_status():
    """현재 WebSocket 연결 상태 조회"""
    return {
        "active_connections": len(manager.active_connections),
        "user_sessions": len(manager.user_sessions),
        "connections": list(manager.active_connections.keys()),
        "users": list(manager.user_sessions.keys()),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/send-message/{user_id}")
async def send_message_to_user(user_id: str, message: Dict[str, Any]):
    """특정 사용자에게 메시지 전송 (REST API)"""
    
    if user_id not in manager.user_sessions:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"User {user_id} is not connected"
        )
    
    ws_message = WebSocketMessage(
        type="system",
        data=message
    )
    
    success = await manager.send_to_user(ws_message.model_dump(), user_id)
    
    if success:
        return {
            "status": "success",
            "message": f"Message sent to user {user_id}",
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message to user {user_id}"
        )
