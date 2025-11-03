import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import geopandas as gpd
import json
from functools import lru_cache

# --- 1. CONFIGURATION AND DATA STRUCTURES ---

# --- A. COUNTY LEVEL CONFIG ---
PILLAR_KEYWORDS_COUNTY = {
    '1. Governance': [
        'Proportion of functional PHC advisory Committees in Place',
        'Proportion of PCNs Established',
        'Proportion of PCNs Gazetted',
        'Availability of a Functional PCN management committee',
        'Proportion of Hospital management boards appointed/gazetted:',
        'Proportion of Health Facilities (level 2&3) with Health Facility Management Committee Appointed/Gazetted',
        'Availability of a functional PHC TWG Score',
        'Proportion of PCNs with an operational budget for the MDT activities:',
        'Perfomance Review Score',
        'CHMT Support Supervision Score',
        'Governance Score',
        'Governance Weighted Score'
    ],
    '2. Human Resources for Health (HRH)': [      
        'Does the County have a mechanism to enhance health workers skills',
        'HRH Score',
        'HRH Weighted Score'
    ],
    '3. Health Product Technologies (HPT)': [      
        'Proportion of county health budget allocated to drugs and supplies',
        'Proportion of county HPT budget allocated to levels 2&3 :',
        'HPT Score',
        'HPT Weighted Score'
    ],
    '4. Service Delivery Systems': [
        'PCNs with functional refferal mechanisms',
        'Service Delivery Systems Score',
        'Service Delivery Systems Weighted Score'
    ],
    '5. Healthcare Financing': [
        'Proportion of households registered on SHA within the County',
        'Healthcare Financing Score',
        'Healthcare Financing Weighted Score'
    ],
    '6. HMIS/Digital Health': [
        'Proportion of SMART PCNs in the County',
        'HMIS Score',
        'HMIS Weighted Score'
    ],
    '7. Quality of Care (QoC) - Management Systems': [
        'Mechanism to Coordinate Quality Improvement Score',
        'Mechanism for Implementation of Support Supervision in Health Facilities Score',
        'Presence of an Infection Prevention Control (IPC) committee Score',
        'QoC Management Systems Score',
        'QoC Management Systems Weighted Score'
    ],
    '8. Multisectoral Partnerships and Coordination': [
        'Number of bi-annual multisectoral stakeholder forums Score',
        'Proportion of MOUs and partnership agreements aligned to PHC signed',
        'Research studies done on PCN implementation Score',
        'Multisectoral Partnerships and Coordination Score',
        'Multisectoral Partnerships and Coordination Weighted Score'
    ],
    '9. Innovations and Learning': [
        'Number of knowledge management and learning forums conducted Score:',
        'No. of research studies done on PCN implementation Score',
        'Innovations and Learning Score',
        'Innovations and Learning Weighted Score'
    ],
    '10. Overall Score': [
        'Total County Score (Total Weighted Score)'
    ]
}

