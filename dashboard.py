import streamlit as st
import pandas as pd
import awswrangler as wr
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Sensorlynk - City Command Center",
    page_icon="🚨",
    layout="wide",
)

# --- App Title ---
st.title("🚨 Sensorlynk - Smart City Command Center")
st.markdown("Live environmental data from our city-wide sensor network.")

# --- AWS Configuration ---
# Make sure this is updated with your ACTUAL Athena query result location from the Athena console settings.
S3_OUTPUT_LOCATION = "s3://sensorlynk-athena-results-2025/" 
DATABASE = "city_intelligence_db"
TABLE = "environmental_data"

# --- Data Loading Function ---
@st.cache_data(ttl=15) # Cache the data for 15 seconds to avoid re-querying too often
def load_data():
    """Function to load data from Athena."""
    query = f'SELECT * FROM "{TABLE}"'
    # The ctas_approach=False parameter prevents the library from trying to create/delete tables in Glue.
    df = wr.athena.read_sql_query(query, database=DATABASE, ctas_approach=False, s3_output=S3_OUTPUT_LOCATION)
    # We explicitly tell pandas the timestamp is in milliseconds ('ms').
    df['server_timestamp'] = pd.to_datetime(df['server_timestamp'], unit='ms') 
    return df

# --- Main App Logic ---
try:
    df = load_data()

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Options")
    # Ensure there's at least one option before creating the selectbox
    locations = df['location'].unique()
    if len(locations) > 0:
        selected_location = st.sidebar.selectbox(
            "Select a Location:",
            options=locations,
            index=0
        )
        filtered_df = df[df['location'] == selected_location]

        # --- Key Metrics (KPIs) ---
        st.header(f"Live Status for: {selected_location}")
        latest_data = filtered_df.sort_values(by="server_timestamp", ascending=False).iloc[0]

        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Latest Air Quality (AQI)", value=f"{latest_data['aqi']}", delta_color="inverse")
        with col2:
            st.metric(label="Latest Noise Level (dB)", value=f"{latest_data['noise_level']}", delta_color="inverse")

        # --- Charts and Map ---
        st.subheader("Live Sensor Map")
        # Corrected line: We add .astype(float) to convert specialized numpy floats to standard Python floats.
        st.map(filtered_df[['latitude', 'longitude']].astype(float).rename(columns={'latitude':'lat', 'longitude':'lon'}))

        st.subheader("Air Quality Trend (AQI)")
        st.line_chart(filtered_df.set_index('server_timestamp')['aqi'])

        st.subheader("Noise Level Trend (dB)")
        st.line_chart(filtered_df.set_index('server_timestamp')['noise_level'])

        # --- Raw Data View ---
        if st.checkbox("Show Raw Sensor Data"):
            st.subheader("Raw Data")
            st.write(filtered_df.sort_values(by="server_timestamp", ascending=False))
    else:
        st.info("No data available yet. Please wait for the simulator to send data.")


except Exception as e:
    st.error(f"An error occurred: {e}")
    st.info("Waiting for new data... The dashboard will refresh automatically.")

# --- Auto-refresh logic ---
time.sleep(15)
st.rerun()