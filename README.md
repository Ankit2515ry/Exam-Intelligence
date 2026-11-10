# Exam Intelligence 🧠

Exam Intelligence is an advanced RAG (Retrieval-Augmented Generation) application designed to ingest context documents (PDFs) and allow users to converse with their documents through an AI grounded prompt shell. 

The project uses a **FastAPI** backend coupled with a **ChromaDB** vector storage engine, and a modern **React (Vite)** frontend tracking layout components via Tailwind CSS.

---

## 📁 Repository Structure

This repository is organized as a Monorepo:

```text
EXAM_INTELLIGENCE/             <-- Project Root
├── backend/                   <-- FastAPI Application Core
│   ├── app/                   <-- Routers, schemas, and pipeline services
│   ├── requirements.txt       <-- Python Dependencies
│   └── .env                   <-- Backend environment secrets
│
└── frontend/                  <-- React + Vite Frontend App
    ├── src/                   <-- Layout UI, Pages, and Hooks
    ├── package.json           <-- JavaScript Dependencies
    └── .env                   <-- Frontend Configuration Variables

🛠️ Getting Started
Follow these instructions to get a local copy of the project up and running.

Prerequisites
Python 3.10+ installed

Node.js (v18+) installed

🚀 Backend Configuration & Setup
Navigate to the backend directory:

Bash
cd backend
Create and activate a virtual environment:

Bash
# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# On Mac/Linux
python3 -m venv venv
source venv/bin/activate
Install dependencies:

Bash
pip install -r requirements.txt
Environment Variables:
Create a .env file inside the backend/ directory and add your configurations (e.g., database keys, application secret key):

Code snippet
SECRET_KEY=your_super_secret_jwt_key
ALGORITHM=HS256
# Add your LLM keys / database configurations here
Start the FastAPI Development Server:

Bash
uvicorn app.main:app --reload
The backend API documentation interface will be accessible at: http://localhost:8000/docs

### Backend health checks and tests

- `GET /health/live` is a liveness check. It confirms the API process can respond and does not contact dependencies.
- `GET /health/ready` is a readiness check. It checks the relational database and ChromaDB and returns HTTP 503 if either is unavailable. It does not call Gemini or run document ingestion.
- The root path (`/`) is informational; use the health paths for deployment probes.

Run the backend health endpoint tests from the `backend/` directory with the virtual environment activated:

```powershell
python -m unittest discover -s tests -v
```

### Backend logs

The backend uses Python's standard logging module at `INFO` level. Logs are written to the console stream, so view them in the same terminal where you run Uvicorn:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

In production, check the hosting provider's application/runtime logs; container platforms collect console output automatically. The application does not currently write logs to a local file.

💻 Frontend Configuration & Setup
Open a new terminal and navigate to the frontend directory:

Bash
cd frontend
Install JavaScript dependencies:

Bash
npm install
Environment Variables:
Create a .env file inside the frontend/ directory to configure the API base routing endpoint:

Code snippet
VITE_API_BASE_URL=http://localhost:8000
Start the Vite development engine:

Bash
npm run dev
Open your browser and navigate to the local server port displayed in your terminal (typically http://localhost:5173).

🔒 Security and Version Control
Both the frontend and backend utilize localized .env tracking protocols.

Sensitive configurations, JWT strings, local SQLite data collections, and database tracking containers (chroma_db/, venv/, node_modules/) are managed securely via separate .gitignore boundary rules and are never committed to version control.

🛠️ Tech Stack Built With
Frontend: React, Vite, Axios, Tailwind CSS, React Hook Form, Lucide React Icons

Backend: FastAPI, Python, SQLAlchemy ORM, Pydantic, Uvicorn

Database & Vector Engine: ChromaDB (Vector Embeddings RAG Pipeline), SQLite / PostgreSQL


---

### 💡 Two Quick Adjustments You Can Make Later
1. **Under Architecture/Structure:** If your inner frontend folder has a specific sub-name (like `frontend/exam_intelligence`), make sure to adjust that line in the tree map text block to match your exact directory naming layout.
2. **Under Tech Stack:** If you're using a specific external LLM model (like OpenAI's GPT-4o, Anthropic's Claude, or a local Ollama model), you can explicitly add it under the Backend/Vector section to show off what model power lies beneath your core prompt engine!