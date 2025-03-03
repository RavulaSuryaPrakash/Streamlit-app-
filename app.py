import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
from google.cloud import bigquery
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import seaborn as sns

# Configure Streamlit page
st.set_page_config(page_title="San Jose Traffic Analysis", layout="wide")

project_id = st.secrets["bigquery"]["project"]
# Initialize BigQuery Client
client = bigquery.Client(project=project_id)

# Query to fetch processed data from BigQuery
query = """
SELECT 
    STREETONE, LATITUDE, LONGITUDE, ADT, COUNTDATE, CITY
FROM `homework-2-452521.Average_Daily_Traffic.AverageDailyTraffic`
"""
df = client.query(query).to_dataframe()

# Convert COUNTDATE to datetime and remove timezone information
df["COUNTDATE"] = pd.to_datetime(df["COUNTDATE"]).dt.tz_localize(None)

# Sidebar: User Input Filters
st.sidebar.header("Filter Data")

# Date range inputs
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2005-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2021-12-31"))

# Convert to naive timestamps
start_date = pd.Timestamp(start_date).tz_localize(None)
end_date = pd.Timestamp(end_date).tz_localize(None)

# Filter by date range
df_filtered = df[
    (df["COUNTDATE"] >= start_date) &
    (df["COUNTDATE"] <= end_date)
].copy()

# Display filtered data
st.title("San Jose Traffic Analysis")
st.write("Filtered Traffic Data", df_filtered.head())

###############################################
# Bar Chart: Top 10 Busiest Streets by ADT
###############################################
st.subheader("Top 10 Busiest Streets in San Jose by ADT")

if not df_filtered.empty:
    # Aggregate ADT per street using the filtered data
    top_streets = df_filtered.groupby("STREETONE")["ADT"].mean().reset_index()
    top_streets = top_streets.sort_values(by="ADT", ascending=False).head(10)
    
    # Create bar chart with Seaborn
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x="ADT", y="STREETONE", data=top_streets, palette="Blues_r", ax=ax)
    ax.set_xlabel("Average Daily Traffic (ADT)")
    ax.set_ylabel("Street Name")
    ax.set_title("Top 10 Busiest Streets in San Jose by ADT")
    st.pyplot(fig)
else:
    st.write("No data available for the selected date range.")

###############################################
# Area Chart: Traffic Volume Over Time
###############################################
st.subheader("Traffic Trends Over Time (Area Chart)")

if not df_filtered.empty:
    # Extract Year from COUNTDATE
    df_filtered["Year"] = df_filtered["COUNTDATE"].dt.year
    
    # Aggregate ADT by year
    df_yearly = df_filtered.groupby("Year")["ADT"].mean().reset_index()
    
    if not df_yearly.empty:
        # Ensure continuous x-axis by including all years in the range
        all_years = np.arange(df_yearly["Year"].min(), df_yearly["Year"].max() + 1)
        df_yearly = df_yearly.set_index("Year").reindex(all_years).interpolate().reset_index()

        # Create area chart
        fig2, ax2 = plt.subplots(figsize=(15, 6))
        ax2.fill_between(df_yearly["Year"], df_yearly["ADT"], color="skyblue", alpha=0.5)
        ax2.plot(df_yearly["Year"], df_yearly["ADT"], marker="o", color="blue")
        ax2.set_xticks(all_years)
        ax2.set_xticklabels(all_years, rotation=45, ha="right")
        ax2.set_xlabel("Year")
        ax2.set_ylabel("Average Daily Traffic (ADT)")
        ax2.set_title("Traffic Volume Over Time (Area Chart)")
        ax2.grid(True)
        st.pyplot(fig2)
    else:
        st.write("No yearly data available for the selected date range.")
else:
    st.write("No data available for the selected date range.")

###############################################
# Heatmap: Traffic Hotspots in San Jose
###############################################
st.subheader("Traffic Hotspots in San Jose (Heatmap)")

if not df_filtered.empty:
    # Drop rows with missing LATITUDE, LONGITUDE, or ADT
    df_filtered_clean = df_filtered.dropna(subset=["LATITUDE", "LONGITUDE", "ADT"])
    
    if not df_filtered_clean.empty:
        # Initialize folium map centered on San Jose
        m = folium.Map(location=[37.3382, -121.8863], zoom_start=12)

        # Prepare heatmap data
        heat_data = df_filtered_clean[["LATITUDE", "LONGITUDE", "ADT"]].values.tolist()

        # Add HeatMap layer
        HeatMap(heat_data, radius=15, blur=10).add_to(m)

        # Display the map in Streamlit
        folium_static(m)
    else:
        st.write("No valid location data available for the selected date range.")
else:
    st.write("No data available for the selected date range.")
