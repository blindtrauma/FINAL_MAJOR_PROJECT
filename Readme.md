	
![image](https://github.com/user-attachments/assets/47ac2730-8cad-42c7-b168-cac13453fd07)

# AI-Powered Interview System Backend

This document outlines the architecture and design of the AI-Powered Interview System backend. The system is engineered to conduct real-time, interactive interviews using Large Language Models (LLMs), manage document processing (Job Descriptions, Resumes), and provide post-interview analysis.

## Table of Contents

1.  [Overview](#overview)
2.  [Key Features](#key-features)
3.  [System Architecture](#system-architecture)
    *   [Block Diagram](#block-diagram)
    *   [Architectural Layers](#architectural-layers)
4.  [Technology Stack](#technology-stack)
5.  [Core Components Breakdown](#core-components-breakdown)
    *   [API Layer](#api-layer)
    *   [Core Business Logic](#core-business-logic)
    *   [Service Layer](#service-layer)
    *   [Task Management Layer (Celery)](#task-management-layer-celery)
6.  [Detailed Workflows](#detailed-workflows)
    *   [Document Upload and Processing](#document-upload-and-processing)
    *   [Interview Session Initiation](#interview-session-initiation)
    *   [Real-time Chat & LLM Interaction](#real-time-chat--llm-interaction)
7.  [API Endpoints](#api-endpoints)
    *   [Document Endpoints](#document-endpoints)
    *   [Interview Endpoints](#interview-endpoints)
    *   [WebSocket Communication](#websocket-communication)
8.  [Setup and Installation](#setup-and-installation)
9.  [Running the System](#running-the-system)

---

## 1. Overview

The backend system provides the core engine for an AI-driven interview platform. It's designed as a modular, scalable, and maintainable architecture. Key components include:

*   **FastAPI Web Server:** Handles HTTP requests for document uploads, interview initiation, and WebSocket connections for real-time chat.
*   **Celery Task Queues:** Manages asynchronous processing of computationally intensive or I/O-bound tasks like document parsing, LLM interactions, and analysis.
*   **Service Layer:** Encapsulates interactions with external APIs (LLMs, ASR/TTS - though ASR/TTS are primarily client-side focused for transcription/playback) and internal logic (document parsing, storage, state management).
*   **Real-time Interaction Logic:** Sophisticated handling of user input chunks and LLM responses to simulate a fluid conversation.

## 2. Key Features

*   **Asynchronous Document Processing:** Upload JDs and Resumes, which are processed in the background.
*   **Real-time Conversational AI:** Engages users in an interview dialogue powered by LLMs.
*   **Dynamic Response Strategy:** Employs a chunking mechanism and tentative LLM responses to minimize perceived latency during live chat.
*   **Modular Service Integration:** Easily integrates with various LLM providers, document parsers, and storage solutions.
*   **Stateful Interview Management:** Maintains the context and history of ongoing interview sessions.
*   **Scalable Task Management:** Leverages Celery and a message broker (Redis/RabbitMQ) for distributed task execution.
*   **Pre- and Post-Interview Analysis:** Capabilities for evaluating documents and interview performance.

## 3. System Architecture

**Diagram Summary:**
The User Client interacts with the FastAPI Web Server via HTTP (for initial requests) and WebSockets (for live chat). The Web Server (Interview Manager) triggers tasks that are enqueued into a Redis/RabbitMQ message broker. Celery Workers pull tasks from this queue. These tasks interact with various internal Services (Document Parser, LLM Service, Mini-LLM, Storage, Analysis). The Services, in turn, may communicate with External APIs (ASR, TTS, LLM Provider API) or Internal Storage (Redis).

### Architectural Layers

The system is structured into logical layers:

1.  **API Layer:** Exposes RESTful endpoints (FastAPI) and WebSocket connections. Handles request validation and routing.
2.  **Core Logic Layer:** Manages interview session state, orchestrates information flow, and implements real-time interaction logic (`InterviewManager`).
3.  **Service Layer:** Provides abstract interfaces for external dependencies (LLMs, document parsing, storage).
4.  **Task Management Layer:** Defines and orchestrates asynchronous Celery tasks, including message queuing and worker processes.
5.  **Data Layer:** Manages data persistence (file storage, Redis for caching/session state, potential database for analysis results).
6.  **Analysis Layer:** Contains logic for evaluating documents and interview performance.
7.  **Configuration & Utilities Layer:** Handles application settings, logging, and helper functions.

## 4. Technology Stack

| Category             | Technology                                            | Purpose                                                                       |
| :------------------- | :---------------------------------------------------- | :---------------------------------------------------------------------------- |
| Web Framework        | FastAPI                                               | High-performance, asynchronous web framework for APIs and WebSockets.         |
| Asynchronous Tasks   | Celery                                                | Distributed task queue for background processing.                             |
| Message Broker       | Redis / RabbitMQ                                      | Backend for Celery to manage task queues. Redis also for caching/session.     |
| AI Models            | Large Language Models (e.g., Groq Llama 70B, GPT)     | Core AI for interview questions, response analysis, conversation flow.        |
| Mini-LLM             | Smaller/Specialized LLM or custom model               | For generating conversational fillers and surprises.                          |
| Document Parsing     | Python Libraries (e.g., `python-docx`, `PyPDF2`)      | Extracting text and data from JD/Resume files.                                |
| File Storage         | Local Filesystem (dev) / Cloud Storage (prod)         | Storing uploaded documents and potentially transcripts.                       |
| Data Validation      | Pydantic                                              | Data modeling and validation, integrated with FastAPI.                        |
| Dependency Mgmt.     | pipenv / poetry                                       | Managing project dependencies.                                                |
| Containerization     | Docker                                                | Packaging the application and dependencies.                                   |
| Orchestration        | Docker Compose                                        | Defining and running multi-container Docker applications (dev/testing).       |
| Async Operations     | asyncio                                               | Python's built-in library for asynchronous programming.                       |

## 5. Core Components Breakdown

*   **`app/api/` (API Layer):**
    *   `v1/endpoints/documents.py`: Handles document uploads, triggers processing tasks.
    *   `v1/endpoints/interview.py`: Manages interview session creation and live chat via WebSockets.
    *   `dependencies.py`: FastAPI dependency injection functions.
*   **`app/core/` (Core Business Logic):**
    *   `interview_manager.py`: Central class for managing interview lifecycles, WebSocket messages, and state.
    *   `interview_state.py`: Defines data structures for active interview session state.
    *   `exceptions.py`: Custom exceptions for core logic.
*   **`app/services/` (Service Layer):**
    *   `llm_service.py`: Communicates with the primary LLM provider.
    *   `mini_llm_service.py`: Communicates with the mini-LLM for fillers.
    *   `document_parser_service.py`: Extracts text/data from documents.
    *   `storage_service.py`: Handles file storage operations.
    *   *(Conceptual)* `audio_processing_service.py` (ASR), `tts_service.py` (TTS).
*   **`app/tasks/` (Task Management Layer - Celery):**
    *   `celery.py`: Celery application instance and configuration.
    *   `document_tasks.py`: Tasks for document processing (e.g., `process_document`).
    *   `llm_tasks.py`: Tasks for primary LLM interactions (e.g., `process_chunk_for_tentative_response`, `process_final_response`).
    *   `interview_tasks.py`: General interview-related background tasks.
    *   `analysis_tasks.py`: Tasks for post-interview analysis.

## 6. Detailed Workflows

### Document Upload and Processing

1.  Client uploads a JD or Resume to a FastAPI endpoint (e.g., `/documents/upload/jd`).
2.  The API endpoint saves the file to a temporary storage location.
3.  A Celery task (`process_document`) is triggered with the file path and document type.
4.  The Celery worker:
    *   Loads the file content.
    *   Uses `DocumentParserService` to extract text and structured data.
    *   Optionally, performs initial analysis (e.g., keyword extraction via `PreInterviewAnalyzer`).
    *   Stores the processed data (e.g., in Redis or a file system) for later retrieval.

### Interview Session Initiation

1.  Client sends a request to `/interview/start` with IDs of the processed JD and Resume.
2.  FastAPI injects the `InterviewManager` instance.
3.  `manager.start_interview()` is called:
    *   Loads processed document data.
    *   Performs pre-interview analysis (identifying key topics, skills).
    *   Sets up the initial session state (conversation history, context).
    *   Generates a unique `interview_id`.
4.  The `interview_id` is returned to the client.

### Real-time Chat & LLM Interaction

This strategy aims to provide a responsive chat experience despite LLM latency.

1.  **User Speaks:** Client's ASR transcribes audio into text chunks and sends them via WebSocket (`ChatMessage: type="chunk"`).
2.  **Accumulate Chunks:** `InterviewManager` appends chunks to a turn-specific buffer.
3.  **Periodic Partial Processing (e.g., every 2 seconds):**
    *   If 2 seconds have passed since the last LLM task for this turn:
        *   A Celery task (`llm_tasks.process_chunk_for_tentative_response`) is triggered with the current buffer content and interview context.
        *   The task prompts the LLM for a *brief, tentative acknowledgement* (e.g., "Okay," "Interesting...").
        *   This tentative response is sent back to the client via WebSocket and stored locally as `last_tentative_response`.
4.  **User Stops Speaking:** Client's ASR sends the final transcribed sentence (`ChatMessage: type="final"`).
5.  **Trigger Final Processing:**
    *   `InterviewManager` triggers a Celery task (`llm_tasks.process_final_response`) with the full user utterance and context. This task prompts the LLM for a complete, considered response or the next question.
6.  **Instantaneous Output Strategy:**
    *   **If final LLM response arrives quickly (e.g., < 1 second):** It's sent directly to the client.
    *   **If final LLM response is delayed:** The previously stored `last_tentative_response` (from step 3) is sent immediately to the client to maintain engagement. The delayed full response might be logged or used to refine future interactions if it arrives later.
7.  **Generate Next Question/Response:** Once a response is sent, the `InterviewManager` updates history and triggers the process for the LLM to generate the next interview question or follow-up.

*(The "Fig 3 State Management flowchart" could be described or embedded here if it adds value to the README context, focusing on the states like "waiting_for_user_input", "processing_answer", "generating_question".)*

## 7. API Endpoints

All endpoints are prefixed with `/api/v1/`.

### Document Endpoints

*   **`POST /documents/upload/jd`**: Upload a Job Description file.
    *   Body: `multipart/form-data` with a `file` field.
    *   Response: JSON with `message`, `filename`, `stored_path`, `task_id`.
*   **`POST /documents/upload/resume`**: Upload a Resume file.
    *   Body: `multipart/form-data` with a `file` field.
    *   Response: JSON with `message`, `filename`, `stored_path`, `task_id`.

### Interview Endpoints

*   **`POST /interview/start`**: Initiate a new interview session.
    *   Request Body (JSON):
        ```json
        {
          "jd_id": "unique_id_of_processed_jd",
          "resume_id": "unique_id_of_processed_resume"
        }
        ```
    *   Response (JSON):
        ```json
        {
          "interview_id": "generated_unique_interview_id"
        }
        ```

### WebSocket Communication

*   **`WS /interview/{interview_id}/chat`**: Establishes a WebSocket connection for live interview chat.
    *   `interview_id`: Path parameter obtained from the `/interview/start` endpoint.

    **Message Types (Client to Server - `ChatMessage`):**

    | Type      | Payload Description                            | `is_final` |
    | :-------- | :--------------------------------------------- | :--------- |
    | `chunk`   | Partial user speech transcription.             | `false`    |
    | `final`   | Final user speech transcription after a pause. | `true`     |
    | `control` | Control message (e.g., "end_interview").       | `true`     |
    *Example Client Message:*
    ```json
    { "type": "chunk", "payload": "The quick brown...", "is_final": false, "timestamp": "..." }
    ```

    **Message Types (Server to Client - `ServerMessage`):**

    | Type                | Payload Description                                   |
    | :------------------ | :---------------------------------------------------- |
    | `llm_response`      | Primary LLM response (tentative or final).            |
    | `mini_llm_filler`   | Mini-LLM filler/surprise.                             |
    | `interview_state`   | System status update (e.g., "Analyzing your answer..."). |
    | `error`             | Error message.                                        |
    | `end`               | Interview conclusion signal.                            |
    *Example Server Message:*
    ```json
    { "type": "llm_response", "payload": "That's an interesting point..." }
    ```

## 8. Setup and Installation

*(This section would typically include steps for setting up the development environment, cloning the repository, installing dependencies, and configuring environment variables.)*

1.  **Prerequisites:**
    *   Python 3.8+
    *   Redis (for Celery broker/backend and caching) or RabbitMQ
    *   pipenv or poetry (as per project choice)
2.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```
3.  **Install dependencies:**
    *   Using pipenv: `pipenv install --dev`
    *   Using poetry: `poetry install`
4.  **Configure environment variables:**
    *   Create a `.env` file based on a `.env.example`.
    *   Set variables like `REDIS_URL`, `LLM_API_KEY`, `STORAGE_PATH`, etc.
5.  **Run database migrations (if applicable).**

## 9. Running the System

*(This section would explain how to start the FastAPI server, Celery workers, and any other necessary services.)*

1.  **Start the Message Broker (Redis):**
    ```bash
    redis-server
    ```
    (Or ensure your RabbitMQ instance is running)
2.  **Start Celery Workers:**
    Open a new terminal in the project root:
    ```bash
    # Ensure your virtual environment is activated
    celery -A app.tasks.celery_app worker -l info
    ```
    (Adjust `app.tasks.celery_app` if your Celery app instance is named differently or located elsewhere)
3.  **Start the FastAPI Application Server:**
    Open another terminal:
    ```bash
    # Ensure your virtual environment is activated
    uvicorn app.main:app --reload
    ```
    (Adjust `app.main:app` if your FastAPI app instance is named differently or located elsewhere)

The API will typically be available at `http://localhost:8000`.
API documentation (Swagger UI) will be at `http://localhost:8000/docs`.
