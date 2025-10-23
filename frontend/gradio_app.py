import gradio as gr
import requests
from typing import List, Tuple

# FastAPI endpoint URL
API_URL = "http://localhost:8000/query"

def process_question(message: str, history: List[Tuple[str, str]]) -> str:
    """
    Process the user's question by sending it to the FastAPI endpoint.
    
    Args:
        message (str): The user's question
        history (list): Chat history
    
    Returns:
        str: The agent's response
    """
    try:
        # Send POST request to FastAPI endpoint
        response = requests.post(
            API_URL,
            json={"question": message}
        )
        
        # Raise an exception for bad status codes
        response.raise_for_status()
        
        # Extract the response from the JSON
        result = response.json()
        return result["response"]
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the API. Make sure the FastAPI server is running (uvicorn app.main:app --reload)"
    except requests.exceptions.RequestException as e:
        return f"Error communicating with API: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

# Create the Gradio interface
demo = gr.ChatInterface(
    fn=process_question,
    title="Retail Database Assistant",
    description="Ask questions about retail data, sales, inventory, and competitor information.",
    examples=[
        "What are our top 5 products by revenue?",
        "Compare our SKU's prices with competitor's prices",
        "Show me the current inventory levels for men's t-shirt category",
        "What products have the highest profit margins?",
        "Show me the sales forecast for next month"
    ],
    theme="soft"
)

# Launch the interface
if __name__ == "__main__":
    demo.launch(share=True)
