# app/services/llm_service.py - Service for interacting with the main LLM (e.g., OpenAI)

import openai
from openai import OpenAI
from typing import List, Dict, Any, Optional
from app.core.exceptions import LLMServiceError # Import custom exception

# Assuming prompt templates are stored in prompts/
from app.prompts import system_prompts, interview_prompts, chunk_prompts

class LLMService:
    """
    Handles communication and interaction with the main LLM model.
    Manages conversation context and generates responses.
    """
    def __init__(self, api_key: str, model_name: str):
        # Initialize the OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

        # Get initial system prompt from prompts module
        self.system_prompt = system_prompts.get_system_interviewer_prompt()
        self.chunk_processing_prompt_template = chunk_prompts.get_chunk_processing_prompt()
        self.final_processing_prompt_template = interview_prompts.get_final_response_prompt()
        self.initial_question_prompt_template = interview_prompts.get_initial_question_prompt()
        # Add other prompt templates as needed

    def _call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 500) -> str:
        """Helper method to make the API call to the LLM."""
        try:
            print(f"Calling LLM with {len(messages)} messages...")
            # print("--- Messages sent to LLM ---")
            # for msg in messages:
            #     print(f"{msg['role'].upper()}: {msg['content'][:100]}...") # Print truncated content
            # print("---------------------------")

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                # stream=True # Can enable streaming if needed for partial responses
            )
            # If streaming, process chunks. If not, get the single response.
            # For non-streaming, get the content from the first choice
            if response.choices and response.choices[0].message.content:
                 return response.choices[0].message.content
            else:
                 print("LLM returned no content.")
                 return "I'm sorry, I couldn't generate a response at this moment."

        except openai.APIError as e:
            print(f"OpenAI API Error: {e}")
            raise LLMServiceError(f"LLM API Error: {e}", original_exception=e)
        except Exception as e:
            print(f"An unexpected error occurred during LLM call: {e}")
            raise LLMServiceError(f"Unexpected LLM error: {e}", original_exception=e)

    def generate_initial_question(self, interview_plan: Dict[str, Any], jd_analysis: Dict[str, Any], resume_analysis: Dict[str, Any]) -> str:
        """Generates the first interview question based on analysis."""
        # Construct the prompt using the templates and analysis data
        prompt_content = self.initial_question_prompt_template.format(
            jd_summary=jd_analysis.get("summary", ""), # Assuming analysis provides summaries
            resume_summary=resume_analysis.get("summary", ""),
            key_topics=interview_plan.get("topics", []),
            initial_questions=interview_plan.get("initial_questions", [])
        )
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt_content}
        ]
        # Keep max_tokens relatively low for initial concise question
        return self._call_llm(messages, temperature=0.8, max_tokens=150)


    def process_incremental_chunk(self, conversation_history: List[Dict[str, str]], current_buffer: str) -> str:
        """
        Processes an incoming transcription chunk while the user is still speaking.
        Generates a preliminary, non-final response draft or internal thought process.
        """
        # Construct messages for the LLM.
        # Include the system prompt, historical conversation, and the current buffer.
        # Use a special prompt indicating the input is incomplete.
        messages = [
            {"role": "system", "content": self.system_prompt},
            *conversation_history, # Include previous turns
            {"role": "user", "content": self.chunk_processing_prompt_template.format(current_buffer=current_buffer)}
            # The chunk prompt tells the LLM "User is speaking, this is a partial utterance.
            # Process it mentally, maybe update your understanding, but DO NOT respond yet
            # with a final answer. If you must output, generate a short draft that acknowledges
            # understanding or prepares for response, marked clearly as draft."
        ]

        # Call LLM with a lower temperature maybe? And potentially lower max_tokens
        # The output here is the "latest draft".
        draft = self._call_llm(messages, temperature=0.5, max_tokens=50) # Drafts should be short
        return draft.strip() # Return the generated draft (could be empty string if LLM follows instruction)


    def process_final_utterance(self, conversation_history: List[Dict[str, str]], full_utterance: str) -> str:
        """
        Processes the full user utterance after a pause is detected.
        Generates the final, definitive response.
        """
        # Construct messages including the full utterance.
        # Use a prompt that signals this is the final input and expects a full response.
        messages = [
            {"role": "system", "content": self.system_prompt},
            *conversation_history, # Include previous turns
            {"role": "user", "content": full_utterance} # Send the full user utterance as the latest user message
            # After this, the LLM's response will be added to conversation_history
        ]

        # Call LLM. Expect a complete response.
        # Use a higher max_tokens than for drafts.
        final_response = self._call_llm(messages, temperature=0.7, max_tokens=300) # Adjust max_tokens based on expected response length

        # TODO: Maybe format the final response based on desired output style?
        # For example, ensure it starts with a question, or includes specific phrasing.
        return final_response.strip()

    # Potentially add methods for function calling/agents if the LLM supports it directly
    # def analyze_code_with_agent(self, code_snippet: str, context: str, job_description_details: Dict[str, Any]):
    #     """Uses LLM agent/function calling to analyze code."""
    #     # This method would involve setting up messages with function definitions
    #     # and calling the LLM API with function_call="auto" or specifying the tool.
    #     # The response might include tool_calls that need to be handled.
    #     pass