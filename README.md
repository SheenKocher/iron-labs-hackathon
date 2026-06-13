# PitchRoute: AI-Powered Sales Assistant with Intelligent Model Routing

An intelligent B2B sales assistant that uses **Iron Labs routing engine** to dynamically select the optimal LLM model (gpt-4o or gpt-4o-mini) based on query complexity and context, optimizing for both accuracy and cost-efficiency.

## 🎯 Overview

PitchRoute is a full-stack application that helps sales teams automate and optimize their outreach through:
- **Intelligent query classification** — Categorizes incoming requests (email generation, prospect research, deal management)
- **Context-aware tool routing** — Routes requests to specialized sales tools
- **Dynamic model selection** — Uses Iron Labs to choose the best model for each task
- **Real-time metadata tracking** — Shows which model and routing method was used

### Key Insight
Instead of using a single LLM model for all tasks, PitchRoute intelligently selects between:
- **gpt-4o** — For high-complexity tasks requiring nuance and accuracy
- **gpt-4o-mini** — For straightforward tasks, optimizing for cost

The Iron Labs routing engine makes this decision based on query complexity, category, and configured tradeoff preferences.

---

## ✨ Capabilities

### 1. **Email Generation & Review**
- **Generate cold emails** — Draft personalized outreach emails with context about prospects
- **Review emails** — Evaluate tone, clarity, and persuasiveness with improvement suggestions
- AI writes compelling subject lines and body copy tailored to the prospect

### 2. **Prospect Research**
- **Lookup prospect** — Search prospect database by name with company, role, recent activity, and notes
- **Find similar leads** — Discover leads in specific industries matching your target profile
- Fallback to sensible defaults if prospect not found

### 3. **Deal Management**
- **Get deal notes** — Retrieve deal stage, value, last contact date, and key notes
- **Track deal progress** — Access information about ongoing negotiations and concerns

### 4. **Sales Intelligence**
- Curated mock database of prospects (Jordan Lee, Sarah Chen, Marcus Wright, Priya Patel)
- Deal pipeline with stages (Negotiation, Proposal, Qualification)
- Industry-specific lead groups (SaaS, Finance, Healthcare, Enterprise)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend (port 3000)              │
│  - Chat interface with quick action buttons                 │
│  - Metadata display (model, tool, category, complexity)     │
│  - Email draft card with Gmail integration                  │
│  - Real-time typing indicator                               │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI Backend (port 8000)                    │
│  POST /api/chat                                             │
│  1. Classify query → category + complexity                  │
│  2. Route to tool → email, lookup, deal, etc.               │
│  3. Select model → Iron Labs vs static fallback             │
│  4. Execute LLM + tool                                      │
│  5. Return response + metadata                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                   ▼
   ┌─────────┐        ┌─────────┐        ┌──────────┐
   │  OpenAI │        │  MongoDB│      │Iron Labs │
   │ Models  │        │Database │      │Router    │
   └─────────┘        └─────────┘      └──────────┘
   (via Emergent)
```

### Request Flow
```
User Message
    ↓
[Classification Step]
- Detect category: email_generation, prospect_research, deal_management, general_inquiry
- Determine complexity: low, medium, high
    ↓
[Tool Routing Step]
- Static table maps category → tool (generate_cold_email, lookup_prospect, etc.)
    ↓
[Model Selection Step]
- Iron Labs API: "Given this query and complexity, pick the best model"
- Fallback: Static complexity-based selection if API unavailable
    ↓
[Execution]
- LLM generates response (with context from selected model)
- Tool runs (if needed): cold email generation, prospect lookup, deal retrieval
    ↓
[Response]
- Return response + metadata (model_used, routed_by, category, complexity)
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Tailwind CSS, React Router, Axios, Lucide Icons |
| **Backend** | FastAPI, Uvicorn, Python 3.9+ |
| **Database** | MongoDB with Motor async driver |
| **LLM** | OpenAI (gpt-4o, gpt-4o-mini) via Emergent Integrations |
| **Routing** | Iron Labs Model Selection API |
| **UI Components** | Radix UI, Shadcn/ui primitives |

---

## 📋 Features in Detail

### Query Classification
The system classifies each incoming message into categories:

| Category | Description | Tools |
|----------|-------------|-------|
| `email_generation` | Draft or improve sales emails | `generate_cold_email`, `review_email` |
| `prospect_research` | Look up people and find leads | `lookup_prospect`, `find_similar_leads` |
| `deal_management` | Retrieve deal information | `get_deal_notes` |
| `general_inquiry` | General questions | LLM-only response |