# --- B. PCN (Sub-County) LEVEL CONFIG ---
PILLAR_KEYWORDS_PCN = {
    '1. Governance': [
        'Proportion of functional Community Health Committees in the PCN',
        'Proportion of Health facilities that have received supportive supervision in the PCN',
        'Functional PCN Management committee',
        'Functionallity of MDTs',
        'Governance Score',
        'Governance Weighted Score'
    ],
    '2. Population Health Needs': [
        'Number of population profiling assessments conducted',
        'Proportion of population health needs that have been addressed',
        'Number of wellness activities conducted within the PCN',
        'Population Needs Score',
        'Population Needs Weighted Score'
    ],
    '3. Capacity Readiness (HPT & Equipment)': [
        'Proportion of facilities in the PCN that had all 22 tracer pharmaceuticals at the time of assessment',
        'Proportion of facilities in the PCN that have all 23 tracer non-pharmaceuticals at the time of assessment',
        'Availability of the whole blood and blood components in the hospitals',
        'Percentage of Health facilities with stock out on any of the 22 tracer pharmaceuticals for 7 consecutive days in a month*',
        'Percentage of Health facilities with stock out on any of the 22 tracer non-pharmaceuticals for 7 consecutive days in a month*',
        'Proportion of hospitals with comprehensive lab services within the PCN',
        'Proportion of spokes with basic lab services within the PCN',
        'Proportion of Facilities within the PCN with all basic tracer equipment available and functional **List provided below the template',
        'Capacity Readiness Score',
        'Capacity Readiness Weighted Score'
    ],
    '4. Health Care Financing': [
        'Proportion of clients accessing Health Services using SHIF',
        'Proportion of the target Health Facilities empanneled on SHA within the PCN',
        'Proportion of Health Facilities in the PCN making SHA claims',
        'Proportion of claims reimbursed to HFs within the PCN',
        'Proportion of FIF collected rolled back to the facilities within PCN',
        'Number of people waived for user fees in Hospitals within the PCN',
        'Total amount of user fees waived in Health care Facilities within the PCN',
        'Healthcare Financing Score',
        'Healthcare Financing Weighted Score'
    ],
    '5. Health Infrastructure': [
        'Proportion of health facilities with accessible road network',
        'Proportion of facilities with the appropriate WASH facilities ***',
        'Proportion of facilities with the tracer list of infrastructure as per KEPH standards',
        'Proportion of facilties with a reliable power source',
        'PCN access to adequate ambulance services',
        'Ambulance request Score',
        'Health infrastructure Score',
        'Health infrastructure Weighted Score'
    ],
    '6. HMIS/ Digital Health': [
        'Proprtion of facilties with reliable internet connection',
        'Proportion of facilities in the PCN with the key OPD reporting tools (6)',
        'No of performance and data quality review meetings held quarterly within the PCN',
        'Proportion of facilities with ICT infrastructure',
        'Proportion of facilities in a PCN with an integrated functional EMR',
        'Proportion of CHUs within the PCN reporting monthly',
        'HMIS Score',
        'HMIS Weighted Score'
    ],
    '7. HRH': [
        'Core HRH density',
        'Doctor to population ratio',
        'Clinical officer to population ratio',
        'Nurse to population ratio',
        'CHA/CHO to population ratio',
        'Proportion of CHPs trained on basic modules',
        'Health care workers sensitized on PHC /PCN',
        'Does the PCN have a mechanism to enhance health workers skills?',
        'Proportion of health workers who have undergone a skills/ competency buliding course within the last 2 years',
        'HRH Score',
        'HRH Weighted Score'
    ],
    '8. Service Delivery': [
        'Number of outreaches conducted by the MDT',
        'Number of in-reaches conducted within the PCN',
        'Service Delivery Score',
        'Service Delivery Weighted Score'
    ],
    '9. Quality of Care - Management Systems': [
        'Proportion of hospitals with functional facility quality improvement teams (QIT)',
        'Proportion of spokes with functional facility work improvement teams (WIT)',
        'Average availability of selected IPC items *(items defined below)',
        'QoC Management Systems Score'
    ],
    '10. Quality of Care - PHC Core Systems': [
        'Adherence to clinical guidelines for Primary health care facilities',
        'Provider Availability (absenteeism) for Primary health care facilities',
        'QoC PHC Core Systems Score'
    ],
    '11. Quality of Care - Outcomes': [
        'Proportion of facilities conducting MPDSR',
        'Fresh Stillbirth rate per 1,000 births in health facilities',
        'Number of maternal deaths reported in Health facilities per 100,000 live births',
        'Proportion of maternal deaths Audited',
        'Number of neonatal deaths per 1,000 live births',
        'Proportion of neonatal deaths audited',
        'TB Treatment Success Rate',
        'QoC Outcomes Score',
        'QoC Outcomes Weighted Score'
    ],
    '12. Social Accountability': [
        'Proportion of facilities which have conducted a client satisfaction survey',
        'No. of MDT engagements with the community',
        'No. of health facilities with functional GRMs',
        'Social Accountability Score',
        'Social Accountability Weighted Score'
    ],
    '13. Multisectoral Partnerships and Coordination': [
        'Proportion of multi-sectoral actions implemented',
        'Number of inter- PCN peer to peer learning sessions held',
        'Multisectoral Partnerships and Coordination Score',
        'Multisectoral Partnerships and Coordination Weighted Score'
    ],
    '14. Innovations and Learning': [
        'Number of PHC related innovations/ best practice implemented/adapted',
        'Innovations and Learning Score',
        'Innovations and Learning Weighted Score'
    ],
    '15. Overall PCN Score': [
        'Total PCN Score (Total Weighted Score)'
    ]
}

