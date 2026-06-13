"""PitchRoute backend API tests"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestHealth:
    """Health check tests"""

    def test_health_root(self):
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"Health check OK: {data['message']}")


class TestChatEndpoint:
    """Chat endpoint classification and routing tests"""

    def test_prospect_lookup(self):
        response = requests.post(f"{BASE_URL}/api/chat", json={"message": "Look up prospect Sarah Chen"}, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["category"] == "prospect_lookup"
        assert data["metadata"]["tool_used"] == "lookup_prospect"
        assert "response" in data
        print(f"Prospect lookup OK: category={data['metadata']['category']}, tool={data['metadata']['tool_used']}")

    def test_cold_email_draft(self):
        response = requests.post(f"{BASE_URL}/api/chat", json={"message": "Draft a cold email to Jordan Lee at Acme Corp about our sales automation platform"}, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["category"] == "cold_email_draft"
        assert data["email_draft"] is not None
        assert "subject" in data["email_draft"]
        assert "body" in data["email_draft"]
        assert len(data["email_draft"]["subject"]) > 0
        assert len(data["email_draft"]["body"]) > 0
        print(f"Cold email draft OK: subject={data['email_draft']['subject'][:50]}")

    def test_email_review(self):
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Review this email: Hi Jordan, I noticed your team is growing fast. We help teams like yours close 30% more deals. Want to grab 15 mins?"},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["category"] == "email_review"
        print(f"Email review OK: category={data['metadata']['category']}")

    def test_deal_lookup(self):
        response = requests.post(f"{BASE_URL}/api/chat", json={"message": "Check deal D-1042"}, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["category"] == "deal_lookup"
        assert data["metadata"]["tool_used"] == "get_deal_notes"
        print(f"Deal lookup OK: category={data['metadata']['category']}")

    def test_find_leads(self):
        response = requests.post(f"{BASE_URL}/api/chat", json={"message": "Find similar leads in the SaaS industry"}, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["category"] == "lead_gen"
        assert data["metadata"]["tool_used"] == "find_similar_leads"
        print(f"Find leads OK: category={data['metadata']['category']}")

    def test_general_question(self):
        response = requests.post(f"{BASE_URL}/api/chat", json={"message": "What is the best sales approach for enterprise deals?"}, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["category"] == "general"
        assert data["metadata"]["tool_used"] == "none"
        print(f"General question OK: category={data['metadata']['category']}")

    def test_empty_message_returns_400(self):
        response = requests.post(f"{BASE_URL}/api/chat", json={"message": ""}, timeout=10)
        assert response.status_code == 400
        print("Empty message 400 OK")

    def test_response_has_metadata_fields(self):
        response = requests.post(f"{BASE_URL}/api/chat", json={"message": "Hello"}, timeout=30)
        assert response.status_code == 200
        data = response.json()
        meta = data["metadata"]
        assert "model_used" in meta
        assert "tool_used" in meta
        assert "category" in meta
        assert "complexity" in meta
        print(f"Metadata fields OK: {meta}")
