from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api.main import app
from app.auth.dependencies import get_current_user
from app.auth.models import AuthenticatedUser


def test_chat_endpoint() -> None:
    mock_user = AuthenticatedUser(
        user_id="demo-user",
        roles=["viewer"],
    )

    app.dependency_overrides[get_current_user] = (
        lambda: mock_user
    )

    mock_result = {
        "final_answer": "Hello from the assistant.",
    }

    try:
        with patch(
            "app.api.routes.chat.agent_graph.ainvoke",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            client = TestClient(app)

            response = client.post(
                "/chat",
                json={
                    "message": "Hello",
                },
            )

        assert response.status_code == 200
        assert response.json() == {
            "answer": "Hello from the assistant."
        }

    finally:
        app.dependency_overrides.clear()
        
def test_chat_requires_authentication() -> None:
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={
            "message": "Hello",
        },
    )

    assert response.status_code == 401