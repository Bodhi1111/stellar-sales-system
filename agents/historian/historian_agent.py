from typing import Dict, Any
from agents.base_agent import BaseAgent
from config.settings import Settings, settings
from core.database.neo4j import neo4j_manager


class HistorianAgent(BaseAgent):
    """
    This agent takes the final processed data and saves it to the 
    Neo4j knowledge graph to build long-term memory.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)

    async def run(self, state: Dict[str, Any]):
        print("📜 HistorianAgent received final data. Building long-term memory...")

        try:
            file_path = state.get("file_path")
            extracted_data = state.get("extracted_data", {})
            customer_name = extracted_data.get(
                "customer_name", "Unknown Client")
            main_objection = extracted_data.get("main_objection")

            # For clean testing, clear any old data for this file
            await neo4j_manager.execute_query(
                "MATCH (m:Meeting {filename: $filename}) DETACH DELETE m",
                {"filename": file_path.name}
            )

            # MERGE the Meeting node (get or create)
            await neo4j_manager.execute_query(
                "MERGE (m:Meeting {filename: $filename})",
                {"filename": file_path.name}
            )

            # MERGE the Client node and connect it to the Meeting
            await neo4j_manager.execute_query(
                """
                MATCH (m:Meeting {filename: $filename})
                MERGE (c:Client {name: $customer_name})
                MERGE (c)-[:PARTICIPATED_IN]->(m)
                """,
                {"filename": file_path.name, "customer_name": customer_name}
            )

            # If an objection was found, MERGE it and connect it
            if main_objection and "Not found" not in main_objection and "Not provided" not in main_objection:
                await neo4j_manager.execute_query(
                    """
                    MATCH (c:Client {name: $customer_name})
                    MATCH (m:Meeting {filename: $filename})
                    MERGE (o:Objection {text: $objection_text})
                    MERGE (c)-[:RAISED]->(o)
                    MERGE (o)-[:DURING]->(m)
                    """,
                    {
                        "customer_name": customer_name,
                        "filename": file_path.name,
                        "objection_text": main_objection
                    }
                )

            print("   ✅ Successfully updated the knowledge graph.")
            return {"historian_status": "success"}

        except Exception as e:
            print(f"   ❌ ERROR: Failed to update knowledge graph: {e}")
            return {"historian_status": "error"}
