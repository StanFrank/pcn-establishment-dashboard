import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import geopandas as gpd
import json


# --- 1. CONFIGURATION AND DATA STRUCTURES ---

# Define the data structure
PILLAR_KEYWORDS = {
    '1. Governance': [
        'PHC Advisory Committees', 'PCNs Established ', 'PCNs Gazetted',
        'Functional PCN Management Committee', 'Hospital Management Boards Appointed/Gazetted',
        'Health Facility Management Committee Appointed/Gazetted',
        'Availability of Functional PHC TWG',
        'Operational Budget for the PCN MDT activities',
        'Perfomance Review Score', 'CHMT Support Supervision Score',
        'Governance Score', 'Governance Weighted Score'
    ],
    '2. Human Resources for Health (HRH)': [
        'County Mechanism to Enhance Health Workers Skills',
        'HRH Score', 'HRH Weighted Score'
    ],
    '3. Health Product Technologies (HPT)': [
        'County Health Budget Allocated to Drugs & Supplies',
        'County HPT Budget Allocated to Levels 2&3',
        'HPT Score', 'HPT Weighted Score'
    ],
    '4. Service Delivery Systems': [
        'PCNs With Functional Referral Mechanisms',
        'Service Delivery Systems Score', 'Service Delivery Systems Weighted Score'
    ],
    '5. Healthcare Financing': [
        'Proportion Of Households Registered on SHA Within the County',
        'Healthcare Financing Score', 'Healthcare Financing Weighted Score'
    ],
    '6. HMIS/Digital Health': [
        'Proportion of Smart PCNs in the County',
        'HMIS Score', 'HMIS Weighted Score'
    ],
    '7. Quality of Care (QoC) - Management Systems': [
        'Mechanism to Coordinate Quality Improvement Score',
        'Mechanism for Implementation of Support Supervision in Health Facilities Score',
        'Presence of an Infection Prevention Control (IPC) committee Score',
        'QoC Management Systems Score', 'QoC Management Systems Weighted Score'
    ],
    '8. Multisectoral Partnerships and Coordination': [
        'Bi-Annual Multisectoral Stakeholder Forums Score',
        'Proportion of MOUs and partnership agreements aligned to PHC signed',
        'Research studies done on PCN implementation Score',
        'Multisectoral Partnerships and Coordination Score',
        'Multisectoral Partnerships and Coordination Weighted Score'
    ],
    '9. Innovations and Learning': [
        'Knowledge Management & Learning Forums Conducted Score',
        'Research Studies Done on PCN Implementation Score',
        'Innovations and Learning Score',
        'Innovations and Learning Weighted Score'
    ],
    '10. Overall Score': [
        'Total County Score (Total Weighted Score)',

    ]
}

# --- 2. DATA LOADING AND CLEANING FUNCTIONS ---
def standardize_name(name):
    """Applies ultra-aggressive cleaning to ensure name matching."""
    if pd.isna(name):
        return name
    
    # 1. Convert to string, strip surrounding whitespace, and convert to Title Case.
    name = str(name).strip().title()
    
    # 2. Normalize common separators and non-breaking spaces to a standard space.
    name = (
        name.replace('\xa0', ' ') # Non-breaking space
        .replace('/', ' ').replace('-', ' ')
        .replace('County', '').strip() # Remove 'County' suffix aggressively
    )
    
    # 3. Aggressively consolidate all multiple spaces into a single space.
    while '  ' in name:
        name = name.replace('  ', ' ')
        
    # 4. Apply specific edge-case mappings AFTER general cleaning (e.g., Nairobi City).
    # Since we removed 'County' above, we only need to catch the "City" part now.
    name_standardization_map = {
        'Nairobi City': 'Nairobi',
    }
    name = name_standardization_map.get(name, name)
        
    # 5. Final strip to eliminate any leading/trailing spaces.
    return name.strip()


# Group column headers into pillar dataframes.
def group_columns_by_pillar(df_raw, pillar_keywords):
    pillar_dfs = {}

    for pillar, keywords in pillar_keywords.items():
        matching_cols = ['County'] + [
            col for col in df_raw.columns
            # Check if any of a list of keywords appear inside a column name
            if any(keyword.lower() in col.lower() for keyword in keywords)
        ]

        if len(matching_cols) > 1:
            pillar_dfs[pillar] = df_raw[matching_cols].copy()

    return pillar_dfs



