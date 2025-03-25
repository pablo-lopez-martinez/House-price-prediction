import streamlit as st
import psycopg2
from psycopg2 import sql
import pandas as pd
import bcrypt

DB_CONFIG = st.secrets["postgresql"]  # Ensure your Streamlit secrets file has a "database" section

class DatabaseManager:
    @staticmethod
    @st.cache_data
    def load_data():
        try:
            with psycopg2.connect(**DB_CONFIG) as conn:
                query = "SELECT * FROM property_sales;"  # Replace 'property_sales' with your actual table name
                df = pd.read_sql_query(query, conn)
                return df

        except psycopg2.OperationalError as e:
            print(f"Database connection failed: {e}")
            return None

    def insert_sale(entry):
        with psycopg2.connect(**DB_CONFIG) as conn:
            query = """INSERT INTO property_sales (datesold, price, postcode, property_type, bedrooms) 
                       VALUES (%s, %s, %s, %s, %s)"""
            with conn.cursor() as cursor:
                cursor.execute(query, (entry["date_sold"], entry["price"], entry["postcode"], entry["property_type"], entry["bedrooms"]))
                conn.commit()

    def verify_duplicate_user(email):
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s", (email,))
                count = cursor.fetchone()[0]
            return count > 0
        
    def authenticate_user(email, password):
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
        
            # Retrieve the stored hashed password for the user
            cursor.execute("SELECT hash_password FROM users WHERE email = %s", (email,))
            stored_hashed_password = cursor.fetchone()
        
            conn.close()

        # Check if a user with the given email was found
        if stored_hashed_password is None:
            return False
    
        stored_hashed_password = stored_hashed_password[0]  # Extract the hash from the tuple

        # Compare the provided password with the stored hashed password
        return bcrypt.checkpw(password.encode(), stored_hashed_password.encode())

    def save_user(email, password, extra_input_params):
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
            
                # Hash the password before saving
                hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')
                
                # Base columns and values
                columns = ['email', 'hash_password']
                values = [email, hashed_password]

                # Add extra input params to the columns and values lists
                for key in extra_input_params.keys():
                    columns.append(key)
                    values.append(st.session_state[f'{key}'])
                
                # Dynamically build the SQL query
                columns_str = ', '.join(columns)
                placeholders = ', '.join(['%s'] * len(values))
                
                query = sql.SQL("INSERT INTO users ({}) VALUES ({})").format(
                    sql.SQL(columns_str),
                    sql.SQL(placeholders))
                
                cursor.execute(query, values)
                conn.commit()
        
        
        
