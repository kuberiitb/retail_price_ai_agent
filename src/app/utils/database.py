import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase

# Load environment variables
load_dotenv()

def get_database():
    """Get SQLDatabase instance using the database URL from environment variables."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///retail_price_agent_v1.db")
    return SQLDatabase.from_uri(database_url)
