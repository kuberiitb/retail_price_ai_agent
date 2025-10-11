import os
from langchain_community.utilities import SQLDatabase
import io
import pandas as pd
import numpy as np
import random
import sqlite3
np.random.seed(42)  # reproducibility

core_data = {'men': ['shirt','t-shirt','jacket','Jeans','Trackpants'],
             'women':['Dress','Kurtas','Tops','t-shirt','Jeans','Trackpants'],
             'kids':['shirt','t-shirt','jacket','Jeans','Trackpants','Dress','Kurtas','Tops']
}

data = []
id = 0
for category, products in core_data.items():
  for product in products:
    data.append([id, product, category])
    id+=1

data_product_category = pd.DataFrame(data, columns = ['id','product', 'category'])

# Step 1: generate monthly dates
# current data till "2025-08-01"
# forecast data for next 6 months till "2026-02-01"
dates = pd.date_range(start="2023-06-01", end="2026-02-01", freq="MS")

# Step 2: turn into DataFrame
dates_df = pd.DataFrame({"date": dates})

# dates_df
# Step 3: cross join
df_expanded = data_product_category.merge(dates_df, how="cross")


metadata = {}
# defaultdict(int)
# Base price, Demand and elasticity differs per product (id)
for id in df_expanded.id.unique():
  metadata[id.item()] = {}
  metadata[id.item()]['base_price'] = random.randint(100, 200)*10
  metadata[id.item()]['base_demand'] = (random.randint(100, 1000)//100) *100
  metadata[id.item()]['elasticity'] = -1 * random.randint(80,120)/100
  metadata[id.item()]['margin'] = -1.0 / metadata[id.item()]['elasticity']

def generate_sales(row):
    # Price with random fluctuation
    base_price = metadata[row["id"]]['base_price']
    margin = metadata[row["id"]]['margin']

    cost = round(base_price / (1 + margin))
    price = base_price + np.random.randint(-10, 10)

    # Random promotion (20% chance)
    promotion = np.random.choice([0, 10, 20, 30], p=[0.5, 0.2, 0.2, 0.1])

    price = round(price * (1-promotion/100))
    # Seasonality factor (e.g., high in Dec, low in Jan/Feb)
    month = row["date"].month
    if month in [11, 12]:      # festive
        seasonality = 1.3
    elif month in [6, 7, 8]:   # summer boost
        seasonality = 1.1
    else:
        seasonality = 0.9

    # Sales formula
    sales = round(100 * (500 / price) * seasonality * (1.2 if promotion > 0 else 1.0))
    # sales = sales *  + np.random.normal(0, 10)  # add noise
    sales_value = price * sales
    profit = (price - cost) * sales

    return pd.Series([price, cost,  promotion, seasonality, sales, round(sales_value), round(profit)])

# Apply generator
df_expanded[["price", "cost","promotion", "seasonality", "sales", "sales_value", "profit"]] = df_expanded.apply(generate_sales, axis=1)

historical_data = df_expanded.loc[df_expanded['date']<='2025-08-01',:]
forecast_data = df_expanded.loc[df_expanded['date']>'2025-08-01',:]

forecast_data = forecast_data.loc[:,['id', 'product', 'category', 'date']]

historical_average = historical_data.groupby(['id', 'product', 'category'])['sales'].mean().round().reset_index()

forecast_data = forecast_data.merge(historical_average, on=['id', 'product', 'category'], how='left')

# 2 to 4 months of sales
inventory_data = historical_average.rename(columns={'sales':'stock'})

inventory_data['stock'] = inventory_data.apply(lambda x:x['stock']*random.randint(2,4),axis=1)

# 2 to 4 months of sales
inventory_data = historical_average.rename(columns={'sales':'stock'})

inventory_data['stock'] = inventory_data.apply(lambda x:x['stock']*random.randint(2,4),axis=1)

our_price = historical_data.groupby(['id', 'product', 'category'])['price'].mean().round().reset_index()

competitior_price = our_price
competitior_price['price'] = competitior_price['price'].map(lambda x:round(x*np.random.choice([0.8,0.9,1.1,1.2])))

competitior_price['promotion'] = competitior_price.apply(lambda x: np.random.choice(['0','0.1','0.2','BOGO','BTGO'], p=[0.2,0.1,0.1,0.3,0.3]),axis=1)

# adjust price by promotion value
promotion_to_price_mapping = {'0':1,'0.1':0.9,'0.2':0.8,'BOGO':0.5,'BTGO':0.7}
competitior_price['price_change'] = competitior_price['promotion'].map(promotion_to_price_mapping)
competitior_price['price'] = competitior_price.apply(lambda x: x['price']* x['price_change'], axis=1)

# Example list of dataframes with names
dataframes = {
    "historical_data": historical_data,
    "forecast_data": forecast_data,
    "inventory_data": inventory_data,
    "competitior_price": competitior_price
}

# Create connection to SQLite database (creates file if not exists)
conn = sqlite3.connect("my_database.db")

# Loop through and save each dataframe as a table
for table_name, df in dataframes.items():
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"Saved {table_name} to SQLite")

# Close connection
conn.close()