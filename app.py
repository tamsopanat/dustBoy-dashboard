import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Config
st.set_page_config(page_title="PM2.5 Patient Monitor", layout="wide")

# 2. Data Loading Functions
@st.cache_data
def get_station_data():
    df = pd.read_csv('./data/amphoe_pm.csv')
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
    (station_df['date'] == selected_date) & (station_df['log_pm25'] > 50)
].copy()
high_pollution_stations['pm25_visual'] = high_pollution_stations['log_pm25'].clip(upper=600)
high_pollution_stations = high_pollution_stations.reset_index(drop=True)


if "selected_province" not in st.session_state:
    st.session_state.selected_province = None
if "selected_amphoe" not in st.session_state:
    st.session_state.selected_amphoe = None
if "selected_indices" not in st.session_state:
    st.session_state.selected_indices = None

st.sidebar.header("⚠️ Critical Areas (> 50)")
critical_list = sorted(high_pollution_stations['amphoe'].unique())

if not critical_list:
    st.sidebar.success("No areas exceed 50 PM2.5")
else:
    provinces = sorted(high_pollution_stations['province'].unique())
    p_index = None
    if st.session_state.get("selected_province") in provinces:
        p_index = provinces.index(st.session_state.selected_province)
    sb_province = st.sidebar.selectbox(
        "1. Select province:",
        options=provinces,
        index=p_index,
    )
    st.session_state.selected_province = sb_province
    if sb_province:
        available_amphoes = sorted(
            high_pollution_stations[high_pollution_stations['province'] == sb_province]['amphoe'].unique()
        )
        a_index = None
        if st.session_state.get("selected_amphoe") in available_amphoes:
            a_index = available_amphoes.index(st.session_state.selected_amphoe)            
        sb_amphoe = st.sidebar.selectbox(
            f"2. Select amphoe in {sb_province}:",
            options=available_amphoes,
            index=a_index,
        )
        st.session_state.selected_amphoe = sb_amphoe

final_df = pd.merge(
    high_pollution_stations, 
    patient_df, 
    on=['province', 'amphoe'], 
    how='inner'
)

# 5. UI Layout
st.title("🏥 PM2.5 & Patient Risk Dashboard")
st.info(f"On **{selected_date}**: Found **{len(critical_list)}** amphoes with PM2.5 more than 50.")

st.subheader("📍 PM2.5 Map")
map_center = {"lat": station_df['location_lat'].mean(), "lon": station_df['location_lon'].mean()}
fig = px.scatter_mapbox(
    high_pollution_stations,
    lat="location_lat",
    lon="location_lon",
    color="log_pm25",
    size="pm25_visual",
    hover_name="amphoe",
    hover_data=["province", "amphoe", "log_pm25"],
    color_continuous_scale="Reds",
    range_color=[0, 200],
    zoom=5.5,
    height=700
)

fig.update_layout(
    coloraxis_showscale=False,
    # clickmode='event+select',
    mapbox_style="open-street-map", 
    mapbox_center=map_center, 
    margin={"r":0,"t":0,"l":0,"b":0}
)

if st.session_state.get("selected_amphoe"):
    print(f"Selected Amphoe: {st.session_state.selected_amphoe}, Province: {st.session_state.selected_province}")
    matched_rows = high_pollution_stations[
        (high_pollution_stations['amphoe'] == st.session_state.selected_amphoe) & 
        (high_pollution_stations['province'] == st.session_state.selected_province)
    ]
    print(matched_rows)
    
    st.session_state.selected_indices = matched_rows.index.tolist()

if not high_pollution_stations.empty:
    fig.update_traces(
        selectedpoints=st.session_state.selected_indices,
        hovertemplate='<b>อ.%{hovertext} จ.%{customdata[0]}</b><br>PM2.5: %{customdata[2]:.0f}',
        selected_marker_opacity=1.0,
        unselected_marker_opacity=0.35
    )
else:
    fig.add_annotation(text="No high pollution areas detected", 
                       showarrow=False, font_size=20)

event = st.plotly_chart(fig, on_select="rerun", width='stretch')

if event and "selection" in event and event["selection"]["points"]:
    point = event["selection"]["points"][0]
    map_amphoe = point["customdata"][1]
    map_province = point["customdata"][0]
    
    if st.session_state.selected_amphoe != map_amphoe and st.session_state.selected_province != map_province:
        st.session_state.selected_amphoe = map_amphoe
        st.session_state.selected_province = map_province
        st.rerun()
        
if st.session_state.selected_amphoe:
    st.info(f"Showing risk patients in: **อ.{st.session_state.selected_amphoe} จ.{st.session_state.selected_province}**")
    
    display_df = final_df[
        (final_df['amphoe'] == st.session_state.selected_amphoe) & (final_df['province'] == st.session_state.selected_province)
    ][['cid', 'age', 'sex']].drop_duplicates()
    
    if not display_df.empty:
        st.dataframe(display_df, width='stretch')
    else:
        st.write(f"No patient data found")

else:
    st.write("📍 Click a station on the map or select from the sidebar to view risk patient data.")