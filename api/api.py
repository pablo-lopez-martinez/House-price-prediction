from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import streamlit as st
from jose import JWTError, jwt
from utils.db_handler import DatabaseManager

# App instance
app = FastAPI(title="Property Sales API", version="1.0")

# JWT Config
SECRET_KEY = st.secrets["api"]["key"] # Generate a random secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"
    extra_input_params: dict = {}  

class UserResponse(BaseModel):
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

class SaleResponse(BaseModel):
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

@app.get("/sales/user/{email}", response_model=List[Dict[str, Any]])
def get_sales_by_user(email: str, current_user: dict = Depends(get_current_user)):
    # Verificar si el usuario está consultando sus propias ventas o es admin
    if current_user["email"] != email and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No puedes ver las ventas de otros usuarios")
        
    user_id = DatabaseManager.get_user_id(email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    
    df = DatabaseManager.get_sales_by_user(user_id)
    return df.to_dict(orient="records")

@app.get("/all_sales", response_model=List[Dict[str, Any]])
def get_all_sales(current_user: dict = Depends(get_current_user)):
    try:
        df = DatabaseManager.load_data()
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No sales data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data loading failed: {str(e)}")
    
    return df.to_dict(orient="records")

@app.get("/sales/filter", response_model=List[Dict[str, Any]])
def filter_sales(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    df = DatabaseManager.load_data()
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No sales data found")

    if start_date:
        df = df[df["date_sold"] >= start_date]
    if end_date:
        df = df[df["date_sold"] <= end_date]

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)