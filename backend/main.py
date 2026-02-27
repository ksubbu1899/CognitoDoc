import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# AI and RAG Imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI

# ==========================================================
# CONFIGURATION
# ==========================================================
load_dotenv()  # Load from .env file

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY or GOOGLE_API_KEY == "YOUR_API_KEY_HERE":
    GOOGLE_API_KEY = ""
    print("\n⚠️  WARNING: GOOGLE_API_KEY not set!")
    print("   Create a .env file in backend/ with: GOOGLE_API_KEY=your_key_here")
    print("   Get a free key from: https://aistudio.google.com/apikey")
    print("   Document upload will still work (local embeddings), but chat needs the key.\n")
else:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    print(f"✅ Gemini API key loaded")

app = FastAPI()

# Allow React (localhost:5173) to talk to FastAPI (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Folder settings
UPLOAD_DIR = "uploads"
CHROMA_PATH = "chroma_db"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==========================================================
# LOCAL Embeddings (Privacy-Preserving)
# Uses all-MiniLM-L6-v2 — runs entirely on CPU, no cloud call
# ==========================================================
print("Loading local embedding model (all-MiniLM-L6-v2)...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
print("✅ Local embedding model loaded!")

# Cloud LLM — used ONLY for final answer generation
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

class ChatRequest(BaseModel):
    query: str

@app.get("/")
async def root():
    return {"message": "CognitoDoc API is Live"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        chunks = text_splitter.split_documents(pages)
        
        # Vectorize locally and store in ChromaDB
        db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PATH
        )
        return {"message": f"Indexed {file.filename}", "chunks": len(chunks)}
    except Exception as e:
        print(f"Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_with_docs(request: ChatRequest):
    if not GOOGLE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key not configured. Add GOOGLE_API_KEY to .env file."
        )
    try:
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
        docs = db.similarity_search(request.query, k=5)
        
        if not docs:
            return {
                "answer": "No relevant documents found. Please upload a PDF first.",
                "sources": []
            }

        context = "\n\n".join([doc.page_content for doc in docs])
        sources = list(set([
            os.path.basename(doc.metadata.get("source", "Unknown"))
            for doc in docs
        ]))
        pages = sorted(set([
            str(doc.metadata.get("page", "?"))
            for doc in docs
        ]))

        prompt = f"""You are CognitoDoc Assistant. Answer based ONLY on the context below.
If the answer is not found in the context, say "I don't have that information in the uploaded documents."

CONTEXT:
{context}

QUESTION:
{request.query}

Provide a clear and helpful answer based strictly on the above context."""
        
        response = llm.invoke(prompt)
        
        source_str = ", ".join(sources)
        page_str = ", ".join(pages)
        
        return {
            "answer": response.content,
            "sources": [f"{source_str} (Pages: {page_str})"]
        }
    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
