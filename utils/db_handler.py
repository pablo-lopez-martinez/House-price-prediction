import streamlit as st
from sqlalchemy import create_engine, URL, text
import uuid
import pandas as pd
import bcrypt

# Load configuration from Streamlit secrets
DB_CONFIG = st.secrets["postgresql"]

# Create the database URL
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_CONFIG["user"],
    password=DB_CONFIG["password"],
    host=DB_CONFIG["host"],
    port=DB_CONFIG["port"],
    database=DB_CONFIG["database"],
)

# Create the engine with a connection pool
engine = create_engine(
    db_url,
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=1800,
    echo=True  # Optional: show queries in the console
)

class DatabaseManager:
    @staticmethod
    @st.cache_data
    def load_data():
        """Load data from the database."""
        try:
            with engine.connect() as conn:
                query = text("SELECT * FROM property_sales;")
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Failed to connect to the database: {e}")
            return None
        
    @staticmethod
    def get_user_by_email(email):
        """Get user details by email."""
        try:
            with engine.connect() as conn:
                query = text("SELECT * FROM users WHERE email = :email")
                result = conn.execute(query, {"email": email}).fetchone()
                if result:
                    result_dict = dict(result._mapping)  # Convert the row to a dictionary
                    return result_dict
                else:
                    return None  # User not found
        except Exception as e:
            print(f"Error retrieving user by email: {e}")
            return None
        
    @staticmethod
    def get_user_id(email):
        try:
            user = DatabaseManager.get_user_by_email(email)
            return user["id"]
        except Exception as e:
            print(f"Error checking finding user id: {e}")
            return None
        
    
    @staticmethod
    def get_user_role(email):
        """Get the role of the user with the given email."""
        try:
            with engine.connect() as conn:
                query = text("SELECT role FROM users WHERE email = :email")
                result = conn.execute(query, {"email": email}).fetchone()
                if result:
                    return result[0]
                else:
                    return "guest"  # Rol por defecto si no se encuentra
        except Exception as e:
            print(f"Error retrieving user role: {e}")
            return "guest"



    @staticmethod
    def insert_sale(entry):
        """Insert a record into the property_sales table."""
        try:
            with engine.connect() as conn:
                user_id = DatabaseManager.get_user_id(entry["user_email"])
                del entry["user_email"]
                entry["user_id"] = user_id
                query = text("""
                    INSERT INTO property_sales (datesold, price, postcode, property_type, bedrooms, user_id) 
                    VALUES (:date_sold, :price, :postcode, :property_type, :bedrooms, :user_id)
                """)
                conn.execute(query, entry)
                conn.commit()
                print("✅ Sale successfully inserted.")
                DatabaseManager.load_data.clear()
                return True
        except Exception as e:
            print(f"Failed to insert sale: {e}")
            return False

    @staticmethod
    def get_sales_by_user(user_id):
        try:
            with engine.connect() as conn:
                query = text("""
                    SELECT datesold, price, postcode, property_type, bedrooms 
                    FROM property_sales 
                    WHERE user_id = :user_id
                    ORDER BY datesold DESC
                """)
                result = conn.execute(query, {"user_id": user_id})
                sales = result.fetchall()

                # Convertir a DataFrame
                if sales:
                    df = pd.DataFrame(sales, columns=["Date Sold", "Price", "Postcode", "Property Type", "Bedrooms"])
                    return df
                else:
                    return pd.DataFrame()  # Devuelve un DataFrame vacío si no hay datos
        except Exception as e:
            print(f"Error retrieving sales data: {e}")
            return pd.DataFrame()
        
    @staticmethod
    def delete_sale(date_sold, price, user_id):
        try:
            with engine.connect() as conn:
                query = text("""
                    DELETE FROM property_sales 
                    WHERE datesold = :date_sold AND price = :price AND user_id = :user_id
                """)
                conn.execute(query, {"date_sold": date_sold, "price": price, "user_id": user_id})
                conn.commit()
                DatabaseManager.load_data.clear()
                return True
        except Exception as e:
            print(f"Error deleting sale: {e}")
            return False




    @staticmethod
    def verify_duplicate_user(email):
        """Check if a user already exists in the database."""
        try:
            with engine.connect() as conn:
                query = text("SELECT COUNT(*) FROM users WHERE email = :email")
                result = conn.execute(query, {"email": email}).scalar()
                return result > 0
        except Exception as e:
            print(f"Error checking for duplicate user: {e}")
            return False

    @staticmethod
    def authenticate_user(email, password):
        """Authenticate a user by comparing the provided password with the stored hash."""
        try:
            with engine.connect() as conn:
                query = text("SELECT hashed_password FROM users WHERE email = :email")
                result = conn.execute(query, {"email": email}).fetchone()

            if not result:
                return False  # User not found

            stored_hashed_password = result[0]

            # Compare provided password with stored hash
            return bcrypt.checkpw(password.encode(), stored_hashed_password.encode())
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    @staticmethod
    def save_user(email, password, role, extra_input_params):
        """Save a new user in the database with a role."""
        try:
            with engine.connect() as conn:
                # Hash the password before storing it
                hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")

                # Construct the SQL query dynamically
                columns = ["id", "email", "hashed_password", "role"]  # 
                values = {
                    "id": uuid.uuid4(),
                    "email": email,
                    "hashed_password": hashed_password,
                    "role": role  
                }

                for key, value in extra_input_params.items():
                    columns.append(key)
                    values[key] = value

                columns_str = ", ".join(columns)
                placeholders = ", ".join([f":{key}" for key in values.keys()])

                query = text(f"INSERT INTO users ({columns_str}) VALUES ({placeholders})")

                conn.execute(query, values)
                conn.commit()
                print("User successfully registered.")
                DatabaseManager.load_data.clear()
                return True
        except Exception as e:
            print(f"Failed to save user: {e}")
            return False
        

    @staticmethod
    def get_all_users():
        """Retrieve all users with their emails and roles."""
        try:
            with engine.connect() as conn:
                query = text("SELECT email, role FROM users ORDER BY email ASC")
                result = conn.execute(query).fetchall()

                if result:
                    df = pd.DataFrame(result, columns=["email", "role"])
                    return df
                else:
                    return pd.DataFrame(columns=["email", "role"])  # Retorna DataFrame vacío si no hay usuarios
        except Exception as e:
            print(f"Error retrieving users: {e}")
            return pd.DataFrame(columns=["email", "role"])
        

    @staticmethod
    def set_user_role(email, new_role):
        """Change the role of a user."""
        try:
            with engine.connect() as conn:
                query = text("UPDATE users SET role = :role WHERE email = :email")
                result = conn.execute(query, {"role": new_role, "email": email})
                
                if result.rowcount > 0:
                    conn.commit()
                    print(f"User {email}'s role has been updated to {new_role}.")
                    DatabaseManager.load_data.clear()
                    return True
                else:
                    print(f"User with email {email} not found.")
                    return False
        except Exception as e:
            print(f"Error updating user role: {e}")
            return False


