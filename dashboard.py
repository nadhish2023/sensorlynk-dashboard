import streamlit as st
import pandas as pd
import awswrangler as wr
import time
import os
import boto3

# --- Page Configuration ---
st.set_page_config(page_title="Sensorlynk Command Center", page_icon="🚨", layout="wide")

# --- AWS Configuration ---
aws_access_key_id = os.environ.get('APP_AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('APP_AWS_SECRET_ACCESS_KEY')
aws_region = os.environ.get('APP_AWS_DEFAULT_REGION', 'ap-south-1')

# Create a boto3 session with these credentials
# This is the key to using custom env vars with awswrangler
boto3_session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

S3_OUTPUT_LOCATION = "s3://sensorlynk-athena-results-2025/"
DATABASE = "city_intelligence_db"
TABLE = "environmental_data"

# --- App Title ---
st.title("🚨 Sensorlynk - Smart City Command Center")
st.markdown("Live environmental data from our city-wide sensor network.")

# --- Data Loading Function ---
@st.cache_data(ttl=15)
def load_data():
    query = f'SELECT * FROM "{TABLE}"'
    # Pass the custom boto3 session to awswrangler
    df = wr.athena.read_sql_query(query, database=DATABASE, ctas_approach=False, s3_output=S3_OUTPUT_LOCATION, boto3_session=boto3_session)
    df['server_timestamp'] = pd.to_datetime(df['server_timestamp'], unit='ms')
    return df

# --- Main App Logic ---
try:
    df = load_data()
    st.sidebar.header("Filter Options")
    locations = df['location'].unique()
    if len(locations) > 0:
        selected_location = st.sidebar.selectbox("Select a Location:", options=locations)
        filtered_df = df[df['location'] == selected_location]
        latest_data = filtered_df.sort_values(by="server_timestamp", ascending=False).iloc[0]
        
        st.header(f"Live Status for: {selected_location}")
        col1, col2 = st.columns(2)
        col1.metric(label="Latest Air Quality (AQI)", value=f"{latest_data['aqi']}")
        col2.metric(label="Latest Noise Level (dB)", value=f"{latest_data['noise_level']}")
        
        st.subheader("Live Sensor Map")
        st.map(filtered_df[['latitude', 'longitude']].astype(float).rename(columns={'latitude':'lat', 'longitude':'lon'}))
        
        st.subheader("Air Quality Trend (AQI)")
        st.line_chart(filtered_df.set_index('server_timestamp')['aqi'])
        
        st.subheader("Noise Level Trend (dB)")
        st.line_chart(filtered_df.set_index('server_timestamp')['noise_level'])
        
        if st.checkbox("Show Raw Sensor Data"):
            st.write(filtered_df.sort_values(by="server_timestamp", ascending=False))
    else:
        st.info("No data available yet. Please wait for the simulator to send data.")
except Exception as e:
    st.error(f"An error occurred: {e}")
    st.info("Waiting for new data...")

time.sleep(15)
st.rerun()