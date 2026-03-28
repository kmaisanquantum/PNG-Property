"""
png_scraper/messenger_bot.py
─────────────────────────────────────────────────────────────────────────────
Messenger Bot Logic: Pre-screens buyers/renters for data-light plans.
Converts social inquiries into "Qualified Leads" for a fee.
"""

from typing import List, Dict, Any, Optional
import random

BOT_QUESTIONS = [
    {"id": "budget", "text": "What is your monthly budget (PGK)?"},
    {"id": "location", "text": "Which suburb are you most interested in (Waigani, Boroko, etc.)?"},
    {"id": "timeline", "text": "When are you planning to move?"},
    {"id": "income", "text": "What is your approximate monthly household income?"}
]

class InquiryBot:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.state = "INIT"
        self.answers = {}

    def get_next_question(self) -> Optional[str]:
        if self.state == "INIT":
            self.state = "budget"
            return BOT_QUESTIONS[0]["text"]
        elif self.state == "budget":
            self.state = "location"
            return BOT_QUESTIONS[1]["text"]
        elif self.state == "location":
            self.state = "timeline"
            return BOT_QUESTIONS[2]["text"]
        elif self.state == "timeline":
            self.state = "income"
            return BOT_QUESTIONS[3]["text"]
        elif self.state == "income":
            self.state = "COMPLETE"
            return "Thank you! Our automated screening shows you are a qualified candidate. An agent will contact you shortly."
        return None

    def process_answer(self, answer: str) -> str:
        current_id = self.state
        self.answers[current_id] = answer
        return self.get_next_question() or "Done"

def qualify_lead(answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Qualifies a lead based on screening answers.
    """
    # Simple qualification logic: if they have a budget > 2000 and timeline < 1 month
    budget_val = 0
    try: budget_val = int(answers.get("budget", "0").replace("K", "").replace(",", ""))
    except: pass

    score = 50 # Baseline
    if budget_val > 5000: score += 30
    elif budget_val > 2500: score += 15

    if "immediately" in answers.get("timeline", "").lower() or "1 month" in answers.get("timeline", "").lower():
        score += 20

    return {
        "is_qualified": score > 70,
        "score": min(100, score),
        "summary": f"Inquiry for {answers.get('location')} (Budget: K{budget_val})",
        "bot_answers": answers
    }

def get_messenger_leads_demo() -> List[Dict]:
    """
    Simulated Messenger-qualified leads for the B2B dashboard.
    """
    return [
        {
            "lead_id": "msg_001",
            "name": "Elias Saro",
            "source": "Facebook Messenger",
            "interest": "Waigani",
            "score": 92,
            "status": "Hot",
            "is_qualified": True,
            "fee_status": "Paid",
            "summary": "3-Step bot screened: High intent, immediate move-in.",
            "last_active": "10m ago"
        },
        {
            "lead_id": "msg_002",
            "name": "Maria Gari",
            "source": "Facebook Messenger",
            "interest": "Boroko",
            "score": 85,
            "status": "Hot",
            "is_qualified": True,
            "fee_status": "Unpaid",
            "summary": "2-Step bot screened: Pre-qualified income.",
            "last_active": "45m ago"
        }
    ]
