import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Config
st.set_page_config(page_title="PM2.5 Patient Monitor", layout="wide")

# 2. Data Loading Functions
@st.cache_data
def get_station_data():
    df = pd.read_csv('./pm_mock.csv')
    df['date'] = pd.to_datetime(df['date']).dt.date
    return df

@st.cache_data
def get_patient_data():
    return pd.read_csv('./patient_mock.csv')

station_df = get_station_data()
patient_df = get_patient_data()

# 3. Sidebar Filters
st.sidebar.header("Dashboard Filters")
available_dates = sorted(station_df['date'].unique(), reverse=False)
selected_date = st.sidebar.selectbox("Select Date", available_dates)

# 4. Processing Logic
# Step A: Filter stations for the date and PM2.5 > 50
high_pollution_stations = station_df[
    (station_df['date'] == selected_date) & (station_df['pm25'] > 50)
]

# Step B: Get unique list of affected Amphoes
affected_amphoes = high_pollution_stations['amphoe'].unique()

# Step C: Merge Patient data with Station data based on Amphoe
# This identifies patients living in the high PM2.5 districts
final_df = pd.merge(
    high_pollution_stations, 
    patient_df, 
    on=['province', 'amphoe'], 
    how='inner'
)

# 5. UI Layout
st.title("🏥 PM2.5 & Patient Risk Dashboard")
st.info(f"On **{selected_date}**: Found **{len(affected_amphoes)}** amphoes with PM2.5 more than 50.")

st.subheader("📍 PM2.5 Map")
map_center = {"lat": station_df['dustboy_lat'].mean(), "lon": station_df['dustboy_lon'].mean()}
fig = px.scatter_mapbox(
    high_pollution_stations if not high_pollution_stations.empty else None,
    lat="dustboy_lat",
    lon="dustboy_lon",
    color="pm25",
    size="pm25",
    hover_name="amphoe",
    hover_data=["province", "amphoe", "pm25"],
    color_continuous_scale="Reds",
    zoom=6.5,
    height=500
)

# 3. Apply styling (This runs even if the dataframe is empty)
fig.update_layout(
    mapbox_style="open-street-map", 
    mapbox_center=map_center, 
    margin={"r":0,"t":0,"l":0,"b":0}
)

# 4. Only update traces if there is actually data to format
if not high_pollution_stations.empty:
    fig.update_traces(
        hovertemplate='<b>อ.%{hovertext} จ.%{customdata[0]}</b><br>PM2.5: %{marker.size:.0f}',
        selected_marker_opacity=1.0,      # Fully solid when clicked
        unselected_marker_opacity=0.35
    )
else:
    fig.add_annotation(text="No high pollution areas detected", 
                  showarrow=False, font_size=20)

event = st.plotly_chart(fig, on_select="rerun", use_container_width=True)

if event and "selection" in event and event["selection"]["points"]:
    # Extract the 'hover_name' or custom data from the clicked point
    # In your map, hover_name was "amphoe"
    selected_amphoe = event["selection"]["points"][0]["hovertext"]
    
    st.info(f"Showing patients in: **{selected_amphoe}**")
    
    # 3. Filter your patient dataframe based on the click
    display_df = final_df[final_df['amphoe'] == selected_amphoe][['province', 'amphoe', 'cid', 'age', 'sex']]
    
    if not display_df.empty:
        st.dataframe(display_df, use_container_width=True)
    else:
        st.write(f"No patient data found for {selected_amphoe}.")

else:
    # Default state when nothing is clicked
    st.write("Click a station on the map to view local patient data.")