SHAPEFILE_PATH = "ken_admbnda_adm1_iebc_20191031.shp"

@st.cache_data
def load_and_clean_data(file_path):
    df_raw = pd.read_csv(file_path, encoding='ISO-8859-1')
    df_raw.columns = df_raw.columns.str.strip().str.replace('\n', ' ').str.replace('\r', '').str.replace(' +', ' ', regex=True)
    
    df = df_raw.head(47).copy()
    df = df.replace(['N/A', 'N\\A', '#DIV/0!', '', ' '], np.nan)
    
    score_cols = [col for col in df.columns if col != 'County']
    
    for col in score_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- CRITICAL FIX: Apply global standardization ---
    df['County'] = df['County'].apply(standardize_name)
    
    # Filtering (to prevent plotting zero-data counties)
    df_filtered = df.dropna(subset=score_cols, how='all').copy()
    df_county_clean = df_filtered.fillna(0).copy()
    
    pillar_dfs = group_columns_by_pillar(df_county_clean, PILLAR_KEYWORDS)
    
    return df_county_clean, pillar_dfs
    
@st.cache_data
def load_geodata(shp_path):
    
    try:
        gdf = gpd.read_file(shp_path)
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
            
        # Select and rename the key column
        gdf_clean = gdf[['ADM1_EN', 'geometry']].rename(columns={'ADM1_EN': 'County_Name_Key'})
        
        # --- CRITICAL FIX ---
        # Apply the standardization function directly to the GeoJSON names
        gdf_clean['County_Name_Key'] = gdf_clean['County_Name_Key'].apply(standardize_name)
        
        # Convert the GeoDataFrame to a Python GeoJSON dictionary object
        geojson_data = json.loads(gdf_clean.to_json())
        
        return geojson_data
    
    except Exception as e:
        st.error(f"Error loading geospatial data: {e}")
        return None

# =======================================================
# --- 3. EXECUTION BLOCK (LOAD DATA & SETUP) ---
# =======================================================

# Path to the main Shapefile (.shp) that geopandas will read
SHAPEFILE_PATH = "ken_admbnda_adm1_iebc_20191031.shp" 
geojson_data = None

# We must now use the key that corresponds to the renamed column in the GeoDataFrame
GEOJSON_COUNTY_KEY = "properties.County_Name_Key" 

try:
    # 1. Load and Clean CSV Data (KEEP THIS)
    # The county_lvl_data.csv MUST have its column names (p1_..., p2_..., etc.) 
    # match or contain the keywords in PILLAR_KEYWORDS.
    df_county_raw, pillar_dfs = load_and_clean_data(
        "county_lvl_data.csv"
    )

    # 2. Load and Convert Shapefile to GeoJSON Object (REPLACE FILE I/O WITH THIS)
    # You MUST have the .shp, .shx, .dbf, and .prj files in the same directory.
    # This function uses geopandas (gpd.read_file) to load the shapefile 
    # and then converts it to a GeoJSON dictionary in memory.
    geojson_data = load_geodata(SHAPEFILE_PATH)
    
    # Check if the GeoJSON object was successfully created
    if geojson_data is None:
        st.error("Error: Geospatial data could not be loaded or converted from Shapefile.")
        st.stop()
    
except FileNotFoundError as e:
    # This will now catch missing CSV or missing Shapefile components
    st.error(f"Error: A required file was not found: {e}. Check your file paths and ensure all Shapefile components are present.")
    st.stop()

except Exception as e:
    # Catch any other data processing error (including geopandas/CRS issues)
    st.error(f"An unexpected error occurred during data processing: {e}")
    st.stop()

# --- 4. STREAMLIT LAYOUT AND INTERACTIVITY ---

st.set_page_config(layout="wide", page_title="Kenya PCN Establishment Dashboard")
st.markdown(
    "<h1 style='text-align: center;'>Kenya PCN Establishment Dashboard</h1>",
    unsafe_allow_html=True
)
#st.title("County-Level PCN Establishment Analysis")
st.markdown(
    """
    <h1 style='text-align: left; color: #1E90FF;'>
        County-Level PCN Establishment Analysis
    </h1>
    """,
    unsafe_allow_html=True
)
st.markdown("""---""")