# --- C. FILE PATHS ---
COUNTY_SHAPEFILE_PATH = "ken_admbnda_adm1_iebc_20191031.shp"
COUNTY_DATA_PATH = "county_lvl_data.csv"
GEOJSON_COUNTY_KEY = "properties.County_Name_Key"

# PLACEHOLDERS for PCN Level
PCN_SHAPEFILE_PATH = "ken_admbnda_adm2.shp" # Sub-county shapefile placeholder
PCN_DATA_PATH = "pcn_lvl_data.csv"
GEOJSON_PCN_KEY = "properties.PCN_Name_Key" # Key name in the PCN GeoJSON features


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
    # This list might need to be expanded based on your data quirks
    name_standardization_map = {
        'Nairobi City': 'Nairobi',
        'Tana River': 'Tana River',
        'Elgeyo Marakwet': 'Elgeyo-Marakwet' # Example for known map inconsistency
    }
    name = name_standardization_map.get(name, name)
        
    # 5. Final strip to eliminate any leading/trailing spaces.
    return name.strip()


# Group column headers into pillar dataframes.
def group_columns_by_pillar(df_raw, pillar_keywords):
    pillar_dfs = {}

    for pillar, keywords in pillar_keywords.items():
        # Ensure we look for the exact column header (case-insensitive)
        matching_cols = ['County'] + [
            col for col in df_raw.columns
            if any(keyword.strip().lower() in col.strip().lower() for keyword in keywords)
        ]
        
        # If Subcounty/PCN column exists, add it here for PCN level
        if 'Subcounty' in df_raw.columns and 'Subcounty' not in matching_cols:
            matching_cols.insert(1, 'Subcounty')

        if len(matching_cols) > 1:
            # Only select the columns that actually exist in the raw DataFrame
            valid_cols = [col for col in matching_cols if col in df_raw.columns]
            if len(valid_cols) > 1:
                 pillar_dfs[pillar] = df_raw[valid_cols].copy()

    return pillar_dfs

def clean_data(df_raw, keyword_dict):
    """General cleaning and type conversion for any dataset."""
    df_raw.columns = df_raw.columns.str.strip().str.replace('\n', ' ').str.replace('\r', '').str.replace(' +', ' ', regex=True)
    
    df = df_raw.copy()
    df = df.replace(['N/A', 'N\\A', '#DIV/0!', '', ' '], np.nan)
    
    # Identify score columns dynamically based on keywords
    all_keywords = [item for sublist in keyword_dict.values() for item in sublist]
    score_cols = [col for col in df.columns if col not in ['County', 'Subcounty', 'PCN'] and 
                  any(keyword.strip().lower() in col.strip().lower() for keyword in all_keywords)]

    for col in score_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df_filtered = df.dropna(subset=score_cols, how='all').copy()
    df_clean = df_filtered.fillna(0).copy()
    
    return df_clean, score_cols

@st.cache_data
def load_and_clean_county_data(file_path):
    df_raw = pd.read_csv(file_path, encoding='ISO-8859-1')
    df_county_clean, score_cols = clean_data(df_raw.head(47), PILLAR_KEYWORDS_COUNTY)
    
    df_county_clean['County'] = df_county_clean['County'].apply(standardize_name)
    pillar_dfs = group_columns_by_pillar(df_county_clean, PILLAR_KEYWORDS_COUNTY)
    
    return df_county_clean, pillar_dfs

@st.cache_data
def load_and_clean_pcn_data(file_path):
    # CRITICAL ASSUMPTION: The PCN file has 'County' and 'Subcounty' columns.
    try:
        df_raw = pd.read_csv(file_path, encoding='ISO-8859-1')
    except Exception:
        return pd.DataFrame(), {}
    
    # Ensure the dataframe has enough rows (not just headers)
    if len(df_raw) < 2:
        return pd.DataFrame(), {}
        
    df_pcn_clean, score_cols = clean_data(df_raw, PILLAR_KEYWORDS_PCN)

    # Apply standardization to County and Subcounty/PCN name columns
    if 'County' in df_pcn_clean.columns:
        df_pcn_clean['County'] = df_pcn_clean['County'].apply(standardize_name)
    if 'Subcounty' in df_pcn_clean.columns:
        df_pcn_clean['Subcounty'] = df_pcn_clean['Subcounty'].apply(standardize_name)
    
    pillar_dfs = group_columns_by_pillar(df_pcn_clean, PILLAR_KEYWORDS_PCN)
    
    return df_pcn_clean, pillar_dfs

