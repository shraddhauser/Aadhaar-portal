"""
backend/routes/chat.py
AI-powered chatbot endpoint — secure Anthropic Claude API proxy.

Flow:
  1. Frontend sends user message + conversation history to /api/chat/ask
  2. This endpoint fetches live portal data from the database
  3. Builds a rich system prompt with real numbers injected
  4. Calls Anthropic Claude with the system prompt + conversation
  5. Returns Claude's response — the API key never touches the frontend
"""

import os
import logging
import time
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models.models import (
    DailyStat, Enrollment, Update, Anomaly, Region, BiometricData,
)
from backend.routes.auth import get_current_admin

router = APIRouter()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str          # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    tokens_used: Optional[int] = None


# ---------------------------------------------------------------------------
# Live data aggregator — pulls stats from existing DB models
# ---------------------------------------------------------------------------

def _gather_portal_context(db: Session) -> str:
    """
    Query the database for current stats and build a dynamic context
    string that gets injected into Claude's system prompt.
    """
    today = date.today()
    last_30 = today - timedelta(days=30)
    last_7 = today - timedelta(days=7)

    # ── KPI summary (today, or most recent date with data) ──
    target_date = today
    has_today = db.query(func.count(DailyStat.stat_id)).filter(
        DailyStat.stat_date == today
    ).scalar()
    if not has_today:
        latest = db.query(func.max(DailyStat.stat_date)).scalar()
        if latest:
            target_date = latest

    kpi = db.query(
        func.sum(DailyStat.total_enrollments).label("enrollments"),
        func.sum(DailyStat.total_updates).label("updates"),
        func.sum(DailyStat.aadhaar_generated).label("generated"),
        func.sum(DailyStat.pending_count).label("pending"),
        func.sum(DailyStat.rejected_count).label("rejected"),
    ).filter(DailyStat.stat_date == target_date).one()

    enrollments = int(kpi.enrollments or 0)
    updates     = int(kpi.updates or 0)
    generated   = int(kpi.generated or 0)
    pending     = int(kpi.pending or 0)
    rejected    = int(kpi.rejected or 0)
    total_processed = enrollments + updates if (enrollments + updates) > 0 else 1
    rejection_rate  = round((rejected / total_processed) * 100, 1)

    # ── Gender distribution (last 30 days) ──
    gender_rows = db.query(
        Enrollment.gender,
        func.count(Enrollment.enrollment_id).label("count"),
    ).filter(
        Enrollment.enrollment_date >= last_30
    ).group_by(Enrollment.gender).all()

    gender_total = sum(r.count for r in gender_rows) or 1
    gender_lines = []
    for r in gender_rows:
        pct = round((r.count / gender_total) * 100, 1)
        gender_lines.append(f"- {r.gender}: ~{pct}% ({r.count:,})")
    gender_text = "\n".join(gender_lines) if gender_lines else "- No data available"

    # ── Age distribution (last 30 days) ──
    age_rows = db.query(
        Enrollment.age_group,
        func.count(Enrollment.enrollment_id).label("count"),
    ).filter(
        Enrollment.enrollment_date >= last_30
    ).group_by(Enrollment.age_group).all()

    age_lines = []
    for r in age_rows:
        age_lines.append(f"- {r.age_group}: {r.count:,}")
    age_text = "\n".join(age_lines) if age_lines else "- No data available"

    # ── Update types (last 30 days) ──
    update_rows = db.query(
        Update.update_type,
        func.count(Update.update_id).label("count"),
    ).filter(
        Update.update_date >= last_30
    ).group_by(Update.update_type).order_by(
        func.count(Update.update_id).desc()
    ).all()

    update_lines = [f"- {r.update_type}: {r.count:,}" for r in update_rows]
    update_text = "\n".join(update_lines) if update_lines else "- No data available"

    # ── Biometric quality ──
    bio = db.query(
        func.avg(BiometricData.fingerprint_quality).label("fp"),
        func.avg(BiometricData.iris_quality).label("iris"),
        func.avg(BiometricData.photo_quality).label("photo"),
    ).one()

    fp_qual   = round(float(bio.fp or 0), 1)
    iris_qual = round(float(bio.iris or 0), 1)
    photo_qual = round(float(bio.photo or 0), 1)

    bio_note = ""
    if fp_qual == 0 and iris_qual == 0 and photo_qual == 0:
        bio_note = "\nNOTE: 0% scores indicate a data pipeline or API integration issue, NOT actual zero quality."

    # ── Coverage gaps (regions with no activity in 7 days) ──
    active_regions = db.query(DailyStat.region_id).filter(
        DailyStat.stat_date >= last_7
    ).distinct().subquery()

    inactive = db.query(Region).filter(
        ~Region.region_id.in_(active_regions)
    ).limit(10).all()

    if inactive:
        inactive_names = ", ".join(
            f"{r.district_name} ({r.state_name})" for r in inactive
        )
        coverage_text = (
            f"COVERAGE GAP ALERT (AI-detected, severity: Medium):\n"
            f"- No activity in last 7 days: {inactive_names}\n"
            f"- Recommended action: Deploy mobile enrollment camps in these regions"
        )
    else:
        coverage_text = "COVERAGE: All regions have recorded activity in the last 7 days. No gaps detected."

    # ── Anomalies summary ──
    anomaly_counts = db.query(
        Anomaly.severity,
        func.count(Anomaly.anomaly_id).label("count"),
    ).filter(
        Anomaly.resolved == False
    ).group_by(Anomaly.severity).all()

    anomaly_lines = [f"- {r.severity}: {r.count}" for r in anomaly_counts]
    anomaly_text = "\n".join(anomaly_lines) if anomaly_lines else "- No unresolved anomalies"

    total_anomalies = sum(r.count for r in anomaly_counts)

    # ── Build final context ──
    context = f"""CURRENT DASHBOARD DATA (as of {today.strftime('%d %B %Y')}):
- Enrollments Today: {enrollments:,}
- Updates Today: {updates:,}
- Aadhaar Generated Today: {generated:,}
- Pending Applications: {pending:,} (awaiting verification)
- Rejected Applications: {rejected:,} (needs review)
- Rejection Rate: ~{rejection_rate}% of total processed

GENDER DISTRIBUTION (Last 30 days):
{gender_text}

AGE GROUP DISTRIBUTION (Last 30 days):
{age_text}

UPDATE REQUEST TYPES (Last 30 days, ranked by volume):
{update_text}

BIOMETRIC QUALITY SCORES:
- Fingerprint Quality: {fp_qual}%
- Iris Quality: {iris_qual}%
- Photo Quality: {photo_qual}%{bio_note}

{coverage_text}

UNRESOLVED ANOMALIES ({total_anomalies} total):
{anomaly_text}"""

    return context


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """You are USTAD (Unified Smart Tracker for Aadhaar Data) — an AI-powered analytics assistant embedded in the Aadhaar Portal Analytics Dashboard. You are a helpful, professional AI assistant for administrators, policy makers, and district officers.

{live_data}

PORTAL SECTIONS:
1. Live Statistics — real-time metrics, gender/age/status charts
2. Past History — monthly trends, year-over-year growth, regional comparison
3. Insights & Improvement — AI recommendations, biometric quality, update breakdown
4. Anomalies — anomaly detection log with severity levels
5. Methodology — data collection methodology explained

EXPORT: CSV and PDF export available top-right of each section.
FILTERS: Region filter (All Regions or specific state) and date range filter with Apply button.

EXAMPLE CONVERSATION FLOWS (respond in this style):

Q: "How many enrollments today?"
→ Cite the exact live enrollment count from CURRENT DASHBOARD DATA. Mention updates and generated counts too.

Q: "Which regions have coverage gaps?"
→ List the inactive cities from the COVERAGE GAP ALERT. Recommend deploying mobile enrollment camps in those specific areas.

Q: "Why are biometric scores showing 0%?"
→ Explain this is a data pipeline or API integration issue, NOT actual zero quality. Suggest checking the data integration pipeline, verifying sensor connections, and reviewing the data ingestion scripts.

Q: "What should we do about rejections?"
→ Cite the exact rejected count and rejection rate. Suggest reviewing document validation rules, retraining operators, and auditing the rejected batch for patterns.

Q: "How do I export this data?"
→ Explain the CSV and PDF export buttons located at the top-right of each section. CSV downloads raw data; PDF uses browser print dialog.

Q: "Show me historical trends"
→ Direct user to the Past History tab in the sidebar. Describe what they'll find: Monthly Enrollment & Update Trend chart, Year-over-Year Growth chart, and Regional Comparison table.

Q: "What is the age group with highest enrollment?"
→ Cite the exact numbers from AGE GROUP DISTRIBUTION data. Identify the highest group with its count.

RESPONSE RULES:
- Introduce yourself as USTAD when first greeted
- Be concise, professional, and data-specific
- Use bullet points for multi-item answers
- Always cite exact numbers when answering data questions
- For recommendations, be actionable and specific (where, what, when)
- If asked something outside dashboard scope, say so politely
- Keep responses under 180 words unless deep analysis is needed
- Conversations should cover: live stats queries, regional coverage gaps, anomaly explanations, historical trends, biometric issues, export guidance, portal navigation help, and policy recommendations
- Format important numbers with commas for readability
- When discussing issues, always suggest a concrete next step"""


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # seconds

