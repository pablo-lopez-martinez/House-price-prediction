import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from functions import load_data, filter_data, make_prediction, prediction_graph
import altair as alt

# Header
st.title("Property Sales Data Prediction")
# Add line breaks and spaces between paragraphs
st.write("\n")


# Load data

raw_data = load_data()

# Input data
st.subheader("Find out the best time to buy or sell a property")
st.write("\n" * 5)

col1, col2 = st.columns(2)

with col1:
    action = st.selectbox("Do you want to buy or sell?", ["Buy", "Sell"])
with col2:
    property_types = st.multiselect("Select the property type", ["House", "Unit"], default=["House", "Unit"])
    property_types = [property.lower() for property in property_types]

st.write("\n" * 5)

#Time parameters
today = pd.Timestamp("2019-07-26 00:00:00")     
selected_year = st.number_input("Select a year to predict into the future", min_value=today.year + 1, max_value=today.year + 20, step=1)


#Prediction
st.write("\n" * 5)
col1, col2 = st.columns(2)

with col1:
    st.subheader("Prediction")

st.write("\n" * 5)

# Data transformation
data_filtered = filter_data(raw_data, "Month", property_types)

# Make prediction
today = pd.Timestamp("2019-07-26 00:00:00")
selected_date = pd.Timestamp(year=selected_year, month=12, day=31)
steps = (selected_date.year - today.year) * 12 + selected_date.month - today.month
future_price_KPI = make_prediction(data_filtered, steps, "Month")

# KPI Calculation

future_price_KPI = future_price_KPI[future_price_KPI['time'].dt.year == selected_year]

max_price_month = future_price_KPI.loc[future_price_KPI['price'].idxmax()]
min_price_month = future_price_KPI.loc[future_price_KPI['price'].idxmin()]

col1, col2, col3 = st.columns(3)
if action == "Buy":
    with col1:
        st.metric(label=f"Best Month to {action}", value=min_price_month['time'].strftime("%B"))
    with col2:
        st.metric(label=f"Estimated Price", value=f"${min_price_month['price']:.2f}")
    with col3:
        st.write(f"Buying in {min_price_month['time'].strftime('%B')} would be ${max_price_month['price'] - min_price_month['price']:.2f} cheaper compared to buying in {max_price_month['time'].strftime('%B')}.")
elif action == "Sell":
    with col1:
        st.metric(label=f"Best Month to {action}", value=max_price_month['time'].strftime("%B"))
    with col2:
        st.metric(label=f"Estimated Price", value=f"${max_price_month['price']:.2f}")
    with col3:
        st.write(f"Selling in {max_price_month['time'].strftime('%B')} would be ${max_price_month['price'] - min_price_month['price']:.2f} more profitable compared to selling in {min_price_month['time'].strftime('%B')}.")
st.write("\n" * 5)


#Select the granularity of the graph 

granularity = st.selectbox("Select the time unit of the graph", ["Day", "Week", "Month", "Year"])
st.write("\n" * 5)


# Calculate the steps based on the granularity 

if granularity == "Day":
    steps = (selected_date - today).days
elif granularity == "Week":
    steps = (selected_date - today).days // 7
elif granularity == "Month":
    steps = (selected_date.year - today.year) * 12 + selected_date.month - today.month
elif granularity == "Year":
    steps = selected_date.year - today

future_price_graph = make_prediction(data_filtered, steps, granularity)

# Make predictiom
future_price_graph = make_prediction(data_filtered, steps, granularity)
final_chart = prediction_graph(data_filtered, future_price_graph)

# Display the chart in Streamlit
st.altair_chart(final_chart, use_container_width=True)

if st.button("Send balloons!"):
    st.balloons()