@st.cache_data
def load_geodata(shp_path, key_column):
    try:
        # Note: geopandas requires all related files (.shp, .shx, .dbf, etc.) to be present
        gdf = gpd.read_file(shp_path)
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
            
        # Select and rename the key column
        gdf_clean = gdf[[key_column, 'geometry']].rename(columns={key_column: 'Name_Key'})
        
        # Apply the standardization function directly to the GeoJSON names
        gdf_clean['Name_Key'] = gdf_clean['Name_Key'].apply(standardize_name)
        
        # Convert the GeoDataFrame to a Python GeoJSON dictionary object
        geojson_data = json.loads(gdf_clean.to_json())
        
        # Update feature properties for Plotly's use
        for feature in geojson_data['features']:
             # Use the new generic Name_Key property name
            feature['properties']['County_Name_Key'] = feature['properties'].pop('Name_Key')
        
        return geojson_data
    
    except Exception as e:
        # Print a specific error in the console for debugging the file issue
        print(f"!!! Error loading geospatial data from {shp_path}. Plotting will be disabled. Error: {e}")
        return None

# --- PLOTLY CHOROPLETH GENERATOR ---
def create_choropleth_map(df_map_data, geojson_data, geojson_key, selected_indicator, center_point, title_text):
    
    # If geojson data is None, return None immediately to prevent plotting errors
    if geojson_data is None:
        return None

    fig_map = px.choropleth_mapbox(
        df_map_data,
        geojson=geojson_data,
        locations=df_map_data.columns[0], # The first column (County/Subcounty) holds the name to match
        featureidkey=geojson_key,
        color=selected_indicator,
        hover_name=df_map_data.columns[0],
        color_continuous_scale="RdYlGn_r", 
        mapbox_style="white-bg",
        zoom=5.0,
        center=center_point,
        opacity=1, 
        labels={df_map_data.columns[0]: 'Area Name', selected_indicator: 'Score (%)'},
    )
    
    # Set border line width and color for all county shapes
    fig_map.update_traces(
        marker_line_width=1,
        marker_line_color='grey', 
        selector=dict(type='choroplethmapbox')
    )

    fig_map.update_layout(
        margin={"r":0, "t":30, "l":0, "b":0},
        mapbox=dict(bearing=0, pitch=0),
        coloraxis_colorbar=dict(
            title=dict(text="Score (%)", side="top", font=dict(color="black", size=12)),
            tickformat=".0f",
            tickfont=dict(color="black", size=11),
            x=0.97, xanchor="right", y=0.5, yanchor="middle",
            len=0.6, thickness=12,
            bgcolor="rgba(255,255,255,0.8)",
            outlinecolor="rgba(0,0,0,0.2)", outlinewidth=1
        )
    )

    fig_map.add_annotation(
        text=title_text,
        xref="paper", yref="paper", x=0.5, y=0.98, showarrow=False,
        font=dict(size=14, color="black", family="Arial Black"),
        bgcolor="rgba(255,255,255,0.7)", bordercolor="black", borderwidth=1, borderpad=6,
    )
    
    return fig_map

# =======================================================
# --- 3. EXECUTION BLOCK (LOAD DATA & SETUP) ---
# =======================================================

KENYA_CENTER = {"lat": 0.5, "lon": 37.9}

# --- COUNTY DATA LOADING ---
df_county_clean, pillar_dfs_county = load_and_clean_county_data(COUNTY_DATA_PATH)
geojson_data_county = load_geodata(COUNTY_SHAPEFILE_PATH, 'ADM1_EN') # ADM1_EN is the county key

# --- PCN DATA LOADING ---
df_pcn_raw, pillar_dfs_pcn = load_and_clean_pcn_data(PCN_DATA_PATH)
# Assuming 'ADM2_EN' in the sub-county shapefile holds the name key
geojson_data_pcn = load_geodata(PCN_SHAPEFILE_PATH, 'ADM2_EN') 

# =======================================================
# --- 4. STREAMLIT LAYOUT AND INTERACTIVITY ---
# =======================================================

st.set_page_config(layout="wide", page_title="Kenya PCN Establishment Dashboard")
st.markdown("<h1 style='text-align: center;'>Kenya PCN Establishment Dashboard</h1>", unsafe_allow_html=True)

