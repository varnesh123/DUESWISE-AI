"""Deterministic scam-risk detector — blueprint §7 Phase 3.

Rules-based scoring from:
- Urgency/threat language
- OTP/PIN/password requests
- Collect request or payment authorisation wording
- Suspicious shortened links
- Lookalike domains
- Unknown payment requests
- Impersonation wording
- Suspicious UPI handles

Score: 0–100. Levels: 0–24 low, 25–49 medium, 50–74 high, 75–100 critical.

The backend calculates the score. AI only explains the supplied assessment.
"""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class ScamResult:
    risk_score: int  # 0-100
    risk_level: str  # low/medium/high/critical
    verdict: str  # legitimate/suspicious/scam
    indicators: List[dict]
    explanation: str
    recommended_actions: List[str]


# Indicator definitions: (code, description, points, keywords)
INDICATORS = [
    ("URGENT_THREAT", "The message uses urgency or threat language to pressure action", 25,
     ["blocked", "suspend", "expire", "immediately", "urgent", "verify now", "act now", "within 24 hours"]),
    ("OTP_REQUEST", "The message requests OTP, PIN, password or credentials", 30,
     ["otp", "pin", "password", "verify your", "share your", "enter your otp", "enter your pin"]),
    ("COLLECT_REQUEST", "The message requests money collection or payment authorisation", 20,
     ["collect request", "request money", "pay now", "authorize payment", "authorise payment", "upi collect"]),
    ("SUSPICIOUS_LINK", "The message contains suspicious shortened links", 20,
     ["bit.ly", "tinyurl", "t.co", "cutt.ly", "rebrand.ly", "click here", "link"]),
    ("LOOKALIKE_DOMAIN", "The message contains lookalike or suspicious domains", 15,
     ["bank-security.com", "verify-bank", "secure-login", "update-kYc", "kyc-update", "account-verify"]),
    ("UNKNOWN_PAYMENT", "The message requests an unknown or unexpected payment", 15,
     ["unexpected payment", "unknown sender", "received money", "refund", "cashback", "you have received"]),
    ("IMPERSONATION", "The message impersonates a bank or authority", 15,
     ["reserve bank of india", "rbi", "income tax", "gst department", "bank of india", "sbi alerts"]),
    ("SUSPICIOUS_UPI", "The message contains suspicious UPI handles", 10,
     ["@upi", "@paytm", "@ybl", "@okaxis", "@okhdfcbank", "@okicici"]),
]


def _score_level(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _verdict_from_level(level: str) -> str:
    if level == "critical":
        return "scam"
    if level == "high":
        return "suspicious"
    if level == "medium":
        return "suspicious"
    return "legitimate"


def analyze_message(message: str) -> ScamResult:
    """Analyze a message for scam risk using deterministic rules.

    Returns a ScamResult with risk_score (0-100), risk_level, verdict,
    indicators, explanation and recommended_actions.
    """
    if not message or not message.strip():
        return ScamResult(
            risk_score=0,
            risk_level="low",
            verdict="legitimate",
            indicators=[],
            explanation="No suspicious content detected.",
            recommended_actions=[],
        )

    low = message.lower()
    triggered: List[dict] = []
    total_score = 0

    for code, description, points, keywords in INDICATORS:
        matched = [kw for kw in keywords if kw.lower() in low]
        if matched:
            triggered.append({
                "code": code,
                "description": description,
                "matched_keywords": matched,
            })
            total_score += points

    # Cap at 100
    risk_score = min(total_score, 100)
    risk_level = _score_level(risk_score)
    verdict = _verdict_from_level(risk_level)

    # Build explanation
    if risk_score == 0:
        explanation = "This message does not exhibit common scam indicators."
        recommended_actions = []
    else:
        indicator_desc = "; ".join(i["description"] for i in triggered)
        explanation = (
            f"This message scores {risk_score}/100 on scam-risk indicators: {indicator_desc}."
        )
        recommended_actions = [
            "Do not share your OTP, UPI PIN or password with anyone.",
            "Do not click on unverified or shortened links.",
            "Verify the request through your bank's official application or website.",
            "If in doubt, contact your bank's customer care directly.",
        ]

    return ScamResult(
        risk_score=risk_score,
        risk_level=risk_level,
        verdict=verdict,
        indicators=[{"code": i["code"], "description": i["description"]} for i in triggered],
        explanation=explanation,
        recommended_actions=recommended_actions,
    )
