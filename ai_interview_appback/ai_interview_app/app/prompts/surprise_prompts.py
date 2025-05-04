# app/prompts/surprise_prompts.py - Prompts for the mini-LLM fillers/surprises

def get_mini_llm_system_prompt() -> str:
    """
    Returns the system prompt for the mini-LLM, defining its role.
    """
    return """
You are a helpful assistant whose only purpose is to generate very short, non-disruptive conversational fillers or acknowledgements during a chat. Your output should be brief, natural-sounding, and appropriate for the given context. You should NOT ask questions or take over the main conversation flow. Keep your responses under 10 words.
"""

def get_surprise_prompt(context: str) -> str:
    """
    Returns a specific prompt template for the mini-LLM based on the context.
    Context examples: "after_chunk", "after_pause_short_delay", "long_silence".
    """
    prompts = {
        "after_chunk": "Generate a very short acknowledgement of hearing a chunk of speech. Something like 'Okay' or 'Got it'. Keep it brief.",
        "after_pause_short_delay": "Generate a brief, non-committal filler while the main AI is processing. Like 'Thinking...' or 'Just a moment'.",
        "long_silence": "Generate a short, gentle prompt to indicate the AI is ready for the next input. Like 'I'm listening.' or 'Ready when you are.'",
        # Add other contexts as needed
    }
    # Include a snippet of recent conversation for better context if available
    # Example: "Recent conversation snippet: '{conversation_snippet}'"

    return prompts.get(context, "Generate a very short, general conversational filler.")