# --- 4A. COUNTY LEVEL ANALYSIS ---
st.markdown("<h1 style='text-align: left; color: #1E90FF;'>County-Level PCN Establishment Analysis</h1>", unsafe_allow_html=True)
st.markdown("""---""")

# Sidebar for Filter Selection (County Level)
st.sidebar.header("County Level Metrics")

pillar_keys_county = list(pillar_dfs_county.keys())

# 1. Select the main Pillar e.g Governance, HRH, HPT
if not pillar_keys_county:
    st.sidebar.error("No County pillar data loaded.")
    selected_indicator_county = None
else:
    selected_pillar_county = st.sidebar.selectbox(
        "County Pillar:",
        options=pillar_keys_county,
        index=0,
        key='county_pillar_select'
    )

    # 2. Get the corresponding Pillar DataFrame
    pillar_df_county = pillar_dfs_county[selected_pillar_county]

    # 3. Get the list of indicators (columns) for the selected pillar
    indicator_options_county = [col for col in pillar_df_county.columns if col != 'County']

    # 4. Select the specific Indicator/Metric within that pillar
    selected_indicator_county = st.sidebar.selectbox(
        "County Indicator:",
        options=indicator_options_county,
        key='county_indicator_select'
    )


# --- COUNTY LEVEL VISUALIZATION ---
if selected_indicator_county:
    col1_c, col2_c = st.columns([1, 1])
    
    # --- COLUMN 1: BAR CHART (County) ---
    with col1_c:
        st.subheader(f"County Bar Chart: {selected_indicator_county}")
        df_chart_c = pillar_df_county[['County', selected_indicator_county]].sort_values(
            by=selected_indicator_county, ascending=False
        )
        
        fig_bar_c = px.bar(
            df_chart_c, x='County', y=selected_indicator_county, color='County', 
            text=selected_indicator_county, height=550, 
            labels={selected_indicator_county: "Score (%)"},
            title=f"{selected_pillar_county} Breakdown"
        )
        fig_bar_c.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_bar_c.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig_bar_c, use_container_width=True)

    # --- COLUMN 2: MAP (County) ---
    with col2_c:
        st.subheader("County Geographic Map")
        if geojson_data_county is None:
            st.error("County Map visualization cannot load: Geospatial data is missing or failed to load.")
            fig_map_c = None
        else:
            df_score_data_c = pillar_df_county[['County', selected_indicator_county]].copy()
            
            # Create a dataframe of all counties to left-merge the score data onto
            geojson_counties = [feature['properties']['County_Name_Key'] for feature in geojson_data_county['features']]
            df_all_counties = pd.DataFrame({'County': geojson_counties})
            
            df_map_data_c = df_all_counties.merge(df_score_data_c, on='County', how='left')

            fig_map_c = create_choropleth_map(
                df_map_data_c.rename(columns={'County': 'County_Name_Key'}), # Rename for generic function
                geojson_data_county, 
                GEOJSON_COUNTY_KEY, 
                selected_indicator_county, 
                KENYA_CENTER, 
                f"County Scores: {selected_indicator_county}"
            )
        
        # CRITICAL FIX: Only update and chart if the map figure was successfully created
        if fig_map_c is not None:
            fig_map_c.update_layout(zoom=5.2) # Default zoom for country map
            st.plotly_chart(fig_map_c, use_container_width=True)

    st.markdown("""---""")
    st.header("County Data Table")
    st.dataframe(pillar_df_county.sort_values(by='County'), use_container_width=True)
    st.markdown("""---""")


# =======================================================
# --- 4B. PCN LEVEL ANALYSIS (Subcounty Drill Down) ---
# =======================================================

st.markdown("<h1 style='text-align: left; color: #FFA500;'>PCN Level Analysis (Subcounty)</h1>", unsafe_allow_html=True)
st.markdown("""---""")

# --- PCN HORIZONTAL FILTER BAR ---
pillar_keys_pcn = list(pillar_dfs_pcn.keys())

if not pillar_keys_pcn:
    st.warning("PCN data could not be loaded. Please ensure 'pcn_lvl_data.csv' exists and has 'County' and 'Subcounty' columns.")