### Complexity Assessment
Messages are rated on complexity:
- **Low** — Simple factual queries, standard templates
- **Medium** — Requires some context and personalization
- **High** — Complex negotiation language, nuanced sales strategy

### Model Selection Rules
Iron Labs chooses models based on:
1. **Tradeoff preference** — "accuracy" for high complexity, "cost" for low/medium
2. **Query context** — The actual message content and intent
3. **Candidate pool** — Available models (gpt-4o, gpt-4o-mini)

**Static Fallback** (if Iron Labs unavailable):
- High complexity → gpt-4o
- Low/Medium complexity → gpt-4o-mini

### Available Tools

#### generate_cold_email
Drafts a personalized cold outreach email given prospect name and company.

**Parameters:**
- `prospect_name` — Person to reach out to
- `company` — Their company
- `context` — What you want to discuss

**Output:** JSON with `subject` and `body`

#### review_email
Reviews an existing email draft for tone, clarity, and persuasiveness.

**Parameters:**
- `draft_text` — The email draft to review

**Output:** JSON with `score` (1-10), `suggestions` (list), `improved_draft`

#### lookup_prospect
Searches the prospect database by name.

**Parameters:**
- `name` — Prospect name (partial match supported)

**Output:** Prospect object with company, role, recent activity, notes

#### get_deal_notes
Retrieves deal information by ID.

**Parameters:**
- `deal_id` — Deal identifier (e.g., "D-1042")

**Output:** Deal object with stage, value, last contact, notes

#### find_similar_leads
Finds leads matching a specific industry.

**Parameters:**
- `industry` — Target industry (e.g., "SaaS", "Finance")
- `criteria` — Optional additional criteria

**Output:** Array of lead objects matching the industry

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ and pip
- Node.js 16+ and npm/yarn
- MongoDB (local or cloud)
- API Keys: `EMERGENT_LLM_KEY`, `IRONLABS_API_KEY`

### Installation

**1. Backend Setup**
```bash
cd backend
pip install -r requirements.txt
```

**2. Frontend Setup**
```bash
cd frontend
npm install --legacy-peer-deps
```

### Configuration

Create `backend/.env`:
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=iron_labs_db
EMERGENT_LLM_KEY=your_key_here
IRONLABS_API_KEY=your_key_here
FAST_MODEL=gpt-4o-mini
STRONG_MODEL=gpt-4o
```

### Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

Open `http://localhost:3000` in your browser.

---

## 📡 API Documentation

### POST /api/chat
Main endpoint for chat requests.

**Request:**
```json
{
  "message": "Draft a cold email to Jordan Lee at Acme Corp"
}
```

**Response:**
```json
{
  "response": "Here's a personalized cold email for Jordan...",
  "metadata": {
    "model_used": "gpt-4o",
    "tool_used": "generate_cold_email",
    "category": "email_generation",
    "complexity": "medium",
    "routed_by": "iron-labs",
    "timestamp": "2024-06-13T10:30:00Z"
  },
  "email_draft": {
    "subject": "Quick thought on Acme's expansion",
    "body": "Hi Jordan,\n\nI noticed Acme is scaling..."
  }
}
```

### GET /api/
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-13T10:30:00Z"
}
```

---

## 📁 Project Structure

```
iron-labs-hackathon/
│
├── backend/
│   ├── server.py              # FastAPI app, routes, classification logic
│   ├── mcp_tools.py           # Tool implementations (email, lookup, deals, leads)
│   ├── mock_data.py           # Sample prospects, deals, industry leads
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables (local)
│   └── .env.example            # Example config template
│
├── frontend/
│   ├── src/
│   │   ├── App.js             # Main chat interface component
│   │   ├── App.css            # Styling
│   │   ├── index.js           # React entry point
│   │   ├── constants/          # Test IDs and constants
│   │   └── components/ui/     # Radix UI + Shadcn primitives
│   ├── package.json           # Node dependencies
│   ├── craco.config.js        # Create React App config overrides
│   ├── tailwind.config.js     # Tailwind CSS configuration
│   └── README.md              # Frontend-specific docs
│
├── SETUP.md                   # Detailed setup and troubleshooting guide
└── README.md                  # This file

