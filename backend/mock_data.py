"""Mock data for PitchRoute MCP tools."""

PROSPECTS = {
    "jordan lee": {
        "name": "Jordan Lee",
        "company": "Acme Corp",
        "role": "VP of Sales",
        "recent_activity": "Downloaded pricing PDF 2 days ago",
        "notes": "Mentioned budget review in Q3"
    },
    "sarah chen": {
        "name": "Sarah Chen",
        "company": "TechFlow Inc",
        "role": "Head of Revenue",
        "recent_activity": "Attended webinar on sales automation last week",
        "notes": "Looking to replace current CRM by Q4"
    },
    "marcus wright": {
        "name": "Marcus Wright",
        "company": "Pinnacle Solutions",
        "role": "Director of Business Development",
        "recent_activity": "Opened 3 emails in the past week",
        "notes": "Has a team of 15 SDRs, interested in outbound tooling"
    },
    "priya patel": {
        "name": "Priya Patel",
        "company": "NovaBridge AI",
        "role": "CRO",
        "recent_activity": "Requested a demo 4 days ago",
        "notes": "Series B company, scaling sales from 10 to 40 reps"
    }
}

DEFAULT_PROSPECT = {
    "name": "Unknown Prospect",
    "company": "N/A",
    "role": "N/A",
    "recent_activity": "No recent activity found",
    "notes": "No existing notes. Consider reaching out for an intro."
}

DEALS = {
    "d-1042": {
        "deal_id": "D-1042",
        "stage": "Negotiation",
        "value": "$24,000",
        "last_contact": "5 days ago",
        "notes": "Prospect concerned about onboarding time"
    },
    "d-1087": {
        "deal_id": "D-1087",
        "stage": "Discovery",
        "value": "$18,500",
        "last_contact": "2 days ago",
        "notes": "Needs integration with Salesforce. Decision expected by end of month."
    },
    "d-1103": {
        "deal_id": "D-1103",
        "stage": "Closed-Won",
        "value": "$42,000",
        "last_contact": "1 day ago",
        "notes": "Contract signed. Onboarding kickoff scheduled for next Monday."
    }
}

DEFAULT_DEAL = {
    "deal_id": "NOT_FOUND",
    "stage": "Unknown",
    "value": "N/A",
    "last_contact": "N/A",
    "notes": "No deal found with this ID."
}

LEADS_BY_INDUSTRY = {
    "saas": [
        {"name": "Sam Patel", "company": "Northwind Tech", "industry": "SaaS", "fit_reason": "Recently raised Series A"},
        {"name": "Riya Shah", "company": "BlueWave Inc", "industry": "SaaS", "fit_reason": "Hiring for sales team"},
        {"name": "Alex Torres", "company": "CloudSync", "industry": "SaaS", "fit_reason": "Expanding into enterprise segment"},
        {"name": "Jamie Koh", "company": "DataVault", "industry": "SaaS", "fit_reason": "Currently evaluating outbound tools"}
    ],
    "fintech": [
        {"name": "Lauren Xu", "company": "PayNova", "industry": "Fintech", "fit_reason": "Building out B2B sales motion"},
        {"name": "Derek Osman", "company": "LedgerAI", "industry": "Fintech", "fit_reason": "VP of Sales recently hired"},
        {"name": "Nina Alvarez", "company": "TrustPay", "industry": "Fintech", "fit_reason": "Raised $20M Series B last quarter"}
    ],
    "healthcare": [
        {"name": "Dr. Kim Nakamura", "company": "MedConnect", "industry": "Healthcare", "fit_reason": "Scaling B2B partnerships"},
        {"name": "Brian Hall", "company": "HealthBridge", "industry": "Healthcare", "fit_reason": "Searching for outreach automation"},
        {"name": "Carla Mendes", "company": "VitalSync", "industry": "Healthcare", "fit_reason": "New VP of Growth, open to demos"}
    ],
    "default": [
        {"name": "Morgan Blake", "company": "Apex Industries", "industry": "General", "fit_reason": "High growth trajectory"},
        {"name": "Taylor Reed", "company": "Summit Group", "industry": "General", "fit_reason": "Recently expanded sales team"},
        {"name": "Casey Dunn", "company": "Horizon Labs", "industry": "General", "fit_reason": "Active on LinkedIn, engaging with sales content"}
    ]
}
