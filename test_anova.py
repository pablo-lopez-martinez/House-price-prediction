import pandas as pd
import scipy.stats as stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd


df = pd.read_csv("dataset/property_sales.csv")

# Perform ANOVA test for property_type = "house" based on the number of bedrooms
house_prices = df[df['property_type'] == 'house']

anova_result_houses = stats.f_oneway(
    house_prices[house_prices['bedrooms'] == 1]['price'],
    house_prices[house_prices['bedrooms'] == 2]['price'],
    house_prices[house_prices['bedrooms'] == 3]['price'],
    house_prices[house_prices['bedrooms'] == 4]['price'],
    house_prices[house_prices['bedrooms'] == 5]['price']
)

# Perform Tukey's HSD test for houses
tukey_hsd_houses = pairwise_tukeyhsd(
    endog=house_prices['price'],
    groups=house_prices['bedrooms'],
    alpha=0.05
)


# Perform ANOVA test for property_type = "unit" based on the number of bedrooms
unit_prices = df[df['property_type'] == 'unit']

anova_result_unit = stats.f_oneway(
    unit_prices[unit_prices['bedrooms'] == 1]['price'],
    unit_prices[unit_prices['bedrooms'] == 2]['price'],
    unit_prices[unit_prices['bedrooms'] == 3]['price'],
    unit_prices[unit_prices['bedrooms'] == 4]['price'],
    unit_prices[unit_prices['bedrooms'] == 5]['price']
)

# Perform Tukey's HSD test for units
tukey_hsd_units = pairwise_tukeyhsd(
    endog=unit_prices['price'],
    groups=unit_prices['bedrooms'],
    alpha=0.05
)

print("Tukey HSD result for houses:\n", tukey_hsd_houses)

print("Tukey HSD result for units:\n", tukey_hsd_units)





