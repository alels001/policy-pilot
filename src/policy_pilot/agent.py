"""Conversation memory for PolicyPilot, built with LangGraph.

A follow-up question such as "And for a Junior?" is rewritten into a standalone
question, then answered by the existing pipeline (generation.answer).
The role always comes from the caller (the API takes it from the JWT),
never from the conversation or the LLM.
"""

import operator
from dataclasses import asdict
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from policy_pilot import config
from policy_pilot.generation import Answer, _client, answer, is_small_talk
from policy_pilot.retrieval import SearchResult

MAX_HISTORY_MESSAGES = 6  # the last 3 questions and 3 answers are enough context

REWRITE_PROMPT = """You rewrite follow-up questions for a company policy search.
Given the conversation and the user's latest question, write ONE standalone question
that can be understood without the conversation.
Rules:
- Keep the language of the latest question.
- Do not answer the question.
- Do not add facts that are not in the conversation.
- If the latest question is already standalone, return it unchanged.
Return only the question."""


class ChatState(TypedDict, total=False):
    role: str
    question: str
    standalone_question: str
    history: Annotated[list[dict[str, str]], operator.add]
    answer_text: str
    answered: bool
    sources: list[dict]


def format_history(history: list[dict[str, str]]) -> str:
    recent = history[-MAX_HISTORY_MESSAGES:]
    return "\n".join(f"{message['role']}: {message['content']}" for message in recent)


def rewrite(state: ChatState) -> dict:
    question = state["question"]
    history = state.get("history", [])
    if not history or is_small_talk(question):
        return {"standalone_question": question}

    response = _client().responses.create(
        model=config.LLM_MODEL,
        reasoning={"effort": config.LLM_REASONING_EFFORT},
        instructions=REWRITE_PROMPT,
        input=f"Conversation:\n{format_history(history)}\n\nLatest question: {question}",
    )
    return {"standalone_question": response.output_text.strip() or question}


def respond(state: ChatState) -> dict:
    result = answer(state["standalone_question"], state["role"])
    return {
        "answer_text": result.text,
        "answered": result.answered,
        "sources": [asdict(source) for source in result.sources],
        "history": [
            {"role": "user", "content": state["standalone_question"]},
            {"role": "assistant", "content": result.text},
        ],
    }


def build_graph(checkpointer=None):
    builder = StateGraph(ChatState)
    builder.add_node("rewrite", rewrite)
    builder.add_node("respond", respond)
    builder.add_edge(START, "rewrite")
    builder.add_edge("rewrite", "respond")
    builder.add_edge("respond", END)
    return builder.compile(checkpointer=checkpointer)


GRAPH = build_graph(InMemorySaver())


def ask(question: str, role: str, thread_id: str) -> Answer:
    state = GRAPH.invoke(
        {"question": question, "role": role},
        {"configurable": {"thread_id": thread_id}},
    )
    sources = [SearchResult(**source) for source in state["sources"]]
    return Answer(state["answer_text"], sources, state["answered"])
