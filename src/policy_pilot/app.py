"""PolicyPilot chat UI. It talks only to the API and never decides roles itself.

Run from the project root, with the API running:
    uv run streamlit run src/policy_pilot/app.py
"""

import time

import streamlit as st

from policy_pilot import client, config
from policy_pilot.users import load_users

st.set_page_config(page_title="PolicyPilot", page_icon="🧭", layout="centered")

DEPARTMENTS = {"hr": "HR", "it": "IT", "quality": "Quality", "compliance": "Compliance"}

EXAMPLES = {
    "employee": [
        "Wie viele Urlaubstage habe ich?",
        "What can I claim for a two-day business trip?",
        "Was tun bei einer Phishing-E-Mail?",
        "What is the salary band for a Senior Engineer?",
    ],
    "hr_specialist": [
        "What is the salary band for a Senior Engineer?",
        "Bis wann kann Resturlaub übertragen werden?",
        "How many days per week can I work from home?",
        "Welche Geschenke darf ich annehmen?",
    ],
    "it_admin": [
        "What are the first steps for a ransomware incident?",
        "Wie richte ich das VPN ein?",
        "Can employees install software themselves?",
        "What is the salary band for a Senior Engineer?",
    ],
    "quality_engineer": [
        "Welche Nebenabweichungen wurden im internen Audit festgestellt?",
        "What are the deadlines for an 8D report?",
        "Wann ist eine 100 %-Prüfung im Wareneingang nötig?",
        "What is the salary band for a Senior Engineer?",
    ],
}


def show_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})", icon=":material/description:"):
        for source in sources:
            st.markdown(f"**[{source['number']}] {source['title']}**")
            st.caption(f"{source['doc_id']} · Version {source['version']} · {source['section']}")
            st.markdown(source["content"])
            if source["number"] < len(sources):
                st.divider()


def show_answer(message: dict) -> None:
    if message["answered"]:
        st.markdown(message["content"])
    else:
        st.info(message["content"], icon=":material/search_off:")
    show_sources(message["sources"])
    if message.get("seconds") is not None:
        st.caption(f"Answered in {message['seconds']:.1f} s")


def ask(question: str) -> None:
    st.session_state.pending = question


def sign_in(user_id: str, password: str) -> None:
    token = client.login(user_id, password)
    st.session_state.token = token
    st.session_state.me = client.get("/me", token)
    st.session_state.access = client.get("/access", token)
    st.session_state.messages = []


def sign_out(notice: str | None = None) -> None:
    for key in ("token", "me", "access", "messages", "pending"):
        st.session_state.pop(key, None)
    if notice:
        st.session_state.notice = notice


# --- Sidebar: sign in, or who is signed in -----------------------------------
with st.sidebar:
    st.markdown("### 🧭 PolicyPilot")
    st.caption("Internal knowledge assistant · Nordwerk Automotive")

    if "token" not in st.session_state:
        with st.form("sign-in"):
            user = st.selectbox(
                "Demo user",
                load_users(config.DATA_DIR),
                format_func=lambda u: f"{u.name} · {u.department}",
            )
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in", width="stretch"):
                try:
                    sign_in(user.user_id, password)
                    st.rerun()
                except client.ApiError as error:
                    st.error(str(error))
        st.caption("Demo login. In production users sign in with the company SSO.")
    else:
        me = st.session_state.me
        st.markdown(f"**{me['name']}**")
        st.badge(me["role"], icon=":material/badge:", color="blue")

        st.markdown("**Your document access**")
        for item in st.session_state.access:
            note = f" · {item['confidential']} confidential" if item["confidential"] else ""
            plural = "s" if item["documents"] != 1 else ""
            name = DEPARTMENTS.get(item["department"], item["department"])
            st.markdown(f"- {name}: {item['documents']} document{plural}{note}")

        if st.button("New chat", icon=":material/add_comment:", width="stretch"):
            st.session_state.messages = []
        st.button("Sign out", icon=":material/logout:", width="stretch", on_click=sign_out)

# --- Main area ----------------------------------------------------------------
st.title("PolicyPilot")
st.caption("Answers only from internal documents you are allowed to see, always with sources.")

if notice := st.session_state.pop("notice", None):
    st.warning(notice)

if "token" not in st.session_state:
    st.info("Please sign in on the left to ask questions.", icon=":material/login:")
    st.stop()

question = st.chat_input("Ask about HR, IT or quality policies ...")
if not question:
    question = st.session_state.pop("pending", None)

if not st.session_state.messages and not question:
    st.markdown("##### Try a question")
    columns = st.columns(2)
    for index, example in enumerate(EXAMPLES.get(st.session_state.me["role"], [])):
        columns[index % 2].button(
            example, key=f"example-{index}", on_click=ask, args=(example,), width="stretch"
        )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            show_answer(message)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching the documents you may see ..."):
                start = time.perf_counter()
                result = client.ask(question, st.session_state.token)
                seconds = time.perf_counter() - start
        except client.NotSignedIn:
            sign_out("Your session has expired. Please sign in again.")
            st.rerun()
        except client.ApiError as error:
            st.error(str(error))
            st.stop()

        message = {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "answered": result["answered"],
            "seconds": seconds,
        }
        show_answer(message)
    st.session_state.messages.append(message)