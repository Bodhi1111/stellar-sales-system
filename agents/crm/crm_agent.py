from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from config.settings import Settings

class CRMAgent(BaseAgent):
    async def run(
        self,
        extracted_data: Dict[str, Any],
        email_draft: Optional[str] = None,
        social_opportunities: Optional[Any] = None,
        coaching_insights: Optional[Any] = None,
        **extra
    ) -> Dict[str, Any]:
        print(f"📠 CRMAgent received data: {extracted_data}")
        crm_ready_data = {
            **(extracted_data or {}),
            "email_draft": email_draft,
            "social_opportunities": social_opportunities,
            "coaching_insights": coaching_insights,
        }
        print(f"   Formatted CRM data: {crm_ready_data}")
        return crm_ready_data