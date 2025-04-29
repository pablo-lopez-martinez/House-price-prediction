from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import streamlit as st
from utils.data_manipulation import make_prediction
import pandas as pd
import os
from jose import JWTError, jwt
from utils.db_handler import DatabaseManager

# App instance
app = FastAPI(title="Property Sales API", version="1.0")

# JWT Config
try:
    SECRET_KEY = st.secrets["api"]["key"]  # Try to get the secret key from Streamlit secrets
except FileNotFoundError:
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")  # Fallback to environment variable or default
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"
    extra_input_params: dict = {}  

class UserRequest(BaseModel):
    email: EmailStr



class RoleUpdate(BaseModel):
    email: EmailStr
    new_role: str

class SaleCreate(BaseModel):
    user_email: EmailStr
    date_sold: str
    price: float
    postcode: str
    property_type: str
    bedrooms: int

class SaleDelete(BaseModel):
    user_email: EmailStr
    date_sold: str
    price: float

class Token(BaseModel):
    access_token: str
    token_type: str

# Auth helpers
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
        user = DatabaseManager.get_user_by_email(email)
        if not user:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

# Auth routes
@app.post("/register", response_model=dict)
def register_user(user: UserCreate):
    if DatabaseManager.verify_duplicate_user(user.email):
        raise HTTPException(status_code=400, detail="Email already registered.")
    success = DatabaseManager.save_user(user.email, user.password, user.role, user.extra_input_params)
    if success:
        return {"message": "User registered successfully"}
    raise HTTPException(status_code=500, detail="Failed to register user.")

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = DatabaseManager.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
    
@app.get("/users", response_model=List[Dict[str, Any]])
def get_users(current_user: dict = Depends(get_current_user)):
    # Verificar si el usuario tiene permisos de administrador
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos para ver todos los usuarios")
    
    users_df = DatabaseManager.get_all_users()
    return users_df.to_dict(orient="records")

@app.get("/users/{email}", response_model=Dict[str, Any])
def get_user_id(email: str, current_user: dict = Depends(get_current_user)):

    if email == "me":
        return {"email": current_user["email"], "id": current_user["id"]}
    
    # Verificar si el usuario tiene permisos de administrador
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos para ver este usuario")
        
    user = DatabaseManager.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"email": user["email"], "id": user["id"]}
    

@app.put("/users/role", response_model=dict)
def update_role(data: RoleUpdate, current_user: dict = Depends(get_current_user)):
    # Verificar si el usuario tiene permisos de administrador
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos para cambiar roles")
        
    if DatabaseManager.set_user_role(data.email, data.new_role):
        return {"message": f"Role updated to {data.new_role}"}
    raise HTTPException(status_code=404, detail="User not found")

# Sales routes
@app.post("/sales", response_model=dict)
def create_sale(sale: SaleCreate, current_user: dict = Depends(get_current_user)):
    # Verificar si el usuario está creando una venta con su propio email o es admin
    if current_user["email"] != sale.user_email and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No puedes crear ventas para otros usuarios")
        
    success = DatabaseManager.insert_sale(dict(sale))
    if success:
        return {"message": "Sale inserted successfully"}
    raise HTTPException(status_code=500, detail="Failed to insert sale.")

@app.get("/sales/user/{id}", response_model=List[Dict[str, Any]])
def get_sales_by_user(id: str, current_user: dict = Depends(get_current_user)):
    # Verificar si el usuario está consultando sus propias ventas o es admin
    if current_user["id"] != id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No puedes ver las ventas de otros usuarios")

    
    df = DatabaseManager.get_sales_by_user(id)
    return df.to_dict(orient="records")

@app.get("/sales", response_model=List[Dict[str, Any]])
def filter_sales(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
):
    df = DatabaseManager.load_data()
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No sales data found")
    if start_date is None or end_date is None:
        raise HTTPException(status_code=400, detail="Both start_date and end_date must be provided")
    print(f"Start Date: {start_date}, End Date: {end_date}")
    from datetime import datetime

    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        df = df[df["datesold"] >= start_date]
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        df = df[df["datesold"] <= end_date]

    return df.to_dict(orient="records")

@app.delete("/sales", response_model=dict)
def delete_sale(sale: SaleDelete, current_user: dict = Depends(get_current_user)):
    # Verificar si el usuario está eliminando su propia venta o es admin
    if current_user["email"] != sale.user_email and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No puedes eliminar ventas de otros usuarios")
        
    user_id = DatabaseManager.get_user_id(sale.user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
        
    success = DatabaseManager.delete_sale(sale.date_sold, sale.price, user_id)
    if success:
        return {"message": "Sale deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete sale.")

@app.get("/predict/months", response_model=Dict[str, Any])
def get_best_and_worst_months(
    year: int,
    action: str = Query(..., regex="^(buy|sell)$", description="Action must be 'buy' or 'sell'"),
    current_user: dict = Depends(get_current_user)
):
    # Load and filter data
    data = DatabaseManager.load_data()
    if data is None or data.empty:
        raise HTTPException(status_code=404, detail="No sales data found")

    try:
        # Calculate number of months to predict
        data.rename(columns={'datesold': 'time'}, inplace=True)
        last_date = data['time'].max()
        prediction_end = pd.Timestamp(year=year, month=12, day=31)
        months_to_predict = (prediction_end.year - last_date.year) * 12 + (prediction_end.month - last_date.month)

        if months_to_predict <= 0:
            raise HTTPException(status_code=400, detail="Prediction year must be in the future")

        forecast = make_prediction(data, months_to_predict, "Month")
        forecast = forecast[forecast['time'].dt.year == year]

        if forecast.empty:
            raise HTTPException(status_code=404, detail="No forecast data available for selected year")

        best_row = forecast.loc[forecast['price'].idxmax()]
        worst_row = forecast.loc[forecast['price'].idxmin()]

        if action == "buy":
            result = {
                "best_month": worst_row['time'].strftime("%B"),
                "best_price": int(worst_row['price']),
                "worst_month": best_row['time'].strftime("%B"),
                "worst_price": int(best_row['price']),
                "savings": int(best_row['price'] - worst_row['price'])
            }
        else:  # sell
            result = {
                "best_month": best_row['time'].strftime("%B"),
                "best_price": int(best_row['price']),
                "worst_month": worst_row['time'].strftime("%B"),
                "worst_price": int(worst_row['price']),
                "profit_diff": int(best_row['price'] - worst_row['price'])
            }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn 
    uvicorn.run(app, host="0.0.0.0", port=8000)