```

---

## 🔄 Workflow Example

**User Types:** "Draft a cold email to Jordan Lee at Acme Corp about our sales automation platform"

1. **Classification** → category: "email_generation", complexity: "medium"
2. **Tool Routing** → tool: "generate_cold_email"
3. **Model Selection** → Iron Labs chooses gpt-4o-mini (cost-effective for medium complexity)
4. **Execution**:
   - Lookup Jordan's data (from mock_data)
   - Call gpt-4o-mini with cold email prompt + context
   - Generate subject and body
5. **Response** includes:
   - Draft email with subject/body
   - Metadata showing gpt-4o-mini was used via Iron Labs routing

---

## 🎨 Frontend Features

### Quick Action Buttons
Pre-filled prompts to get started:
- Draft cold email
- Review an email
- Look up prospect
- Check deal
- Find leads

### Metadata Badges
Each response displays:
- **Model Used** — Which model generated the response
- **Tool Used** — Which sales tool was invoked
- **Category** — Query classification
- **Complexity** — Assessed complexity level
- **Routing Source** — Iron Labs vs static fallback

### Email Draft Card
When emails are generated:
- Display subject and body
- "Send via Gmail" button (opens Gmail composer pre-filled)
- Copy-friendly formatting

### Chat History
Scrollable conversation history with:
- User messages
- AI responses with metadata
- Markdown rendering for formatted text
- Typing indicator while generating

---

## 🧪 Testing

### Mock Data
The application includes curated mock data for realistic testing:

**Prospects:** Jordan Lee (Acme), Sarah Chen (TechFlow), Marcus Wright (Pinnacle), Priya Patel (NovaBridge)

**Deals:** D-1042 (Negotiation, $24k), D-1087, D-1103, etc.

**Industries:** SaaS, Finance, Healthcare, Enterprise Software

Try queries like:
- "Look up Sarah Chen"
- "Get deal D-1042"
- "Find SaaS leads"
- "Draft email to Marcus Wright at Pinnacle Solutions"

---

## 🚨 Error Handling

### Iron Labs Fallback
If the Iron Labs API is unavailable or `IRONLABS_API_KEY` is not set:
- System automatically falls back to static complexity-based routing
- Response includes `"routed_by": "static-fallback"` in metadata
- No user-facing errors—seamless degradation

### Tool Failures
If a tool execution fails:
- Graceful error handling with logging
- User receives informative error message
- Metadata includes which tool failed

### LLM Errors
If OpenAI API fails:
- System retries with exponential backoff (via Emergent)
- Falls back to default responses if retries exhausted
- Logged for debugging

---

## 📊 Metrics & Monitoring

Track in response metadata:
- `model_used` — Which LLM handled the request
- `routed_by` — "iron-labs" vs "static-fallback"
- `category` — Query classification
- `complexity` — Assessed complexity
- `tool_used` — Which tool was invoked
- `timestamp` — When the request was processed

These metrics help optimize:
- Cost vs. quality tradeoffs
- Model selection accuracy
- Tool routing effectiveness

---

## 🔧 Development Notes

### Adding New Tools
1. Implement async function in `backend/mcp_tools.py`
2. Add classification mapping in `server.py` `get_route()`
3. Add to prompt templates in classification logic

### Customizing Classification
Edit the classification prompts in `server.py` to:
- Add new categories
- Adjust complexity assessment
- Change routing rules

### Extending the Frontend
The React app uses:
- Axios for API calls
- Tailwind for styling
- Lucide for icons
- Radix UI for accessible primitives

---

## 📚 Additional Resources

- **SETUP.md** — Detailed setup, troubleshooting, and deployment guides
- **backend/server.py** — FastAPI route definitions and business logic
- **frontend/src/App.js** — React component implementation
- **backend/mcp_tools.py** — Tool implementation details

---

## 🤝 Contributing

When adding features:
1. Update mock data in `backend/mock_data.py` for realistic testing
2. Add corresponding tool in `backend/mcp_tools.py`
3. Update classification logic to recognize new query types
4. Test with various prompt examples
5. Update this README with new capabilities

---

## 📝 License

Part of the Iron Labs hackathon project.

---

## 🔗 Key Integration Points

| Integration | Purpose | Config |
|-----------|---------|--------|
| OpenAI API | LLM generation | `EMERGENT_LLM_KEY` |
| Iron Labs | Model selection | `IRONLABS_API_KEY` |
| MongoDB | Conversation history | `MONGO_URL`, `DB_NAME` |
| Emergent Integrations | LLM abstraction layer | Handled internally |

---

**Ready to use?** Start with the Quick Start section above, or see **SETUP.md** for detailed troubleshooting and deployment guidance.

