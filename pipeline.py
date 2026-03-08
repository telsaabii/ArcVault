import os 
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from prompts import CLASSIFICATION_PROMPT,ENRICHMENT_PROMPT
from schemas import InboundMessage,Classification,Enrichment
import asyncio

def build_llm(provider: str = "openai"):
    """
    Returns the appropriate chat model
    
    Args:
    provider: "openai" or "ollama"
    """

    if provider == "openai":
        return ChatOpenAI(
            model = "gpt-4o",
            temperature=0,#DETERMINISTIC MODEL -> better for strict classification 
            api_key = os.environ["OPENAI_API_KEY"],
        )
    
    elif provider == "ollama":
        return ChatOllama(
            model = "qwen2:7b",
            temperature=0,
        )
    
    else:
        raise ValueError(f"Unknown provider '{provider}'. Choose 'openai' or 'ollama'.")


def build_classification_chain(provider:str = "openai"):
    """Returns a runnable chain: str → Classification"""
    #with_structured_output forces the llm to reply using the exact JSON structure defined in the 'Classification' Pydantic model
    llm = build_llm(provider).with_structured_output(Classification)
    #the '|' pipe operator literally means: "take classification prompt, fill in the variables, and pass resulting text into llm"
    return CLASSIFICATION_PROMPT | llm


def build_enrichment_chain(provider: str = "openai"):
    """Returns a runnable chain: str → EnrichmentResult"""
    llm = build_llm(provider).with_structured_output(Enrichment)
    return ENRICHMENT_PROMPT | llm


async def run_pipeline(
    payload: InboundMessage,
    provider: str = "openai",
) -> dict:
    """
    Runs the full classification + enrichment pipeline on an inbound message.

    Args:
        payload:  Validated InboundMessage from the ingestion endpoint.
        provider: "openai" or "ollama"

    Returns:
        dict with classification and enrichment results merged.
    """

    #setting up our chains
    classification_chain = build_classification_chain(provider)
    enrichment_chain = build_enrichment_chain(provider)


    # .ainvoke() stands for "asynchronous invoke". it triggers the chain but lets the FastAPI server handle other users while we wait for the llm to reply.
    # we pass in the payload.message to fill in the {message} variable in the prompt
    #asyncio.gather groups multiple asynchronous tasks together and tells the event loop to fire them all off at the exact same time.
    classification, enrichment = await asyncio.gather(
        classification_chain.ainvoke({"message": payload.message}),
        enrichment_chain.ainvoke({"message": payload.message})
    )

    #constructing final dictionary to return to ingest endpoint
    return {
        # ── original payload ──
        "sender": payload.sender,
        "source": payload.source,
        "raw_message": payload.message,
        # ── classification 2 ──
        "category": classification.category,
        "priority": classification.priority,
        "confidence_score": classification.confidence_score,
        # ── enrichment ──
        "core_issue": enrichment.core_issue,
        # .model_dump() converts a nested Pydantic model back into a standard Python dictionary.
        "identifiers": enrichment.identifiers.model_dump(exclude_none=True),
        "urgency_signal": enrichment.urgency_signal,
    }
