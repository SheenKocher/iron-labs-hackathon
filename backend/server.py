from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from emergentintegrations.llm.chat import LlmChat, UserMessage
import asyncio
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


# --- Classification & Planning ---

CLASSIFICATION_PROMPT = """You are a request planner for a sales assistant. Analyze the user's message and create an execution plan.

Available tools:
- cold_email_draft: Draft a cold outreach email
- email_review: Review/improve an email draft
- prospect_lookup: Look up prospect info by name
- deal_lookup: Look up deal info by deal ID
- lead_gen: Find similar leads by industry
- none: General question, no tool needed

If the request requires MULTIPLE steps (e.g. "look up deal D-1042 then draft an email about it"), list ALL steps in order.

Rate overall complexity as "low", "medium", or "high".

Respond ONLY with JSON:
{
  "steps": [
    {"tool": "deal_lookup", "reason": "Fetch deal D-1042 details"},
    {"tool": "cold_email_draft", "reason": "Draft email using deal context"}
  ],
  "complexity": "medium"
}

For simple single-tool requests, just return one step. For general questions with no tool, use [{"tool": "none", "reason": "..."}]."""


async def plan_request(message: str) -> dict:
    """Plan the execution steps for a user request."""
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
        steps = result.get("steps", [])
        if not steps:
            steps = [{"tool": "none", "reason": "general"}]
        return {
            "steps": steps,
            "complexity": result.get("complexity", "low")
        }
    except Exception as e:
        logger.error(f"Planning error: {e}")
        return {"steps": [{"tool": "none", "reason": "fallback"}], "complexity": "low"}


# Map tool names to categories for metadata
TOOL_TO_CATEGORY = {
    "generate_cold_email": "cold_email_draft",
    "cold_email_draft": "cold_email_draft",
    "review_email": "email_review",
    "email_review": "email_review",
    "lookup_prospect": "prospect_lookup",
    "prospect_lookup": "prospect_lookup",
    "get_deal_notes": "deal_lookup",
    "deal_lookup": "deal_lookup",
    "find_similar_leads": "lead_gen",
    "lead_gen": "lead_gen",
    "none": "general",
}

