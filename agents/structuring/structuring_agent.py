import json
import requests
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from config.settings import Settings, settings
from core.nlp_processor import get_nlp_processor


class StructuringAgent(BaseAgent):
    """
    Analyzes raw transcript using semantic NLP to extract rich metadata:
    - Conversation phases with timestamps
    - Speaker intent and sentiment per turn
    - Key entities and topics discussed
    - Discourse structure (questions, objections, confirmations)

    This metadata enriches the entire downstream pipeline.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME
        self.nlp_processor = get_nlp_processor()  # Centralized NLP processor

    def _format_dialogue_for_prompt(self, dialogue: List[Dict[str, Any]]) -> str:
        """Formats the structured dialogue into a simple text block."""
        return "\\n".join([f"[{turn['timestamp']}] {turn['speaker']}: {turn['text']}" for turn in dialogue])

    def _construct_semantic_nlp_prompt(self, formatted_dialogue: str) -> str:
        """
        Constructs prompt for SEMANTIC NLP ANALYSIS to extract rich metadata.
        This metadata will enrich the entire downstream pipeline.
        """
        prompt = """TASK: Perform SEMANTIC NLP ANALYSIS on estate planning sales transcript

GOAL: Extract rich semantic metadata that will enrich downstream processing:
1. Conversation phases (structural segmentation)
2. Semantic features per turn (intent, sentiment, topics)
3. Key entities and their relationships
4. Discourse markers (transitions, confirmations, objections)

OUTPUT FORMAT:
{
  "conversation_phases": [
    {
      "phase": "phase_name",
      "start_timestamp": "HH:MM:SS",
      "end_timestamp": "HH:MM:SS",
      "dominant_speaker": "speaker_name",
      "key_topics": ["topic1", "topic2"],
      "sentiment": "positive|neutral|negative|mixed"
    }
  ],
  "semantic_turns": [
    {
      "timestamp": "HH:MM:SS",
      "speaker": "speaker_name",
      "intent": "question|statement|objection|agreement|proposal|clarification",
      "sentiment": "positive|neutral|negative|concerned|excited",
      "contains_entity": true|false,
      "discourse_marker": "transition|confirmation|hedge|emphasis|none"
    }
  ],
  "key_entities": {
    "monetary_values": ["$5000", "$250,000"],
    "dates": ["next Tuesday", "December 15"],
    "locations": ["California", "San Diego"],
    "products_mentioned": ["revocable living trust", "pour-over will"]
  },
  "overall_structure": {
    "total_phases": 12,
    "client_engagement": "high|medium|low",
    "objections_count": 2,
    "questions_count": 15
  }
}

TRANSCRIPT TO ANALYZE:
---
"""
        prompt += formatted_dialogue
        prompt += "\n---\n\nJSON OUTPUT (complete semantic analysis):"
        return prompt

    def _construct_prompt(self, formatted_dialogue: str) -> str:
        """Constructs a prompt for the LLM to identify conversation phases with detailed anatomical understanding."""
        phase_list = [
            "greeting", "introduction", "client's motivation for the meeting", "agenda", "about us",
            "client's goals", "client's estate details", "compare will versus trust",
            "revocable living trust structure", "additional estate planning documents",
            "our additional benefits", "comparing price", "closing", "objection/rebuttal",
            "price negotiation", "scheduling client meeting", "collecting money", "ending meeting"
        ]

        # Enhanced prompt with transcript anatomy understanding
        prompt = """TASK: Analyze estate planning sales transcript and identify conversation phases

TRANSCRIPT ANATOMY:
This is a timestamped sales conversation between a sales representative and a client.
Each turn has: [HH:MM:SS] Speaker Name: Dialogue text

CONVERSATION FLOW (Typical Estate Planning Meeting):
1. OPENING (00:00 - 00:10): greeting, introduction, agenda setting
2. DISCOVERY (00:10 - 00:30): client's motivation, goals, estate details (assets, family, concerns)
3. EDUCATION (00:30 - 00:50): about us, compare will vs trust, trust structure, additional documents, benefits
4. CLOSING (00:50 - end): comparing price, objection handling, price negotiation, collecting money, scheduling, ending

