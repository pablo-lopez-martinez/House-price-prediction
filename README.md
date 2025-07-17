# Property Sales Prediction App

## Overview

This application is a web-based tool built with Streamlit that predicts property prices based on historical sales data. It allows users to filter data by property type and number of bedrooms, visualize predictions, and manage property sales records. The app also includes an API for programmatic access to the data and predictions, with user authentication and role-based access control.

### Features

- **Price Prediction:** Predict future property prices using the Prophet forecasting model, with customizable granularity (Month, Quarter, Year).

- **Data Filtering:** Filter property sales data by property type (House, Unit) and number of bedrooms.

- **Visualization:** Interactive charts using Altair to display historical and predicted property prices with confidence intervals.

- **User Authentication:** Secure user registration and login with bcrypt password hashing.

- **Role-Based Access Control:**

  - **Users:** Add, view, and delete their own property sale records.

  - **Admins:** Manage user roles and delete users.

  - **Analysts:** Export sales data as CSV.

  - **Guests:** View predictions without adding or modifying data.

- **Sales Management:** Authenticated users can add and delete property sale records.

- **API:** FastAPI-based API for managing users, sales, and predictions, secured with JWT authentication.

- **Database Integration:** PostgreSQL database for storing user and sales data.

## Technologies Used

- **Python:** Core programming language.

- **Streamlit:** Web interface for data visualization and user interaction.

- **FastAPI:** Backend API for programmatic access.

- **PostgreSQL:** Database for storing property sales and user data.

- **SQLAlchemy:** ORM for database interactions.

- **Pandas:** Data manipulation and analysis.

- **Prophet:** Time-series forecasting for price predictions.

- **Altair:** Interactive data visualizations.

- **bcrypt:** Password hashing for secure authentication.

- **JWT:** Token-based authentication for API security.

- **Pyodide:** (Implied for potential browser-based execution, not explicitly used in code).

## Data

The application uses two CSV files located in the `data` folder:

- `property_sales.csv`: Historical property sales data.

- `property_sales_new.csv`: Additional property sales data.

These files contain columns such as `datesold`, `price`, `postcode`, `property_type`, `bedrooms`, and `user_id`.

## Deployment Instructions

Follow these steps to deploy the application locally:

### Prerequisites

- Python 3.8+

- PostgreSQL database

- pip for installing Python packages

- Git for cloning the repository

### Steps

1. **Clone the Repository:**

   ```bash
   git clone <repository-url>
   cd <repository-directory>

2. **Install dependencies:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

3. Create a PostgreSQL database and ensure it has tables for users and property_sales.

    ```bash
    CREATE TABLE users (
        id UUID PRIMARY KEY,
        email VARCHAR UNIQUE NOT NULL,
        hashed_password VARCHAR NOT NULL,
        role VARCHAR NOT NULL
    );
    
    CREATE TABLE property_sales (
        id SERIAL PRIMARY KEY,
        datesold DATE NOT NULL,
        price FLOAT NOT NULL,
        postcode VARCHAR NOT NULL,
        property_type VARCHAR NOT NULL,
        bedrooms INTEGER NOT NULL,
        user_id UUID REFERENCES users(id)
    );

4. Run the Streamlit App

    ```bash
    streamlit run streamlit_app.py

5. Run the FastAPI Server (optional, for API access):

    ```bash
    uvicorn api:app --host 0.0.0.0 --port 8000
