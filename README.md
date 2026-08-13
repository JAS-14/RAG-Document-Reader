# RAG Document Reader

A full-stack Retrieval-Augmented Generation application that allows users to upload PDF documents and ask questions about their content through an interactive chat interface.

The application combines a React frontend with a Python backend to process documents, retrieve relevant information, and generate context-aware answers using an LLM.

## Features

- User registration and login.
- Protected routes for authenticated users.
- PDF document upload.
- Text extraction and document processing.
- Document chunking for efficient retrieval.
- Embedding-based document search.
- Question answering over uploaded documents.
- Interactive chat interface.
- Context-aware responses using Retrieval-Augmented Generation.
- React frontend with responsive styling.
- Python backend with API-based communication.
- Environment-variable support for sensitive configuration.

## Application Flow

```text
User
 │
 ├── Creates an account or logs in
 │
 ├── Uploads a PDF document
 │
 ├── Backend extracts text from the document
 │
 ├── Text is divided into smaller chunks
 │
 ├── Chunks are converted into vector representations
 │
 ├── Relevant chunks are retrieved for each question
 │
 ├── Retrieved context is sent to the language model
 │
 └── Grounded answer is displayed in the chat interface
```

## Technology Stack

### Frontend

- React.js
- JavaScript
- CSS
- React Context API
- Fetch API or Axios
- Client-side protected routes

### Backend

- Python
- FastAPI
- PDF document processing
- Retrieval-Augmented Generation
- Embeddings
- LLM integration
- JSON or vector-based document storage

### Development Tools

- Git and GitHub
- npm
- Python virtual environment
- REST APIs
- Environment variables

## Project Structure

```text
RAG-Document-Reader/
│
├── Project/
│   │
│   ├── backend/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── model.py
│   │   ├── rag.py
│   │   ├── requirement.txt
│   │   ├── uploads/
│   │   └── .env
│   │
│   └── frontend/
│       ├── public/
│       ├── src/
│       │   ├── Components/
│       │   │   ├── Login.js
│       │   │   ├── Signup.js
│       │   │   ├── ProtectedRoute.js
│       │   │   ├── chat.js
│       │   │   └── style.css
│       │   ├── AuthContext.js
│       │   ├── api.js
│       │   ├── App.js
│       │   ├── App.css
│       │   └── images/
│       │       └── background.gif
│       ├── package.json
│       └── package-lock.json
│
└── README.md
```

## Prerequisites

Install the following before running the project:

- Python 3.10 or later
- Node.js 18 or later
- npm
- Git
- An API key for the language model and embedding service used by the backend

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/JAS-14/RAG-Document-Reader.git
cd RAG-Document-Reader
```

### 2. Set up the backend

```bash
cd Project/backend
```

Create a virtual environment:

#### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the backend dependencies:

```bash
pip install -r requirement.txt
```

Create a `.env` file inside `Project/backend`:

```env
# Add the variables required by your backend
LLM_API_KEY=your_api_key_here
DATABASE_URL=your_database_url_here
VECTOR_DATABASE_URL=your_vector_database_url_here
```

Do not commit the real `.env` file to GitHub.

Start the backend:

```bash
uvicorn main:app --reload
```

The backend should be available at:

```text
http://127.0.0.1:8000
```

If FastAPI documentation is enabled, visit:

```text
http://127.0.0.1:8000/docs
```

### 3. Set up the frontend

Open a second terminal:

```bash
cd Project/frontend
```

Install the frontend dependencies:

```bash
npm install
```

Start the React development server:

```bash
npm start
```

The frontend should be available at:

```text
http://localhost:3000
```

## Environment Variables

The exact environment variables depend on the services configured in the backend.

Example:

```env
LLM_API_KEY=
EMBEDDING_API_KEY=
DATABASE_URL=
VECTOR_DATABASE_URL=
SECRET_KEY=
```

Create a template file for other developers:

```text
.env.example
```

The template should contain variable names only and must not contain real credentials.

## How to Use

1. Open the frontend in your browser.
2. Create a new account.
3. Log in using your credentials.
4. Upload a PDF document.
5. Wait for the document to finish processing.
6. Ask a question related to the uploaded document.
7. Review the generated answer in the chat interface.

Example questions:

```text
What is the main topic of this document?

Explain the important concepts from chapter one.

Summarize the document in simple language.

What are the key points discussed in this PDF?
```

## RAG Pipeline

The project follows a standard Retrieval-Augmented Generation workflow:

### 1. Document ingestion

The user uploads a PDF through the React frontend.

### 2. Text extraction

The backend extracts readable text from the uploaded document.

### 3. Chunking

The extracted text is divided into smaller chunks. Chunking allows the application to retrieve only the most relevant sections instead of sending the entire document to the language model.

### 4. Embedding generation

Each text chunk is converted into a numerical vector representation using an embedding model.

### 5. Retrieval

When the user submits a question, the system compares the question with stored document vectors and retrieves the most relevant chunks.

### 6. Context construction

The retrieved chunks are added to the prompt as supporting context.

### 7. Answer generation

The language model generates an answer using the retrieved document context.

## API Overview

The backend exposes API endpoints for functionality such as:

- User registration.
- User login.
- Authentication.
- PDF upload.
- Document processing.
- Question answering.
- Chat interaction.

To view the exact available endpoints, start the backend and open:

```text
http://127.0.0.1:8000/docs
```

## Security Considerations

The following files should not be committed to GitHub:

```text
.env
__pycache__/
*.pyc
uploads/
chunk_store.json
node_modules/
```

Add them to `.gitignore`:

```gitignore
# Environment files
.env
.env.*
!.env.example

# Python files
__pycache__/
*.py[cod]

# Generated and uploaded files
Project/backend/uploads/
Project/backend/chunk_store.json

# Frontend dependencies
node_modules/
build/
```

If an API key has already been pushed to GitHub, revoke it and generate a new one immediately.

## Current Limitations

- The quality of answers depends on the quality of the uploaded document.
- Scanned PDFs may require OCR before text can be retrieved.
- Incorrect chunk size can reduce retrieval quality.
- The application may produce incomplete answers when relevant information is missing.
- Uploaded documents require proper user-level access control in a production environment.
- Large documents may increase processing time and API cost.
- Retrieval quality should be evaluated using a dedicated test
