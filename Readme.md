CHAPTER 3: SYSTEM ARCHITECTURE	
3.1 OVERALL SYSTEM DESIGN
The backend system is designed as a modular architecture to ensure scalability, maintainability, and separation of concerns. At its core, it is built around a FastAPI web server handling incoming HTTP requests and WebSocket connections. Asynchronous task processing is managed by Celery, which communicates via a message broker and stores results in a backend. Various services encapsulate interactions with external APIs (LLMs, potentially ASR/TTS) and internal logic (document parsing, storage, state management). A dedicated analysis module handles pre- and post-interview evaluations. The file structure provided serves as the blueprint for organizing these components into logical directories and modules.
Fig 1 Layers of system
•	API Layer: Exposes functionality via RESTful endpoints and WebSocket connections. Handles request validation and routes requests to the appropriate core logic or triggers background tasks. 
•	Core Logic Layer: Manages the state of interview sessions, orchestrates the flow of information, and implements the complex real-time interaction logic.
•	Service Layer: Provides abstract interfaces for external dependencies and internal utilities (LLM interaction, document processing, storage).
•	Task Management Layer: Defines and orchestrates asynchronous tasks using Celery, including message queuing and worker processes.
•	Data Layer: Manages data persistence (temporary file storage, potentially a database for interview states or analysis results). 
•	Analysis Layer: Contains the logic for evaluating documents and interview performance, including the code analysis component. 
•	Configuration & Utilities Layer: Handles application settings, logging, and helper functions.
3.2 COMPONENT BREAKDOWN
Based on the provided file structure, the system components are organized as follows:4
3.2.1 API Layer
1.	API Layer Located in `app/api/`, this layer contains versioned API endpoints (`app/api/v1/endpoints/`). 
2.	documents.py`: Handles document upload (/documents/upload/jd, /documents/upload/resume`). Triggers document processing tasks. 
3.	interview.py`: Handles interview session creation (`/interview/start`) and manages the real-time chat via a WebSocket (`/interview/{interview_id}/cha`).  
4.	dependencies.py`: Contains dependency injection functions (e.g., get_settings`, get_interview_manager`) for FastAPI.
 3.2.2  Core Business Logic
1.	Located in `app/core/`, this directory contains the central logic for managing interview sessions. 
2.	interview_manager.py: The core class managing the lifecycle of interview sessions. It handles starting interviews, receiving WebSocket messages, interacting with Celery tasks and services, and managing interview state. 
3.	interview_state.py: Defines data structures and logic for storing the state of an active interview session (e.g., conversation history, JD/Resume data, WebSocket connection reference).
4.	exceptions.py: Defines custom exceptions for the core logic (e.g., `InterviewNotFound`, `InvalidInterviewState`).

3.2.3  Service Layer
Fig 2 Service Layers
1.	llm_service.py`: Handles communication with the primary LLM provider API. Contains methods for generating interview questions, analyzing responses, etc. 
2.	mini_llm_service.py`: Handles communication with the mini-LLM used for fillers/surprises. Contains methods for generating short, contextually relevant interjections. 
3.	document_parser.py`: Contains logic for extracting text and potentially structured data from uploaded documents (PDF, DOCX). 
4.	storage_service.py: Handles file storage operations (saving uploaded documents, potentially storing interview transcripts). 
5.	audio_processing_service.py`: (Conceptual) Interface for ASR - receives audio/chunks and returns text. The backend focuses on receiving text transcription from the client. 
6.	tts_service.py`: (Conceptual) Interface for TTS - receives text and returns audio data. The backend sends text to the client, which might use a TTS service.
3.2.4 Task Management Layer
1.	Located in `app/tasks/`, this layer defines the Celery tasks.  
2.	celery.py: Celery application instance and basic configuration. 
3.	document_tasks.py`: Celery tasks for processing uploaded documents (parsing, analyzing, preparing data for interview). Includes `process_document`. 
4.	llm_tasks.py`: Celery tasks for calling the primary LLM (e.g., generating the next question, analyzing a final response chunk). 
5.	interview_tasks.py`: Other general interview-related tasks (e.g., saving session state periodically). 
6.	analysis_tasks.py`: Celery tasks for running post-interview analysis, including code analysis.
3.2.5 Rest of the Layers
1.	Data link layer provides storage service and manages storage state
2.	Analysis layer analyses components JD AND Resume based on skills experience mad potential interview topics
3.3 Technology Stack
Table 1 TECHNOLOGY STACK
Category
	Technoloy	Purpose
•	Web Framework	•	FastAPI	•	High-performance, asynchronous web framework for APIs and WebSockets.
•	Asynchronous Tasks	•	Celery	•	Distributed task queue for background processing.
•	Message Broker	•	Redis / RabbitMQ	•	Backend for Celery to manage task queues. Redis is often also used for caching or session state.
•	AI Models	•	Large Language Models (Groq Llama 70B GPT)	•	Core AI for interview questions, response analysis, conversation flow, code analysis (via agents/function calling).
•	Mini-LLM	•	Smaller/Specialized LLM or custom model	•	For generating conversational fillers and surprises.
•	Document Parsing	•	Python Libraries (e.g., python-docx, PyPDF2, textract)	•	Extracting text and data from JD/Resume files.
•	File Storage	•	Local Filesystem (for development)	•	Storing uploaded documents and potentially transcripts. (Cloud storage in production).
•	Data Validation	•	Pydantic	•	Data modeling and validation, integrated with FastAPI.
•	Dependency Mgmt.	•	pipenv / poetry	•	Managing project dependencies.
•	Containerization	•	Docker	•	Packaging the application and dependencies.
•	Orchestration	•	Docker Compose	•	Defining and running multi-container Docker applications (development/testing).
•	Async Operations	•	asyncio	•	Python's built-in library for asynchronous programming.
