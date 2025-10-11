import pandas as pd
import numpy as np
import random
import sqlite3
np.random.seed(42)

# --- PRODUCT SETUP ---
core_data = {'men': ['shirt','t-shirt','jacket','Jeans','Trackpants'],
             'women':['Dress','Kurtas','Tops','t-shirt','Jeans','Trackpants'],
             'kids':['shirt','t-shirt','jacket','Jeans','Trackpants','Dress','Kurtas','Tops']}

historical_data_renaming_dict = {
    'id': 'sku_id',
    'product': 'product_name',
    'price': 'unit_price',
    'cost': 'unit_cost',
    'promotion': 'discount_pct',
    'seasonality': 'seasonality_factor',
    'sales': 'units_sold',
    'sales_value': 'revenue'
}

forecast_data_rename_dict = {
    'id': 'sku_id',
    'product': 'product_name',
    'sales': 'units_sale'
}

inventory_data_rename_dict = rename_dict = {
    'id': 'sku_id',
    'product': 'product_name'
}

competitor_data_rename_dict =  {
    'id': 'sku_id',
    'product': 'product_name',
    'competitor_price': 'unit_price',
    'competitor_promotion': 'promotion',
    'price_change': 'discount_pct'
}

data = []
id = 0
for category, products in core_data.items():
    for product in products:
        data.append([id, product, category])
        id += 1

data_product_category = pd.DataFrame(data, columns=['id','product','category'])
data_product_category = data_product_category.loc[data_product_category['id'].isin([1,8]), :]

# --- DATE SETUP ---
dates = pd.date_range(start="2023-06-01", end="2026-02-01", freq="MS")
dates_df = pd.DataFrame({"date": dates})
df_expanded = data_product_category.merge(dates_df, how="cross")

# --- METADATA ---
metadata = {}
for id in df_expanded.id.unique(): # the formatting of below lines is changed
    metadata[id.item()] = {
        'base_price': random.randint(100, 200)*10,
        'base_demand': (random.randint(100, 1000)//100) * 100,
        'elasticity': -1 * random.randint(80,120)/100
    }
    metadata[id.item()]['margin'] = -1.0 / metadata[id.item()]['elasticity']

# --- SALES GENERATOR ---
def generate_sales(row):
    base_price = metadata[row["id"]]['base_price']
    margin = metadata[row["id"]]['margin']
    elasticity = metadata[row["id"]]['elasticity'] # new code

    cost = round(base_price / (1 + margin))
    price = base_price + np.random.randint(-10, 10)
    promotion = np.random.choice([0, 10, 20, 30], p=[0.5, 0.2, 0.2, 0.1])
    price = round(price * (1 - promotion / 100))

    month = row["date"].month
    seasonality = 1.3 if month in [11, 12] else 1.1 if month in [6, 7, 8] else 0.9 # formatting changed

    sales = round(100 * (500 / price) * seasonality * (1.2 if promotion > 0 else 1.0))
    sales_value = price * sales
    profit = (price - cost) * sales
    profit_margin = round((price - cost) / price, 2) if price != 0 else 0.0 # new feature

    return pd.Series([
        price, cost, promotion, seasonality, sales, round(sales_value), round(profit),
        round(elasticity, 2), profit_margin # these are new
    ])

df_expanded[[
    "price", "cost", "promotion", "seasonality", "sales",
    "sales_value", "profit", "price_elasticity", "profit_margin" # the last two are new
]] = df_expanded.apply(generate_sales, axis=1)

# --- CURRENT PRODUCT INFORMATION (one row per SKU) ---
latest_ids = df_expanded.groupby('id')['date'].idxmax()  # get last record index for each SKU
latest_records = df_expanded.loc[latest_ids]

current_product_information = pd.DataFrame([
    {
        'sku_id': row['id'],
        'base_price': metadata[row['id']]['base_price'],
        'base_demand': metadata[row['id']]['base_demand'],
        'elasticity': metadata[row['id']]['elasticity'],
        'margin': metadata[row['id']]['margin']
    }
    for _, row in latest_records.iterrows()
])

# --- SPLIT DATASETS ---
historical_data = df_expanded[df_expanded['date'] <= '2025-08-01']
forecast_data = df_expanded[df_expanded['date'] > '2025-08-01']

# --- FORECAST ---
forecast_data = forecast_data[['id', 'product', 'category', 'date']]
historical_average = historical_data.groupby(['id', 'product', 'category'])['sales'].mean().round().reset_index()
forecast_data = forecast_data.merge(historical_average, on=['id', 'product', 'category'], how='left')

# --- INVENTORY ---
inventory_data = historical_average.rename(columns={'sales':'stock'})
inventory_data['stock'] = inventory_data['stock'] * np.random.randint(2, 5, size=len(inventory_data)) # reformatted new line

# --- COMPETITOR PRICING ---
our_price = historical_data.groupby(['id', 'product', 'category'])['price'].mean().round().reset_index()
competitior_price = our_price.copy() # new format
competitior_price['price'] = competitior_price['price'].map(lambda x:round(x*np.random.choice([0.8,0.9,1.1,1.2])))
competitior_price['promotion'] = competitior_price.apply(lambda x: np.random.choice(['0','0.1','0.2','BOGO','BTGO'], p=[0.2,0.1,0.1,0.3,0.3]),axis=1)

promotion_to_price_mapping = {'0':1,'0.1':0.9,'0.2':0.8,'BOGO':0.5,'BTGO':0.7}
competitior_price['price_change'] = competitior_price['promotion'].map(promotion_to_price_mapping)
competitior_price['price'] = competitior_price['price'] * competitior_price['price_change'] # reformatted new line
competitior_price = competitior_price.rename(columns={"price": "competitor_price", "promotion": "competitor_promotion"}) # new line

# --- MERGE INTO HISTORICAL DATA ---
# historical_data = historical_data.merge(
#     competitior_price[['id', 'product', 'category', 'competitor_price', 'competitor_promotion']],
#     on=['id', 'product', 'category'],
#     how='left'
# )

# --- SAVE TO SQLITE ---
dataframes = {
    "historical_data": historical_data.rename(columns=historical_data_renaming_dict),
    "current_product_information":current_product_information,
    "forecast_data": forecast_data.rename(columns=forecast_data_rename_dict),
    "inventory_data": inventory_data.rename(columns=inventory_data_rename_dict),
    "competitor_information": competitior_price.rename(columns=competitor_data_rename_dict)
}

conn = sqlite3.connect("data/enhanced_retail_data.db")
for table_name, df in dataframes.items():
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"✅ Saved {table_name} to SQLite")
conn.close()
