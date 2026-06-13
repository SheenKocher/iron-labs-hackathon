from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os
import json
import uuid
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

from mock_data import PROSPECTS, DEALS, LEADS_BY_INDUSTRY
from mcp_tools import generate_cold_email, review_email, lookup_prospect, get_deal_notes, find_similar_leads
from ironlabs_router import ironlabs_model_select

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client[os.environ['DB_NAME']]

# LLM Config
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
FAST_MODEL = os.environ.get('FAST_MODEL', 'gpt-4o-mini')
STRONG_MODEL = os.environ.get('STRONG_MODEL', 'gpt-4o')

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Pydantic Models ---

class ChatRequest(BaseModel):
    message: str

class MetadataResponse(BaseModel):
    model_used: str
    tool_used: str
    category: str
    complexity: str
    routing_source: str = "local"

class EmailDraft(BaseModel):
    subject: str
    body: str

class ChatResponse(BaseModel):
    response: str
    metadata: MetadataResponse
    email_draft: Optional[EmailDraft] = None


# --- Classification ---

CLASSIFICATION_PROMPT = """You are a request classifier for a sales assistant.
Classify the user's message into exactly one category:
- cold_email_draft
- email_review
- prospect_lookup
- deal_lookup
- lead_gen
- general

Also rate complexity as "low", "medium", or "high".

Respond ONLY with JSON: {"category": "...", "complexity": "..."}"""


async def classify_request(message: str) -> dict:
    """Classify a user request using the fast model."""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=str(uuid.uuid4()),
            system_message=CLASSIFICATION_PROMPT,
        ).with_model("openai", FAST_MODEL)

        content = await chat.send_message(UserMessage(text=message))
        content = content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        result = json.loads(content)
        return {
            "category": result.get("category", "general"),
            "complexity": result.get("complexity", "low")
        }
    except Exception as e:
        logger.error(f"Classification error: {e}")
        return {"category": "general", "complexity": "low"}


# --- Routing Table ---

ROUTING_TABLE = {
    "cold_email_draft": {"tool": "generate_cold_email", "model_rule": lambda c: STRONG_MODEL if c == "high" else FAST_MODEL},
    "email_review": {"tool": "review_email", "model_rule": lambda c: STRONG_MODEL},
    "prospect_lookup": {"tool": "lookup_prospect", "model_rule": lambda c: FAST_MODEL},
    "deal_lookup": {"tool": "get_deal_notes", "model_rule": lambda c: FAST_MODEL},
    "lead_gen": {"tool": "find_similar_leads", "model_rule": lambda c: FAST_MODEL},
    "general": {"tool": "none", "model_rule": lambda c: STRONG_MODEL if c == "high" else FAST_MODEL},
}


def get_route(category: str, complexity: str) -> dict:
    """Determine the tool and model based on category and complexity."""
    route = ROUTING_TABLE.get(category, ROUTING_TABLE["general"])
    return {
        "tool": route["tool"],
        "model": route["model_rule"](complexity)
    }


# --- Tool Execution ---

async def execute_tool(tool_name: str, model: str, user_message: str) -> dict:
    """Execute the appropriate MCP tool based on the routing decision."""
    if tool_name == "generate_cold_email":
        parts = user_message.lower()
        prospect_name = "Prospect"
        company = "their company"
        context = user_message

        for name in PROSPECTS:
            if name in parts:
                prospect_name = PROSPECTS[name]["name"]
                company = PROSPECTS[name]["company"]
                break

        result = await generate_cold_email(EMERGENT_LLM_KEY, model, prospect_name, company, context)
        return {"type": "email_draft", "data": result}

    elif tool_name == "review_email":
        result = await review_email(EMERGENT_LLM_KEY, model, user_message)
        return {"type": "email_review", "data": result}

    elif tool_name == "lookup_prospect":
        name = user_message
        for key in ["look up", "lookup", "find", "search", "prospect", "about", "info on", "who is"]:
            if key in user_message.lower():
                name = user_message.lower().split(key)[-1].strip().rstrip("?.!")
                break
        result = lookup_prospect(name)
        return {"type": "prospect_data", "data": result}

    elif tool_name == "get_deal_notes":
        deal_id = ""
        words = user_message.split()
        for word in words:
            cleaned = word.strip(",.!?").upper()
            if cleaned.startswith("D-"):
                deal_id = cleaned
                break
        if not deal_id:
            for word in words:
                cleaned = word.strip(",.!?")
                if any(c.isdigit() for c in cleaned):
                    deal_id = f"D-{cleaned.replace('D-', '').replace('d-', '')}"
                    break
        if not deal_id:
            deal_id = "D-1042"
        result = get_deal_notes(deal_id)
        return {"type": "deal_data", "data": result}

    elif tool_name == "find_similar_leads":
        industry = "default"
        for ind in ["saas", "fintech", "healthcare"]:
            if ind in user_message.lower():
                industry = ind
                break
        criteria = user_message
        result = find_similar_leads(industry, criteria)
        return {"type": "lead_list", "data": result}

    return {"type": "none", "data": None}


# --- Final Response Generation ---

