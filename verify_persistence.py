import os
import shutil
from unittest.mock import MagicMock
import sys

# Mock OpenAIEmbeddings before importing rag_agent
mock_embeddings = MagicMock()
mock_embeddings.embed_documents.return_value = [[0.1] * 1536]  # Mock vector
mock_embeddings.embed_query.return_value = [0.1] * 1536

# We need to patch the class in the module where it is used
# But since we import RAGAgent, we can patch it in sys.modules or use unittest.mock.patch
# Simpler: Mock the class in langchain_community.embeddings
sys.modules["langchain_community.embeddings"] = MagicMock()
sys.modules["langchain_community.embeddings"].OpenAIEmbeddings = MagicMock(return_value=mock_embeddings)

# Also mock ChatOpenAI to avoid key check
sys.modules["langchain_community.chat_models"] = MagicMock()
sys.modules["langchain_community.chat_models"].ChatOpenAI = MagicMock()

from rag_api_service import initialize_vector_db
from rag_agent import RAGAgent

PDF_PATH = "sample.pdf"
DB_DIR = "./chroma_db"

def verify_persistence():
    print("Starting persistence verification...")
    
    # 1. Clean up existing DB
    if os.path.exists(DB_DIR):
        print(f"Removing existing {DB_DIR}...")
        shutil.rmtree(DB_DIR)
    
    # 2. Trigger initialization
    print("Triggering initialize_vector_db()...")
    initialize_vector_db()
    
    # 3. Check if DB dir exists
    if os.path.exists(DB_DIR) and os.listdir(DB_DIR):
        print(f"SUCCESS: {DB_DIR} created and populated.")
    else:
        print(f"FAILURE: {DB_DIR} not found or empty.")
        return

    # 4. Verify Querying
    print("Verifying query capability...")
    try:
        agent = RAGAgent(pdf_path=PDF_PATH)
        response = agent.run_query("What is the topic?")
        print(f"Query Response: {response}")
        if response:
            print("SUCCESS: Agent returned a response.")
    except Exception as e:
        print(f"FAILURE: Query failed: {e}")

if __name__ == "__main__":
    # Ensure sample.pdf exists
    if not os.path.exists(PDF_PATH):
        print(f"Creating dummy {PDF_PATH}...")
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(PDF_PATH)
        c.drawString(100, 750, "This is a sample policy document for the RAG agent.")
        c.save()
        
    verify_persistence()
