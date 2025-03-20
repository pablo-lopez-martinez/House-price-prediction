import streamlit as st
import psycopg2
import pandas as pd


DB_CONFIG = st.secrets["postgresql"]  # Ensure your Streamlit secrets file has a "database" section

class DatabaseManager:
    @staticmethod
    @st.cache_data
    def load_data():
        try:
            with psycopg2.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname=DB_CONFIG["database"]
            ) as conn:
                query = "SELECT * FROM property_sales;"  # Replace 'property_sales' with your actual table name
                df = pd.read_sql_query(query, conn)
                return df

        except psycopg2.OperationalError as e:
            print(f"Database connection failed: {e}")
            return None
        

    def insert_sale(entry):
        with psycopg2.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname=DB_CONFIG["database"]
            ) as conn:
            query = f"""INSERT INTO property_sales (datesold, price, postcode, property_type, bedrooms) 
                        VALUES ({entry["date_sold"]}, {entry["price"]}, {entry["postcode"]}, {entry["property_type"]}, {entry["bedrooms"]})"""
            cursor = conn.cursor()
            cursor.execute(query)

    def insert_user(entry):
        with psycopg2.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname=DB_CONFIG["database"]
            ) as conn:

            query = f"""INSERT INTO users (username, name, surname, email, password)
                        VALUES ({entry["username"]}, {entry["name"]}, {entry["surname"]}, {entry["email"]}, {entry["password"]})"""
            cursor = conn.cursor()
            cursor.execute(query)
        
