from typing import Dict, Any
from agents.base_agent import BaseAgent
from config.settings import Settings

class CRMAgent(BaseAgent):
    """
    This agent takes extracted data and formats it for a CRM system.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        # Any CRM-specific setup can go here

    async def run(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        print(f"📠 CRMAgent received data: {extracted_data}")

        # In the future, we can add logic here to map fields,
        # clean data, or validate against a CRM schema.

        # For now, we'll just pass the data through.
        crm_ready_data = extracted_data
        print(f"   Formatted CRM data: {crm_ready_data}")
        return crm_ready_data