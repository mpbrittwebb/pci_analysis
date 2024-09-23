import streamlit as st
import pandas as pd
from data_processing import process_boarding, process_daycare, aggregate_data
from datetime import datetime

st.title("Occupancy Analysis")

# File upload section
st.subheader("Upload Excel Files")

# Accept both .xls and .xlsx file types
file1 = st.file_uploader("Upload Total Days Boarded Excel File", type=['xls', 'xlsx'])
file2 = st.file_uploader("Upload Daycare Weekly Report Excel File", type=['xls', 'xlsx'])

if file1 and file2:
    st.success("Both files successfully uploaded!")
    
    # Process boarding and daycare data
    boarding_df = process_boarding(file1)
    daycare_df = process_daycare(file2)
    sorted_df, aggregated_df = aggregate_data(boarding_df, daycare_df)
    
    # Get the available data range
    data_start = sorted_df['Date'].min()
    data_end = sorted_df['Date'].max()

    # Get today's date
    today = pd.Timestamp(datetime.now().date())
    
    # Show the available data range to users
    st.write(f"### Available data from: {data_start.date()} to {data_end.date()}")
    
    # Date filtering section with default values set to today's date
    st.subheader("Select Date Range")
    start_date = st.date_input(
        "Start Date", 
        min_value=data_start.date(), 
        max_value=data_end.date(), 
        value=today.date()  # Default start date set to today
    )
    
    end_date = st.date_input(
        "End Date", 
        min_value=data_start.date(), 
        max_value=data_end.date(), 
        value=today.date()  # Default end date set to today
    )
    
    # Convert start_date and end_date to pandas Timestamps for comparison
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    # Check if the selected date range has no data
    if start_date < data_start or end_date > data_end:
        st.warning(f"Selected date range is outside available data. Data starts from {data_start.date()} and ends on {data_end.date()}.")
    else:
        # Filter the data based on selected dates
        filtered_df = aggregated_df[(aggregated_df['Date'] >= start_date) &
                                    (aggregated_df['Date'] <= end_date)]
        
        # Display results
        st.write("### Aggregated Dataframe", filtered_df)
        
        # Download the output
        st.subheader("Download the output")
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name='aggregated_data.csv',
            mime='text/csv',
        )
