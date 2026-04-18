from __future__ import annotations

from dotenv import load_dotenv
import os
import uuid
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from model import build_fallback_response, classify_risk, get_next_steps, get_resources
from openai import OpenAI

# Load environment variables
load_dotenv()

print("API KEY LOADED:", bool(os.getenv("OPENAI_API_KEY")))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = FastAPI(title="MindBridge API", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# Memory (simple demo memory)
# ==========================
SESSION_MEMORY: dict[str, list[str]] = {}

# ==========================
# Request / Response Models
# ==========================

class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1000)


class ChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=600)
    session_id: str | None = None
    history: list[ChatHistoryItem] = []


class ChatResponse(BaseModel):
    reply: str
    resources: list[dict]
    next_steps: list[str]
    session_id: str


# ==========================
# Prompting
# ==========================

SYSTEM_PROMPT = """
You are MindBridge, a supportive mental health chatbot for young people.

You must:
- Sound like a real human, not a chatbot
- Be warm, natural, and conversational
- Reflect the user's exact situation
- Avoid generic phrases completely
- Keep replies short (2-4 sentences)
- Ask ONE natural follow-up question when appropriate

CRITICAL:
If the user expresses suicidal thoughts or self-harm:
- Be more direct and urgent
- Clearly tell them to contact Samaritans (116 123), NHS 111, or 999 if in danger
- Encourage reaching a trusted person NOW
- Ask if they are safe right now

Never mention:
- risk level
- analysis
- classifications
""".strip()


# ==========================
# Memory Helpers
# ==========================

def get_memory(session_id: str, history: list[ChatHistoryItem]) -> list[str]:
    if history:
        return [f"{item.role.upper()}: {item.content}" for item in history[-6:]]
    return SESSION_MEMORY.get(session_id, [])


def save_memory(session_id: str, user_text: str, reply: str) -> None:
    SESSION_MEMORY.setdefault(session_id, [])
    SESSION_MEMORY[session_id].append(f"USER: {user_text}")
    SESSION_MEMORY[session_id].append(f"ASSISTANT: {reply}")
    SESSION_MEMORY[session_id] = SESSION_MEMORY[session_id][-10:]


# ==========================
# Hybrid NLP Classification
# ==========================

def ai_risk_check(text: str) -> str | None:
    """
    AI-based NLP classifier.
    Used alongside the rule-based/logistic-regression-style classifier
    from model.py to improve contextual understanding.
    """
    if client is None:
        return None

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a mental health risk classifier. "
                        "Classify the message into exactly one label: low, medium, or high."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""
Classify this message:

"{text}"

Definitions:
- low = mild stress, general low mood, normal emotional difficulty
- medium = significant distress, hopelessness, anxiety, feeling unable to cope
- high = suicidal thoughts, self-harm intent, immediate danger, desire to die

Return only one word:
low
medium
or
high
""".strip(),
                },
            ],
            temperature=0,
        )

        label = response.output[0].content[0].text.strip().lower()
        if label in {"low", "medium", "high"}:
            return label
        return None

    except Exception as e:
        print("AI classification failed:", e)
        return None


def combine_risk(
    rule_risk: str,
    rule_confidence: float,
    ai_risk: str | None,
) -> tuple[str, float]:
    """
    Combines model.py classifier with AI NLP classifier.
    Conservative design: escalate when AI detects more severe risk.
    """
    final_risk = rule_risk
    final_confidence = rule_confidence

    if ai_risk == "high":
        final_risk = "high"
        final_confidence = max(rule_confidence, 0.9)
    elif ai_risk == "medium":
        if rule_risk == "low":
            final_risk = "medium"
            final_confidence = max(rule_confidence, 0.78)
    elif ai_risk == "low":
        # Do not downgrade medium/high from the main model
        final_risk = rule_risk

    return final_risk, round(final_confidence, 2)


def log_internal(
    text: str,
    rule_risk: str,
    rule_confidence: float,
    ai_risk: str | None,
    final_risk: str,
    final_confidence: float,
) -> None:
    print("\n========== INTERNAL ANALYSIS ==========")
    print("TEXT:", text)
    print("RULE MODEL RISK:", rule_risk)
    print("RULE MODEL CONFIDENCE:", round(rule_confidence, 2))
    print("AI NLP RISK:", ai_risk)
    print("FINAL HYBRID RISK:", final_risk)
    print("FINAL HYBRID CONFIDENCE:", final_confidence)
    print("=======================================\n")


# ==========================
# AI Reply Generation
# ==========================

def generate_ai_reply(user_text: str, risk_level: str, history: list[str]) -> str | None:
    if client is None:
        return None

    print("USING OPENAI")

    urgency = ""
    if risk_level == "high":
        urgency = """
IMPORTANT:
The user may be suicidal or in danger.
Be urgent and direct.
Encourage contacting Samaritans, NHS 111, or 999 immediately if needed.
"""

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"""
User message: "{user_text}"

Internal context:
- Final hybrid risk: {risk_level}

Conversation:
{chr(10).join(history) if history else "No earlier conversation."}

{urgency}

Instructions:
- Be human and natural
- Be specific to the user's exact situation
- Avoid generic sympathy
- Ask one follow-up question when appropriate
- Keep it short

Reply:
""".strip(),
                },
            ],
            temperature=0.9,
        )

        return response.output[0].content[0].text.strip()

    except Exception as e:
        print("OpenAI reply generation failed:", e)
        return None


# ==========================
# Routes
# ==========================

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "openai_enabled": bool(OPENAI_API_KEY),
        "model": OPENAI_MODEL,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    session_id = payload.session_id or str(uuid.uuid4())

    # 1) Rule-based / logistic-regression-style classifier from model.py
    rule_risk, rule_confidence, _ = classify_risk(payload.text)

    # 2) AI-based NLP classifier
    ai_risk = ai_risk_check(payload.text)

    # 3) Hybrid final decision
    final_risk, final_confidence = combine_risk(rule_risk, rule_confidence, ai_risk)

    # Internal terminal log only (not shown to user)
    log_internal(
        payload.text,
        rule_risk,
        rule_confidence,
        ai_risk,
        final_risk,
        final_confidence,
    )

    resources = get_resources(final_risk)
    next_steps = get_next_steps(final_risk)

    memory = get_memory(session_id, payload.history)

    reply = generate_ai_reply(payload.text, final_risk, memory)

    if not reply:
        if final_risk == "high":
            reply = (
                "That sounds really serious, and I’m really glad you said it. "
                "If you feel like you might act on these thoughts, please call 999 now or go somewhere safe. "
                "You can also call Samaritans on 116 123 right now. "
                "Are you able to reach someone you trust at the moment?"
            )
        else:
            reply = build_fallback_response(payload.text, final_risk)

    save_memory(session_id, payload.text, reply)

    return ChatResponse(
        reply=reply,
        resources=resources,
        next_steps=next_steps,
        session_id=session_id,
    )