"""MCP Server - In-process tool functions for PitchRoute using Emergent Integrations."""

import json
import logging
import uuid
from emergentintegrations.llm.chat import LlmChat, UserMessage
from mock_data import PROSPECTS, DEFAULT_PROSPECT, DEALS, DEFAULT_DEAL, LEADS_BY_INDUSTRY

logger = logging.getLogger(__name__)


async def _llm_call(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    """Helper to make a non-streaming LLM call."""
    chat = LlmChat(
        api_key=api_key,
        session_id=str(uuid.uuid4()),
        system_message=system_prompt,
    ).with_model("openai", model)

    response = await chat.send_message(UserMessage(text=user_prompt))
    return response


async def generate_cold_email(api_key: str, model: str, prospect_name: str, company: str, context: str) -> dict:
    """Generate a personalized cold outreach email."""
    system_prompt = "You are an expert B2B sales copywriter. You write personalized, concise cold outreach emails."
    user_prompt = f"""Draft a personalized cold outreach email.

Prospect: {prospect_name}
Company: {company}
Context: {context}

Write a compelling, concise cold email with:
- A personalized subject line
- A short, engaging opening that references something specific about them
- A clear value proposition (1-2 sentences)
- A soft CTA (not pushy)

Respond ONLY with JSON: {{"subject": "...", "body": "..."}}"""

    try:
        content = await _llm_call(api_key, model, system_prompt, user_prompt)
        content = content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)
    except json.JSONDecodeError:
        return {"subject": "Let's connect", "body": content}
    except Exception as e:
        logger.error(f"generate_cold_email error: {e}")
        raise


async def review_email(api_key: str, model: str, draft_text: str) -> dict:
    """Review a sales email draft for tone, clarity, and persuasiveness."""
    system_prompt = "You are a sales email coach. You review email drafts for tone, clarity, and persuasiveness."
    user_prompt = f"""Review this draft for tone, clarity, and persuasiveness.
Give a score (1-10) and 2-3 specific suggestions. Also provide an improved version of the draft.

Draft:
{draft_text}

Respond ONLY with JSON: {{"score": <number>, "suggestions": ["...", "..."], "improved_draft": "..."}}"""

    try:
        content = await _llm_call(api_key, model, system_prompt, user_prompt)
        content = content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)
    except json.JSONDecodeError:
        return {"score": 0, "suggestions": ["Could not parse review"], "improved_draft": draft_text}
    except Exception as e:
        logger.error(f"review_email error: {e}")
        raise


def lookup_prospect(name: str) -> dict:
    """Look up a prospect by name from mock data."""
    key = name.strip().lower()
    for prospect_key, prospect_data in PROSPECTS.items():
        if key in prospect_key or prospect_key in key:
            return prospect_data
    return {**DEFAULT_PROSPECT, "name": name}


def get_deal_notes(deal_id: str) -> dict:
    """Get deal notes by deal ID from mock data."""
    key = deal_id.strip().lower()
    for deal_key, deal_data in DEALS.items():
        if key in deal_key or deal_key in key:
            return deal_data
    return {**DEFAULT_DEAL, "deal_id": deal_id}


def find_similar_leads(industry: str, criteria: str = "") -> list:
    """Find similar leads matching industry/criteria from mock data."""
    key = industry.strip().lower()
    for ind_key, leads in LEADS_BY_INDUSTRY.items():
        if key in ind_key or ind_key in key:
            return leads
    return LEADS_BY_INDUSTRY["default"]