else:
    # Get list of all available counties in the PCN dataset
    all_pcn_counties = sorted(df_pcn_raw['County'].unique().tolist())
    
    col_pcn_1, col_pcn_2, col_pcn_3, col_pcn_4 = st.columns(4)

    with col_pcn_1:
        selected_county_pcn = st.selectbox("1. Select County:", options=all_pcn_counties, key='pcn_county_select')
        
    # Filter the PCN data based on the selected County
    df_pcn_filtered = df_pcn_raw[df_pcn_raw['County'] == selected_county_pcn].copy()
    pcn_subcounty_options = sorted(df_pcn_filtered['Subcounty'].unique().tolist())

    with col_pcn_2:
        selected_subcounty_pcn = st.selectbox(
            "2. Select Subcounty/PCN (Optional):", 
            options=['All Subcounties'] + pcn_subcounty_options, 
            key='pcn_subcounty_select'
        )
        
    with col_pcn_3:
        selected_pillar_pcn = st.selectbox("3. Select Pillar:", options=pillar_keys_pcn, key='pcn_pillar_select')
        # We need the pillar_dfs_pcn that covers the whole raw dataset
        pillar_df_pcn = pillar_dfs_pcn[selected_pillar_pcn]
        indicator_options_pcn = [col for col in pillar_df_pcn.columns if col not in ['County', 'Subcounty']]

    with col_pcn_4:
        selected_indicator_pcn = st.selectbox(
            "4. Select Indicator/Metric:", 
            options=indicator_options_pcn, 
            key='pcn_indicator_select'
        )
        
    # --- FINAL DATA FILTERING FOR PCN VISUALIZATIONS ---
    # Apply County filter to the full pillar dataframe
    df_pcn_viz = pillar_df_pcn[pillar_df_pcn['County'] == selected_county_pcn].copy()

    # Apply Subcounty filter if "All Subcounties" is not selected
    if selected_subcounty_pcn != 'All Subcounties':
        df_pcn_viz = df_pcn_viz[df_pcn_viz['Subcounty'] == selected_subcounty_pcn].copy()
        
    # --- PCN LEVEL VISUALIZATION ---
    col1_pcn, col2_pcn = st.columns([1, 1])

    # --- COLUMN 1: BAR CHART (PCN) ---
    with col1_pcn:
        st.subheader(f"Bar Chart: {selected_county_pcn}")
        
        # Use Subcounty as the x-axis for the bar chart
        df_chart_pcn = df_pcn_viz[['Subcounty', selected_indicator_pcn]].sort_values(
            by=selected_indicator_pcn, ascending=False
        )
        
        fig_bar_pcn = px.bar(
            df_chart_pcn, x='Subcounty', y=selected_indicator_pcn, color='Subcounty', 
            text=selected_indicator_pcn, height=550, 
            labels={selected_indicator_pcn: "Score (%)"},
            title=f"{selected_pillar_pcn} Breakdown in {selected_county_pcn}"
        )
        fig_bar_pcn.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_bar_pcn.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig_bar_pcn, use_container_width=True)

    # --- COLUMN 2: MAP (PCN) ---
    with col2_pcn:
        st.subheader(f"Geographic Map: {selected_county_pcn}")
        if geojson_data_pcn is None:
            st.error("PCN Map visualization cannot load. Check if 'ken_admbnda_adm2.shp' and all components are uploaded.")
            fig_map_pcn = None
        else:
            # Prepare map data, merging score data onto all subcounties
            df_score_data_pcn = df_pcn_viz[['Subcounty', selected_indicator_pcn]].copy()
            
            fig_map_pcn = create_choropleth_map(
                df_score_data_pcn.rename(columns={'Subcounty': 'PCN_Name_Key'}),
                geojson_data_pcn, 
                GEOJSON_PCN_KEY, 
                selected_indicator_pcn, 
                KENYA_CENTER, 
                f"PCN Scores: {selected_indicator_pcn} in {selected_county_pcn}"
            )
            
        # CRITICAL FIX: Only update and chart if the map figure was successfully created
        if fig_map_pcn is not None:
            fig_map_pcn.update_layout(zoom=6.5) # Zoom closer to show subcounties
            st.plotly_chart(fig_map_pcn, use_container_width=True)

    st.markdown("""---""")
    st.header(f"PCN Data Table for {selected_county_pcn}")
    st.dataframe(df_pcn_viz.sort_values(by='Subcounty'), use_container_width=True)


