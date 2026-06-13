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


COLD_EMAIL_SYSTEM_PROMPT = """You are an expert B2B sales copywriter specializing in cold outreach emails.
Your emails are concise, personalized, and avoid generic sales language ("I hope this finds you well", "I wanted to reach out", "synergy", etc.).

Given details about a prospect and context, write a cold outreach email that:
- Has a short, specific subject line (under 8 words, no clickbait)
- Opens with a personalized hook based on the prospect's role/company/recent activity (not a generic greeting)
- States a clear, specific value proposition in 1-2 sentences
- Ends with a low-friction call to action (e.g., a question or a short meeting ask, NOT "let me know if you're interested")
- Is no longer than 100 words total in the body
- Uses a professional but conversational tone — not robotic, not overly casual

Respond ONLY with valid JSON in this exact format:
{"subject": "...", "body": "..."}"""


EMAIL_REVIEW_SYSTEM_PROMPT = """You are an experienced sales coach who reviews cold outreach emails for B2B sales reps.

Given a draft email, evaluate it on these dimensions:
- Personalization (is it specific to the prospect, or generic?)
- Clarity of value proposition (is the "why should I care" obvious in the first few lines?)
- Tone (professional but human, not robotic or overly salesy)
- Call to action (is it low-friction and clear, or vague/pushy?)
- Length and readability (concise, scannable, no unnecessary filler)

Provide:
- An overall score from 1-10
- 2-3 specific, actionable suggestions for improvement (reference exact phrases from the draft where relevant)
- An improved version of the email that applies your suggestions

Be direct and specific — avoid vague praise like "good job" or "nice email." Point out exactly what works and what doesn't.

Respond ONLY with valid JSON in this exact format:
{
  "score": <number>,
  "suggestions": ["...", "...", "..."],
  "improved_draft": {"subject": "...", "body": "..."}
}"""


def _parse_json_response(content: str) -> dict:
    """Parse JSON from an LLM response, handling code blocks."""
    content = content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    return json.loads(content)


async def generate_cold_email(api_key: str, model: str, prospect_name: str, company: str, context: str) -> dict:
    """Generate a personalized cold outreach email."""
    user_prompt = f"""Prospect: {prospect_name}
Company: {company}
Context: {context}"""

    try:
        content = await _llm_call(api_key, model, COLD_EMAIL_SYSTEM_PROMPT, user_prompt)
        return _parse_json_response(content)
    except json.JSONDecodeError:
        return {"subject": "Let's connect", "body": content.strip()}
    except Exception as e:
        logger.error(f"generate_cold_email error: {e}")
        raise


async def review_email(api_key: str, model: str, draft_text: str) -> dict:
    """Review a sales email draft for tone, clarity, and persuasiveness."""
    user_prompt = f"""Draft to review:
{draft_text}"""

    try:
        content = await _llm_call(api_key, model, EMAIL_REVIEW_SYSTEM_PROMPT, user_prompt)
        result = _parse_json_response(content)
        # Normalize improved_draft to always be a dict with subject/body
        improved = result.get("improved_draft")
        if isinstance(improved, str):
            result["improved_draft"] = {"subject": "Improved Draft", "body": improved}
        elif isinstance(improved, dict):
            if "subject" not in improved:
                improved["subject"] = "Improved Draft"
            if "body" not in improved:
                improved["body"] = str(improved)
        return result
    except json.JSONDecodeError:
        return {"score": 0, "suggestions": ["Could not parse review"], "improved_draft": {"subject": "N/A", "body": draft_text}}
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
