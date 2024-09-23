import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.title("Expired Vaccinations Data")

# File upload section
uploaded_file = st.file_uploader("Upload Expired Vaccinations Excel File", type=['xls', 'xlsx'])

# Proceed if a file is uploaded
if uploaded_file is not None:
    # Load the uploaded file
    df = pd.read_excel(uploaded_file)

    # Rename columns appropriately
    df.rename(columns={'Unnamed: 4': 'Client', 'Unnamed: 6': 'Pet', 
                       'Unnamed: 11': 'Vaccination', 'Unnamed: 16': 'Phone Number', 'Unnamed: 19': 'Expiration Date'}, inplace=True)

    # Select relevant columns
    df = df[['Client', 'Pet', 'Vaccination', 'Phone Number', 'Expiration Date']]

    # Drop columns and rows with all NaN values
    df = df.dropna(how='all', axis=1)
    df = df.dropna(how='all', axis=0)
    df.reset_index(drop=True, inplace=True)

    # Step 1: Find the index where 'Client' equals 'Owner'
    owner_index = df[df['Client'] == 'Owner'].index[0]

    # Step 2: Slice the dataframe starting from the row after 'Owner'
    df = df.iloc[owner_index+1:].reset_index(drop=True)

    # Step 3: Fill down 'Client', 'Phone Number', and 'Pet' information for subsequent rows using ffill()
    df['Client'] = df['Client'].ffill()
    df['Phone Number'] = df['Phone Number'].ffill()
    df['Pet'] = df['Pet'].ffill()

    # Step 4: Drop rows that do not have vaccination information
    df = df.dropna(subset=['Vaccination', 'Expiration Date'], how='all')

    # Display available data range
    data_start = df['Expiration Date'].min()
    data_end = df['Expiration Date'].max()
    st.write(f"### Available data from: {data_start.date()} to {data_end.date()}")

    # Get today's date and one year ago
    today = pd.Timestamp(datetime.now().date())
    one_year_ago = today - timedelta(days=365)

    # Allow the user to select lookback period (by days or by start date)
    selection_method = st.radio("Choose how to select the lookback period:", ("Slider (Days)", "Calendar (Start Date)"))

    if selection_method == "Slider (Days)":
        # Slider for lookback days
        st.subheader("Select Time Period to Look Back (Days)")
        lookback_days = st.slider("Select how many days to look back:", min_value=7, max_value=365, value=30)

        # Calculate the date range for the past
        lookback_date = today - timedelta(days=lookback_days)

    elif selection_method == "Calendar (Start Date)":
        # Date picker for the start date of the lookback period with default set to one year ago
        st.subheader("Select Start Date for Lookback")
        lookback_date = st.date_input("Pick a start date", min_value=data_start.date(), max_value=today.date(), value=one_year_ago.date())
        lookback_date = pd.Timestamp(lookback_date)  # Convert to pandas.Timestamp

    # Add an end date picker for the future, defaulting to today's date
    st.subheader("Select End Date for Future Vaccinations")
    end_date = st.date_input("Pick an end date", min_value=lookback_date.date(), max_value=today.date(), value=today.date())
    end_date = pd.Timestamp(end_date)  # Convert to pandas.Timestamp

    # Filter the data based on the lookback period and end date
    df_filtered = df[(df['Expiration Date'] >= lookback_date) & (df['Expiration Date'] <= end_date)]

    # Step 5: Group by Client and Pet
    final_df = df_filtered.groupby(['Client', 'Pet', 'Phone Number']).agg({
        'Vaccination': lambda x: ', '.join(df.loc[x.index, 'Expiration Date'].dt.strftime('%Y-%m-%d') + ' ' + x),  # Concatenate date space vaccination
        'Expiration Date': 'min'  # Get the earliest expiration date
    }).reset_index()

    # Rename the columns for clarity
    final_df.columns = ['Client', 'Pet', 'Phone Number', 'Vaccination Info', 'Earliest Expiration']

    # Sort by 'Earliest Expiration' in ascending order
    final_df = final_df.sort_values(by='Earliest Expiration', ascending=True).reset_index(drop=True)

    # Display the final dataframe
    st.write(final_df)

    # Optional: Save the final dataframe to a CSV file
    final_df.to_csv('final_output.csv', index=False)

    # Provide a download button for the user
    csv = final_df.to_csv(index=False)
    st.download_button(
        label="Download Data as CSV",
        data=csv,
        file_name='final_output.csv',
        mime='text/csv',
    )
