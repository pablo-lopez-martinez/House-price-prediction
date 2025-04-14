from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import Optional
from utils.db_handler import DatabaseManager  # Asegúrate de que este archivo exista

app = FastAPI(title="Property Sales API", version="1.0")

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"
    extra_input_params: dict = {}

class UserLogin(BaseModel):
    email: EmailStr
    password: str

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

class RoleUpdate(BaseModel):
    email: EmailStr
    new_role: str


# Rutas de autenticación y usuarios
@app.post("/register")
def register_user(user: UserCreate):
    if DatabaseManager.verify_duplicate_user(user.email):
        raise HTTPException(status_code=400, detail="Email already registered.")
    success = DatabaseManager.save_user(user.email, user.password, user.role, user.extra_input_params)
    if success:
        return {"message": "User registered successfully"}
    raise HTTPException(status_code=500, detail="Failed to register user.")

@app.get("/users")
def get_users():
    return DatabaseManager.get_all_users().to_dict(orient="records")

@app.put("/users/role")
def update_role(data: RoleUpdate):
    if DatabaseManager.set_user_role(data.email, data.new_role):
        return {"message": f"Role updated to {data.new_role}"}
    raise HTTPException(status_code=404, detail="User not found")


# Rutas de ventas
@app.post("/sales")
def create_sale(sale: SaleCreate):
    success = DatabaseManager.insert_sale(dict(sale))
    if success:
        return {"message": "Sale inserted successfully"}
    raise HTTPException(status_code=500, detail="Failed to insert sale.")

@app.get("/sales/user/{email}")
def get_sales_by_user(email: str):
    user_id = DatabaseManager.get_user_id(email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    df = DatabaseManager.get_sales_by_user(user_id)
    return df.to_dict(orient="records")


@app.get("/sales/filter")
def filter_sales(
    postcode: Optional[str] = Query(None),
    property_type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None)
):
    df = DatabaseManager.load_data()
    if df is None:
        raise HTTPException(status_code=500, detail="Data loading failed")

    if postcode:
        df = df[df["postcode"] == postcode]
    if property_type:
        df = df[df["property_type"] == property_type]
    if min_price is not None:
        df = df[df["price"] >= min_price]
    if max_price is not None:
        df = df[df["price"] <= max_price]

    return df.to_dict(orient="records")

@app.delete("/sales")
def delete_sale(sale: SaleDelete):
    user_id = DatabaseManager.get_user_id(sale.user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    success = DatabaseManager.delete_sale(sale.date_sold, sale.price, user_id)
    if success:
        return {"message": "Sale deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete sale.")
