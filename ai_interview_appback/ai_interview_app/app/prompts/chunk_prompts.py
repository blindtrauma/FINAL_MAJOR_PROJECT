# app/prompts/chunk_prompts.py - Prompts for processing incremental user speech chunks

def get_chunk_processing_prompt() -> str:
    """
    Returns the prompt template used when the user is still speaking
    and an incremental chunk is received.
    Instructs the LLM on how to process incomplete input.
    """
    return """
The user is currently speaking, and you have received a portion of their ongoing utterance. This is NOT their final statement for this turn.

Current accumulated utterance so far in this turn:
"{current_buffer}"

Your task is to process this partial input INTERNALLY. Do not generate a public response or interrupt the user.
Based on this partial input and the conversation history, update your internal understanding of what the user is likely saying or where their response is heading.
Mentally prepare for potential follow-up questions or points to address once they finish speaking.

If you are required to output *anything* in response to this *partial* input for system purposes (e.g., generating a placeholder or a quick non-interrupting acknowledgement), ensure it is extremely brief, non-committal, and clearly marked as an internal note or draft. Ideally, output nothing or a specific token if the system allows, but if text is required, keep it minimal.

Example minimal internal thought/draft if required:
[DRAFT] User is talking about their previous job responsibilities...
[DRAFT] Sounds like they are addressing the required skills...

Do not generate a full interview question or response. ONLY generate a brief internal thought/draft if absolutely necessary for your model's flow, and preface it clearly (e.g., with [DRAFT]). If possible, output nothing.
"""