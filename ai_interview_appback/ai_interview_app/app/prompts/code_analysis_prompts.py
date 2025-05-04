# app/prompts/code_analysis_prompts.py - Prompts and function definitions for code analysis

# Example function definition for OpenAI function calling
# This structure is specific to OpenAI's API
def get_code_analysis_function_definition() -> Dict[str, Any]:
    """
    Returns the JSON schema definition for a function the LLM can call
    to analyze a code snippet.
    """
    return {
        "name": "analyze_code_snippet",
        "description": "Analyze a given code snippet for correctness, efficiency, style, and relevance to job requirements.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The code snippet to analyze."
                },
                "language": {
                    "type": "string",
                    "description": "The programming language of the code snippet.",
                    "enum": ["python", "javascript", "java", "c++", "other"] # Add supported languages
                },
                "analysis_focus": {
                    "type": "string",
                    "description": "Specific aspects to focus the analysis on (e.g., correctness, efficiency, error handling, specific algorithm).",
                    "default": "overall evaluation"
                },
                "context": {
                     "type": "string",
                     "description": "Context from the interview about why this code was provided."
                },
                "job_requirements": {
                    "type": "string",
                    "description": "Summary of relevant technical requirements from the job description."
                }
            },
            "required": ["code", "language", "context"]
        }
    }


def get_code_analysis_prompt() -> str:
    """
    Returns the prompt template that guides the LLM on how to analyze code,
    potentially referencing the function calling capability.
    """
    return """
You are an AI interviewer capable of evaluating code snippets.
Analyze the following code snippet provided by the candidate.

Code Snippet:

Context from the interview: {context}

Relevant job requirements from the Job Description:
{job_description_summary}

Evaluate the code for:
- Correctness (does it solve the problem?)
- Efficiency (time and space complexity)
- Code style and readability
- Suitability for the context given the interview question
- Relevance to the job requirements

Provide your analysis and assessment. Structure your response clearly, highlighting strengths and weaknesses. If appropriate, suggest improvements or ask clarifying questions about their approach.
"""
# Note: If using function calling, the primary instruction might be implicit
# in the `tools` parameter, and the prompt focuses more on providing context.
# The LLM decides whether to call the function or respond conversationally.
# Forcing the function call (`tool_choice` parameter) is an option.