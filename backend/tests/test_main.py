from fastapi.testclient import TestClient
from app.main import app

# Create a TestClient instance
# TestClient 인스턴스 생성
client = TestClient(app)


def test_read_root():
    """
    Test the root endpoint.
    루트 엔드포인트를 테스트합니다.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome!"}


def test_health_check():
    """
    Test the health check endpoint.
    /health 엔드포인트를 테스트합니다.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# To run tests: pytest
# 테스트 실행: pytest