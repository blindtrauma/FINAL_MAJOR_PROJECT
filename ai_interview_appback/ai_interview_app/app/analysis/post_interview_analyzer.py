# app/analysis/post_interview_analyzer.py - Logic for post-interview analysis

from typing import Dict, Any
from app.services.llm_service import LLMService # Needs LLM for analysis
from app.services.storage_service import StorageService # Needs Storage to load previous analysis
from app.core.exceptions import LLMServiceError, StorageError # Import exceptions
from app.prompts import analysis_prompts # Needs prompts for analysis

class PostInterviewAnalyzer:
    """
    Analyzes the complete interview transcript against the Job Description
    and Resume analysis to generate a performance evaluation.
    """
    def __init__(self, llm_service: LLMService, storage_service: StorageService):
        self.llm_service = llm_service
        self.storage_service = storage_service
        # Get the specific prompt for post-interview analysis
        self.analysis_prompt_template = analysis_prompts.get_post_interview_analysis_prompt()


    def analyze(self, interview_id: str, transcript: str, jd_analysis: Dict[str, Any], resume_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes the full interview transcript using the pre-interview analysis
        results for context.
        """
        print(f"Running post-interview analysis for interview ID: {interview_id}")
        try:
            # Prepare data for the prompt
            jd_summary = jd_analysis.get("summary", "No JD summary available.") # Assuming analysis results have a summary field
            resume_summary = resume_analysis.get("summary", "No Resume summary available.")
            # Extract other relevant data from analyses as needed for the prompt

            # Construct the detailed prompt for the LLM
            analysis_instructions = self.analysis_prompt_template.format(
                job_description_summary=jd_summary,
                resume_summary=resume_summary,
                interview_transcript=transcript
                # Add other parameters based on prompt template
            )

            messages = [
                 {"role": "user", "content": analysis_instructions}
            ]

            # Call the LLM
            raw_llm_response = self.llm_service._call_llm(messages, temperature=0.3, max_tokens=1500) # Allow longer response for analysis report
            print(f"Raw LLM post-analysis response: {raw_llm_response[:200]}...")

            # TODO: Parse the raw LLM response into a structured dictionary (e.g., score, key strengths/weaknesses, relevance to JD)
            # Again, function calling or robust JSON parsing is recommended.
            # For now, simulate parsing
            try:
                 import json
                 import re
                 json_match = re.search(r"```json\s*(.*?)\s*```", raw_llm_response, re.DOTALL)
                 if json_match:
                     structured_result = json.loads(json_match.group(1))
                 else:
                     print("Warning: No JSON block found in LLM post-analysis response. Attempting basic parsing.")
                     structured_result = {"raw_output": raw_llm_response, "warning": "Could not parse structured JSON."}

            except json.JSONDecodeError as e:
                 print(f"JSON parsing failed for LLM post-analysis response: {e}")
                 structured_result = {"raw_output": raw_llm_response, "error": f"JSON parsing failed: {e}"}

            except Exception as e:
                 print(f"Unexpected error during LLM post-analysis response parsing: {e}")
                 structured_result = {"raw_output": raw_llm_response, "error": f"Unexpected parsing error: {e}"}


            # Include metadata
            structured_result["__metadata__"] = {"interview_id": interview_id}


            print(f"Post-interview analysis successful for interview ID: {interview_id}")
            return structured_result

        except (StorageError, LLMServiceError) as e:
            print(f"Post-interview analysis failed for {interview_id}: {e}")
            raise e # Re-raise to be caught by the calling task
        except Exception as e:
             print(f"Unexpected error during post-interview analysis for {interview_id}: {e}")
             raise e