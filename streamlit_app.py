import os
import requests
import streamlit as st

st.set_page_config(
    page_title="Enterprise AI Assistant",
    page_icon="🤖",
    layout="wide",
)

# Backend URL is configurable per environment.
API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000",
)

# Require an authenticated Keycloak/OIDC session before
# exposing the enterprise assistant.
if not st.user.is_logged_in:
    st.title("Enterprise AI Assistant")

    st.write(
        "Secure enterprise knowledge and research assistant."
    )

    st.button(
        "Login with Keycloak",
        on_click=st.login,
        args=("keycloak",),
        type="primary",
    )

    st.stop()


user = st.user

with st.sidebar:
    st.title("Enterprise AI Assistant")

    st.success("Authenticated")

    username = user.get("preferred_username")

    if username:
        st.write(f"**User:** {username}")

    if st.button("Logout"):
        st.logout()


st.title("Enterprise AI Assistant")

st.caption(
    "Ask questions about your enterprise knowledge base."
)

# Conversation state is maintained by the Streamlit session
# while the backend persists the conversation in PostgreSQL.
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


prompt = st.chat_input(
    "Ask a question..."
)


if prompt:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    # Pass the Keycloak access token to the FastAPI backend
    # for authentication and authorization.
    access_token = st.user.tokens.get("access")

    if not access_token:
        st.error(
            "No access token is available for the session."
        )
        st.stop()

    payload = {
        "message": prompt,
        "conversation_id": (
            st.session_state.conversation_id
        ),
    }

    status_placeholder = st.empty()

    try:
        status_placeholder.caption("Thinking...")

        # Use the streaming endpoint so generated tokens
        # can be displayed progressively in the UI.
        response = requests.post(
            f"{API_URL}/chat/stream",
            headers={
                "Authorization": (
                    f"Bearer {access_token}"
                ),
                "Accept": "text/event-stream",
            },
            json=payload,
            stream=True,
            timeout=120,
        )

        if response.status_code == 401:
            status_placeholder.empty()

            st.warning(
                "Your session has expired. "
                "Please log in again."
            )

            st.logout()
            st.stop()

        if response.status_code != 200:
            status_placeholder.empty()

            st.error(
                f"Request failed: "
                f"{response.status_code}"
            )

            st.code(response.text)
            st.stop()

        answer_parts: list[str] = []
        conversation_id = None
        event_type = None

        answer_placeholder = None

        # Parse the Server-Sent Events stream produced by
        # the FastAPI /chat/stream endpoint.
        for line in response.iter_lines(
            decode_unicode=True
        ):
            if not line:
                continue

            if line.startswith("event:"):
                event_type = line.removeprefix(
                    "event: "
                )
                continue

            if not line.startswith("data:"):
                continue

            data = line.removeprefix(
                "data: "
            )

            if event_type == "token":
                answer_parts.append(data)

                if answer_placeholder is None:
                    status_placeholder.empty()

                    with st.chat_message(
                        "assistant"
                    ):
                        answer_placeholder = st.empty()

                answer_placeholder.markdown(
                    "".join(answer_parts)
                )

            elif event_type == "metadata":
                conversation_id = data

            elif event_type == "done":
                break

        answer = "".join(answer_parts)

        if conversation_id:
            st.session_state.conversation_id = (
                conversation_id
            )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

    except requests.exceptions.ConnectionError:
        status_placeholder.empty()

        st.error(
            "Unable to connect to the FastAPI backend."
        )

    except requests.exceptions.Timeout:
        status_placeholder.empty()

        st.error(
            "The request timed out."
        )