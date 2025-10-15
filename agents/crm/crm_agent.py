"""
CRM Agent for Estate Planning Business
Captures all required fields for complete business intelligence
"""

import json
import requests
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from agents.base_agent import BaseAgent
from config.settings import Settings


class CRMAgent(BaseAgent):
    """
    CRM Agent that captures all required fields for estate planning business.

    IMPORTANT: Class name kept as CRMAgent for backward compatibility.
    Enhanced to capture complete client profiles, financial data, meeting outcomes,
    and business intelligence for maximum sales effectiveness.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME

        # Define product choices for estate planning business
        self.product_choices = [
            "Life Insurance", "Estate Planning", "Trust Services",
            "Will Preparation", "Tax Planning", "Investment Advisory"
        ]

        # Define outcome statuses
        self.outcome_choices = ["Won", "Lost", "Pending",
                                "Follow-up Scheduled", "Needs More Info"]

        # Define marital status options
        self.marital_status_choices = [
            "Single", "Married", "Divorced", "Widowed", "Separated"]

    async def run(
        self,
        extracted_data: Dict[str, Any],
        chunks: Optional[List[str]] = None,  # NEW: Accept transcript chunks
        header_metadata: Optional[Dict[str, Any]] = None,  # NEW: Header metadata from parser
        email_draft: Optional[str] = None,
        social_opportunities: Optional[Any] = None,
        coaching_insights: Optional[Any] = None,
        **extra  # Keep for any additional parameters
    ) -> Dict[str, Any]:
        """
        Process complete CRM data with all required fields for estate planning business.

        Args:
            extracted_data: Base customer/meeting data from Extractor
            chunks: Full transcript chunks for detailed analysis (NEW!)
            header_metadata: Extracted header metadata (meeting_title, client_name, email, date, etc.)
            email_draft: Follow-up email content from Email Agent
            social_opportunities: Social content from Social Agent
            coaching_insights: Performance feedback from Sales Coach Agent
            **extra: Additional parameters for flexibility

        Returns:
            Comprehensive CRM record with all business-required fields
        """
        print("📠 CRMAgent: Building comprehensive estate planning CRM record...")

        # Handle None values and ensure dict types
        extracted_data = extracted_data or {}
        chunks = chunks or []  # Default to empty list if no chunks provided
        header_metadata = header_metadata or {}  # Default to empty dict
        social_opportunities = social_opportunities or {}
        coaching_insights = coaching_insights or {}
        email_draft = email_draft or ""

        # Extract file_path if available in extra
        file_path = extra.get('file_path', None)

        try:
            # Generate comprehensive CRM record
            crm_record = await self._build_comprehensive_crm_record(
                extracted_data, chunks, header_metadata, email_draft, social_opportunities, coaching_insights, file_path
            )

            print(
                f"   🎯 Generated comprehensive CRM record with {len(crm_record)} fields")
            return crm_record

        except Exception as e:
            print(f"   ⚠️ Warning: Enhanced CRM processing failed: {e}")
            print(f"   📋 Falling back to basic CRM record")
            # Fallback to basic record that maintains compatibility
            return await self._build_basic_crm_record(
                extracted_data, chunks, header_metadata, email_draft, social_opportunities, coaching_insights, file_path
            )

    async def _build_comprehensive_crm_record(
        self,
        extracted_data: Dict[str, Any],
        chunks: List[str],  # NEW: Accept chunks for full transcript analysis
        header_metadata: Dict[str, Any],  # NEW: Header metadata from parser
        email_draft: str,
        social_opportunities: Dict[str, Any],
        coaching_insights: Dict[str, Any],
        file_path: Optional[Path]
    ) -> Dict[str, Any]:
        """Build complete CRM record with all required fields"""

        # Core identifier and metadata
        transcript_id = str(uuid.uuid4())[:8]  # Short unique ID
        current_timestamp = datetime.now()

        # PRIORITY 1: Use header metadata if available (fast + accurate)
        if header_metadata:
            print("   ✅ Using header metadata for CRM fields (accurate + fast)")

        # Extract enhanced data using LLM with FULL TRANSCRIPT for missing fields
        enhanced_extraction = await self._extract_missing_fields(extracted_data, chunks)

        # PRIORITY ORDER: header_metadata > extracted_data > enhanced_extraction (LLM)
        # This ensures fast, accurate data from headers is used first
        client_name = (
            header_metadata.get('client_name') if header_metadata.get('client_name')
            else extracted_data.get("client_name") or enhanced_extraction.get("client_name", "")
        )
        client_email = (
            header_metadata.get('client_email') if header_metadata.get('client_email')
            else extracted_data.get("client_email") or enhanced_extraction.get("client_email", "")
        )
        meeting_date = (
            header_metadata.get('meeting_date') if header_metadata.get('meeting_date')
            else self._extract_meeting_date(extracted_data, current_timestamp)
        )
        meeting_title = header_metadata.get('meeting_title', '') if header_metadata else ''
        transcript_id_from_header = header_metadata.get('transcript_id', '') if header_metadata else ''
        meeting_time = header_metadata.get('meeting_time', '') if header_metadata else ''
        duration_minutes = header_metadata.get('duration_minutes', 0) if header_metadata else 0

        # Build comprehensive CRM record
        crm_record = {
            # === BACKWARD COMPATIBILITY FIELDS (original fields) ===
            "client_name_legacy": extracted_data.get("client_name", ""),
            "main_objection": extracted_data.get("main_objection", ""),
            "next_steps": extracted_data.get("next_steps", ""),

            # === CORE MEETING DATA ===
            "transcript_id": transcript_id_from_header or transcript_id,  # Prefer header ID
            "meeting_title": meeting_title,  # NEW: Human-readable meeting identifier
            "meeting_date": meeting_date,
            "meeting_time": meeting_time,  # NEW: Time component from header
            "duration_minutes": duration_minutes,  # NEW: Meeting duration from header
            "timestamp": current_timestamp.isoformat(),
            "transcript_filename": file_path.name if file_path else "unknown.txt",

            # === CLIENT INFORMATION ===
            "client_name": client_name,  # Prioritized from header
            "client_email": client_email,  # Prioritized from header

            # === CLIENT PROFILE (Estate Planning Specific) ===
            "marital_status": enhanced_extraction.get("marital_status", ""),
            "children_count": enhanced_extraction.get("children_count", 0),
            "estate_value": enhanced_extraction.get("estate_value", 0),
            "real_estate_count": enhanced_extraction.get("real_estate_count", 0),
            "llc_interest": enhanced_extraction.get("llc_interest", ""),

            # === SALES DATA === (Determine outcome FIRST for validation)
            "product_discussed": self._extract_products_discussed(extracted_data, enhanced_extraction),
            "objections_raised": self._consolidate_objections(extracted_data, enhanced_extraction),
            "outcome": self._determine_outcome(extracted_data, enhanced_extraction),
            "action_items": self._extract_next_steps(extracted_data, email_draft),

            # === FINANCIAL DATA === (CRITICAL: Set to $0 if outcome != Won)
            "deal": self._validate_deal_amount(enhanced_extraction, self._determine_outcome(extracted_data, enhanced_extraction)),
            "deposit": self._validate_deposit_amount(enhanced_extraction, self._determine_outcome(extracted_data, enhanced_extraction)),

            # === DEAL TRACKING (NEW) ===
            # Set close_date to meeting_date if deal is Won
            "close_date": meeting_date if self._determine_outcome(extracted_data, enhanced_extraction) == "Won" else "",
            # Set win_probability based on outcome (1.0 = Won, 0.0 = Lost, 0.5 = Pending)
            "win_probability": self._calculate_win_probability(self._determine_outcome(extracted_data, enhanced_extraction)),

            # === CONTENT AND INSIGHTS ===
            "transcript_summary": extracted_data.get("summary", enhanced_extraction.get("summary", "")),
            "follow_up_email_draft": email_draft,
            "social_media_quote": self._extract_social_quote(social_opportunities),
            "coaching_opportunities": self._extract_coaching_opportunities(coaching_insights),

            # === ORIGINAL FIELDS FOR COMPATIBILITY ===
            "email_draft": email_draft,
            "social_opportunities": social_opportunities,
            "coaching_insights": coaching_insights,

            # === SYSTEM DATA ===
            # Full extracted data as JSON blob
            "crm_data_populated": json.dumps(extracted_data),

            # === ENHANCEMENT METADATA ===
            "data_sources_count": self._count_data_sources(email_draft, social_opportunities, coaching_insights),
            "record_completeness": "comprehensive",
            "processing_timestamp": current_timestamp.isoformat()
        }

        # Add validation and cleanup
        crm_record = self._validate_and_clean_record(crm_record)

        return crm_record

    def _extract_dollar_amounts(self, full_transcript: str) -> Dict[str, float]:
        """
        REGEX-BASED dollar amount extraction from ENTIRE transcript.
        Uses CONFIDENCE SCORING to identify final deal total vs component prices.

        Based on user annotations: "that would bring the entirety of your balance to is just $3,225 for everything"
        """
        import re

        # Find all dollar amounts
        pattern = r'\$([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)'
        amounts_found = []

        for match in re.finditer(pattern, full_transcript):
            amount_str = match.group(1).replace(',', '')
            amount = float(amount_str)

            # Get LARGER context window (200 chars) for better phrase matching
            context_start = max(0, match.start() - 150)
            context_end = min(len(full_transcript), match.end() + 150)
            context = full_transcript[context_start:context_end].lower()

            amounts_found.append({
                'amount': amount,
                'context': context,
                'position': match.start()
            })

        # Confidence scoring system
        best_deal_candidate = None
        best_deal_score = 0
        best_deposit_candidate = None
        best_deposit_score = 0

        last_30_percent = len(full_transcript) * 0.7

        for item in amounts_found:
            # Skip large amounts (likely estate values > $100k)
            if item['amount'] > 100000:
                continue

            # === DEAL AMOUNT CONFIDENCE SCORING ===
            deal_score = 0

            # High-confidence final total phrases (from user annotation)
            final_total_kw = [
                'bring the entirety', 'bring your balance', 'bring the balance',
                'is just', 'for everything', 'entirety of your balance',
                'balance to is', 'final balance', 'total balance'
            ]

            # Medium-confidence deal keywords
            deal_kw = ['balance', 'total', 'entirety', 'everything', 'bring', 'price', 'fee', 'cost']

            # Low-confidence partial payment keywords (reduce score)
            partial_kw = ['down', 'deposit', 'upfront', 'initial', 'first payment', 'half']

            # Position scoring (closing section = higher confidence)
            in_closing = item['position'] > last_30_percent

            # Calculate deal score
            if any(kw in item['context'] for kw in final_total_kw):
                deal_score += 5  # Very high confidence for exact phrases

            if any(kw in item['context'] for kw in deal_kw):
                deal_score += 2  # Medium confidence

            if in_closing:
                deal_score += 3  # Higher confidence in closing section

            # REDUCE score if it looks like a partial payment
            if any(kw in item['context'] for kw in partial_kw):
                deal_score -= 2

            # Check for amounts between $1k-$50k (typical deal range)
            if 1000 <= item['amount'] <= 50000:
                deal_score += 1

            # Update best candidate if this has higher score
            if deal_score > best_deal_score:
                best_deal_score = deal_score
                best_deal_candidate = item
                print(f"      🎯 New best deal candidate: ${item['amount']} (score={deal_score})")
                print(f"         Context: ...{item['context'][:80]}...")

            # === DEPOSIT AMOUNT SCORING ===
            deposit_score = 0
            deposit_kw = ['deposit', 'down payment', 'upfront', 'initial', 'today', 'now', 'first payment']

            if any(kw in item['context'] for kw in deposit_kw):
                deposit_score += 3

            # Skip large amounts (deposits should be < $10k typically)
            if item['amount'] > 10000:
                deposit_score = 0

            # Prefer amounts in closing section
            if in_closing and deposit_score > 0:
                deposit_score += 2

            if deposit_score > best_deposit_score:
                best_deposit_score = deposit_score
                best_deposit_candidate = item

        # Extract final amounts
        deal_amount = best_deal_candidate['amount'] if best_deal_candidate else 0
        deposit_amount = best_deposit_candidate['amount'] if best_deposit_candidate else 0

        if best_deal_candidate:
            print(f"      ✅ FINAL: Selected deal=${deal_amount} with confidence score={best_deal_score}")
        if best_deposit_candidate:
            print(f"      ✅ FINAL: Selected deposit=${deposit_amount} with confidence score={best_deposit_score}")

        return {'deal_amount': deal_amount, 'deposit_amount': deposit_amount}

    async def _extract_missing_fields(self, extracted_data: Dict[str, Any], chunks: List[str]) -> Dict[str, Any]:
        """Extract fields using HYBRID strategy: REGEX + LLM

        Pass 1: REGEX for dollar amounts (fast, accurate, scans ENTIRE transcript)
        Pass 2: LLM for contextual fields (outcome, marital status, etc.)
        """

        # Handle chunks (can be list of strings OR list of dicts with 'text' key)
        if chunks and isinstance(chunks[0], dict):
            chunk_texts = [c.get('text', str(c)) for c in chunks]
        else:
            chunk_texts = chunks if chunks else []

        # Combine chunks
        full_transcript = "\n\n".join(chunk_texts) if chunk_texts else ""
        transcript_length = len(full_transcript)

        # PASS 1: REGEX extraction (searches ENTIRE transcript)
        print("   💰 REGEX: Scanning transcript for dollar amounts...")
        regex_amounts = self._extract_dollar_amounts(full_transcript)
        print(f"      💵 REGEX found: deal=${regex_amounts['deal_amount']}, deposit=${regex_amounts['deposit_amount']}")

        # PASS 2: LLM extraction for contextual data

        # PASS 1: Extract CLIENT DETAILS from beginning (first 3000 chars)
        client_section = full_transcript[:3000]

        # PASS 2: Extract FINANCIAL DATA from end (last 6000 chars - CRITICAL FOR CLOSING)
        # This is where "I'm ready to move forward", credit card processing, and amounts appear
        financial_section = full_transcript[max(0, transcript_length - 6000):]

        # Create targeted prompt with BOTH sections but emphasize financial
        prompt = f"""
        Analyze this sales conversation for estate planning information.

        BEGINNING (Client details):
        {client_section}

        ... [middle section omitted] ...

        END OF TRANSCRIPT (CRITICAL - Deal closing, payment, final decision):
        {financial_section}

        ADDITIONAL CONTEXT:
        {json.dumps(extracted_data, indent=2)}

        Extract the following fields (use "not_found" if not mentioned):

        1. Client personal details:
           - client_name (full name of the client/prospect)
           - marital_status (Single/Married/Divorced/Widowed/Separated)
           - children_count (number)
           - client_email (email address)
           - client_phone (phone number - ONLY extract actual phone numbers in format XXX-XXX-XXXX, do NOT extract numbers from timeline discussions like "3 days" or "5 business days")

        2. Estate information:
           - estate_value (estimated total value in dollars, number only)
           - real_estate_count (number of properties)
           - llc_interest (any LLC or business interests mentioned)

        3. Financial terms (CRITICAL - Look for payment discussions near end of transcript):
           - deal_amount (total service cost in dollars - look for phrases like "$3,200", "three thousand", payment amounts)
           - deposit_amount (initial payment or deposit in dollars)

           IMPORTANT: Search the ENTIRE transcript for dollar amounts, especially:
           - Around timestamps 01:00:00 and later (closing phase)
           - When discussing "moving forward", "let's do it", "ready to proceed"
           - Payment plan discussions, credit card processing
           - Look for patterns like "$X,XXX" or "X thousand" or "X hundred"

        4. Objections (CRITICAL - What's blocking the sale?):
           - objections_raised (single word describing PRIMARY objection)

           **OBJECTION DETECTION RULES**:
           Look for phrases that indicate what's blocking the sale:
           - "Spouse" = needs to discuss with spouse/wife/husband/partner
           - "Price" = too expensive, cost concerns, affordability issues
           - "Time" = need to think about it, not ready yet
           - "Authority" = need to talk to someone else (not spouse)
           - "None" = no objections raised, ready to proceed

           Examples:
           - "I need to discuss this with my wife" → "Spouse"
           - "Let me talk to my husband about it" → "Spouse"
           - "That's more than I expected to pay" → "Price"
           - "I need some time to think" → "Time"

        5. Meeting outcome (CRITICAL - ONLY mark Won if payment processed):
           - summary (brief meeting summary)
           - outcome_indication (Won/Lost/Follow-up Scheduled/Pending)
           - payment_processed (boolean - did client provide credit card/payment details?)

           **STRICT RULES FOR OUTCOME**:

           Mark as "Won" ONLY IF ALL of these are true:
           - Client provides credit card number, security code, billing zip code
           - Payment is actually processed in the closing section (usually last 5-10 minutes)
           - Look for phrases like: "card number", "security code", "CVV", "zip code", "expiration date"
           - Explicit confirmation of payment processing

           Mark as "Follow-up Scheduled" if:
           - Client needs to "discuss with spouse"
           - Client needs to "think about it"
           - Client says "I'll get back to you"
           - No payment information provided

           Mark as "Lost" if client explicitly declines or says not interested
           Mark as "Pending" if outcome is unclear

        Respond ONLY in JSON format:
        {{
            "client_name": "John Doe",
            "marital_status": "Married",
            "children_count": 2,
            "client_email": "client@example.com",
            "client_phone": "555-123-4567",
            "estate_value": 500000,
            "real_estate_count": 1,
            "llc_interest": "Tech startup LLC",
            "objections_raised": "None",
            "deal_amount": 3200,
            "deposit_amount": 700,
            "payment_processed": true,
            "summary": "Discussion about estate planning needs, payment processed",
            "outcome_indication": "Won"
        }}

        Example for NO payment (Follow-up with Spouse objection):
        {{
            "client_name": "Jane Smith",
            "marital_status": "Married",
            "children_count": 1,
            "client_email": "jane@example.com",
            "client_phone": "555-987-6543",
            "estate_value": 0,
            "real_estate_count": 0,
            "llc_interest": "",
            "objections_raised": "Spouse",
            "deal_amount": 0,
            "deposit_amount": 0,
            "payment_processed": false,
            "summary": "Needs to discuss with spouse before proceeding",
            "outcome_indication": "Follow-up Scheduled"
        }}
        """

        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "format": "json",
                "stream": False
            }

            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()

            response_data = response.json()
            result = json.loads(response_data.get("response", "{}"))

            # Clean up "not_found" values
            cleaned_result = {}
            for key, value in result.items():
                if value != "not_found" and value != "" and value is not None:
                    # Convert numeric strings to numbers
                    if key in ["children_count", "estate_value", "real_estate_count", "deal_amount", "deposit_amount"]:
                        try:
                            cleaned_result[key] = float(
                                value) if '.' in str(value) else int(value)
                        except (ValueError, TypeError):
                            cleaned_result[key] = 0
                    else:
                        cleaned_result[key] = value
                else:
                    # Set appropriate defaults
                    if key in ["children_count", "estate_value", "real_estate_count", "deal_amount", "deposit_amount"]:
                        cleaned_result[key] = 0
                    else:
                        cleaned_result[key] = ""

            # MERGE: Override LLM amounts with REGEX amounts (more accurate)
            if regex_amounts['deal_amount'] > 0:
                cleaned_result['deal_amount'] = regex_amounts['deal_amount']
                print(f"      ✅ Using REGEX deal_amount: ${regex_amounts['deal_amount']}")
            if regex_amounts['deposit_amount'] > 0:
                cleaned_result['deposit_amount'] = regex_amounts['deposit_amount']
                print(f"      ✅ Using REGEX deposit_amount: ${regex_amounts['deposit_amount']}")

            print("   ✅ Enhanced extraction completed (HYBRID: REGEX + LLM)")
            return cleaned_result

        except Exception as e:
            print(f"   ⚠️ Warning: Enhanced extraction failed: {e}")
            # Still return REGEX amounts even if LLM fails
            return {
                'deal_amount': regex_amounts.get('deal_amount', 0),
                'deposit_amount': regex_amounts.get('deposit_amount', 0)
            }

    def _extract_meeting_date(self, extracted_data: Dict[str, Any], fallback: datetime) -> str:
        """Extract or determine meeting date"""
        # Look for date in extracted data
        if "meeting_date" in extracted_data:
            return extracted_data["meeting_date"]
        if "date" in extracted_data:
            return extracted_data["date"]

        # Use current date as fallback
        return fallback.strftime("%Y-%m-%d")

    def _extract_products_discussed(self, extracted_data: Dict[str, Any], enhanced_data: Dict[str, Any]) -> str:
        """Determine what products/services were discussed"""
        products = []

        # Check extracted data for product mentions
        text_to_check = " ".join([
            str(extracted_data.get("summary", "")),
            str(extracted_data.get("pain_points", [])),
            str(extracted_data.get("needs", []))
        ]).lower()

        # Check for estate planning keywords
        if any(keyword in text_to_check for keyword in ["trust", "estate", "will", "inheritance"]):
            products.append("Estate Planning")
        if any(keyword in text_to_check for keyword in ["life insurance", "insurance", "policy"]):
            products.append("Life Insurance")
        if any(keyword in text_to_check for keyword in ["tax", "taxes", "tax planning"]):
            products.append("Tax Planning")

        return ", ".join(products) if products else "Estate Planning"

    def _consolidate_objections(self, extracted_data: Dict[str, Any], enhanced_data: Dict[str, Any] = None) -> str:
        """
        Consolidate all objections raised during the meeting.

        Priority: LLM-extracted objections > legacy extracted_data
        """
        enhanced_data = enhanced_data or {}
        objections = []

        # PRIORITY 1: LLM-extracted objection (most accurate)
        llm_objection = enhanced_data.get("objections_raised", "")
        if llm_objection and llm_objection.lower() not in ["none", "not_found", ""]:
            return llm_objection

        # FALLBACK: Legacy objections from extracted_data
        main_objection = extracted_data.get("main_objection", "")
        if main_objection and "not found" not in main_objection.lower():
            objections.append(main_objection)

        # Other objections
        other_objections = extracted_data.get("objections", [])
        if isinstance(other_objections, list):
            objections.extend(other_objections)
        elif isinstance(other_objections, str) and other_objections:
            objections.append(other_objections)

        return "; ".join(objections) if objections else ""

    def _determine_outcome(self, extracted_data: Dict[str, Any], enhanced_data: Dict[str, Any]) -> str:
        """
        Determine meeting outcome based on PAYMENT PROCESSING.

        STRICT RULE: "Won" ONLY if payment was processed (credit card details provided).
        """
        # Check if payment was actually processed
        payment_processed = enhanced_data.get("payment_processed", False)

        # VALIDATION: Won REQUIRES payment processing
        outcome_indication = enhanced_data.get("outcome_indication", "")

        if outcome_indication == "Won":
            # Double-check: Won requires payment_processed = true
            if not payment_processed:
                print(f"   ⚠️ VALIDATION: Outcome was 'Won' but no payment processed. Changing to 'Follow-up Scheduled'")
                return "Follow-up Scheduled"
            return "Won"

        # If outcome is explicitly in valid choices, use it
        if outcome_indication in self.outcome_choices:
            return outcome_indication

        # Fallback: Check for outcome indicators in extracted data
        next_steps = str(extracted_data.get("next_steps", "")).lower()
        if any(indicator in next_steps for indicator in ["not interested", "declined", "passed"]):
            return "Lost"
        elif any(indicator in next_steps for indicator in ["follow up", "schedule", "think about", "discuss with spouse"]):
            return "Follow-up Scheduled"
        else:
            return "Pending"

    def _calculate_win_probability(self, outcome: str) -> float:
        """Calculate win probability based on deal outcome (0.0 to 1.0)"""
        probability_map = {
            "Won": 1.0,
            "Lost": 0.0,
            "Pending": 0.5,
            "Follow-up Scheduled": 0.6,
            "Needs More Info": 0.4
        }
        return probability_map.get(outcome, 0.5)

    def _validate_deal_amount(self, enhanced_data: Dict[str, Any], outcome: str) -> float:
        """
        Validate deal amount: ONLY non-zero if outcome = Won.

        STRICT RULE: If deal not closed (outcome != Won), deal amount MUST be $0.
        """
        deal_amount = enhanced_data.get("deal_amount", 0)

        if outcome != "Won":
            if deal_amount > 0:
                print(f"   ⚠️ VALIDATION: Outcome='{outcome}' but deal_amount=${deal_amount}. Setting to $0.")
            return 0.0

        return float(deal_amount)

    def _validate_deposit_amount(self, enhanced_data: Dict[str, Any], outcome: str) -> float:
        """
        Validate deposit amount: ONLY non-zero if outcome = Won.

        STRICT RULE: If deal not closed (outcome != Won), deposit MUST be $0.
        """
        deposit_amount = enhanced_data.get("deposit_amount", 0)

        if outcome != "Won":
            if deposit_amount > 0:
                print(f"   ⚠️ VALIDATION: Outcome='{outcome}' but deposit_amount=${deposit_amount}. Setting to $0.")
            return 0.0

        return float(deposit_amount)

    def _extract_next_steps(self, extracted_data: Dict[str, Any], email_draft: str) -> str:
        """Extract and consolidate next steps"""
        next_steps = []

        # From extracted data
        extracted_next_steps = extracted_data.get("next_steps", "")
        if extracted_next_steps:
            next_steps.append(extracted_next_steps)

        # From email insights (look for action items)
        if email_draft:
            email_lower = email_draft.lower()
            if "follow up" in email_lower or "schedule" in email_lower:
                if "Follow-up communication planned" not in next_steps:
                    next_steps.append("Follow-up communication planned")
            if "send" in email_lower and "Send additional information" not in next_steps:
                next_steps.append("Send additional information")

        return "; ".join(next_steps) if next_steps else ""

    def _extract_social_quote(self, social_opportunities: Dict[str, Any]) -> str:
        """Extract the best social media quote"""
        if not social_opportunities:
            return ""

        # Handle both dict and string types
        if isinstance(social_opportunities, str):
            return social_opportunities[:200] if len(social_opportunities) > 200 else social_opportunities

        # Look for testimonials or memorable quotes
        testimonial = social_opportunities.get("testimonial", "")
        if testimonial:
            return testimonial

        # Look for social posts
        social_posts = social_opportunities.get("social_posts", [])
        if social_posts and isinstance(social_posts, list) and len(social_posts) > 0:
            return str(social_posts[0])

        # Look for other social content
        linkedin_post = social_opportunities.get("linkedin_post", "")
        if linkedin_post:
            # Extract first sentence as quote
            sentences = linkedin_post.split(".")
            if sentences:
                return sentences[0].strip() + "."

        return ""

    def _extract_coaching_opportunities(self, coaching_insights: Dict[str, Any]) -> str:
        """Extract coaching opportunities and recommendations"""
        if not coaching_insights:
            return ""

        # Handle both dict and string types
        if isinstance(coaching_insights, str):
            return coaching_insights[:500] if len(coaching_insights) > 500 else coaching_insights

        opportunities = []

        # Areas for improvement
        areas = coaching_insights.get("areas_for_improvement", [])
        if isinstance(areas, list):
            opportunities.extend(areas)
        elif isinstance(areas, str) and areas:
            opportunities.append(areas)

        # Specific recommendations
        recommendations = coaching_insights.get("recommendations", "")
        if recommendations and recommendations not in opportunities:
            opportunities.append(recommendations)

        # Feedback
        feedback = coaching_insights.get("feedback", "")
        if feedback and feedback not in opportunities:
            opportunities.append(feedback)

        return "; ".join(opportunities) if opportunities else ""

    def _count_data_sources(self, email_draft: str, social_opportunities: Dict[str, Any], coaching_insights: Dict[str, Any]) -> int:
        """Count how many data sources were integrated"""
        count = 1  # Base extraction always counts
        if email_draft:
            count += 1
        if social_opportunities:
            count += 1
        if coaching_insights:
            count += 1
        return count

    def _validate_and_clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the CRM record"""
        # Ensure numeric fields are actually numeric
        numeric_fields = ["children_count", "estate_value",
                          "real_estate_count", "deal", "deposit"]
        for field in numeric_fields:
            if field in record:
                try:
                    record[field] = float(record[field]) if '.' in str(
                        record[field]) else int(record[field])
                except (ValueError, TypeError):
                    record[field] = 0

        # Ensure choice fields have valid values
        if record.get("outcome") not in self.outcome_choices:
            record["outcome"] = "Pending"

        if record.get("marital_status") and record.get("marital_status") not in self.marital_status_choices:
            record["marital_status"] = ""

        # Clean up empty strings and None values
        for key, value in record.items():
            if value is None:
                record[key] = "" if isinstance(record.get(key, ""), str) else 0

        return record

    async def _build_basic_crm_record(
        self,
        extracted_data: Dict[str, Any],
        chunks: List[str],  # Accept chunks for consistency
        header_metadata: Dict[str, Any],  # NEW: Header metadata
        email_draft: str,
        social_opportunities: Dict[str, Any],
        coaching_insights: Dict[str, Any],
        file_path: Optional[Path]
    ) -> Dict[str, Any]:
        """Fallback method to build basic CRM record if enhanced processing fails"""

        # Create basic record that maintains backward compatibility
        basic_record = {
            # Original fields for compatibility
            "client_name_legacy": extracted_data.get("client_name", ""),
            "main_objection": extracted_data.get("main_objection", ""),
            "next_steps": extracted_data.get("next_steps", ""),
            "email_draft": email_draft,
            "social_opportunities": social_opportunities,
            "coaching_insights": coaching_insights,

            # Additional basic fields
            "transcript_id": str(uuid.uuid4())[:8],
            "meeting_date": datetime.now().strftime("%Y-%m-%d"),
            "client_name": extracted_data.get("client_name", ""),
            "client_email": extracted_data.get("client_email", ""),
            "product_discussed": "Estate Planning",
            "objections_raised": extracted_data.get("main_objection", ""),
            "transcript_summary": extracted_data.get("summary", ""),
            "outcome": "Pending",
            "action_items": extracted_data.get("next_steps", ""),
            "timestamp": datetime.now().isoformat(),
            "record_completeness": "basic",

            # Include all extracted data for compatibility
            **extracted_data
        }

        return basic_record
