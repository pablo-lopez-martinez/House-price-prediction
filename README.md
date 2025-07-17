# Property Sales Prediction App

## Overview
This application is a web-based tool built with Streamlit that predicts property prices based on historical sales data. It allows users to filter data by property type and number of bedrooms, visualize predictions through interactive charts, and manage property sales records. The app includes a secure user authentication system and role-based access control, enabling different levels of interaction for users, admins, analysts, and guests. Additionally, a FastAPI-based API provides programmatic access to data and predictions, secured with JWT authentication. The application is deployed on Streamlit Cloud and uses a Neon PostgreSQL database for data storage.

## Features
- **Price Prediction**:
  - Utilizes the **Prophet** forecasting model to predict future property prices based on historical sales data.
  - Users can select a future year (up to 20 years from the current date) to forecast prices.
  - Offers customizable time granularity (Month, Quarter, Year) for predictions, allowing users to analyze trends at different time scales.
  - Displays the best and worst months to buy or sell, along with estimated prices and potential savings or profit differences. For example, when buying, the app highlights the month with the lowest predicted price and calculates savings compared to the highest price month.
  - Predictions include confidence intervals (lowest and highest price estimates) to provide a range of expected values.

- **Data Filtering**:
  - Users can filter property sales data by **property type** (House, Unit) and **number of bedrooms** (1 to 5, depending on property type).
  - The filtering process aggregates data by averaging prices for the selected criteria and interpolates missing values to ensure a continuous time series, enhancing prediction accuracy.
  - Supports dynamic filtering: for example, selecting "House" limits bedroom options to 2–5, while "Unit" limits them to 1–3, reflecting typical property configurations.

- **Visualization**:
  - Generates interactive line charts using **Altair** to display historical and predicted property prices.
  - Historical data is shown in red, and future predictions in yellow, with a light blue shaded area representing the confidence interval for predicted prices.
  - Users can adjust the time granularity (Month, Quarter, Year) of the charts, with appropriate date formatting (e.g., "Jan 2023" for months, "2023-Q1" for quarters).
  - Charts include tooltips for precise data inspection, showing the date, price, and whether the data is historical or predicted.

- **User Authentication**:
  - Secure user registration and login system using **bcrypt** for password hashing.
  - Validates email formats during signup and checks for duplicate users to prevent multiple registrations with the same email.
  - Supports guest access, allowing unauthenticated users to view predictions and charts without modifying data.
  - Includes a streamlined login interface with error handling for invalid credentials or incomplete forms.

- **Role-Based Access Control**:
  - **Users**: Can add new property sale records (e.g., date sold, price, postcode, property type, bedrooms) and view or delete their own records. The interface displays a table of their sales history with options to delete entries.
  - **Admins**: Have full control over user management, including viewing all users, updating their roles (e.g., to "user," "analyst," or "admin"), and deleting users. This is accessible via a dedicated admin panel.
  - **Analysts**: Can export the entire property sales dataset as a CSV file for further analysis, with sensitive user IDs removed from the export.
  - **Guests**: Can explore predictions and visualizations but are restricted from adding, modifying, or deleting data.

- **Sales Management**:
  - Authenticated users can submit new property sale records through a form that validates inputs (e.g., numeric postcode, price between $10,000 and $10,000,000, valid date range).
  - Users can delete their own sale records directly from the sales history table, with changes immediately reflected in the database and predictions.
  - All data modifications (additions and deletions) clear relevant caches to ensure predictions are updated with the latest data.

- **API**:
  - A **FastAPI**-based API provides programmatic access to user management, sales data, and price predictions.
  - Endpoints include:
    - `/register`: Create new users.
    - `/login`: Authenticate users and issue JWT tokens.
    - `/users`: Retrieve all users (admin-only).
    - `/sales`: Manage sales data, including filtering by date range or user ID.
    - `/predict/months`: Get the best and worst months to buy or sell for a given year.
  - Secured with **JWT authentication**, ensuring only authorized users can access protected endpoints.
  - Supports role-based restrictions, such as limiting non-admin users to their own sales data.

- **Database Integration**:
  - Uses a **Neon PostgreSQL** database to store user information (email, hashed password, role) and property sales data (date sold, price, postcode, property type, bedrooms, user ID).
  - Employs **SQLAlchemy** for robust database interactions, including connection pooling for efficient query handling.
  - Data is cached using Streamlit’s `@st.cache_data` to optimize performance for frequent queries.

## Technologies Used
- **Python**: Core programming language.
- **Streamlit**: Web interface for data visualization and user interaction.
- **FastAPI**: Backend API for programmatic access (requires separate deployment).
- **PostgreSQL (Neon)**: Cloud-hosted database for storing property sales and user data.
- **SQLAlchemy**: ORM for database interactions.
- **Pandas**: Data manipulation and analysis.
- **Prophet**: Time-series forecasting for price predictions.
- **Altair**: Interactive data visualizations.
- **bcrypt**: Password hashing for secure authentication.
- **JWT**: Token-based authentication for API security.
- **Pyodide**: (Implied for potential browser-based execution, not explicitly used in code).

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

4. Configure Environment Variables: Create .streamlit/secrets.toml file or set environment variables for database access:

    ```bash
    [postgresql]
    user = "your_db_user"
    password = "your_db_password"
    host = "localhost"
    port = "5432"
    database = "your_db_name"
    
    [api]
    key = "your_secret_key_for_jwt"

5. Run the Streamlit App

    ```bash
    streamlit run streamlit_app.py

6. Run the FastAPI Server (optional, for API access):

    ```bash
    uvicorn api:app --host 0.0.0.0 --port 8000
