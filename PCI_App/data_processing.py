import pandas as pd
from datetime import datetime

# Function to process boarding data
def process_boarding(file):
    df = pd.read_excel(file)
    df = df.dropna(how='all', axis=1)
    df = df[df['Pet Companions, inc.'].notna()]
    df.reset_index(drop=True, inplace=True)
    df.rename(columns={'Pet Companions, inc.':'Client', 'Unnamed: 8':'Pet', 
                       'Unnamed: 15': 'In-Date', 'Unnamed: 21':'Out-Date'}, inplace=True)
    df = df[['Client', 'Pet', 'In-Date', 'Out-Date']]
    df = df.drop(0).reset_index(drop=True)

    # Convert In-Date and Out-Date to datetime format
    df['In-Date'] = pd.to_datetime(df['In-Date'])
    df['Out-Date'] = pd.to_datetime(df['Out-Date'])
    
    # Create a new dataframe to expand the rows
    expanded_rows = []
    
    for i, row in df.iterrows():
        visit_days = pd.date_range(row['In-Date'], row['Out-Date'], freq='D')
            
        for visit_day in visit_days:
            if visit_day == row['In-Date']: 
                board_type = 'arriving'
            elif visit_day == row['Out-Date']:
                board_type = 'departing'
            else: 
                board_type = 'ongoing'
                
            expanded_rows.append({
                'Date': visit_day,
                'Day of Week': pd.Timestamp(visit_day).day_name(),  # Convert to pandas Timestamp for day_name()
                'Client': row['Client'],
                'Pet': row['Pet'],
                'Visit Type': 'boarding',
                'board_type': board_type
            })
    
    expanded_df = pd.DataFrame(expanded_rows)
    expanded_df = expanded_df.sort_values(by='Date', ascending=True).reset_index(drop=True)
    return expanded_df

# Function to process daycare data
def process_daycare(file):
    daycare_df = pd.read_excel(file)
    daycare_df = daycare_df.dropna(how='all', axis=1).dropna(how='all', axis=0)
    daycare_df.rename(columns={'Pet Companions, inc.': 'Data'}, inplace=True)
    daycare_df = daycare_df[daycare_df['Data'].notna()][['Data']].reset_index(drop=True).drop(0).reset_index(drop=True)

    def is_date(value):
        if isinstance(value, datetime):
            return True
        try:
            datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return True
        except (ValueError, TypeError):
            return False
    
    current_date = None
    rows = []
    
    for i in range(len(daycare_df)):
        row_data = daycare_df.loc[i, 'Data']
        if is_date(row_data):
            current_date = pd.Timestamp(row_data)  # Convert to pandas Timestamp
        elif ':' in row_data:
            client, pet = row_data.split(': ')
            rows.append({
                'Date': current_date,
                'Day of Week': current_date.day_name(),  # Use pandas Timestamp day_name()
                'Client': client,
                'Pet': pet,
                'Visit Type':'daycare',
                'board_type': None
            })
    
    output_df = pd.DataFrame(rows)
    return output_df

# Function to aggregate data
def aggregate_data(df1, df2):
    # Concatenate the two dataframes
    df = pd.concat([df1, df2])
    
    # Sort the dataframe by 'Date' and 'Visit Type'
    sorted_df = df.sort_values(by=['Date', 'Visit Type'], ascending=True).reset_index(drop=True)
    
    # Group by 'Date' and aggregate the counts for each column
    aggregated_df = sorted_df.groupby('Date').agg(
        daycare_visits=('Visit Type', lambda x: (x == 'daycare').sum()),
        boarding_visits=('Visit Type', lambda x: (x == 'boarding').sum()),
        arriving_count=('board_type', lambda x: (x == 'arriving').sum()),
        ongoing_count=('board_type', lambda x: (x == 'ongoing').sum()),
        departing_count=('board_type', lambda x: (x == 'departing').sum())
    ).reset_index()

    # Add the 'headcount' column with the specified formula
    aggregated_df['headcount'] = (
        aggregated_df['daycare_visits'] + 
        aggregated_df['arriving_count'] + 
        aggregated_df['ongoing_count'] + 
        0.5 * aggregated_df['departing_count']
    )
    
    # Add the day of the week to the aggregated dataframe
    aggregated_df['Day of Week'] = aggregated_df['Date'].dt.day_name()
    
    # Return both sorted_df and aggregated_df
    return sorted_df, aggregated_df

