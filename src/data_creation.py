# !pip install langchain_community --quiet

import os
import io
import pandas as pd
import numpy as np
import random

# Dataset Creation
# Keep only two product for now.

core_data = {'men': ['shirt','t-shirt','jacket','Jeans','Trackpants'],
             'women':['Dress','Kurtas','Tops','t-shirt','Jeans','Trackpants'],
             'kids':['shirt','t-shirt','jacket','Jeans','Trackpants','Dress','Kurtas','Tops']
}

data = []
sku_id = 0
for category, products in core_data.items():
  for product in products:
    data.append([sku_id, product, category])
    sku_id+=1

data_product_category = pd.DataFrame(data, columns = ['sku_id','product_name', 'category'])

data_product_category.head(10)

data_product_category = data_product_category.loc[data_product_category['sku_id'].isin([1,8]),:]
data_product_category

# Step 1: generate monthly dates
# current data till "2025-08-01"
# forecast data for next 6 months till "2026-02-01"
dates = pd.date_range(start="2023-06-01", end="2026-02-01", freq="MS")

# Step 2: turn into DataFrame
dates_df = pd.DataFrame({"date": dates})

# dates_df
# Step 3: cross join
df_expanded = data_product_category.merge(dates_df, how="cross")

print(df_expanded.shape)
print(df_expanded.head())

# Generating other columns like price, cost etc for the products
np.random.seed(42)  # reproducibility

metadata = {}
# defaultdict(int)
# Base price, Demand and elasticity differs per product (id)
for sku_id in df_expanded.sku_id.unique():
  metadata[sku_id.item()] = {}
  metadata[sku_id.item()]['base_price'] = random.randint(100, 200)*10
  metadata[sku_id.item()]['base_demand'] = (random.randint(100, 1000)//100) *100
  metadata[sku_id.item()]['elasticity'] = -1 * random.randint(80,120)/100
  metadata[sku_id.item()]['margin'] = round(-1.0 / metadata[sku_id.item()]['elasticity'], 2)

def generate_sales(row):
    # Price with random fluctuation
    base_price = metadata[row["sku_id"]]['base_price']
    margin = metadata[row["sku_id"]]['margin']

    unit_cost = round(base_price / (1 + margin))
    price = base_price + np.random.randint(-10, 10)

    # Random promotion (20% chance)
    discount_pct = np.random.choice([0, 10, 20, 30], p=[0.5, 0.2, 0.2, 0.1])

    price = round(price * (1-discount_pct/100))
    # Seasonality factor (e.g., high in Dec, low in Jan/Feb)
    month = row["date"].month
    if month in [11, 12]:      # festive
        seasonality_factor = 1.3
    elif month in [6, 7, 8]:   # summer boost
        seasonality_factor = 1.1
    else:
        seasonality_factor = 0.9

    # Sales formula
    units_sold = round(100 * (500 / price) * seasonality_factor * (1.2 if discount_pct > 0 else 1.0),0)
    # units_sold = units_sold  + np.random.normal(0, 10)  # add noise
    revenue = round(price * units_sold)
    profit = round((price - unit_cost) * units_sold)

    return pd.Series([price, unit_cost,  discount_pct, seasonality_factor, units_sold, revenue, profit])

# Apply generator
df_expanded[["unit_price", "unit_cost","discount_pct", "seasonality_factor", "units_sold", "revenue", "profit"]] = df_expanded.apply(generate_sales, axis=1)

print(df_expanded.head(10))

# Creating historical and forecast data

historical_data = df_expanded.loc[df_expanded['date']<='2025-08-01',:]
forecast_data = df_expanded.loc[df_expanded['date']>'2025-08-01',:]

print(historical_data.head())

# Update units_sold on forecast_data

forecast_data = forecast_data.loc[:,['sku_id', 'product_name', 'category', 'date']]

historical_average = historical_data.groupby(['sku_id', 'product_name', 'category'])['units_sold'].mean().round().reset_index()
historical_average.rename(columns={'units_sold':'units_sale'},inplace=True)
print("historical_average")
print(historical_average)

forecast_data = forecast_data.merge(historical_average, on=['sku_id', 'product_name', 'category'], how='left')
print("forecast_data")
print(forecast_data)

# Create current inventory

# 2 to 4 months of sales
inventory_data = historical_average.rename(columns={'units_sale':'stock'})
print("inventory_data")
print(inventory_data)

inventory_data['stock'] = inventory_data.apply(lambda x:x['stock']*random.randint(2,4),axis=1)
print(inventory_data)

# Create competitior current price
our_price = historical_data.groupby(['sku_id', 'product_name', 'category'])['unit_price'].mean().round().reset_index()
print("Our Price")
print(our_price)

competitior_information = our_price.copy()
competitior_information['unit_price'] = competitior_information['unit_price'].map(lambda x:round(x*np.random.choice([0.8,0.9,1.1,1.2])))

print("competitior_information")
print(competitior_information)
# adjust price by promotion value
promotion_to_discount_pct_mapping = {'BOGO':0.5,'BTGO':0.3,'NONE':0}
def try_float_or_map(x):
    try:
        return float(x)
    except (ValueError, TypeError):
        return promotion_to_discount_pct_mapping.get(x, np.nan)

competitior_information['promotion'] = competitior_information.apply(lambda x: np.random.choice(['NONE','0.1','0.2','BOGO','BTGO'], p=[0.2,0.1,0.1,0.3,0.3]),axis=1)
competitior_information['discount_pct'] = competitior_information['promotion'].map(try_float_or_map)
competitior_information['unit_price'] = competitior_information.apply(lambda x: x['unit_price']* (1-x['discount_pct']), axis=1)

print("competitior_information")
print(competitior_information)

print(metadata)
current_product_information = pd.DataFrame(metadata).T.reset_index()
current_product_information = current_product_information.rename(columns={'index':'sku_id'})
print(current_product_information)

import sqlite3

# Example list of dataframes with names
dataframes = {
    "historical_data": historical_data,
    "current_product_information": current_product_information,
    "forecast_data": forecast_data,
    "inventory_data": inventory_data,
    "competitior_information": competitior_information
}

# Create connection to SQLite database (creates file if not exists)
conn = sqlite3.connect("retail_price_agent.db")

# Loop through and save each dataframe as a table
for table_name, df in dataframes.items():
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"Saved {table_name} to SQLite")

# Close connection
conn.close()

# Save the datsets to SQLite so that later Text2SQL agent can use it

db = sqlite3.connect("retail_price_agent.db")

df_current = pd.read_sql("SELECT * FROM current_product_information", db)
df_historical = pd.read_sql("SELECT * FROM historical_data", db)
df_forecast = pd.read_sql("SELECT * FROM forecast_data", db)
df_inventory = pd.read_sql("SELECT * FROM inventory_data", db)
df_competitior = pd.read_sql("SELECT * FROM competitior_information", db)
print(historical_data.head())
print(df_forecast.head())
print(df_inventory)
print(df_competitior.head())

db.close()

# Loop through and save each dataframe as a table
for table_name, df in dataframes.items():
    print("TABLE:", table_name)
    for column_name in df.columns:
      print("COLUMN:", column_name)
    print()


# Langchain agent will use SQLAlchemy format similar like this
from sqlalchemy import create_engine

db = SQLDatabase.from_uri("sqlite:///retail_price_agent.db")
print(db.get_usable_table_names())


print(db.run("SELECT * FROM historical_data LIMIT 10;"))
print(db.run("SELECT * FROM competitior_information LIMIT 10;"))
print(db.run("SELECT * FROM forecast_data LIMIT 10;"))
