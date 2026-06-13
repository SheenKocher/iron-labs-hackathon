# PitchRoute PRD

## Original Problem Statement
Build PitchRoute — an AI sales assistant chat app. Reps type requests (draft cold emails, review emails, look up prospects, check deals, find leads) and the app classifies, routes to MCP tools, and returns responses with metadata badges.

## Architecture
- **Frontend**: React + Tailwind + Shadcn UI (dark theme, Swiss High-Contrast design)
- **Backend**: FastAPI + MongoDB + Emergent Integrations (OpenAI gpt-4o / gpt-4o-mini)
- **LLM**: Emergent Universal Key → OpenAI models (IronLabs API unreachable from env)

## User Personas
- Sales Development Representatives (SDRs)
- Account Executives drafting outreach

## Core Requirements
- Chat-style UI with message input and scrollable thread
- Request classification (6 categories)
- Deterministic routing table (tool + model selection)
- 5 MCP tools: generate_cold_email, review_email, lookup_prospect, get_deal_notes, find_similar_leads
- Metadata badges: model, tool, category
- Send via Gmail button (pre-filled compose URL)

## What's Been Implemented (Dec 2025)
- Full chat UI with dark theme, Chivo/IBM Plex/JetBrains Mono fonts
- All 5 MCP tools working with mock data + LLM
- Classification → routing → tool execution → response pipeline
- Metadata badges on every response
- Email draft card with Send via Gmail button
- Quick action chips for common prompts
- Markdown rendering in AI responses
- MongoDB conversation logging

## Prioritized Backlog
### P0 (Done)
- Chat UI, routing pipeline, all 5 tools, metadata badges, Gmail button

### P1
- Streaming responses (SSE) for better UX
- Conversation history persistence (load previous chats)
- IronLabs API integration when their endpoint is available

### P2
- Content safety guardrails (LlamaGuard-style)
- Real CRM/Gmail/lead data integrations
- Multi-turn conversation context
- User authentication

## Next Tasks
1. Add streaming for LLM responses
2. Persist and reload conversation history
3. Test with actual IronLabs API key when their DNS resolves
