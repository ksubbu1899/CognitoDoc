# CognitoDoc -- Privacy-Preserving RAG System for Document Intelligence

CognitoDoc is a Retrieval-Augmented Generation (RAG) system that lets you chat with your PDF documents while keeping your data private. Documents are embedded and stored locally -- only minimal context is sent to the cloud LLM for answer generation.

## Features

- **Local Vectorization** -- Documents are embedded on your machine using `all-MiniLM-L6-v2`. No raw text leaves your environment during ingestion.
- **Semantic Search** -- Queries are matched using Cosine Similarity against a local ChromaDB (HNSW index), not keyword search.
- **Grounded Answers** -- Gemini 2.5 Flash generates responses strictly from retrieved context, reducing hallucinations.
- **Source Citations** -- Every answer includes the source document name and page number.
- **Modern Chat UI** -- React + Tailwind CSS interface with real-time upload and chat.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite 7, Tailwind CSS 4 |
| Backend | Python, FastAPI, Uvicorn |
| Embeddings | all-MiniLM-L6-v2 (Local, Sentence-Transformers) |
| Vector Store | ChromaDB with HNSW indexing |
| LLM | Google Gemini 2.5 Flash (via API) |
| Orchestration | LangChain |
| PDF Parsing | PyPDF |

## Project Structure

```
CognitoDoc/
├── backend/
│   ├── main.py              # FastAPI server with RAG pipeline
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Gemini API key (create this)
│   ├── uploads/             # Uploaded PDFs stored here
│   └── chroma_db/           # Local vector database (auto-created)
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main chat UI component
│   │   ├── main.jsx         # React entry point
│   │   ├── index.css        # Tailwind imports
│   │   └── App.css          # Custom styles
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 20+
- Google Gemini API Key ([Get one free here](https://aistudio.google.com/apikey))

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` folder:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

Start the backend:
```bash
python main.py
```
The API will be running at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run start
```
The UI will be running at `http://localhost:5173`

## How It Works

1. **Upload** -- User uploads a PDF through the React UI
2. **Parse & Chunk** -- Text is extracted (PyPDF) and split into 1000-token chunks with 200-token overlap
3. **Local Embedding** -- Each chunk is converted to a 384-dimensional vector using all-MiniLM-L6-v2 on the local CPU
4. **Store** -- Vectors are indexed in a local ChromaDB instance using HNSW algorithm
5. **Query** -- User's question is embedded locally and matched against stored vectors via Cosine Similarity
6. **Generate** -- Top-5 matching chunks are sent to Gemini as context; Gemini produces a grounded answer
7. **Cite** -- The answer is returned to the user along with source document name and page numbers

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/upload` | Upload and index a PDF |
| POST | `/chat` | Query the indexed documents |

## Authors

- **Subramanian K** -- M.Tech (AI & DS), SRM Institute of Science and Technology
- **Dr. Umamaheswari K M** -- Associate Professor, Dept. of Computing Technologies, SRMIST

## License

This project was developed as part of M.Tech Project Work at SRM Institute of Science and Technology.
