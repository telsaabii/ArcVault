from pipeline import build_llm
from prompts import ROUTING_PROMPT
from schemas import RoutingResult
import re
import logging
from write_to_sheets import _write_to_sheets
logger = logging.getLogger(__name__)
import asyncio

# Escalation keyword patterns (case-insensitive)
ESCALATION_KEYWORDS = re.compile(
    r"outage|down for all users|billing error.*\$\s*[5-9]\d{2,}|"   # > $500
    r"billing error.*\$[1-9]\d{3,}|"                                # catches $1,000–$4,999 missed by pattern above.
    r"data loss|security breach|unauthorized access",
    re.IGNORECASE,
)

CONFIDENCE_THRESHOLD = 0.70
HIGH_PRIORITY_CONFIDENCE_THRESHOLD = 0.85


def _escalation_check(pipeline_result: dict) -> tuple[bool, str | None]:
    """
    Returns (should_escalate: bool, reason: str | None).

    Checks happen in priority order:
      1. Low-confidence classification
      2. Keyword match in the raw message
    """
    confidence: float = pipeline_result.get("confidence_score", 1.0)
    priority: str = pipeline_result.get("priority", "")
    urgency: str = pipeline_result.get("urgency_signal", "")

    if confidence < CONFIDENCE_THRESHOLD:
        return True, (
            f"Confidence score {confidence:.0%} is below the {CONFIDENCE_THRESHOLD:.0%} threshold."
        )
    
    if priority == "High" and confidence < HIGH_PRIORITY_CONFIDENCE_THRESHOLD:
        return True, (
            f"High priority message has confidence score {confidence:.0%}, "
            f"below the {HIGH_PRIORITY_CONFIDENCE_THRESHOLD:.0%} threshold required for high priority records."
        )
    
    if urgency == "Critical":
        return True, (
            "Enrichment agent independently assessed urgency as Critical."
        )


    raw: str = pipeline_result.get("raw_message", "")
    match = ESCALATION_KEYWORDS.search(raw)
    if match:
        # match.group(0) extracts the exact text that triggered the regex
        return True, f"Escalation keyword detected: '{match.group(0)}'."

    return False, None


async def run_routing(pipeline_result: dict, provider: str = "openai") -> dict:
    """
    Takes the merged dict returned by pipeline.run_pipeline(), determines the
    correct queue, writes to Google Sheets, and returns the fully enriched record.

    Args:
        pipeline_result : dict returned by run_pipeline()
        provider        : "openai" or "ollama"

    Returns:
        The same dict with routing fields merged in.
    """
    # Step 1 — hard-coded escalation pre-check (no LLM needed)
    should_escalate, escalation_reason = _escalation_check(pipeline_result)

    if should_escalate:
        routing = RoutingResult(
            queue="Escalation",
            routing_reason="Automatically escalated — see escalation_reason for details.",
            escalated=True,
            escalation_reason=escalation_reason,
            summary=f"AUTOMATED ESCALATION: This message was flagged for human review because: {escalation_reason}. Please review the raw message immediately."
        )
        logger.info("Escalated | reason=%s", escalation_reason)

    else:
        # Step 2 — LLM picks the queue
        llm   = build_llm(provider).with_structured_output(RoutingResult)
        chain = ROUTING_PROMPT | llm

        routing: RoutingResult = await chain.ainvoke({
            "confidence_threshold": f"{CONFIDENCE_THRESHOLD:.0%}",
            "category":         pipeline_result.get("category", ""),
            "priority":         pipeline_result.get("priority", ""),
            "confidence_score": pipeline_result.get("confidence_score", ""),
            "core_issue":       pipeline_result.get("core_issue", ""),
            "urgency_signal":   pipeline_result.get("urgency_signal", ""),
            "raw_message":      pipeline_result.get("raw_message", ""),
        })
        logger.info("Routed to %s", routing.queue)

    # Step 3 — merge routing fields into the record
    full_record = {
        **pipeline_result,
        "queue":             routing.queue,
        "routing_reason":    routing.routing_reason,
        "escalated":         routing.escalated,
        "escalation_reason": routing.escalation_reason,
        "summary":           routing.summary,
    }

    # Step 4 — persist to Google Sheets
    #_write_to_sheets(full_record)
    #Offloads to a background thread , asyncio to thread takes a blocking, synchronous function and tosses it into a separate background thread.
    await asyncio.to_thread(_write_to_sheets, full_record)

    logger.info("Successfully wrote record to Google Sheets.")

    return full_record