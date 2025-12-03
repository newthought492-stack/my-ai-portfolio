from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
from pydantic import BaseModel
from passlib.context import CryptContext
import uvicorn
import os
import jwt
from datetime import datetime, timedelta
from rag_agent import RAGAgent
from langchain.tools import tool
from googleapiclient.discovery import build
import google.auth

# Placeholder for Google Sheets API setup
# In a real scenario, you would handle auth here (e.g., service account or OAuth)

@tool
def read_google_sheet_data(spreadsheet_id: str, range_name: str):
    """
    Reads data from a Google Sheet.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet.
        range_name (str): The range to read, e.g., 'Sheet1!A1:B10'.
        
    Returns:
        list: A list of lists containing the cell values.
    """
    try:
        # This will attempt to find default credentials. 
        # Ensure you have set up GOOGLE_APPLICATION_CREDENTIALS or have run `gcloud auth application-default login`
        creds, _ = google.auth.default()
        
        service = build('sheets', 'v4', credentials=creds)

        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                    range=range_name).execute()
        values = result.get('values', [])
        return values
    except Exception as e:
        return f"Error reading Google Sheet: {str(e)}"

@tool
def read_financial_data(sheet_id: str, range: str):
    """
    Retrieves financial data from a specified spreadsheet range. 
    Use this when asked about revenue, expenses, or financial performance.
    
    Args:
        sheet_id (str): The ID of the spreadsheet.
        range (str): The range to read.
        
    Returns:
        list: A list of lists containing financial data, or a fallback message if unavailable.
    """
    max_retries = 2
    for attempt in range(1, max_retries + 1):
        try:
            # Placeholder data for demonstration
            # In a real scenario, this would be an API call that might fail
            return [
                ['Item', 'Value'],
                ['Revenue', 100000],
                ['Expenses', 50000],
                ['Profit', 50000]
            ]
        except Exception as e:
            print(f"Attempt {attempt} failed: {str(e)}")
            if attempt == max_retries:
                print("Max retries reached. Returning fallback response.")
    
    return "Financial data service is temporarily offline. I will provide the audit based only on policy documents."



def initialize_vector_db():
    """
    Initializes the Vector Database (ChromaDB) on server startup.
    It checks if the DB exists; if not, it uses RAGAgent to create it from the PDF.
    """
    print("Initializing Vector Database (ChromaDB)...")
    pdf_path = "sample.pdf"
    
    # Instantiate RAGAgent to trigger DB creation/loading
    # We don't need tools here, just the DB setup
    try:
        agent = RAGAgent(pdf_path=pdf_path)
        print("Vector Database initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Vector Database: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    initialize_vector_db()
    yield
    # Shutdown logic (if any)

app = FastAPI(title="RAG Agent API", lifespan=lifespan)

# Security / Auth
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT Configuration
SECRET_KEY = "supersecretkey"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    return username

class UserLogin(BaseModel):
    username: str
    password: str

class UserInDB(BaseModel):
    username: str
    hashed_password: str

def verify_password(plain_password, hashed_password):
    # Truncate to 72 bytes to avoid bcrypt limitation
    return pwd_context.verify(plain_password[:72], hashed_password)

def hash_password(password):
    # Truncate to 72 bytes to avoid bcrypt limitation
    return pwd_context.hash(password[:72])

# Mock user database
# In a real app, this would come from a database
# Password is "secret"
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": hash_password("secret"),
    }
}

@app.post("/token")
async def login(user: UserLogin):
    if user.username not in fake_users_db:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    user_in_db = fake_users_db[user.username]
    hashed_password = user_in_db["hashed_password"]
    
    if not verify_password(user.password, hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/admin/leads")
async def get_leads(current_user: str = Depends(get_current_user)):
    """
    Protected endpoint to retrieve leads data.
    Requires a valid JWT token.
    """
    return {
        "leads": [
            {"name": "Alice Smith", "email": "alice@example.com"},
            {"name": "Bob Jones", "email": "bob@example.com"},
            {"name": "Charlie Brown", "email": "charlie@example.com"}
        ],
        "user": current_user
    }

class QueryRequest(BaseModel):
    query: str

@app.post("/rag-query")
async def rag_query(request: QueryRequest):
    """
    Endpoint to query the RAG agent.
    Instantiates the agent for each request as per instructions.
    """
    pdf_path = "sample.pdf"
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="sample.pdf not found on server.")
    
    try:
        # Instantiate the agent with tools
        # Note: In production, this should be a global singleton
        tools = [read_google_sheet_data, read_financial_data]
        agent = RAGAgent(pdf_path, tools=tools)
        response = agent.run_query(request.query)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
