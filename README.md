# AI Document Research Assistant

A full-stack web application that allows users to upload PDF documents and ask questions about their content using Retrieval-Augmented Generation (RAG).

## Tech Stack
- **Backend**: Django, Django REST Framework, MySQL
- **Frontend**: React, Vite, TailwindCSS
- **AI/RAG**: LangChain, ChromaDB, HuggingFace Embeddings, Google Gemini

## Setup Instructions for Windows

### 1. Database Setup
Ensure you have MySQL 8.0+ installed.
```sql
CREATE DATABASE ai_doc_research;
```

### 2. Backend Setup
```powershell
# Open a terminal in the root project folder
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Edit the .env file in the backend directory:
# - DB_PASSWORD
# - LLM_API_KEY (Your Google Gemini API Key)

# Run database migrations
python manage.py migrate

# Start the server
python manage.py runserver
```

### 3. Frontend Setup
```powershell
# Open a new terminal in the root project folder
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

## Usage
1. Open `http://localhost:5173` in your browser.
2. Register a new account and log in.
3. Upload a PDF document from the Dashboard.
4. Wait for the status to change from `PROCESSING` to `COMPLETED`.
5. Click **Chat with Document** and ask questions based on the PDF's context!
