import streamlit as st
import pandas as pd
from prophet import Prophet
import altair as alt


@st.cache_data
def load_data():
    data = pd.read_csv("dataset/property_sales.csv", parse_dates=['date_sold'])
    return data


@st.cache_data
def filter_data(data, granularity, property_type, num_rooms):
    data_filtered = data.copy()

    #Rename date sold column 
    data_filtered.rename(columns={'date_sold': 'time'}, inplace=True)

    #Filter by property type
    data_filtered = data_filtered[data_filtered['property_type'].isin(property_type)]

    #Filter by number of rooms
    data_filtered = data_filtered[data_filtered['bedrooms'].isin(num_rooms)]

    # Reduce table
    data_filtered = data_filtered[['time', 'price']]
    
    # Group by day
    data_filtered = data_filtered[["time", "price"]].groupby(['time']).mean().reset_index()

    # Interpolate missing values
    date_range = pd.date_range(start=data_filtered['time'].min(), end=data_filtered['time'].max())
    data_filtered = data_filtered.set_index('time').reindex(date_range).interpolate().reset_index()
    data_filtered.rename(columns={'index': 'time'}, inplace=True)
    
    # Time granularity
    if granularity == "Day":
        data_filtered['time'] = data_filtered['time']
    elif granularity == "Week":
        data_filtered['time'] = data_filtered['time'].dt.to_period('W').dt.to_timestamp()
    elif granularity == "Month":
        data_filtered['time'] = data_filtered['time'].dt.to_period('M').dt.to_timestamp()
    elif granularity == "Year":
        data_filtered['time'] = data_filtered['time'].dt.to_period('Y').dt.to_timestamp()

    # Group by granularity
    data_filtered = data_filtered.groupby(['time'], sort=False).mean().reset_index()
    
    # Round the price    
    data_filtered['price'] = data_filtered['price'].round(0)
        
    return data_filtered


def make_prediction(data, steps, granularity):
    # Prepare data
    data = data.rename(columns={'time': 'ds', 'price': 'y'})

    # Fit model
    model = Prophet()
    model.fit(data)
    
    # Make prediction
    if granularity == "Day":
        future = model.make_future_dataframe(periods=steps, freq='D')
    elif granularity == "Week":
        future = model.make_future_dataframe(periods=steps, freq='W')
    elif granularity == "Month":
        future = model.make_future_dataframe(periods=steps, freq='M')
    elif granularity == "Year":
        future = model.make_future_dataframe(periods=steps, freq='Y')

    forecast = model.predict(future)
    
    # Round the predicted price to the nearest integer
    forecast['yhat'] = forecast[['yhat']].round(0)
    
    # Return the predicted price at the specified time
    forecast = forecast.rename(columns={'ds': 'time', 'yhat': 'price', 'yhat_lower': 'lowest price', 'yhat_upper': 'highest price'})
    return forecast[['time', 'price', 'lowest price', 'highest price']].tail(steps)


def prediction_graph(historical_data, future_data):
    
    # Combine historical and future data
    historical_data['type'] = 'Historical'
    future_data['type'] = 'Future'
    combined_data = pd.concat([historical_data, future_data])

    # Create Altair chart for historical and future data lines with different colors
    line_chart = alt.Chart(combined_data).mark_line().encode(
        x='time:T',
        y='price:Q',
        color=alt.Color('type:N', scale=alt.Scale(domain=['Historical', 'Future'], range=['#FF6347', '#FFFF00'])),  # Red for historical, Yellow for future
        tooltip=['time:T', 'price:Q', 'type:N']
    )

    # Add confidence interval area for future data
    confidence_area = alt.Chart(future_data).mark_area(
        opacity=0.3,
        color='lightblue'
    ).encode(
        x='time:T',
        y=alt.Y('lowest price:Q', title='price'),
        y2='highest price:Q'
    )

    # Combine historical and future price lines with confidence area
    return line_chart + confidence_area

