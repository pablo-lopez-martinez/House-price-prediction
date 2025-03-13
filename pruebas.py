import pandas as pd

df = pd.read_csv("dataset/property_sales.csv")

# Number of rows of property_type = "house" for each number of bedrooms
house_prices = df[df['property_type'] == 'house']
house_prices = house_prices.groupby('bedrooms').size().reset_index(name='count')

# Number of rows of property_type = "unit" for each number of bedrooms
unit_prices = df[df['property_type'] == 'unit']
unit_prices = unit_prices.groupby('bedrooms').size().reset_index(name='count')

print("House prices:\n", house_prices)
print("Unit prices:\n", unit_prices)