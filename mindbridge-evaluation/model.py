from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import re


@dataclass
class Resource:
    name: str
    description: str
    contact_label: str
    contact_value: str
    url: str | None = None


HIGH_RISK_PATTERNS = [
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bwant to die\b",
    r"\bdon't want to live\b",
    r"\bdo not want to live\b",
    r"\bsuicid(?:e|al)\b",
    r"\bself[- ]?harm\b",
    r"\bhurt myself\b",
    r"\boverdose\b",
    r"\bcut myself\b",
    r"\bno point in living\b",
]

MEDIUM_RISK_PATTERNS = [
    r"\banxious\b",
    r"\bpanic\b",
    r"\bstressed\b",
    r"\boverwhelmed\b",
    r"\bburnt? out\b",
    r"\bdepressed\b",
    r"\blow\b",
    r"\bworthless\b",
    r"\bhopeless\b",
    r"\bcan't cope\b",
    r"\bcan not cope\b",
    r"\bstruggling\b",
    r"\blonely\b",
    r"\bempty\b",
    r"\bcrying\b",
    r"\bexhausted\b",
    r"\bcan't sleep\b",
    r"\bcan not sleep\b",
]

LOW_RISK_PATTERNS = [
    r"\bokay\b",
    r"\bfine\b",
    r"\balright\b",
    r"\bdoing well\b",
    r"\bbetter\b",
]

SUPPORT_RESOURCES = {
    "high": [
        Resource(
            name="Samaritans",
            description="24/7 support if you are in distress or need someone to talk to right now.",
            contact_label="Call",
            contact_value="116 123",
            url="https://www.samaritans.org/",
        ),
        Resource(
            name="NHS 111",
            description="Urgent mental health support and advice in the UK.",
            contact_label="Call",
            contact_value="111",
            url="https://www.nhs.uk/nhs-services/urgent-and-emergency-care-services/when-to-use-111/",
        ),
        Resource(
            name="YoungMinds Crisis Messenger",
            description="Text support if you are experiencing a mental health crisis.",
            contact_label="Text",
            contact_value="YM to 85258",
            url="https://www.youngminds.org.uk/young-person/your-guide-to-support/urgent-help/",
        ),
    ],
    "medium": [
        Resource(
            name="YoungMinds",
            description="Advice and support for young people struggling with feelings, stress, or anxiety.",
            contact_label="Visit",
            contact_value="YoungMinds support",
            url="https://www.youngminds.org.uk/",
        ),
        Resource(
            name="Mind",
            description="Information on mental health problems, coping strategies, and how to get support.",
            contact_label="Visit",
            contact_value="Mind information hub",
            url="https://www.mind.org.uk/",
        ),
    ],
    "low": [
        Resource(
            name="NHS Mental Wellbeing",
            description="Practical self-help advice for stress, mood, sleep, and wellbeing.",
            contact_label="Visit",
            contact_value="NHS wellbeing guide",
            url="https://www.nhs.uk/every-mind-matters/",
        )
    ],
}


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def count_matches(patterns: Iterable[str], text: str) -> int:
    return sum(1 for pattern in patterns if re.search(pattern, text))


def classify_risk(text: str) -> tuple[str, float, list[str]]:
    cleaned = normalise(text)
    reasons: list[str] = []

    high_hits = count_matches(HIGH_RISK_PATTERNS, cleaned)
    medium_hits = count_matches(MEDIUM_RISK_PATTERNS, cleaned)
    low_hits = count_matches(LOW_RISK_PATTERNS, cleaned)

    if high_hits:
        reasons.append("direct crisis language detected")
        return "high", min(0.85 + high_hits * 0.04, 0.99), reasons

    if medium_hits >= 2:
        reasons.append("multiple distress indicators detected")
        return "medium", min(0.62 + medium_hits * 0.05, 0.9), reasons

    if medium_hits == 1:
        reasons.append("single distress indicator detected")
        return "medium", 0.68, reasons

    if low_hits:
        reasons.append("low concern language detected")
        return "low", 0.74, reasons

    reasons.append("no explicit risk phrase detected")
    return "low", 0.56, reasons


def get_resources(risk_level: str) -> list[dict]:
    return [resource.__dict__ for resource in SUPPORT_RESOURCES.get(risk_level, [])]


def get_next_steps(risk_level: str) -> list[str]:
    if risk_level == "high":
        return [
            "Please contact a trusted adult, Samaritans, NHS 111, or emergency services if you are in immediate danger."
        ]
    if risk_level == "medium":
        return [
            "It may help to talk through what has been weighing on you and consider reaching out to a trusted person or support service."
        ]
    return [
        "You can keep talking here, or explore self-help and wellbeing resources if that feels useful."
    ]


def build_fallback_response(text: str, risk_level: str) -> str:
    cleaned = normalise(text)

    if risk_level == "high":
        return (
            "Thank you for telling me that. What you have shared sounds serious, and I am really glad you said it out loud. "
            "I am not able to provide emergency help, but I strongly encourage you to contact Samaritans on 116 123, NHS 111, "
            "or emergency services right now if you might act on these thoughts. If possible, please tell a trusted person near you today."
        )

    if risk_level == "medium":
        if any(word in cleaned for word in ["university", "exam", "course", "deadline"]):
            return (
                "It sounds like university pressure may be taking a lot out of you right now. That can build up quickly, especially "
                "when stress, expectations, and tiredness all come together. If you want, tell me what part feels heaviest at the moment."
            )
        if any(word in cleaned for word in ["anxious", "panic", "overwhelmed"]):
            return (
                "That sounds overwhelming. When anxiety builds, it can make everything feel more intense than usual. We can slow it down "
                "together. What usually seems to trigger these feelings most?"
            )
        return (
            "Thank you for sharing that. It sounds like you have been carrying a lot. You do not have to solve everything at once. "
            "If you want, you can tell me a bit more about what has been hardest lately."
        )

    return (
        "Thank you for sharing that with me. I am here to listen. You can tell me more about how things have been recently, "
        "or ask for support options if you would like practical next steps."
    )
