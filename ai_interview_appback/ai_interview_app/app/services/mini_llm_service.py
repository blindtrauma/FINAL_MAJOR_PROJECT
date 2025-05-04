# app/services/mini_llm_service.py - Service for the mini-LLM (fillers, surprises)

import openai
from openai import OpenAI
from typing import List, Dict, Any
from app.core.exceptions import LLMServiceError # Re-use LLM service error
from app.prompts import surprise_prompts # Assuming surprise prompts exist

class MiniLLMService:
    """
    Handles communication with a smaller LLM for generating
    short fillers, acknowledgements, or surprises during the interview.
    """
    def __init__(self, api_key: str, model_name: str):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        # Get the system prompt specific to the mini-LLM's role
        self.system_prompt = surprise_prompts.get_mini_llm_system_prompt()


    def generate_surprise(self, context: str, conversation_snippet: str) -> str:
        """
        Generates a short filler/surprise based on the current context.
        Context could be "after_chunk", "after_pause", "random_interval", etc.
        Conversation snippet provides recent turn context.
        """
        # Choose a specific prompt based on context
        prompt_template = surprise_prompts.get_surprise_prompt(context)
        if not prompt_template:
             print(f"Warning: No surprise prompt template found for context: {context}")
             return "" # Return empty string if no suitable prompt

        # Construct the user message with relevant context information
        user_message = prompt_template.format(conversation_snippet=conversation_snippet)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message}
        ]

        try:
            print(f"Calling Mini-LLM for surprise (context: {context})...")
            # Keep temperature slightly higher for creativity, but max_tokens low
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.9,
                max_tokens=30 # Fillers should be very short
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            else:
                print("Mini-LLM returned no content.")
                return ""

        except openai.APIError as e:
            print(f"OpenAI API Error (Mini-LLM): {e}")
            # Decide if mini-LLM errors should raise or just return empty/default
            return "" # Don't necessarily crash for a filler error
        except Exception as e:
            print(f"An unexpected error occurred during Mini-LLM call: {e}")
            return ""