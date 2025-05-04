# app/analysis/pre_interview_analyzer.py - Logic for pre-interview analysis

from typing import Dict, Any
from app.services.llm_service import LLMService # Needs LLM for analysis
from app.services.storage_service import StorageService # Needs Storage to load docs
from app.core.exceptions import LLMServiceError, StorageError # Import exceptions
from app.prompts import interview_prompts # Needs prompts for analysis

class PreInterviewAnalyzer:
    """
    Analyzes the Job Description and Resume documents to prepare
    for the interview. Identifies key skills, experience, requirements,
    and potentially generates an initial interview plan/questions.
    """
    def __init__(self, llm_service: LLMService, storage_service: StorageService):
        self.llm_service = llm_service
        self.storage_service = storage_service
        # Get the specific prompt for pre-interview analysis
        self.analysis_prompt_template = interview_prompts.get_pre_interview_analysis_prompt()

    def analyze(self, doc_id: str, document_type: str) -> Dict[str, Any]:
        """
        Analyzes a single document (JD or Resume) and extracts key information.
        Can also cross-analyze JD and Resume if both available (though this method
        is designed for single doc input, orchestrated by a task).
        """
        print(f"Running pre-interview analysis on {document_type} ID: {doc_id}")
        try:
            # Load the parsed text content
            doc_content = self.storage_service.load_document_content(doc_id)
            print(f"Loaded content for {doc_id}, length: {len(doc_content)}")

            # Prepare messages for the LLM
            # Include system prompt (from LLMService) and the specific analysis prompt
            # The analysis prompt should instruct the LLM on what to extract and format.
            # Consider using function calling here to structure the output reliably.
            # For simplicity, let's use a text prompt asking for structured JSON-like output.

            # Prompt instructions need to tell the LLM if it's a JD or Resume
            analysis_instructions = self.analysis_prompt_template.format(
                document_type=document_type,
                document_content=doc_content
            )

            # Example messages (assuming LLMService handles getting its system prompt)
            messages = [
                {"role": "user", "content": analysis_instructions}
            ]

            # Use LLMService to get the analysis result
            # Need a method in LLMService that takes messages and potentially expects structured output
            # Let's add a generic `analyze_with_prompt` method to LLMService or make _call_llm public/flexible.
            # Or use a specific method like `extract_structured_data`.

            # For now, let's mock or assume _call_llm can be used and we parse its string output.
            # A better approach involves Pydantic + Function Calling.

            # Simulating LLM call and parsing response (placeholder)
            raw_llm_response = self.llm_service._call_llm(messages, temperature=0.1, max_tokens=1000) # Use lower temp for structured output
            print(f"Raw LLM analysis response: {raw_llm_response[:200]}...")

            # TODO: Parse the raw LLM response into a structured dictionary
            # This is crucial. Regex, JSON parsing (if LLM outputs JSON), or function calling parsing.
            # For robust structured output, LLM function calling is recommended.
            # Example: Assume LLM outputs a JSON string within ```json ... ```
            try:
                 # Find JSON block and parse it
                 import json
                 import re
                 json_match = re.search(r"```json\s*(.*?)\s*```", raw_llm_response, re.DOTALL)
                 if json_match:
                     structured_result = json.loads(json_match.group(1))
                 else:
                     # Fallback or error if JSON block not found
                     print("Warning: No JSON block found in LLM analysis response. Attempting basic parsing.")
                     # Basic parsing fallback, or raise error
                     structured_result = {"raw_output": raw_llm_response, "warning": "Could not parse structured JSON."}

            except json.JSONDecodeError as e:
                print(f"JSON parsing failed for LLM response: {e}")
                structured_result = {"raw_output": raw_llm_response, "error": f"JSON parsing failed: {e}"}
                # Decide if this should raise DocumentProcessingError or return partial result

            except Exception as e:
                 print(f"Unexpected error during LLM response parsing: {e}")
                 structured_result = {"raw_output": raw_llm_response, "error": f"Unexpected parsing error: {e}"}


            # Include metadata
            structured_result["__metadata__"] = {"doc_id": doc_id, "document_type": document_type}


            # TODO: If this method should produce the *combined* interview plan, it would need *both* doc_ids,
            # load both analyses, and run a *third* LLM call to synthesize the plan.
            # Let's simplify: This method analyzes *one* document. The task `generate_initial_interview_plan`
            # (or a separate task/manager logic) combines the two analysis results into the final plan.

            print(f"Pre-interview analysis successful for {document_type} ID: {doc_id}")
            return structured_result

        except (StorageError, LLMServiceError) as e:
            print(f"Pre-interview analysis failed for {doc_id}: {e}")
            # Re-raise to be caught by the calling task
            raise e
        except Exception as e:
             print(f"Unexpected error during pre-interview analysis for {doc_id}: {e}")
             raise e