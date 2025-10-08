import asyncio
import sys
from agents.sales_copilot.sales_copilot_agent import SalesCopilotAgent
from config.settings import settings


async def main(question: str):
    """
    Initializes and runs the SalesCopilotAgent with a user's question.
    """
    copilot = SalesCopilotAgent(settings)
    answer = await copilot.run(query=question)

    print("\\n--- Sales Copilot Answer ---")
    print(answer)
    print("--------------------------")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_question = " ".join(sys.argv[1:])
        asyncio.run(main(question=user_question))
    else:
        print("Usage: python scripts/ask_copilot.py 'Your question here'")
