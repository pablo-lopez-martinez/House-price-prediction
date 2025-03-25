import streamlit as st
import pandas as pd
from page.login_page import login_page
from utils.data_manipulation import filter_data, make_prediction, prediction_graph
from utils.db_handler import DatabaseManager

def app_page():
    st.empty()

    col1, col2 = st.columns([0.85,0.15])

    if st.session_state["guest_mode"]:
        with col2:
            if st.button("LogIn"):
                st.session_state['page'] = 'login'
                st.session_state["authenticated"] = False
                st.rerun()    
    else:
        with col2:
            if st.button("Close Session"):
                st.session_state['page'] = 'login'
                st.session_state['authenticated'] = False
                st.rerun()


    # Header
    st.title("Property Sales Data Prediction")


    st.write("\n" * 10)
    st.write("\n" * 10)


    # Enter parameters
    col1, col2, empty, col3 = st.columns([1, 1, 0.25, 1])

    with col1:
        action = st.radio("Do you want to buy or sell?", ["Buy", "Sell"])
    with col2:
        property_types = st.multiselect("Select the property type", ["House", "Unit"], default=["House", "Unit"])
        property_types = [property.lower() for property in property_types]
    with col3:
        if "house" in property_types and "unit" not in property_types:
            num_rooms = st.multiselect("Select number of rooms", options=[2, 3, 4, 5], default=[2,3,4,5])
        elif "unit" in property_types and "house" not in property_types:
            num_rooms = st.multiselect("Select number of rooms", options=[1, 2, 3], default=[1,2,3])
        else:
            num_rooms = st.multiselect("Select number of rooms", options=[1, 2, 3, 4, 5], default=[1,2,3,4,5])


    st.write("\n" * 10)
    st.write("\n" * 10)


    # Load data
    raw_data = DatabaseManager.load_data()

    # Time parameters
    today = pd.Timestamp("2019-07-26 00:00:00")     
    selected_year = st.number_input("Select a year to predict into the future", min_value=today.year+1, max_value=today.year + 20, step=1) 


    st.write("\n" * 5)


    # Prediction
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Prediction")


    st.write("\n" * 5)


    if property_types and num_rooms:
        # Data transformation
        data_filtered = filter_data(raw_data, property_types, num_rooms)

        # Make prediction
        today = data_filtered['time'].max()
        selected_date = pd.Timestamp(year=selected_year, month=12, day=31)
        steps = (selected_date.year - today.year) * 12 + selected_date.month - today.month
        future_price_KPI = make_prediction(data_filtered, steps, "Month")

        # KPI Calculation
        future_price_KPI = future_price_KPI[future_price_KPI['time'].dt.year == selected_year]

        max_price_month = future_price_KPI.loc[future_price_KPI['price'].idxmax()]
        min_price_month = future_price_KPI.loc[future_price_KPI['price'].idxmin()]

        col1, col2, col3 = st.columns(3)
        best_month = max_price_month['time'].strftime("%B")
        worst_month = min_price_month['time'].strftime("%B")
        best_price = max_price_month['price']
        worst_price = min_price_month['price']

        if action == "Buy":
            with col1:
                st.metric(label=f"Best Month to {action}", value=worst_month)
                st.metric(label=f"Worst Month to {action}", value=best_month)
            with col2:
                st.metric(label=f"Estimated Price", value=f"${worst_price:,.0f}".replace(",", "."))
                st.metric(label=f"Estimated Price", value=f"${best_price:,.0f}".replace(",", "."))
            with col3:
                st.write("\n" * 10)
                st.write(f"Buying in {worst_month} would be ${best_price - worst_price:,.0f}".replace(",", ".") + " cheaper compared to buying in " + best_month + ".")
        elif action == "Sell":
            with col1:
                st.metric(label=f"Best Month to {action}", value=best_month)
                st.metric(label=f"Worst Month to {action}", value=worst_month)
            with col2:
                st.metric(label=f"Estimated Price", value=f"${best_price:,.0f}".replace(",", "."))
                st.metric(label=f"Estimated Price", value=f"${worst_price:,.0f}".replace(",", "."))
            with col3:
                st.write("\n" * 20)
                st.write(f"Selling in {best_month} would be ${best_price - worst_price:,.0f}".replace(",", ".") + " more profitable compared to selling in " + worst_month + ".")
        st.write("\n" * 5)

        # Select the granularity of the graph 
        granularity = st.selectbox("Select the time unit of the graph", ["Month", "Quarter", "Year"])
        st.write("\n" * 5)

        # Calculate the steps based on the granularity 
        if granularity == "Quarter":
            steps = (selected_date.year - today.year) * 4 + (selected_date.month - today.month) // 3
        elif granularity == "Month":
            steps = (selected_date.year - today.year) * 12 + selected_date.month - today.month
        elif granularity == "Year":
            steps = selected_date.year - today.year

        # Make prediction
        future_price_graph = make_prediction(data_filtered, steps, granularity)
        final_chart = prediction_graph(data_filtered, future_price_graph, granularity)
        
        # Display 
        st.altair_chart(final_chart, use_container_width=True)
        
    else:
        st.write("Please select a property type to make a prediction.")



    st.write("\n" * 5)


    # Form to add a new property
    if not st.session_state["guest_mode"]:
        with st.expander("➕ Add a new property sale record"):
            # Check authentication when expanding
            if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
                st.warning("You are not authenticated. Redirecting to login page...")
                st.session_state['page'] = 'login'
                st.session_state["authenticated"] = False
                st.rerun()

            with st.form("property_form"):
                st.write("Enter the property details")

                # Form fields
                property_type = st.selectbox("Property Type", ["House", "Unit"])
                price = st.number_input("Sale Price ($)", min_value=10000, step=5000, format="%d")
                postcode = st.text_input("Postcode", value="", max_chars=5)
                if postcode and not postcode.isdigit():
                    st.warning("Postcode must be numeric.")
                bedrooms = st.number_input("Number of Bedrooms", min_value=1, max_value=5, step=1)
                date_sold = st.date_input("Date Sold", min_value=pd.Timestamp("2007-02-07"), max_value=today)

                # Submit button
                if st.form_submit_button("Submit"):
                    # Check if all fields are complete
                    if all([property_type, price, postcode, bedrooms, date_sold]) and postcode.isdigit():
                        st.session_state["form_complete"] = True

                        # Data to add
                        new_entry = {
                            "property_type": property_type.lower(),
                            "price": price,
                            "postcode": postcode,
                            "bedrooms": bedrooms,
                            "date_sold": date_sold.strftime("%Y-%m-%d"),
                        }

                        DatabaseManager.insert_sale(new_entry)
                        st.success("Form successfully submitted!")
                    else:
                        st.warning("Please fill in all fields before submitting.")
    else:
        st.info("You need to log in to add property sale records.")



