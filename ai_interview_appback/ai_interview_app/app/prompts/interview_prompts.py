# app/prompts/interview_prompts.py - Prompts for generating interview questions and responses

def get_initial_question_prompt() -> str:
    """
    Returns the prompt template for generating the first interview question.
    Needs JD/Resume summaries and key topics from pre-analysis.
    """
    return """
Based on the following Job Description summary and Resume summary, and the identified key topics for this interview:

Job Description Summary:
{jd_summary}

Resume Summary:
{resume_summary}

Key Interview Topics:
{key_topics}

Generate the very first question for the candidate to start the interview.
This question should be a standard opening question, such as "Tell me about yourself" or "Walk me through your resume," tailored slightly to the context of the role.

Initial Questions to Consider (choose one or start with similar):
{initial_questions}

Generate ONLY the question text. Do not include any conversational filler before the question.
"""

def get_final_response_prompt() -> str:
    """
    Returns the prompt template for generating the main LLM response
    after the user has finished speaking (final utterance).
    The LLM's conversation history up to this point will be provided.
    """
    return """
The user has just finished speaking. Their complete utterance is provided as the last message in the conversation history.

Your task is to formulate a precise and relevant response based on their statement and the ongoing interview context.
Your response should:
1. Acknowledge the user's input.
2. Ask a follow-up question or make a relevant statement that moves the interview forward, focusing on the Job Description and Resume.
3. Keep the conversation professional and aligned with your role as an interviewer.
4. Aim to cover the key interview topics outlined in the interview plan over the course of the session.
5. If the user's input requires specific analysis (e.g., code), integrate that need into your response or queue it internally.

Generate ONLY your response text. Do not preface it with "AI:" or similar. Ensure it sounds like a natural, albeit structured, interview question or statement.
"""

# You could add prompts for evaluating answers, generating follow-up questions based on specific topics, etc.
# def get_follow_up_prompt(): ...
# def get_answer_evaluation_prompt(): ...
# def get_pre_interview_analysis_prompt():
#     """Prompt for PreInterviewAnalyzer - asks LLM to extract structured info from JD/Resume."""
#     return """
# Analyze the following {document_type} document content.
# Extract key information relevant to a job interview process.
# For a Job Description, extract required skills, desired skills, qualifications, responsibilities, company industry, location, role level.
# For a Resume, extract work experience summary (company, title, dates, key achievements), education, skills (technical, soft), relevant projects.
#
# Provide the output as a JSON object formatted within ```json ... ```.
#
# Document Content:
# {document_content}
# """