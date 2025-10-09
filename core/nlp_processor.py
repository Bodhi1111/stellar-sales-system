"""
NLP Processor - Semantic Analysis Core

This module centralizes all NLP operations for the Stellar Sales System.
It performs document-level semantic analysis that produces "NLP awareness" metadata
for downstream agents.

Best Practices:
1. Document segmentation (conversation phase detection)
2. Named Entity Recognition (NER) - people, orgs, money, dates, locations
3. Topic extraction/classification
4. Semantic role labeling (speaker intent, sentiment)
5. Relationship extraction
6. Document-level and section-level metadata assignment

This NLP analysis happens ONCE at the start (StructuringAgent) and is enriched
by downstream agents, never duplicated.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import logging

# Lazy imports to avoid startup delays
_spacy_nlp = None
_sentiment_pipeline = None

logger = logging.getLogger(__name__)


class NLPProcessor:
    """
    Centralized NLP processor using spaCy and transformers.
    Performs semantic analysis on raw transcripts to extract rich metadata.
    """

    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """
        Initialize NLP processor with spaCy model.

        Args:
            spacy_model: spaCy model name (en_core_web_sm, en_core_web_md, en_core_web_lg)
        """
        self.spacy_model_name = spacy_model
        self._ensure_models_loaded()

    def _ensure_models_loaded(self):
        """Lazy load NLP models to avoid startup delays"""
        global _spacy_nlp, _sentiment_pipeline

        if _spacy_nlp is None:
            try:
                import spacy
                logger.info(f"Loading spaCy model: {self.spacy_model_name}")
                _spacy_nlp = spacy.load(self.spacy_model_name)
                logger.info("✅ spaCy model loaded")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load spaCy model: {e}")
                logger.warning("   NLP analysis will be limited. Run: python -m spacy download en_core_web_sm")
                _spacy_nlp = None

        if _sentiment_pipeline is None:
            try:
                from transformers import pipeline
                logger.info("Loading sentiment analysis pipeline (distilbert)")
                _sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1  # CPU
                )
                logger.info("✅ Sentiment pipeline loaded")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load sentiment pipeline: {e}")
                _sentiment_pipeline = None

    def analyze_transcript(self, raw_transcript: str) -> Dict[str, Any]:
        """
        Perform comprehensive NLP analysis on raw transcript.

        This is the CORE NLP ANALYSIS that produces semantic awareness metadata.

        Args:
            raw_transcript: Raw transcript text

        Returns:
            Dictionary with rich NLP metadata:
            {
                "document_metadata": {...},
                "named_entities": {...},
                "topics": [...],
                "semantic_turns": [...],
                "conversation_structure": {...}
            }
        """
        logger.info("🧠 Starting NLP semantic analysis...")

        # Parse dialogue turns
        turns = self._parse_dialogue_turns(raw_transcript)

        # 1. Document Segmentation - Identify conversation phases
        conversation_phases = self._segment_conversation(turns)

        # 2. Named Entity Recognition (NER)
        entities = self._extract_named_entities(raw_transcript, turns)

        # 3. Topic Extraction
        topics = self._extract_topics(turns)

        # 4. Semantic Role Labeling (intent, sentiment per turn)
        semantic_turns = self._analyze_turn_semantics(turns)

        # 5. Relationship Extraction
        relationships = self._extract_relationships(entities, turns)

        # 6. Document-level metadata
        doc_metadata = self._compute_document_metadata(turns, semantic_turns, entities)

        result = {
            "conversation_phases": conversation_phases,
            "named_entities": entities,
            "topics": topics,
            "semantic_turns": semantic_turns,
            "relationships": relationships,
            "document_metadata": doc_metadata
        }

        logger.info(f"✅ NLP analysis complete:")
        logger.info(f"   - {len(conversation_phases)} conversation phases")
        logger.info(f"   - {len(semantic_turns)} turns analyzed")
        logger.info(f"   - {sum(len(v) for v in entities.values())} entities extracted")
        logger.info(f"   - {len(topics)} topics identified")

        return result

    def _parse_dialogue_turns(self, raw_transcript: str) -> List[Dict[str, Any]]:
        """Parse transcript into dialogue turns"""
        turns = []

        # Pattern: [HH:MM:SS] Speaker: Text or HH:MM:SS - Speaker
        bracketed_pattern = re.compile(r'\[(.*?)\]\s+([^:]+):\s+(.*)')
        dashed_pattern = re.compile(r'^\s*(\d{2}:\d{2}:\d{2})\s+-\s+(.+)$')

        lines = raw_transcript.strip().split('\n')

        for line in lines:
            # Try bracketed format
            match = bracketed_pattern.match(line)
            if match:
                timestamp, speaker, text = match.groups()
                turns.append({
                    "timestamp": timestamp.strip(),
                    "speaker": speaker.strip(),
                    "text": text.strip()
                })
                continue

            # Try dashed format (timestamp on one line, text follows)
            match = dashed_pattern.match(line)
            if match:
                # For now, just capture what we can
                timestamp, speaker = match.groups()
                turns.append({
                    "timestamp": timestamp.strip(),
                    "speaker": speaker.strip(),
                    "text": ""  # Would need multi-line parsing
                })

        return turns

    def _segment_conversation(self, turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Segment conversation into phases using topic shifts and speaker patterns.

        Best Practice: Use semantic similarity between consecutive turns to detect phase boundaries.
        """
        if not turns:
            return []

        phases = []

        # Simple heuristic: Detect topic shifts every N turns
        # In production, use semantic similarity (sentence embeddings)
        window_size = 10

        for i in range(0, len(turns), window_size):
            window_turns = turns[i:i + window_size]
            if not window_turns:
                continue

            # Extract dominant topics from window
            window_text = " ".join(turn["text"] for turn in window_turns)
            topics = self._extract_topics_from_text(window_text)

            phases.append({
                "phase": topics[0] if topics else "general_discussion",
                "start_timestamp": window_turns[0]["timestamp"],
                "end_timestamp": window_turns[-1]["timestamp"],
                "turn_count": len(window_turns),
                "key_topics": topics[:3]
            })

        return phases

    def _extract_named_entities(self, raw_transcript: str, turns: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Named Entity Recognition (NER) using spaCy.

        Best Practice: Extract PERSON, ORG, MONEY, DATE, GPE (location), PRODUCT entities.
        """
        entities = {
            "people": [],
            "organizations": [],
            "monetary_values": [],
            "dates": [],
            "locations": [],
            "products": []
        }

        if _spacy_nlp is None:
            # Fallback to regex-based entity extraction
            return self._fallback_entity_extraction(raw_transcript)

        # Process with spaCy
        doc = _spacy_nlp(raw_transcript)

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities["people"].append(ent.text)
            elif ent.label_ == "ORG":
                entities["organizations"].append(ent.text)
            elif ent.label_ == "MONEY":
                entities["monetary_values"].append(ent.text)
            elif ent.label_ == "DATE":
                entities["dates"].append(ent.text)
            elif ent.label_ in ["GPE", "LOC"]:
                entities["locations"].append(ent.text)
            elif ent.label_ == "PRODUCT":
                entities["products"].append(ent.text)

        # Deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def _fallback_entity_extraction(self, text: str) -> Dict[str, List[str]]:
        """Regex-based entity extraction when spaCy unavailable"""
        entities = {
            "people": [],
            "organizations": [],
            "monetary_values": [],
            "dates": [],
            "locations": [],
            "products": []
        }

        # Money pattern: $X,XXX or $X.XX
        money_pattern = re.compile(r'\$[\d,]+(?:\.\d{2})?')
        entities["monetary_values"] = list(set(money_pattern.findall(text)))

        # Date patterns
        date_pattern = re.compile(r'\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b')
        entities["dates"] = list(set(date_pattern.findall(text)))

        # Estate planning products
        product_keywords = [
            "trust", "revocable living trust", "will", "pour-over will",
            "power of attorney", "healthcare directive", "LLC"
        ]
        for keyword in product_keywords:
            if keyword.lower() in text.lower():
                entities["products"].append(keyword)

        return entities

    def _extract_topics(self, turns: List[Dict[str, Any]]) -> List[str]:
        """Extract main topics from conversation"""
        all_text = " ".join(turn["text"] for turn in turns)
        return self._extract_topics_from_text(all_text)

    def _extract_topics_from_text(self, text: str) -> List[str]:
        """
        Topic extraction using keyword frequency.

        Best Practice: Use topic modeling (LDA) or transformer-based classification.
        """
        # Estate planning domain keywords
        topic_keywords = {
            "estate_planning": ["estate", "planning", "plan", "property", "assets"],
            "trusts": ["trust", "revocable", "irrevocable", "living trust"],
            "wills": ["will", "testament", "pour-over"],
            "power_of_attorney": ["power of attorney", "POA", "healthcare directive"],
            "pricing": ["price", "cost", "fee", "deposit", "payment", "$"],
            "real_estate": ["house", "property", "real estate", "home"],
            "family": ["spouse", "children", "family", "married", "kids"],
            "business": ["LLC", "business", "company", "corporation"]
        }

        text_lower = text.lower()
        topic_scores = {}

        for topic, keywords in topic_keywords.items():
            score = sum(text_lower.count(kw.lower()) for kw in keywords)
            if score > 0:
                topic_scores[topic] = score

        # Return topics sorted by frequency
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, score in sorted_topics]

    def _analyze_turn_semantics(self, turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze semantic features of each turn: intent, sentiment, discourse markers.

        Best Practice: Use intent classification models and sentiment analysis.
        """
        semantic_turns = []

        for turn in turns:
            text = turn["text"]

            # Intent detection (rule-based for now)
            intent = self._detect_intent(text)

            # Sentiment analysis
            sentiment = self._analyze_sentiment(text)

            # Discourse markers
            discourse = self._detect_discourse_markers(text)

            semantic_turns.append({
                "timestamp": turn["timestamp"],
                "speaker": turn["speaker"],
                "intent": intent,
                "sentiment": sentiment,
                "discourse_marker": discourse,
                "contains_entity": self._contains_entity(text),
                "word_count": len(text.split())
            })

        return semantic_turns

    def _detect_intent(self, text: str) -> str:
        """Detect speaker intent (question, statement, objection, agreement, etc.)"""
        text_lower = text.lower().strip()

        # Question patterns
        if text.endswith("?") or any(text_lower.startswith(q) for q in ["what", "when", "where", "why", "how", "who", "can", "could", "would", "should"]):
            return "question"

        # Objection patterns
        objection_markers = ["but ", "however", "i don't think", "i'm not sure", "concern", "worried"]
        if any(marker in text_lower for marker in objection_markers):
            return "objection"

        # Agreement patterns
        agreement_markers = ["yes", "right", "exactly", "i agree", "that sounds", "perfect", "great"]
        if any(marker in text_lower for marker in agreement_markers):
            return "agreement"

        # Proposal/offer patterns
        if any(word in text_lower for word in ["we can", "i can help", "what if", "how about"]):
            return "proposal"

        # Default
        return "statement"

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment using transformer model"""
        if _sentiment_pipeline is None:
            return "neutral"

        try:
            # Truncate to 512 tokens (BERT limit)
            result = _sentiment_pipeline(text[:512])[0]
            label = result["label"].lower()  # POSITIVE or NEGATIVE

            # Map to our labels
            if label == "positive":
                return "positive"
            elif label == "negative":
                return "negative"
            else:
                return "neutral"
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return "neutral"

    def _detect_discourse_markers(self, text: str) -> str:
        """Detect discourse markers (transition, confirmation, hedge, emphasis)"""
        text_lower = text.lower()

        # Transition markers
        if any(marker in text_lower for marker in ["so", "now", "let's", "next", "moving on"]):
            return "transition"

        # Confirmation markers
        if any(marker in text_lower for marker in ["right?", "okay?", "make sense", "understand"]):
            return "confirmation"

        # Hedge markers
        if any(marker in text_lower for marker in ["maybe", "perhaps", "probably", "i think", "i believe"]):
            return "hedge"

        # Emphasis markers
        if any(marker in text_lower for marker in ["very", "really", "absolutely", "definitely", "important"]):
            return "emphasis"

        return "none"

    def _contains_entity(self, text: str) -> bool:
        """Quick check if text contains likely entities (money, dates, names)"""
        # Money pattern
        if re.search(r'\$[\d,]+', text):
            return True
        # Date pattern
        if re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}', text):
            return True
        # Capitalized words (potential names)
        if re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text):
            return True
        return False

    def _extract_relationships(self, entities: Dict[str, List[str]], turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract relationships between entities.

        Best Practice: Use dependency parsing to extract subject-verb-object triples.
        """
        relationships = []

        # Simple relationship: Client owns property in Location
        people = entities.get("people", [])
        locations = entities.get("locations", [])

        if people and locations:
            relationships.append({
                "subject": people[0] if people else "Client",
                "predicate": "owns property in",
                "object": locations[0] if locations else "Unknown"
            })

        return relationships

    def _compute_document_metadata(self, turns: List[Dict[str, Any]], semantic_turns: List[Dict[str, Any]], entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Compute document-level metadata"""
        # Speaker statistics
        speakers = [turn["speaker"] for turn in turns]
        speaker_counts = Counter(speakers)

        # Intent distribution
        intents = [st["intent"] for st in semantic_turns]
        intent_counts = Counter(intents)

        # Sentiment distribution
        sentiments = [st["sentiment"] for st in semantic_turns]
        sentiment_counts = Counter(sentiments)

        # Calculate engagement
        question_count = intent_counts.get("question", 0)
        total_turns = len(turns)
        engagement = "high" if question_count > total_turns * 0.2 else "medium" if question_count > total_turns * 0.1 else "low"

        return {
            "total_turns": total_turns,
            "speaker_distribution": dict(speaker_counts),
            "intent_distribution": dict(intent_counts),
            "sentiment_distribution": dict(sentiment_counts),
            "question_count": question_count,
            "objection_count": intent_counts.get("objection", 0),
            "client_engagement": engagement,
            "entity_count": sum(len(v) for v in entities.values())
        }


# Singleton instance
_nlp_processor = None


def get_nlp_processor() -> NLPProcessor:
    """Get singleton NLP processor instance"""
    global _nlp_processor
    if _nlp_processor is None:
        _nlp_processor = NLPProcessor()
    return _nlp_processor
