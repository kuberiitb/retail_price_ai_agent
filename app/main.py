import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from app.utils.database import get_database
from app.core.agent import RetailAgent


# Load environment variables
load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI app
app = FastAPI(
    title="Retail Agent API",
    description="API for interacting with the retail agent for database queries and analysis",
    version="1.0.0"
)

class Query(BaseModel):
    question: str

# Initialize database and agent
db = get_database()
retail_agent = RetailAgent(db)

@app.post("/query")
async def query_retail_agent(query: Query):
    """
    Submit a question to the retail agent.
    """
    try:
        response = retail_agent.get_response(query.question)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Load environment variables
load_dotenv(".env")

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI app
app = FastAPI(
    title="Retail Agent API",
    description="API for interacting with the retail agent for database queries and analysis",
    version="1.0.0"
)

# Initialize database and agent
db = get_database()
retail_agent = RetailAgent(db)

class Query(BaseModel):
    question: str


@app.post("/query")
async def query_retail_agent(query: Query):
    """
    Submit a question to the retail agent.
    """
    try:
        response = retail_agent.get_response(query.question)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Check if the API is running.
    """
    return {"status": "healthy"}
