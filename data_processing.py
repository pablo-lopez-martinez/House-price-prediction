import streamlit as st
import pandas as pd
from functions import load_data, filter_data, make_prediction

# Header
st.title("Property Sales Data Prediction")
# Add line breaks and spaces between paragraphs
st.write("\n")


# Load data

raw_data = load_data()

# Input data
st.subheader("Select the data you want to predict")

granularity = st.selectbox("Select the granularity", ["Day", "Week", "Month", "Year"])

# Data transformation

data_filtered = filter_data(raw_data, granularity)

print(data_filtered.set_index('time'))

print(data_filtered)

# Scatter plot of the data
st.subheader("Historic Prices")
st.scatter_chart(data_filtered.set_index('time'))

# User input for number of steps in the future

steps = st.number_input("Enter the number of steps to predict into the future", min_value=1, step=1)

# Make prediction
future_price = make_prediction(data_filtered, steps, granularity)

# Show prediction
st.subheader("Prediction")
# Combine historical data with predictions
combined_data = pd.concat([data_filtered, future_price])

# Plot historical data and predictions with different colors
st.line_chart(combined_data.set_index('time'))



if st.button("Send balloons!"):
    st.balloons()