INSTRUCTIONS:
1. Read the ENTIRE transcript carefully (don't stop at first few exchanges)
2. Identify where each conversation phase begins by looking for topic shifts
3. A typical meeting will have 8-15 distinct phases
4. Mark the EXACT timestamp where each new phase starts
5. Only use phase names from the list below

PHASE LIST:
"""
        prompt += ", ".join(phase_list) + "\n\n"

        prompt += """CRITICAL RULES:
- Return a JSON array with ALL phases found (typically 8-15 phases in a full meeting)
- Each object must have: {"phase": "phase_name", "start_timestamp": "HH:MM:SS"}
- Timestamps must be in HH:MM:SS format (e.g., "00:15:30")
- Phases must appear in chronological order
- If unsure, include the phase (better to over-identify than miss key sections)

EXAMPLE OUTPUT:
[
  {"phase": "greeting", "start_timestamp": "00:00:05"},
  {"phase": "introduction", "start_timestamp": "00:01:30"},
  {"phase": "client's motivation for the meeting", "start_timestamp": "00:03:45"},
  {"phase": "agenda", "start_timestamp": "00:05:20"},
  {"phase": "about us", "start_timestamp": "00:07:15"},
  {"phase": "client's goals", "start_timestamp": "00:12:30"},
  {"phase": "client's estate details", "start_timestamp": "00:18:45"},
  {"phase": "compare will versus trust", "start_timestamp": "00:25:10"},
  {"phase": "revocable living trust structure", "start_timestamp": "00:32:00"},
  {"phase": "comparing price", "start_timestamp": "00:45:15"},
  {"phase": "objection/rebuttal", "start_timestamp": "00:52:30"},
  {"phase": "closing", "start_timestamp": "00:58:00"}
]

TRANSCRIPT TO ANALYZE:
---
"""
        prompt += formatted_dialogue
        prompt += "\n---\n\nJSON OUTPUT (array of ALL phases found):"

        return prompt

    async def run(self, raw_transcript: str = None, structured_dialogue: List[Dict[str, Any]] = None,
                  use_semantic_nlp: bool = False) -> Dict[str, Any]:
        """
        NEW ARCHITECTURE: Run on raw transcript FIRST (before parsing)
        Performs semantic NLP analysis to extract rich metadata for downstream enrichment.

        Args:
            raw_transcript: Raw transcript text (preferred - runs FIRST in pipeline)
            structured_dialogue: Parsed dialogue (fallback for backward compatibility)
            use_semantic_nlp: If True, perform full semantic NLP analysis (experimental)

        Returns:
            If use_semantic_nlp=True: Dict with {conversation_phases, semantic_turns, key_entities, overall_structure}
            If use_semantic_nlp=False: List[Dict] with conversation phases (backward compatible)
        """
        print("🏗️ StructuringAgent: Analyzing transcript structure...")

        # Prefer raw transcript (new architecture)
        if raw_transcript:
            print("   📄 Using raw transcript (runs FIRST in pipeline)")
            formatted_dialogue = raw_transcript
        # Fallback to parsed dialogue (old architecture)
        elif structured_dialogue:
            print("   ⚠️ Using parsed dialogue (backward compatibility mode)")
            formatted_dialogue = self._format_dialogue_for_prompt(structured_dialogue)
        else:
            raise ValueError("Must provide either raw_transcript or structured_dialogue")

        # Choose analysis mode
        if use_semantic_nlp:
            print("   🧠 Using SEMANTIC NLP ANALYSIS mode (spaCy + transformers)")
            # Use NLP processor for semantic analysis
            try:
                nlp_result = self.nlp_processor.analyze_transcript(formatted_dialogue)
                return nlp_result
            except Exception as e:
                print(f"   ⚠️ NLP analysis failed: {e}, falling back to LLM mode")
                # Fall back to LLM-based analysis
                prompt = self._construct_semantic_nlp_prompt(formatted_dialogue)
        else:
            print("   📊 Using standard phase identification mode")
            prompt = self._construct_prompt(formatted_dialogue)

        payload = {"model": self.model_name, "prompt": prompt,
                   "format": "json", "stream": False}

        try:
            response = requests.post(self.api_url, json=payload, timeout=180)
            response.raise_for_status()
            response_data = response.json()
            result = json.loads(response_data.get("response", "{}"))

            if use_semantic_nlp:
                # Return full semantic NLP structure
                if isinstance(result, dict) and "conversation_phases" in result:
                    phases = result["conversation_phases"]
                    semantic_turns = result.get("semantic_turns", [])
                    key_entities = result.get("key_entities", {})
                    overall = result.get("overall_structure", {})

                    print(f"   ✅ Semantic NLP analysis complete:")
                    print(f"      - {len(phases)} conversation phases")
                    print(f"      - {len(semantic_turns)} turns with intent/sentiment")
                    print(f"      - {len(key_entities)} entity types extracted")

                    return result
                else:
                    print(f"   ⚠️ WARNING: Unexpected semantic NLP format, falling back to basic mode")
                    # Fall through to basic mode parsing
                    use_semantic_nlp = False
                    result = result.get("conversation_phases", [])

            # Basic mode (backward compatible) - return just phases list
            phases = result if isinstance(result, list) else []

            # CRITICAL FIX: Mistral sometimes returns unexpected formats
            # Case 1: Single dict instead of list
            if isinstance(phases, dict):
                # Check if it's wrapped in a 'transcript' key
                if 'transcript' in phases and isinstance(phases['transcript'], list):
                    phases = phases['transcript']
                else:
                    phases = [phases]
            # Case 2: List with nested 'transcript' key
            elif isinstance(phases, list) and len(phases) > 0:
                if isinstance(phases[0], dict) and 'transcript' in phases[0]:
                    phases = phases[0]['transcript']
            elif not isinstance(phases, list):
                print(f"   ⚠️ WARNING: LLM returned unexpected type: {type(phases)}, defaulting to empty list")
                phases = []

            print(f"   Successfully identified {len(phases)} phases.")
            return phases

        except Exception as e:
            print(
                f"   ❌ ERROR: An unexpected error occurred during phase identification: {e}")
            return [] if not use_semantic_nlp else {
                "conversation_phases": [],
                "semantic_turns": [],
                "key_entities": {},
                "overall_structure": {}
            }
