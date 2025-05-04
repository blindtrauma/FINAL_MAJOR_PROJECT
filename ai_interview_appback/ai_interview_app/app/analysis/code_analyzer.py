# app/analysis/code_analyzer.py - Logic for analyzing code snippets

from typing import Dict, Any
from app.services.llm_service import LLMService # Needs LLM for analysis
from app.prompts import code_analysis_prompts # Needs prompts and potentially function definitions

class CodeAnalyzer:
    """
    Analyzes code snippets provided by the user during the interview.
    Uses LLM function calling or agents to evaluate correctness, style, efficiency, etc.
    """
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        # Load function definitions and relevant prompts
        self.code_analysis_function = code_analysis_prompts.get_code_analysis_function_definition()
        self.analysis_prompt_template = code_analysis_prompts.get_code_analysis_prompt()


    def analyze(self, code_snippet: str, context: str, jd_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes a code snippet using the LLM.
        """
        print(f"Analyzing code snippet. Snippet length: {len(code_snippet)}")
        try:
            # Prepare the prompt for the LLM, including context and JD details
            jd_summary = jd_analysis.get("summary", "No JD summary provided.")
            analysis_instructions = self.analysis_prompt_template.format(
                code_snippet=code_snippet,
                context=context,
                job_description_summary=jd_summary
            )

            # Messages for the LLM. Include the system prompt from LLMService.
            # If using function calling, include the function definition.
            messages = [
                 {"role": "user", "content": analysis_instructions}
            ]

            # Example using assumed function calling support in LLMService
            # LLMService would need a dedicated method for this.
            # Let's add a placeholder method call.

            # Simulating LLM call with potential function calling (placeholder)
            # raw_llm_response = self.llm_service.call_with_function_calling(
            #     messages=messages,
            #     tools=[{"type": "function", "function": self.code_analysis_function}],
            #     tool_choice={"type": "function", "function": {"name": self.code_analysis_function['name']}} # Force function call
            # )

            # For now, let's just use a regular LLM call assuming the prompt guides it
            # to output analysis text, perhaps in a structured format.
            raw_llm_response = self.llm_service._call_llm(messages, temperature=0.5, max_tokens=500)
            print(f"Raw LLM code analysis response: {raw_llm_response[:200]}...")


            # TODO: Parse the raw LLM response. If using function calling, process the tool call.
            # If not, parse the text output (e.g., JSON block).
            # Simulating parsing output
            structured_result = {"analysis": raw_llm_response, "evaluated_snippet": code_snippet} # Basic structure


            print(f"Code analysis successful for snippet.")
            return structured_result

        except Exception as e:
            print(f"Code analysis failed: Error interacting with LLM: {e}")
            raise e # Re-raise to be caught by the calling task
        except Exception as e:
             print(f"Unexpected error during code analysis: {e}")
             raise e