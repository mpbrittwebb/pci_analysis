import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_processing import process_boarding, process_daycare

st.title("Suggested Bookings")

# Placeholder for instructions
st.markdown("""
This page identifies clients who have visited in the past but do not have any future bookings.
You can select a time period to filter past visits and identify these clients.
""")

# File upload section for boarding and daycare data
st.subheader("Upload Excel Files")

# Accept both .xls and .xlsx file types
file1 = st.file_uploader("Upload Total Days Boarded Excel File", type=['xls', 'xlsx'])
file2 = st.file_uploader("Upload Daycare Weekly Report Excel File", type=['xls', 'xlsx'])

if file1 and file2:
    st.success("Both files successfully uploaded!")
    
    # Process the uploaded files to generate the sorted_df
    boarding_df = process_boarding(file1)
    daycare_df = process_daycare(file2)
    sorted_df = pd.concat([boarding_df, daycare_df]).sort_values(by=['Date', 'Visit Type'], ascending=True).reset_index(drop=True)
    
    # Get the available data range
    data_start = sorted_df['Date'].min()
    data_end = sorted_df['Date'].max()
    
    # Show the available data range to users
    st.write(f"### Available data from: {data_start.date()} to {data_end.date()}")
    
    # User selects whether to use a slider or calendar
    selection_method = st.radio("Choose how to select the lookback period:", ("Slider (Days)", "Calendar (Start Date)"))

    if selection_method == "Slider (Days)":
        # Slider for lookback days
        st.subheader("Select Time Period to Look Back (Days)")
        lookback_days = st.slider("Select how many days to look back:", min_value=7, max_value=365, value=30)

        # Calculate the date range for the past
        current_date = pd.Timestamp(datetime.now().date())
        lookback_date = current_date - timedelta(days=lookback_days)

    elif selection_method == "Calendar (Start Date)":
        # Date picker for the start date of the lookback period
        st.subheader("Select Start Date for Lookback")
        lookback_date = st.date_input("Pick a start date", min_value=data_start.date(), max_value=data_end.date(), value=data_start.date())
        lookback_date = pd.Timestamp(lookback_date)  # Convert to pandas.Timestamp
        current_date = pd.Timestamp(datetime.now().date())  # Set current date for comparison

    # Check if the selected lookback date has no data
    if lookback_date < data_start:
        st.warning(f"Selected lookback period is outside the available data. Data starts from {data_start.date()}.")
    else:
        # Separate the dataframe into past and future visits based on the selected lookback period
        df_past = sorted_df[(sorted_df['Date'] <= current_date) & (sorted_df['Date'] >= lookback_date)]
        df_future = sorted_df[sorted_df['Date'] > current_date]
    
        # Group by 'Client' to get booking statistics for past data
        client_summary_past = df_past.groupby('Client').agg(
            total_visits=('Date', 'count'),  # Total number of visits in the past
            last_visit=('Date', 'max')       # Most recent visit date in the past
        ).reset_index()
    
        # Group by 'Client' to check if they have any future bookings
        client_summary_future = df_future.groupby('Client').agg(
            future_visits=('Date', 'count')  # Count of future visits
        ).reset_index()
    
        # Merge past and future data on 'Client'
        client_summary = pd.merge(client_summary_past, client_summary_future, on='Client', how='left')
    
        # Fill NaN values in 'future_visits' with 0 for clients without future bookings
        client_summary['future_visits'].fillna(0, inplace=True)
    
        # Determine if the client has any future bookings
        client_summary['has_future_booking'] = np.where(client_summary['future_visits'] > 0, 'Yes', 'No')
    
        # Filter to only show clients with no future bookings
        suggested_bookings = client_summary[client_summary['has_future_booking'] == 'No']
    
        # Display the suggested bookings
        st.write("### Clients with No Future Bookings")
        st.write(suggested_bookings)
    
        # Download the suggested bookings as CSV
        csv = suggested_bookings.to_csv(index=False)
        st.download_button(
            label="Download Suggested Bookings as CSV",
            data=csv,
            file_name='suggested_bookings.csv',
            mime='text/csv',
        )
