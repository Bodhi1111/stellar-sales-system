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
        social_opportunities = social_opportunities or {}
        coaching_insights = coaching_insights or {}
        email_draft = email_draft or ""

        # Extract file_path if available in extra
        file_path = extra.get('file_path', None)

        try:
            # Generate comprehensive CRM record
            crm_record = await self._build_comprehensive_crm_record(
                extracted_data, chunks, email_draft, social_opportunities, coaching_insights, file_path
            )

            print(
                f"   🎯 Generated comprehensive CRM record with {len(crm_record)} fields")
            return crm_record

        except Exception as e:
            print(f"   ⚠️ Warning: Enhanced CRM processing failed: {e}")
            print(f"   📋 Falling back to basic CRM record")
            # Fallback to basic record that maintains compatibility
            return await self._build_basic_crm_record(
                extracted_data, chunks, email_draft, social_opportunities, coaching_insights, file_path
            )

    async def _build_comprehensive_crm_record(
        self,
        extracted_data: Dict[str, Any],
        chunks: List[str],  # NEW: Accept chunks for full transcript analysis
        email_draft: str,
        social_opportunities: Dict[str, Any],
        coaching_insights: Dict[str, Any],
        file_path: Optional[Path]
    ) -> Dict[str, Any]:
        """Build complete CRM record with all required fields"""

        # Core identifier and metadata
        transcript_id = str(uuid.uuid4())[:8]  # Short unique ID
        current_timestamp = datetime.now()

        # Extract enhanced data using LLM with FULL TRANSCRIPT for missing fields
        enhanced_extraction = await self._extract_missing_fields(extracted_data, chunks)

        # Build comprehensive CRM record
        crm_record = {
            # === BACKWARD COMPATIBILITY FIELDS (original fields) ===
            "client_name_legacy": extracted_data.get("client_name", ""),
            "main_objection": extracted_data.get("main_objection", ""),
            "next_steps": extracted_data.get("next_steps", ""),

            # === CORE MEETING DATA ===
            "transcript_id": transcript_id,
            "meeting_date": self._extract_meeting_date(extracted_data, current_timestamp),
            "timestamp": current_timestamp.isoformat(),
            "transcript_filename": file_path.name if file_path else "unknown.txt",

            # === CLIENT INFORMATION ===
            "client_name": extracted_data.get("client_name") or enhanced_extraction.get("client_name", ""),
            "client_email": extracted_data.get("client_email") or enhanced_extraction.get("client_email", ""),

            # === CLIENT PROFILE (Estate Planning Specific) ===
            "marital_status": enhanced_extraction.get("marital_status", ""),
            "children_count": enhanced_extraction.get("children_count", 0),
            "estate_value": enhanced_extraction.get("estate_value", 0),
            "real_estate_count": enhanced_extraction.get("real_estate_count", 0),
            "llc_interest": enhanced_extraction.get("llc_interest", ""),

            # === FINANCIAL DATA ===
            "deal": enhanced_extraction.get("deal_amount", 0),
            "deposit": enhanced_extraction.get("deposit_amount", 0),

            # === SALES DATA ===
            "product_discussed": self._extract_products_discussed(extracted_data, enhanced_extraction),
            "objections_raised": self._consolidate_objections(extracted_data),
            "outcome": self._determine_outcome(extracted_data, enhanced_extraction),
            "action_items": self._extract_next_steps(extracted_data, email_draft),

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

    async def _extract_missing_fields(self, extracted_data: Dict[str, Any], chunks: List[str]) -> Dict[str, Any]:
        """Use LLM to extract estate planning specific fields from FULL TRANSCRIPT"""

        # Handle chunks (can be list of strings OR list of dicts with 'text' key)
        if chunks and isinstance(chunks[0], dict):
            chunk_texts = [c.get('text', str(c)) for c in chunks]
        else:
            chunk_texts = chunks if chunks else []

        # Combine chunks into full transcript for comprehensive analysis
        full_transcript = "\n\n".join(chunk_texts) if chunk_texts else ""

        # Create a focused prompt for estate planning data extraction
        prompt = f"""
        Analyze this sales conversation transcript for estate planning specific information.

        FULL TRANSCRIPT:
        {full_transcript[:8000]}  # Limit to 8000 chars to avoid token limits

        ADDITIONAL CONTEXT (extracted summary):
        {json.dumps(extracted_data, indent=2)}

        Extract the following estate planning fields (use "not_found" if information not available):

        1. Client personal details:
           - client_name (full name of the client/prospect)
           - marital_status (Single/Married/Divorced/Widowed/Separated)
           - children_count (number)
           - client_email (email address)

        2. Estate information:
           - estate_value (estimated total value in dollars, number only)
           - real_estate_count (number of properties)
           - llc_interest (any LLC or business interests mentioned)

        3. Financial terms:
           - deal_amount (total estate planning service cost in dollars, number only)
           - deposit_amount (any deposit or partial payment mentioned in dollars, number only)

        4. Meeting outcome:
           - summary (brief meeting summary)
           - outcome_indication (Won/Lost/Pending based on conversation tone)

        Respond ONLY in JSON format:
        {{
            "client_name": "John Doe",
            "marital_status": "Married",
            "children_count": 2,
            "client_email": "client@example.com",
            "estate_value": 500000,
            "real_estate_count": 1,
            "llc_interest": "Tech startup LLC",
            "deal_amount": 15000,
            "deposit_amount": 5000,
            "summary": "Discussion about estate planning needs",
            "outcome_indication": "Pending"
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

            print("   ✅ Enhanced extraction completed with LLM analysis")
            return cleaned_result

        except Exception as e:
            print(f"   ⚠️ Warning: Enhanced extraction failed: {e}")
            return {}

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

    def _consolidate_objections(self, extracted_data: Dict[str, Any]) -> str:
        """Consolidate all objections raised during the meeting"""
        objections = []

        # Main objection
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
        """Determine meeting outcome based on available data"""
        # Check enhanced extraction first
        outcome_indication = enhanced_data.get("outcome_indication", "")
        if outcome_indication in self.outcome_choices:
            return outcome_indication

        # Check for outcome indicators in extracted data
        next_steps = str(extracted_data.get("next_steps", "")).lower()
        if any(indicator in next_steps for indicator in ["signed", "contract", "agreement", "closed"]):
            return "Won"
        elif any(indicator in next_steps for indicator in ["not interested", "declined", "passed"]):
            return "Lost"
        elif any(indicator in next_steps for indicator in ["follow up", "schedule", "think about"]):
            return "Follow-up Scheduled"
        else:
            return "Pending"

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
