import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# AI and RAG Imports
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

# ==========================================================
# 1. API CONFIGURATION
# PASTE YOUR KEY FROM GOOGLE AI STUDIO BETWEEN THE QUOTES BELOW
# ==========================================================
os.environ["GOOGLE_API_KEY"] = "AIzaSyDb1oAFGlDGydfMChex1q9vu-VBsPM6Qow"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

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

# Initialize Models
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

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
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(pages)
        
        # This creates the chroma_db folder automatically
        db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PATH
        )
        return {"message": f"Indexed {file.filename}", "chunks": len(chunks)}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_with_docs(request: ChatRequest):
    try:
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
        docs = db.similarity_search(request.query, k=3)
        
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))

        prompt = f"""
        You are CognitoDoc Assistant. Answer based ONLY on the context.
        If not in context, say "I don't have that information."
        
        CONTEXT:
        {context}
        
        QUESTION:
        {request.query}
        """
        
        response = llm.invoke(prompt)
        return {"answer": response.content, "sources": sources}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)