async def generate_final_response(model: str, user_message: str, tool_output: dict, category: str) -> str:
    """Generate the final response using the selected model, incorporating tool output."""
    system_prompt = "You are PitchRoute, an expert AI sales assistant. You help sales reps with cold emails, email reviews, prospect research, deal tracking, and lead generation. Be concise, actionable, and professional. Use bullet points where appropriate."

    context_parts = [f"User request: {user_message}"]

    if tool_output["type"] == "email_draft":
        data = tool_output["data"]
        context_parts.append(f"\nGenerated email draft:\nSubject: {data.get('subject', '')}\nBody: {data.get('body', '')}")
        context_parts.append("\nPresent this email draft to the user. Briefly explain why you chose this approach.")

    elif tool_output["type"] == "email_review":
        data = tool_output["data"]
        context_parts.append(f"\nEmail review results:\nScore: {data.get('score', 'N/A')}/10\nSuggestions: {json.dumps(data.get('suggestions', []))}")
        if data.get("improved_draft"):
            context_parts.append(f"\nImproved draft: {data['improved_draft']}")
        context_parts.append("\nPresent the review feedback clearly with the score, suggestions, and improved version.")

    elif tool_output["type"] == "prospect_data":
        data = tool_output["data"]
        context_parts.append(f"\nProspect data found:\n{json.dumps(data, indent=2)}")
        context_parts.append("\nSummarize this prospect info and suggest next steps for the rep.")

    elif tool_output["type"] == "deal_data":
        data = tool_output["data"]
        context_parts.append(f"\nDeal data found:\n{json.dumps(data, indent=2)}")
        context_parts.append("\nSummarize the deal status and suggest actions based on the current stage.")

    elif tool_output["type"] == "lead_list":
        data = tool_output["data"]
        context_parts.append(f"\nSimilar leads found:\n{json.dumps(data, indent=2)}")
        context_parts.append("\nPresent these leads in a clear format and suggest outreach priorities.")

    full_context = "\n".join(context_parts)

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=str(uuid.uuid4()),
            system_message=system_prompt,
        ).with_model("openai", model)

        response = await chat.send_message(UserMessage(text=full_context))
        return response.strip()
    except Exception as e:
        logger.error(f"Final response generation error: {e}")
        raise


# --- API Routes ---

@api_router.get("/")
async def root():
    return {"message": "PitchRoute API is running"}


@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint that processes user requests through the routing pipeline."""
    user_message = request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Step 1: Classify the request
    classification = await classify_request(user_message)
    category = classification["category"]
    complexity = classification["complexity"]
    logger.info(f"Classification: category={category}, complexity={complexity}")

    # Step 2: Get routing decision (try IronLabs first, fall back to local)
    route = get_route(category, complexity)
    tool_name = route["tool"]
    model = route["model"]
    routing_source = "local"

    # Try IronLabs intelligent routing for model selection
    ironlabs_result = await ironlabs_model_select(
        messages=[{"role": "user", "content": user_message}],
        models=[
            {"provider": "openai", "model": FAST_MODEL},
            {"provider": "openai", "model": STRONG_MODEL},
        ],
        tradeoff="performance",
    )
    if ironlabs_result:
        model = ironlabs_result["model"]
        routing_source = "ironlabs"
        logger.info(f"IronLabs routing selected model: {model}")
    else:
        logger.info(f"Using local routing: tool={tool_name}, model={model}")
    logger.info(f"Routing [{routing_source}]: tool={tool_name}, model={model}")

    # Step 3: Execute tool if needed
    tool_output = {"type": "none", "data": None}
    if tool_name != "none":
        try:
            tool_output = await execute_tool(tool_name, model, user_message)
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            tool_output = {"type": "error", "data": str(e)}

    # Step 4: Generate final response
    try:
        response_text = await generate_final_response(model, user_message, tool_output, category)
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        response_text = f"I encountered an issue processing your request. Error: {str(e)}"

    # Build email_draft if applicable
    email_draft = None
    if tool_output["type"] == "email_draft" and isinstance(tool_output["data"], dict):
        email_draft = EmailDraft(
            subject=tool_output["data"].get("subject", ""),
            body=tool_output["data"].get("body", "")
        )
    elif tool_output["type"] == "email_review" and isinstance(tool_output["data"], dict):
        improved = tool_output["data"].get("improved_draft")
        if improved:
            email_draft = EmailDraft(
                subject="Re: Improved Draft",
                body=improved
            )

    # Save conversation to DB
    try:
        await db.conversations.insert_one({
            "user_message": user_message,
            "ai_response": response_text,
            "category": category,
            "complexity": complexity,
            "tool_used": tool_name,
            "model_used": model,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"DB save error: {e}")

    return ChatResponse(
        response=response_text,
        metadata=MetadataResponse(
            model_used=model,
            tool_used=tool_name,
            category=category,
            complexity=complexity,
            routing_source=routing_source
        ),
        email_draft=email_draft
    )


@api_router.get("/conversations")
async def get_conversations():
    """Get recent conversations."""
    convos = await db.conversations.find(
        {}, {"_id": 0}
    ).sort("timestamp", -1).to_list(50)
    return convos


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    mongo_client.close()
