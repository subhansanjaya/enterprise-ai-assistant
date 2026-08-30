import requests
import streamlit as st


st.set_page_config(
    page_title="Enterprise AI Assistant",
    page_icon="🤖",
    layout="wide",
)


API_URL = "http://127.0.0.1:8000"


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

    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = requests.post(
                    f"{API_URL}/chat",
                    headers={
                        "Authorization": (
                            f"Bearer {access_token}"
                        )
                    },
                    json=payload,
                    timeout=120,
                )

            if response.status_code == 401:
                st.error(
                    "Authentication failed. "
                    "Please log in again."
                )
                st.stop()

            if response.status_code != 200:
                st.error(
                    f"Request failed: "
                    f"{response.status_code}"
                )
                st.code(response.text)
                st.stop()

            data = response.json()

            st.session_state.conversation_id = (
                data["conversation_id"]
            )

            answer = data["answer"]

            st.markdown(answer)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

            sources = data.get("sources", [])

            if sources:
                st.divider()
                st.subheader("Sources")

                seen = set()

                for source in sources:
                    document_id = source["document_id"]

                    if document_id in seen:
                        continue

                    seen.add(document_id)

                    with st.container(border=True):
                        st.markdown(
                            f"**{document_id}**"
                        )

                        st.caption(
                            f"{source['document_type']} • "
                            f"{source['department']} • "
                            f"{source['access_level']} • "
                            f"{source['created_date']}"
                        )

    except requests.exceptions.ConnectionError:
        st.error(
            "Unable to connect to the FastAPI backend."
        )

    except requests.exceptions.Timeout:
        st.error(
            "The request timed out."
        )