from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_chat_endpoint() -> None:
    mock_result = {
        "messages": [],
        "user_id": "demo-user",
        "user_role": "viewer",
        "intent": "general",
        "final_answer": "Hello from the AI assistant.",
    }

    with patch(
        "app.api.routes.chat.agent_graph.ainvoke",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        response = client.post(
            "/chat",
            json={
                "message": "Hello",
                "user_id": "demo-user",
                "user_role": "viewer",
            },
        )

    assert response.status_code == 200
    assert response.json()["answer"] == "Hello from the AI assistant."