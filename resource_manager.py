import streamlit as st
import psycopg2
import pandas as pd

class ResourceManager: 
    def __init__(self, resource):
        self.resource = resource

    @staticmethod
    @st.cache_data
    def load_data():
        try:
            db_config = st.secrets["postgresql"]
            with psycopg2.connect(
                host=db_config["host"],
                port=db_config["port"],
                user=db_config["user"],
                password=db_config["password"],
                dbname=db_config["database"]) as conn:
        
                query = "SELECT * FROM property_sales;"  # Replace 'your_table_name' with your actual table name
                df = pd.read_sql_query(query, conn)
                return df

        except psycopg2.OperationalError as e:
            print(f"Database connection failed: {e}")
            return None
