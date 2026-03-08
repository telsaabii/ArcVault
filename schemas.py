from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum

class MessageSource(str, Enum):
    EMAIL = "email"
    WEB_FORM = "web_form"
    SUPPORT_PORTAL = "support_portal"

class InboundMessage(BaseModel):
    message: str = Field(
        ...,#required field
        min_length=1,
        description="Raw unstructured message content from the customer",
    )
    source: MessageSource = Field(
        ...,
        description="Channel the message arrived from: email, web_form, or support_portal",
    )
    sender: str = Field(
        ...,
        min_length=1,
        description="Identifier for the sender — email address or user ID",
    )

class Classification(BaseModel):
    """
    LLM-Assigned classification for inbound message
    """
    category : Literal[
        "Bug Report",
        "Feature Request",
        "Billing Issue",
        "Technical Question",
        "Incident/Outage",
    ] = Field(
        description = "The category that best describes the message"
    )

    priority : Literal[
        "Low"
        ,"Medium"
        ,"High",
    ] = Field(
        description = "Urgency level of message based on impact on the business "
    )

    confidence_score: float = Field(
        ge = 0.0,
        le=1.0,
        description = "Model's confidence in the classification and must lie between 0.0 and 1.0"
    )

class Identifiers(BaseModel):
    """Structured bag of identifiers extracted from the message. All optional."""

    account_id: Optional[str] = Field(None, description="Customer or account ID if mentioned.")
    invoice_number: Optional[str] = Field(None, description="Invoice number if mentioned.")
    error_code: Optional[str] = Field(None, description="Error or status code if mentioned.")
    other: Optional[str] = Field(
        None, description="Any other relevant identifier not covered above."
    )

class Enrichment(BaseModel):
    """Structured entities extracted from the inbound message."""

    core_issue: str = Field(
        description="One-sentence summary of the core problem or request."
    )
    identifiers: Identifiers = Field(
        description="Key identifiers mentioned in the message (account IDs, invoice numbers, error codes, etc.)."
    )
    urgency_signal: Literal["Low", "Moderate", "High", "Critical"] = Field(
        description=(
            "Urgency derived from tone and content: "
            "Critical = production down / all users affected, "
            "High = significant business impact "
            "Moderate = degraded experience, "
            "Low = general inquiry"
        )
    )


Routing_Queue = Literal[
    "Engineering",
    "Billing",
    "Product",
    "IT/Security",
    "Escalation",
]

class RoutingResult(BaseModel):
    """Destination queue and reasoning for an inbound message."""

    queue: Routing_Queue = Field(
        description=(
            "The destination queue for this message. "
            "Must be one of: Engineering, Billing, Product, Security, Escalation."
        )
    )
    routing_reason: str = Field(
        description="One sentence explaining why this queue was chosen."
    )
    escalated: bool = Field(
        description="True if the record was sent to the Escalation queue for human review."
    )
    escalation_reason: Optional[str] = Field(
        None,
        description="Populated only when escalated=True. Explains the specific trigger.",
    )
    summary: str = Field(
        description="A 2-3 sentence human-readable summary of the entire request, the classification, and why it is being routed to this specific team."
    )