@router.post("/ask", response_model=ChatResponse)
async def chat_ask(
    req: ChatRequest,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Secure Anthropic Claude API proxy.
    Fetches live portal data, builds the system prompt, calls Claude,
    returns the response. API key never leaves the backend.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Chatbot is not configured. Please set ANTHROPIC_API_KEY in your .env file.",
        )

    # 1. Gather live data from the database
    try:
        live_context = _gather_portal_context(db)
    except Exception as e:
        logger.warning(f"Failed to gather portal context: {e}")
        live_context = "DASHBOARD DATA: Unable to fetch live data at this time. Answer based on general Aadhaar portal knowledge."

    # 2. Build the system prompt with real numbers
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(live_data=live_context)

    # 3. Build message list for Anthropic Claude
    # Claude uses a separate system parameter, not a system message in the list
    messages = []
    for msg in req.history[-20:]:  # Keep last 20 messages for context window
        messages.append({
            "role": msg.role,  # "user" or "assistant"
            "content": msg.content,
        })
    messages.append({
        "role": "user",
        "content": req.message,
    })

    # 4. Call Anthropic Claude API with retry logic for rate limits
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)

            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
            )

            # Extract reply text from Claude's response
            reply_text = ""
            for block in response.content:
                if block.type == "text":
                    reply_text += block.text

            if not reply_text:
                reply_text = "I apologize, I received an empty response. Please try again."

            tokens = None
            if response.usage:
                tokens = response.usage.input_tokens + response.usage.output_tokens

            return ChatResponse(reply=reply_text, tokens_used=tokens)

        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            logger.warning(f"Anthropic API attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")

            # Only retry on rate limit / overloaded errors
            is_rate_limit = any(kw in error_str for kw in [
                "rate", "quota", "limit", "overloaded", "529", "429", "too many"
            ])

            if is_rate_limit and attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)  # 2s, 4s, 8s
                logger.info(f"Rate limited. Retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                break

    # All retries exhausted or non-retryable error
    error_str = str(last_error).lower()
    logger.error(f"Anthropic API error after {MAX_RETRIES} attempts: {last_error}")

    if "api_key" in error_str or "unauthorized" in error_str or "authentication" in error_str or "invalid x-api-key" in error_str:
        raise HTTPException(
            status_code=401,
            detail="Invalid Anthropic API key. Please check your ANTHROPIC_API_KEY in .env.",
        )
    elif any(kw in error_str for kw in ["rate", "quota", "limit", "overloaded", "529", "429", "too many"]):
        raise HTTPException(
            status_code=429,
            detail="API rate limit reached. Please wait 30 seconds and try again.",
        )
    else:
        raise HTTPException(
            status_code=502,
            detail=f"AI service temporarily unavailable: {str(last_error)}",
        )
