import streamlit as st
import pandas as pd
from prophet import Prophet
import altair as alt


@st.cache_data
def load_data():
    data = pd.read_csv("dataset/property_sales.csv", parse_dates=['date_sold'])
    return data


@st.cache_data
def filter_data(data, property_type, num_rooms):
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
    
   # Month prices
    data_filtered['time'] = data_filtered['time'].dt.to_period('M').dt.to_timestamp()


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
    

    if granularity == "Month":
        future = model.make_future_dataframe(periods=steps, freq='M')
    if granularity == "Quarter":
        future = model.make_future_dataframe(periods=steps, freq='Q')
    elif granularity == "Year":
        future = model.make_future_dataframe(periods=steps, freq='Y')

    forecast = model.predict(future)
    
    # Round the predicted price to the nearest integer
    forecast['yhat'] = forecast[['yhat']].round(0)
    
    # Return the predicted price at the specified time
    forecast = forecast.rename(columns={'ds': 'time', 'yhat': 'price', 'yhat_lower': 'lowest price', 'yhat_upper': 'highest price'})
    return forecast[['time', 'price', 'lowest price', 'highest price']].tail(steps)



def prediction_graph(historical_data, future_data, granularity):
    
    # Convertir las fechas según la granularidad seleccionada
    if granularity == "Month":
        historical_data['time'] = historical_data['time'].dt.to_period('M').dt.to_timestamp()  # Mes
        x_axis_format = '%b %Y'  # Formato de mes en letras (e.g., Jan 2023)
    elif granularity == "Quarter":
        historical_data['time'] = historical_data['time'].dt.to_period('Q').dt.to_timestamp()  # Trimestre
        x_axis_format = '%Y-Q%q'  # Formato de trimestre
    elif granularity == "Year":
        historical_data['time'] = historical_data['time'].dt.to_period('Y').dt.to_timestamp()  # Año
        x_axis_format = '%Y'  # Formato de año

    # Agrupar datos históricos por el tiempo ajustado según granularidad
    historical_data = historical_data.groupby(['time'], sort=False).mean().reset_index()

    # Combinar datos históricos y futuros
    historical_data['type'] = 'Historical'
    future_data['type'] = 'Future'
    combined_data = pd.concat([historical_data, future_data])

    # Crear gráfico de Altair para las líneas de datos históricos y futuros con diferentes colores
    line_chart = alt.Chart(combined_data).mark_line().encode(
        x=alt.X('time:T', title='Time', 
                axis=alt.Axis(
                    format=x_axis_format,  # Mostrar según el formato ajustado
                    labelAngle=45  # Rotar las etiquetas del eje X si es necesario
                )),
        y='price:Q',
        color=alt.Color('type:N', scale=alt.Scale(domain=['Historical', 'Future'], range=['#FF6347', '#FFFF00'])),  # Rojo para histórico, amarillo para futuro
        tooltip=['time:T', 'price:Q', 'type:N']
    )

    # Agregar área de intervalo de confianza para los datos futuros
    confidence_area = alt.Chart(future_data).mark_area(
        opacity=0.3,
        color='lightblue'
    ).encode(
        x='time:T',
        y=alt.Y('lowest price:Q', title='price'),
        y2='highest price:Q'
    )

    # Combinar las líneas de datos históricos y futuros con el área de confianza
    return line_chart + confidence_area


