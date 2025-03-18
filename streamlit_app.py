import streamlit as st
import pandas as pd
from functions import load_data, filter_data, make_prediction, prediction_graph

# Header
st.title("Property Sales Data Prediction")
# Add line breaks and spaces between paragraphs
st.write("\n")

# Load data

raw_data = load_data()

# Input data
st.subheader("Find out the best time to buy or sell a property")
st.write("\n" * 5)

col1, col2, col3 = st.columns(3)

with col1:
    action = st.radio("Do you want to buy or sell?", ["Buy", "Sell"])
with col2:
    property_types = st.multiselect("Select the property type", ["House", "Unit"], default=["House", "Unit"])
    property_types = [property.lower() for property in property_types]
with col3:
    if "house" in property_types and "unit" not in property_types:
        num_rooms = st.multiselect("Select number of rooms", options=[2, 3, 4, 5], default=[2,3,4,5])
    elif "unit" in property_types and "house" not in property_types:
        num_rooms = st.multiselect("Select number of rooms", options=[1, 2, 3], default=[1,2,3])
    else:
        num_rooms = st.multiselect("Select number of rooms", options=[1, 2, 3, 4, 5], default=[1,2,3,4,5])


st.write("\n" * 5)

#Time parameters
today = pd.Timestamp("2019-07-26 00:00:00")     
selected_year = st.number_input("Select a year to predict into the future", min_value=today.year+1, max_value=today.year + 20, step=1) 


#Prediction
st.write("\n" * 5)
col1, col2 = st.columns(2)

with col1:
    st.subheader("Prediction")

st.write("\n" * 5)

if property_types and num_rooms:
    # Data transformation
    data_filtered = filter_data(raw_data, property_types, num_rooms)

    # Make prediction
    today = data_filtered['time'].max()
    selected_date = pd.Timestamp(year=selected_year, month=12, day=31)
    steps = (selected_date.year - today.year) * 12 + selected_date.month - today.month
    future_price_KPI = make_prediction(data_filtered, steps, "Month")

    # KPI Calculation
    future_price_KPI = future_price_KPI[future_price_KPI['time'].dt.year == selected_year]

    max_price_month = future_price_KPI.loc[future_price_KPI['price'].idxmax()]
    min_price_month = future_price_KPI.loc[future_price_KPI['price'].idxmin()]

    col1, col2, col3 = st.columns(3)
    best_month = max_price_month['time'].strftime("%B")
    worst_month = min_price_month['time'].strftime("%B")
    best_price = max_price_month['price']
    worst_price = min_price_month['price']

    if action == "Buy":
        with col1:
            st.metric(label=f"Best Month to {action}", value=worst_month)
            st.metric(label=f"Worst Month to {action}", value=best_month)
        with col2:
            st.metric(label=f"Estimated Price", value=f"${worst_price:,.0f}".replace(",", "."))
            st.metric(label=f"Estimated Price", value=f"${best_price:,.0f}".replace(",", "."))
        with col3:
            st.write("\n" * 10)
            st.write(f"Buying in {worst_month} would be ${best_price - worst_price:,.0f}".replace(",", ".") + " cheaper compared to buying in " + best_month + ".")
    elif action == "Sell":
        with col1:
            st.metric(label=f"Best Month to {action}", value=best_month)
            st.metric(label=f"Worst Month to {action}", value=worst_month)
        with col2:
            st.metric(label=f"Estimated Price", value=f"${best_price:,.0f}".replace(",", "."))
            st.metric(label=f"Estimated Price", value=f"${worst_price:,.0f}".replace(",", "."))
        with col3:
            st.write("\n" * 20)
            st.write(f"Selling in {best_month} would be ${best_price - worst_price:,.0f}".replace(",", ".") + " more profitable compared to selling in " + worst_month + ".")
    st.write("\n" * 5)

    # Select the granularity of the graph 
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
        steps = selected_date.year - today.year


    # Make prediction
    future_price_graph = make_prediction(data_filtered, steps, granularity)
    final_chart = prediction_graph(data_filtered, future_price_graph, granularity)

    # Display the chart in Streamlit
    st.altair_chart(final_chart, use_container_width=True)

    if st.button("Send balloons!"):
        st.balloons()
else:
    st.write("Please select a property type to make a prediction.")