# Sidebar for Filter Selection
st.sidebar.header("Select Performance Metrics")

# 1. Get the list of available pillars
pillar_keys = list(pillar_dfs.keys())

# Check if there are any pillars loaded
if not pillar_keys:
    st.error("No pillar data was successfully loaded. Check data and column names.")
    st.stop()

# 1. Select the main Pillar e.g Governance, HRH, HPT
selected_pillar = st.sidebar.selectbox(
    "1. Select Pillar:",
    options=pillar_keys,
    index = 0 
)

# 2. Get the corresponding Pillar DataFrame
pillar_df = pillar_dfs[selected_pillar]

# 3. Get the list of indicators (columns) for the selected pillar
indicator_options = [col for col in pillar_df.columns if col != 'County']

# 4. Select the specific Indicator/Metric within that pillar
selected_indicator = st.sidebar.selectbox(
    "2. Select Indicator/Metric:",
    options=indicator_options # FIX 2: Correctly pass the list of column names
)


# --- 5. DUAL VISUALIZATION LAYOUT (Map and Bar Chart) ---

# Use columns for side-by-side visualization
col1, col2 = st.columns([1, 1])
# --- COLUMN 1: BAR CHART ---
with col1:
    st.subheader(f"Bar Chart")

    # Prepare data for the bar chart (use the correct pillar_df)
    df_chart = pillar_df[['County', selected_indicator]].sort_values(by=selected_indicator, ascending=False)
    
    # Create the Bar Chart using Plotly
    fig_bar = px.bar(
        df_chart,
        x='County',
        y=selected_indicator,
        color='County',
        text=selected_indicator,
        height=550,
        labels={selected_indicator: "Score (%)"},
        title=f"{selected_pillar} - {selected_indicator}"
    )
    
    fig_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig_bar.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis={'categoryorder':'total descending'})
    
    st.plotly_chart(fig_bar, use_container_width=True)

# --- COLUMN 2: MAP ---
with col2:
    st.subheader("Geographic Map")

    KENYA_CENTER = {"lat": 0.5, "lon": 37.9}

    if geojson_data is None or GEOJSON_COUNTY_KEY is None:
        st.error("Map visualization cannot load: Geospatial data is missing.")
    else:
        # --- 1. DATA PREPARATION ---
        geojson_counties = [
            feature['properties']['County_Name_Key']
            for feature in geojson_data['features']
        ]

        df_all_counties = pd.DataFrame({'County': geojson_counties})
        df_score_data = pillar_df[['County', selected_indicator]].copy()
        df_map_data = df_all_counties.merge(df_score_data, on='County', how='left')

        # --- 2. CREATE MAP ---
        # Fill NaN with 0 temporarily (so they render as the lowest value)
        df_map_data[selected_indicator] = df_map_data[selected_indicator].fillna(0)

        fig_map = px.choropleth_mapbox(
            df_map_data,
            geojson=geojson_data,
            locations='County',
            featureidkey=GEOJSON_COUNTY_KEY,
            color=selected_indicator,
            hover_name='County',
            color_continuous_scale="RdYlGn",
            mapbox_style="white-bg",
            zoom=5.0,
            center=KENYA_CENTER,
            opacity=0.8,
            labels={'County': 'County', selected_indicator: 'Score (%)'},
        )

        # --- 3. REFINEMENT & STYLING ---
        fig_map.update_traces(
            marker_line_width=0.5,
            marker_line_color="white",
            hovertemplate="<b>%{location}</b><br>Score: %{z:.1f}%<extra></extra>",
            marker=dict(opacity=0.85),
        )

        fig_map.update_layout(
            margin={"r":0, "t":30, "l":0, "b": 0},
            coloraxis_colorbar=dict(
                title=selected_indicator,
                tickformat=".0f",
                title_side="right",
            ),
        )
        # --- 4. Manually make missing data appear white ---
        for trace in fig_map.data:
            if hasattr(trace, "marker"):
                trace.marker.missing = {"color": "white"}
        
        
        
        st.plotly_chart(fig_map, use_container_width=True)

st.markdown("""---""")

st.header("County Data Table")
# Use the filtered pillar_df for the table

st.dataframe(pillar_df.sort_values(by='County'), use_container_width=True)

































































