"""PolicyPilot chat UI.

Run from the project root:
    uv run streamlit run src/policy_pilot/app.py
"""

import time
from collections import Counter

import streamlit as st

from policy_pilot import config
from policy_pilot.catalog import current_documents, load_catalog
from policy_pilot.embeddings import embed_query
from policy_pilot.generation import answer
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


@st.cache_resource
def warm_up() -> bool:
    embed_query("warm up")  # load the embedding model once, not on the first question
    return True


@st.cache_data
def catalog():
    return current_documents(load_catalog(config.DATA_DIR))


def access_summary(role: str) -> list[tuple[str, int, int]]:
    """Per department: number of documents the role may see, and how many are confidential."""
    visible = [doc for doc in catalog() if role in doc.allowed_roles]
    total = Counter(doc.department for doc in visible)
    confidential = Counter(doc.department for doc in visible if doc.classification == "confidential")
    return [(DEPARTMENTS[d], total[d], confidential[d]) for d in DEPARTMENTS if total[d]]


def show_sources(sources) -> None:
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})", icon=":material/description:"):
        for number, source in enumerate(sources, start=1):
            st.markdown(f"**[{number}] {source.title}**")
            st.caption(f"{source.doc_id} · Version {source.version} · {source.section}")
            st.markdown(source.content)
            if number < len(sources):
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


# --- Sidebar: who is asking, and what may they see? ------------------------
users = load_users(config.DATA_DIR)
with st.sidebar:
    st.markdown("### 🧭 PolicyPilot")
    st.caption("Internal knowledge assistant · Nordwerk Automotive")

    st.markdown("**Signed in as**")
    user = st.selectbox(
        "Demo user",
        users,
        format_func=lambda u: f"{u.name} · {u.department}",
        label_visibility="collapsed",
    )
    st.badge(user.role, icon=":material/badge:", color="blue")

    st.markdown("**Your document access**")
    for department, count, confidential in access_summary(user.role):
        note = f" · {confidential} confidential" if confidential else ""
        plural = "s" if count != 1 else ""
        st.markdown(f"- {department}: {count} document{plural}{note}")

    if st.button("New chat", icon=":material/add_comment:", width="stretch"):
        st.session_state.messages = []

    st.divider()
    st.caption(
        "Demo: the user is chosen here. In production the role comes from the "
        "company login (SSO), never from the chat."
    )

# A new user must never see the previous user's answers.
if st.session_state.get("user_id") != user.user_id:
    st.session_state.user_id = user.user_id
    st.session_state.messages = []

# --- Main area --------------------------------------------------------------
st.title("PolicyPilot")
st.caption("Answers only from internal documents you are allowed to see, always with sources.")
warm_up()

question = st.chat_input("Ask about HR, IT or quality policies ...")
if not question:
    question = st.session_state.pop("pending", None)

if not st.session_state.messages and not question:
    st.markdown("##### Try a question")
    columns = st.columns(2)
    for index, example in enumerate(EXAMPLES[user.role]):
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
        with st.spinner("Searching the documents you may see ..."):
            start = time.perf_counter()
            result = answer(question, user.role)
            seconds = time.perf_counter() - start
        message = {
            "role": "assistant",
            "content": result.text,
            "sources": result.sources,
            "answered": result.answered,
            "seconds": seconds,
        }
        show_answer(message)
    st.session_state.messages.append(message)