# Map plan tool names to actual function tool names
PLAN_TO_TOOL = {
    "cold_email_draft": "generate_cold_email",
    "email_review": "review_email",
    "prospect_lookup": "lookup_prospect",
    "deal_lookup": "get_deal_notes",
    "lead_gen": "find_similar_leads",
    "generate_cold_email": "generate_cold_email",
    "review_email": "review_email",
    "lookup_prospect": "lookup_prospect",
    "get_deal_notes": "get_deal_notes",
    "find_similar_leads": "find_similar_leads",
    "none": "none",
}


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

    def append_tool_context(output):
        if output["type"] == "email_draft":
            data = output["data"]
            context_parts.append(f"\nGenerated email draft:\nSubject: {data.get('subject', '')}\nBody: {data.get('body', '')}")
            context_parts.append("\nPresent this email draft to the user. Briefly explain why you chose this approach.")
        elif output["type"] == "email_review":
            data = output["data"]
            context_parts.append(f"\nEmail review results:\nScore: {data.get('score', 'N/A')}/10\nSuggestions: {json.dumps(data.get('suggestions', []))}")
            if data.get("improved_draft"):
                context_parts.append(f"\nImproved draft: {data['improved_draft']}")
            context_parts.append("\nPresent the review feedback clearly with the score, suggestions, and improved version.")
        elif output["type"] == "prospect_data":
            data = output["data"]
            context_parts.append(f"\nProspect data found:\n{json.dumps(data, indent=2)}")
            context_parts.append("\nSummarize this prospect info and suggest next steps for the rep.")
        elif output["type"] == "deal_data":
            data = output["data"]
            context_parts.append(f"\nDeal data found:\n{json.dumps(data, indent=2)}")
            context_parts.append("\nSummarize the deal status and suggest actions based on the current stage.")
        elif output["type"] == "lead_list":
            data = output["data"]
            context_parts.append(f"\nSimilar leads found:\n{json.dumps(data, indent=2)}")
            context_parts.append("\nPresent these leads in a clear format and suggest outreach priorities.")

    if tool_output["type"] == "multi_step":
        # Multi-step: append context from all tool outputs
        context_parts.append("\n--- Multi-step execution results ---")
        for i, step_output in enumerate(tool_output["data"]):
            context_parts.append(f"\n[Step {i+1}]")
            append_tool_context(step_output)
        context_parts.append("\nSynthesize ALL the above results into a cohesive response that addresses the user's full request. If there's an email draft, present it clearly.")
    else:
        append_tool_context(tool_output)

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
    """Main chat endpoint with multi-step planning support."""
    user_message = request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Step 1: Plan the request (may produce multiple steps)
    plan = await plan_request(user_message)
    steps = plan["steps"]
    complexity = plan["complexity"]
    logger.info(f"Plan: {len(steps)} step(s), complexity={complexity}")
    for i, s in enumerate(steps):
        logger.info(f"  Step {i+1}: {s['tool']} — {s.get('reason', '')}")

    # Determine model tier based on complexity
    model = STRONG_MODEL if complexity == "high" else FAST_MODEL
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

    # Step 2: Execute all tool steps sequentially, accumulating context
    all_tool_outputs = []
    tools_used = []
    categories = []
    accumulated_context = ""

    for step in steps:
        raw_tool = step.get("tool", "none")
        tool_name = PLAN_TO_TOOL.get(raw_tool, "none")
        category = TOOL_TO_CATEGORY.get(raw_tool, "general")
        categories.append(category)

        if tool_name == "none":
            tools_used.append("none")
            continue

        tools_used.append(tool_name)

        # For subsequent steps, enrich the message with accumulated context
        enriched_message = user_message
        if accumulated_context:
            enriched_message = f"{user_message}\n\n--- Context from previous steps ---\n{accumulated_context}"

        # Use strong model for email drafting when it follows a data lookup
        step_model = model
        if tool_name == "generate_cold_email" and accumulated_context:
            step_model = STRONG_MODEL
        elif tool_name == "review_email":
            step_model = STRONG_MODEL

        try:
            tool_output = await execute_tool(tool_name, step_model, enriched_message)
            all_tool_outputs.append(tool_output)

            # Build accumulated context from this tool's output
            if tool_output["type"] == "deal_data" and isinstance(tool_output["data"], dict):
                accumulated_context += f"\nDeal info: {json.dumps(tool_output['data'], indent=2)}"
            elif tool_output["type"] == "prospect_data" and isinstance(tool_output["data"], dict):
                accumulated_context += f"\nProspect info: {json.dumps(tool_output['data'], indent=2)}"
            elif tool_output["type"] == "lead_list" and isinstance(tool_output["data"], list):
                accumulated_context += f"\nLead list: {json.dumps(tool_output['data'], indent=2)}"
            elif tool_output["type"] == "email_draft" and isinstance(tool_output["data"], dict):
                accumulated_context += f"\nEmail draft — Subject: {tool_output['data'].get('subject', '')}\nBody: {tool_output['data'].get('body', '')}"
            elif tool_output["type"] == "email_review" and isinstance(tool_output["data"], dict):
                accumulated_context += f"\nEmail review — Score: {tool_output['data'].get('score', 'N/A')}, Suggestions: {json.dumps(tool_output['data'].get('suggestions', []))}"

        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            all_tool_outputs.append({"type": "error", "data": str(e)})

    # Step 3: Generate final response using all accumulated context
    # Merge all tool outputs into a combined output for the final response
    combined_output = {"type": "none", "data": None}
    if len(all_tool_outputs) == 1:
        combined_output = all_tool_outputs[0]
    elif len(all_tool_outputs) > 1:
        combined_output = {
            "type": "multi_step",
            "data": all_tool_outputs,
            "accumulated_context": accumulated_context
        }

    # Determine the primary category (last meaningful one)
    primary_category = categories[-1] if categories else "general"

    try:
        response_text = await generate_final_response(
            STRONG_MODEL if len(steps) > 1 else model,
            user_message,
            combined_output,
            primary_category
        )
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        response_text = f"I encountered an issue processing your request. Error: {str(e)}"

    # Build email_draft from the last email-producing tool output
    email_draft = None
    for tool_output in reversed(all_tool_outputs):
        if tool_output.get("type") == "email_draft" and isinstance(tool_output.get("data"), dict):
            email_draft = EmailDraft(
                subject=tool_output["data"].get("subject", ""),
                body=tool_output["data"].get("body", "")
            )
            break
        elif tool_output.get("type") == "email_review" and isinstance(tool_output.get("data"), dict):
            improved = tool_output["data"].get("improved_draft")
            if improved:
                email_draft = EmailDraft(subject="Re: Improved Draft", body=improved)
                break

    # Tools/categories summary for metadata
    tools_str = " → ".join(tools_used) if tools_used else "none"
    categories_str = " → ".join(categories) if categories else "general"

    # Save conversation to DB
    try:
        await db.conversations.insert_one({
            "user_message": user_message,
            "ai_response": response_text,
            "category": categories_str,
            "complexity": complexity,
            "tool_used": tools_str,
            "model_used": model,
            "steps": len(steps),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"DB save error: {e}")

    return ChatResponse(
        response=response_text,
        metadata=MetadataResponse(
            model_used=STRONG_MODEL if len(steps) > 1 else model,
            tool_used=tools_str,
            category=categories_str,
            complexity=complexity,
            routing_source=routing_source
        ),
        email_draft=email_draft
    )


def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@api_router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE streaming chat endpoint with real-time step progress."""
    user_message = request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    async def event_generator():
        # --- Planning phase ---
        yield _sse_event("planning", {"status": "Analyzing request..."})

        plan = await plan_request(user_message)
        steps = plan["steps"]
        complexity = plan["complexity"]

        step_summaries = [
            {"tool": PLAN_TO_TOOL.get(s.get("tool", "none"), "none"),
             "category": TOOL_TO_CATEGORY.get(s.get("tool", "none"), "general"),
             "reason": s.get("reason", "")}
            for s in steps
        ]

        yield _sse_event("plan", {
            "steps": step_summaries,
            "complexity": complexity,
            "total_steps": len(steps),
        })

        # --- Model routing ---
        model = STRONG_MODEL if complexity == "high" else FAST_MODEL
        routing_source = "local"

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

        # --- Execute tool steps ---
        all_tool_outputs = []
        tools_used = []
        categories = []
        accumulated_context = ""

        for idx, step in enumerate(steps):
            raw_tool = step.get("tool", "none")
            tool_name = PLAN_TO_TOOL.get(raw_tool, "none")
            category = TOOL_TO_CATEGORY.get(raw_tool, "general")
            categories.append(category)

            if tool_name == "none":
                tools_used.append("none")
                yield _sse_event("step_start", {
                    "step": idx, "tool": "none", "category": category,
                    "reason": step.get("reason", "General response"),
                })
                yield _sse_event("step_complete", {"step": idx, "tool": "none", "status": "skipped"})
                continue

            tools_used.append(tool_name)

            yield _sse_event("step_start", {
                "step": idx, "tool": tool_name, "category": category,
                "reason": step.get("reason", ""),
            })

            enriched_message = user_message
            if accumulated_context:
                enriched_message = f"{user_message}\n\n--- Context from previous steps ---\n{accumulated_context}"

            step_model = model
            if tool_name == "generate_cold_email" and accumulated_context:
                step_model = STRONG_MODEL
            elif tool_name == "review_email":
                step_model = STRONG_MODEL

            try:
                tool_output = await execute_tool(tool_name, step_model, enriched_message)
                all_tool_outputs.append(tool_output)

                if tool_output["type"] == "deal_data" and isinstance(tool_output["data"], dict):
                    accumulated_context += f"\nDeal info: {json.dumps(tool_output['data'], indent=2)}"
                elif tool_output["type"] == "prospect_data" and isinstance(tool_output["data"], dict):
                    accumulated_context += f"\nProspect info: {json.dumps(tool_output['data'], indent=2)}"
                elif tool_output["type"] == "lead_list" and isinstance(tool_output["data"], list):
                    accumulated_context += f"\nLead list: {json.dumps(tool_output['data'], indent=2)}"
                elif tool_output["type"] == "email_draft" and isinstance(tool_output["data"], dict):
                    accumulated_context += f"\nEmail draft — Subject: {tool_output['data'].get('subject', '')}\nBody: {tool_output['data'].get('body', '')}"
                elif tool_output["type"] == "email_review" and isinstance(tool_output["data"], dict):
                    accumulated_context += f"\nEmail review — Score: {tool_output['data'].get('score', 'N/A')}, Suggestions: {json.dumps(tool_output['data'].get('suggestions', []))}"

                yield _sse_event("step_complete", {"step": idx, "tool": tool_name, "status": "done"})

            except Exception as e:
                logger.error(f"Tool execution error ({tool_name}): {e}")
                all_tool_outputs.append({"type": "error", "data": str(e)})
                yield _sse_event("step_complete", {"step": idx, "tool": tool_name, "status": "error", "error": str(e)})

        # --- Final response generation ---
        yield _sse_event("generating", {"status": "Synthesizing final response..."})

        combined_output = {"type": "none", "data": None}
        if len(all_tool_outputs) == 1:
            combined_output = all_tool_outputs[0]
        elif len(all_tool_outputs) > 1:
            combined_output = {"type": "multi_step", "data": all_tool_outputs, "accumulated_context": accumulated_context}

        primary_category = categories[-1] if categories else "general"
        final_model = STRONG_MODEL if len(steps) > 1 else model

        try:
            response_text = await generate_final_response(final_model, user_message, combined_output, primary_category)
        except Exception as e:
            response_text = f"Error generating response: {str(e)}"

        # Build email_draft
        email_draft_data = None
        for tool_output in reversed(all_tool_outputs):
            if tool_output.get("type") == "email_draft" and isinstance(tool_output.get("data"), dict):
                email_draft_data = {"subject": tool_output["data"].get("subject", ""), "body": tool_output["data"].get("body", "")}
                break
            elif tool_output.get("type") == "email_review" and isinstance(tool_output.get("data"), dict):
                improved = tool_output["data"].get("improved_draft")
                if improved:
                    email_draft_data = {"subject": "Re: Improved Draft", "body": improved}
                    break

        tools_str = " → ".join(tools_used) if tools_used else "none"
        categories_str = " → ".join(categories) if categories else "general"

        # Save to DB
        try:
            await db.conversations.insert_one({
                "user_message": user_message, "ai_response": response_text,
                "category": categories_str, "complexity": complexity,
                "tool_used": tools_str, "model_used": final_model,
                "steps": len(steps), "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"DB save error: {e}")

        # Final done event with full payload
        yield _sse_event("done", {
            "response": response_text,
            "metadata": {
                "model_used": final_model, "tool_used": tools_str,
                "category": categories_str, "complexity": complexity,
                "routing_source": routing_source,
            },
            "email_draft": email_draft_data,
        })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
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
