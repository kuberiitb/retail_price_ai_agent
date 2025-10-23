from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langgraph.prebuilt import create_react_agent

class RetailAgent:
    """A class to handle retail database interactions using a language model."""
    
    database_information = """"
    TABLE: historical_data - Contains historical monthly-level sales, pricing, and profit data for each SKU.

COLUMN: sku_id - Unique identifier for each product-category combination.

COLUMN: product_name - Name of the specific product.

COLUMN: category - Category or department the product belongs to.

COLUMN: date - Month (or month-start date) representing the sales period.

COLUMN: unit_price - Actual selling price per unit after applying discounts.

COLUMN: unit_cost - Cost to produce or acquire one unit of the product.

COLUMN: discount_pct - Percentage discount applied to the base price.

COLUMN: seasonality_factor - Seasonal adjustment factor reflecting demand fluctuations.

COLUMN: units_sold - Total quantity sold for the SKU during the given period.

COLUMN: revenue - Total revenue generated = unit_price * units_sold.

COLUMN: profit - Total profit = (unit_price - unit_cost) * units_sold.

#########################################################################################

TABLE: current_product_information - Stores reference or metadata information about each of our SKU used for pricing and forecasting.

COLUMN: sku_id - Unique identifier for each product-category combination.

COLUMN: base_price - Reference or standard list price of the product.

COLUMN: base_demand - Baseline expected demand level for the product.

COLUMN: elasticity - Price elasticity coefficient indicating sensitivity of demand to price changes.

COLUMN: margin - Target profit margin ratio derived from elasticity or business rules.

#########################################################################################
TABLE: forecast_data - Contains forecasted monthly unit sales for each SKU based on predictive modeling.

COLUMN: sku_id - Unique identifier for each product-category combination.

COLUMN: product_name - Name of the specific product.

COLUMN: category - Category or department the product belongs to.

COLUMN: date - Forecast month or future period.

COLUMN: units_sale - Forecasted number of units expected to be sold.

#########################################################################################

TABLE: inventory_data - Tracks current stock levels for each SKU in the inventory.

COLUMN: sku_id - Unique identifier for each product-category combination.

COLUMN: product_name - Name of the specific product.

COLUMN: category - Category or department the product belongs to.

COLUMN: stock - Current quantity of the SKU available in inventory.

#########################################################################################

TABLE: competitior_information - Captures competitor pricing and promotion details for comparative analysis.

COLUMN: sku_id - Unique identifier representing the same or equivalent SKU.

COLUMN: product_name - Name of the product for cross-reference with competitors.

COLUMN: category - Product category for comparison.

COLUMN: unit_price - Competitor’s selling price for the product.

COLUMN: promotion - Competitor’s promotion or offer label (e.g., "BOGO","NONE" or discount value).

COLUMN: discount_pct - Discount percentage applied by the competitor, if available.
"""

    extra_details_about_data = """
    1. SKU means product_name+category combination, can be represented by sku_id
    2. product means product_name unless specified otherwise.
    3. While returning SKU information, mention its details like product_name and category.
    4. All the price and revenue information is in INR.
    """

    def __init__(self, db: SQLDatabase, model_name: str = "gpt-4-turbo-preview"):
        """
        Initialize the RetailAgent.
        
        Args:
            db (SQLDatabase): The database instance to connect to
            model_name (str): The name of the OpenAI model to use
        """
        self.db = db
        self.model_name = model_name
        self.agent = self._create_agent()

    def _create_system_message(self) -> str:
        """Create the system message for the agent."""
        return f"""
        You are an agent designed to interact with a SQL database.
        Given an input question, create a syntactically correct SQLite query to run,
        then look at the results of the query and return the answer. Unless the user
        specifies a specific number of examples they wish to obtain, always limit your
        query to at most 5 results.

        {self.extra_details_about_data}

        You can order the results by a relevant column to return the most interesting
        examples in the database. Never query for all the columns from a specific table,
        only ask for the relevant columns given the question.

        You MUST double check your query before executing it. If you get an error while
        executing a query, rewrite the query and try again.

        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
        database.

        To start you should ALWAYS look at the tables in the database to see what you
        can query. Do NOT skip this step.

        Use this description of tables and columns for reference.
        {self.database_information}

        Then you should query the schema of the most relevant tables.

        Business context:
        Product usually means product-category combination.
        """

    def _create_agent(self):
        """Create and configure the retail agent."""
        llm = ChatOpenAI(model=self.model_name)
        toolkit = SQLDatabaseToolkit(db=self.db, llm=llm)
        tools = toolkit.get_tools()
        
        return create_react_agent(
            name="Retail_Data_Agent",
            model=llm,
            tools=tools,
            prompt=self._create_system_message(),
        )

    def get_response(self, question: str) -> str:
        """
        Get response from the retail agent for a given question.
        
        Args:
            question (str): The question to ask the agent
            
        Returns:
            str: The agent's response or "I don't know" if unable to process
        """
        for step in self.agent.stream(
            {"messages": [{"role": "user", "content": question}]},
            {"configurable": {"thread_id": "1"}},
            stream_mode="values",
        ):
            if step['messages'][-1].response_metadata.get('finish_reason') == 'stop':
                try:
                    return step['messages'][-1].content
                except:
                    return "I don't know"
        return "No response received"
