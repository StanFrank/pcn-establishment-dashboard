import pandas as pd
import streamlit as st
import numpy as np
import json
import plotly.express as px
import io
# import geopandas as gpd # NOTE: geopandas is not needed for Plotly choropleth with GeoJSON

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

@st.cache_data
def load_and_clean_data(file_path):
    # Load the raw data
    df_raw = pd.read_csv(file_path, encoding='ISO-8859-1')
    
    # 1. CLEANING: Standardize column names (strip whitespace, remove newlines)
    df_raw.columns = df_raw.columns.str.strip()
    df_raw.columns = df_raw.columns.str.replace('\n', ' ').str.replace('\r', '')
    df_raw.columns = df_raw.columns.str.replace(' +', ' ', regex=True)
    
    # 2. FILTER: Keep only the 6 county rows (excluding national averages)
    df = df_raw.head(6).copy() 

    # 3. CONVERSION & FILLING: Replace non-numeric with NaN and convert to numeric
    df = df.replace(['N/A', 'N\\A', '#DIV/0!', '', ' '], np.nan)
    
    score_cols = [col for col in df.columns if col != 'County']
    
    for col in score_cols:
        # Convert to numeric, forcing errors to NaN (important for data type)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Fill NaNs with 0 AFTER conversion (so 'N/A' becomes 0)
    df = df.fillna(0)

    # 4. RENAMING (CRITICAL FIX): You need a central DataFrame with all FINAL column names 
    # for the map visualization to work, as the map is built on a single DF.
    
    # This requires manual matching of raw pX_ names to clean names. 
    # Since I don't have the raw names, I will use a dummy map and advise you to fill it.
    
    # --- IMPORTANT: FILL THIS MAP with the ACTUAL raw column names from your CSV ---
    # Example: 'p1_PHC Advisory Committees' : 'PHC Advisory Committees'
    RAW_TO_CLEAN_MAP = {
        # Fill this section with the actual column names from your CSV (first 6 rows) 
        # and map them to the clean names in PILLAR_KEYWORDS
        # e.g., 'p1_PHC Advisory Committees_raw': 'PHC Advisory Committees',
        # e.g., 'p1_Governance Weighted Score_raw': 'Governance Weighted Score',
        # ... ensure all columns used in PILLAR_KEYWORDS are mapped.
    }
    
    # DUMMY implementation (YOU MUST REPLACE/VALIDATE THIS):
    # This is the point where the raw column names MUST be renamed to the clean column names
    # to create one 'df_county' containing all the clean-named columns.
    
    # For now, we will assume a successful rename has happened and 
    # the df returned has all the clean columns:
    # df_county_clean = df.rename(columns=RAW_TO_CLEAN_MAP) 
    
    # Since I cannot perform the rename, I will make the function return the raw DF and 
    # rely on the pillar grouping logic below to handle the clean column names
    # (assuming the pillar grouping can find the column names based on keywords).
    
    # Better approach: return the cleaned DF and the pillar DFs.
    df_county_clean = df.copy() # The DF with raw column names, but cleaned data types
    pillar_dfs = group_columns_by_pillar(df_county_clean, PILLAR_KEYWORDS)

    # We need a single DF with all clean names for the map (df_county). 
    # The pillar_dfs structure is confusing this.
    # Let's create a simplified final DF containing only the required columns.
    
    all_clean_cols = ['County']
    for keywords in PILLAR_KEYWORDS.values():
        all_clean_cols.extend(keywords)
    
    # We will assume that the raw DF (after stripping and cleaning) 
    # contains the column names that are close enough to the keywords to be selected.
    # We will simplify the return structure:
    return df_county_clean, pillar_dfs # df_county_clean still has the raw/stripped names


# --- 3. EXECUTION BLOCK (LOAD DATA & SETUP) ---
geojson_data= None
GEOJSON_PATH = "kenya_counties_adm1.geojson"
GEOJSON_COUNTY_KEY = "properties.NAME_1"
try:
    #  The county_lvl_data.csv MUST have its column names 
    # (p1_..., p2_..., etc.) match or contain the keywords in PILLAR_KEYWORDS.
    df_county_raw, pillar_dfs = load_and_clean_data(
        r"C:\Users\PC\Desktop\Frank\Projects - Frank\county_lvl_data.csv"
    )

    with open(GEOJSON_PATH, 'r') as f:
        geojson_data = json.load(f)
    
    # You MUST verify this key:
    GEOJSON_COUNTY_KEY = "properties.NAME_1"

except FileNotFoundError as e:
    st.error("Error: GeoJSON or County data file not found. Check your file paths.")
    st.stop()

except Exception as e:
    # Catch any other data processing error
    st.error(f"An error occurred during data processing: {e}")
    st.stop()


# --- 4. STREAMLIT LAYOUT AND INTERACTIVITY ---

st.set_page_config(layout="wide", page_title="Kenya PCN Establishment Dashboard")
st.title("🇰🇪 County-Level PCN Establishment Analysis")

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
    st.subheader(f"Bar Chart: {selected_indicator}")

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
    st.subheader(f"Geographic Map: {selected_indicator}")

    # FIX 3: Use the pillar_df for mapping as it contains the correct, clean column names.
    # The map creation needs a DF that contains the selected_indicator column.
    # Since pillar_df is guaranteed to contain 'County' and 'selected_indicator', we use it.
    
    # Create the Choropleth map using Plotly Mapbox
    fig_map = px.choropleth_mapbox(
        pillar_df, # Use the correctly filtered DF
        geojson=geojson_data,
        locations='County',           # Column in the DataFrame with the county name
        featureidkey=GEOJSON_COUNTY_KEY, # Key in the GeoJSON that matches the county name
        color=selected_indicator,     # Column to determine the color intensity
        hover_name='County',          # Text to show on hover
        color_continuous_scale="RdYlGn", 
        mapbox_style="carto-positron", 
        zoom=5.5,                     
        center={"lat": 0.02, "lon": 37.9}, 
        opacity=0.8,
        title=f'County Distribution by {selected_indicator}',
        labels={selected_indicator: 'Score (%)'}
    )

    fig_map.update_layout(
        margin={"r":0,"t":40,"l":0,"b":0},
        height=550
    )

    st.plotly_chart(fig_map, use_container_width=True)


if geojson_data is None:
    st.error("Map visualization cannot load: GeoJSON data is missing.")
else:
   
    with col2:
        st.subheader(f"Geographic Map: {selected_indicator}")

        # Create the Choropleth map using Plotly Mapbox
        fig_map = px.choropleth_mapbox(
            pillar_df, 
            geojson=geojson_data, # This line now safely references the initialized variable
            locations='County',           
            featureidkey=GEOJSON_COUNTY_KEY,
            # ... (rest of map code) ...
        )

        st.plotly_chart(fig_map, use_container_width=True)

if geojson_data is None or GEOJSON_COUNTY_KEY is None:
    st.error("Map visualization cannot load: GeoJSON data or its key is missing.")
    # You may want to stop the script here or skip the map drawing.
else:
    # --- COLUMN 2: MAP ---
    with col2:
        # ... map code runs here ...
        fig_map = px.choropleth_mapbox(
            pillar_df, 
            geojson=geojson_data, 
            locations='County',           
            featureidkey=GEOJSON_COUNTY_KEY, # Now safely defined
            # ... (rest of map code) ...
        )

st.markdown("""---""")

st.header("County Data Table")
# Use the filtered pillar_df for the table
st.dataframe(pillar_df.sort_values(by='County'), use_container_width=True)