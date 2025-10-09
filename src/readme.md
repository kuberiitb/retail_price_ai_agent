## List of Tables with Columns descriptions
#########################################################################################
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
TABLE: current_product_information - Stores reference or metadata information about each SKU used for pricing and forecasting.

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
