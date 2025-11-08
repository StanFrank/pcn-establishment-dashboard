import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import geopandas as gpd
import json

# -------------------------
# 1. CONFIG (kept from your final script)
# -------------------------

# --- 1. CONFIGURATION AND DATA STRUCTURES ---

PILLAR_KEYWORDS = {
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
        'Total County Score (Total Weighted Score)',
    ]
}

# PCN-level pillar keywords (based on the long header you shared).
# Use substrings from the header so group_columns_by_pillar will catch the right columns.
PCN_PILLAR_KEYWORDS = {
    '1. Governance': [
        'Proportion of functional Community Health Committees',
        'Proportion of Health facilities that have received supportive supervision',
        'Functional PCN Management committee',
        'Functionallity of MDTs',
        'Governance Score', 'Governance Weighted Score'
    ],
    '2. Population Health Needs': [
        'Number of population profiling assessments conducted',
        'Proportion of population health needs that have been addressed',
        'Number of wellness activities conducted',
        'Population Needs Score', 'Population Needs Weighted Score'
    ],
    '3. Capacity Readiness': [
        'Proportion of facilities in the PCN that had all 22 tracer pharmaceuticals',
        'Proportion of facilities in the PCN that have all 23 tracer non-pharmaceuticals',
        'Availability of the whole blood and blood components',
        'Percentage of Health facilities with stock out on any of the 22 tracer pharmaceuticals',
        'Percentage of Health facilities with stock out on any of the 22 tracer non-pharmaceuticals',
        'Proportion of hospitals with comprehensive lab services',
        'Proportion of spokes with basic lab services',
        'Proportion of Facilities within the PCN with all basic tracer equipment',
        'Capacity Readiness Score', 'Capacity Readiness Weighted Score'
    ],
    '4. Healthcare Financing': [
        'Proportion of clients accessing Health Services using SHIF',
        'Proportion of the target Health Facilities empanneled on SHA',
        'Proportion of Health Facilities in the PCN making SHA claims',
        'Proportion of claims reimbursed to HFs within the PCN',
        'Proportion of FIF collected rolled back to the facilities within PCN',
        'Number of people waived for user fees',
        'Total amount of user fees waived',
        'Healthcare Financing Score', 'Healthcare Financing Weighted Score'
    ],
    '5. Health Infrastructure': [
        'Proportion of health facilities with accessible road network',
        'Proportion of facilities with the appropriate WASH facilities',
        'Proportion of facilities with the tracer list of infrastructure',
        'Proportion of facilties with a reliable power source',
        'PCN access to adequate ambulance services',
        'Ambulance request Score', 'Health infrastructure Score', 'Health infrastructure Weighted Score'
    ],
    '6. HMIS/Digital Health': [
        'Proprtion of facilties with reliable internet connection',
        'Proportion of facilities in the PCN with the key OPD reporting tools',
        'No of performance and data quality review meetings held quarterly',
        'Proportion of facilities with ICT infrastructure',
        'Proportion of facilities in a PCN with an integrated functional EMR',
        'Proportion of CHUs within the PCN reporting monthly',
        'HMIS Score', 'HMIS Weighted Score'
    ],
    '7. Human Resources for Health (HRH)': [
        'Core HRH density', 'Doctor to population ratio', 'Clinical officer to  population ratio',
        'Nurse to population ratio', 'CHA/CHO  to population ratio',
        'Proportion of CHPs trained on basic modules',
        'Health care workers sensitized on PHC /PCN',
        'Does the PCN have a mechanism to enhance health workers skills',
        'Proportion of health workers who have undergone a skills/ competency buliding course',
        'HRH Score', 'HRH Weighted Score'
    ],
    '8. Service Delivery': [
        'Number of outreaches conducted by the MDT',
        'Number of in-reaches conducted within the PCN',
        'Service Delivery Score', 'Service Delivery Weighted Score'
    ],
    '9. Quality of Care - Management Systems': [
        'Proportion of hospitals with functional facility quality improvement teams',
        'Proportion of spokes with functional facility work improvement teams',
        'Average availability of selected IPC items',
        'QoC Management Systems Score', 'QoC Management Systems Weighted Score'
    ],
    '10. Quality of Care - PHC Core Systems': [
        'Adherence to clinical guidelines', 'Provider Availability (absenteeism)',
        'QoC PHC Core Systems Score'
    ],
    '11. Quality of Care - Outcomes': [
        'Proportion of facilities conducting MPDSR',
        'Fresh Stillbirth rate', 'Number of maternal deaths', 'Proportion of maternal deaths Audited',
        'Number of neonatal deaths', 'Proportion of neonatal deaths audited',
        'TB Treatment Success Rate',
        'QoC Outcomes Score'
    ],
    '12. Social Accountability': [
        'Proportion of facilities which have conducted a client satisfaction survey',
        'No. of MDT engagements with the community',
        'No. of health facilities with functional GRMs',
        'Social Accountability Score'
    ],
    '13. Multisectoral Partnerships and Coordination': [
        'Proportion of multi-sectoral actions implemented',
        'Number of inter- PCN peer to peer learning sessions held',
        'Multisectoral Partnerships and Coordination Score'
    ],
    '14. Innovations and Learning': [
        'Number of PHC related innovations', 'Innovations and Learning Score', 'Innovations and Learning Weighted Score'
    ],
    '15. Overall PCN Score': [
        'Total PCN Score', 'Total PCN Score (Total Weighted Score)'
    ]
}
# -------------------------
# 2. UTILITIES (kept and restored)
# -------------------------
def standardize_name(name):
    if pd.isna(name):
        return name
    name = str(name).strip().title()
    name = (
        name.replace('\xa0', ' ')
        .replace('/', ' ')
        .replace('-', ' ')
        .replace('County', '')
    )
    while '  ' in name:
        name = name.replace('  ', ' ')
    name_standardization_map = {
        'Nairobi City': 'Nairobi',
    }
    name = name_standardization_map.get(name, name)
    return name.strip()

def group_columns_by_pillar(df_raw, pillar_keywords):
    pillar_dfs = {}
    for pillar, keywords in pillar_keywords.items():
        # match any keyword substring (case-insensitive) appearing inside column names
        matching_cols = ['County'] + [
            col for col in df_raw.columns
            if any(keyword.lower() in col.lower() for keyword in keywords)
        ]
        if len(matching_cols) > 1:
            pillar_dfs[pillar] = df_raw[matching_cols].copy()
    return pillar_dfs

# restore load_geodata for counties (your previous working function)
@st.cache_data
def load_geodata(shp_path):
    try:
        gdf = gpd.read_file(shp_path)
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        gdf_clean = gdf[['ADM1_EN', 'geometry']].rename(columns={'ADM1_EN': 'County_Name_Key'})
        gdf_clean['County_Name_Key'] = gdf_clean['County_Name_Key'].apply(standardize_name)
        geojson_data = json.loads(gdf_clean.to_json())
        return geojson_data
    except Exception as e:
        st.error(f"Error loading geospatial data: {e}")
        return None

# helper to load subcounty shapefile / geojson when available
@st.cache_data
def load_subcounty_geodata(shp_path):
    try:
        gdf = gpd.read_file(shp_path)
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        # you may need to rename the subcounty property to match whatever property you use
        # we'll try common names (SUBCOUNTY, SUB_COUNTY, SUBCOUNTY_NAM etc.)
        # here we detect the first non-geometry column that likely holds the name
        name_col = None
        for c in gdf.columns:
            if c.lower() not in ['geometry', 'objectid', 'fid']:
                # heuristics: contains 'sub' or 'name'
                if 'sub' in c.lower() or 'name' in c.lower():
                    name_col = c
                    break
        if name_col is None:
            # fallback to first non-geometry column
            name_col = [c for c in gdf.columns if c.lower() != 'geometry'][0]
        gdf_clean = gdf[[name_col, 'geometry']].rename(columns={name_col: 'Subcounty_Name_Key'})
        gdf_clean['Subcounty_Name_Key'] = gdf_clean['Subcounty_Name_Key'].apply(standardize_name)
        geojson_data = json.loads(gdf_clean.to_json())
        return geojson_data
    except Exception as e:
        st.error(f"Error loading subcounty geospatial data: {e}")
        return None

# -------------------------
# 3. LOAD & CLEAN CSVs (preserve original logic)
# -------------------------
@st.cache_data
def load_and_clean_county_csv(path):
    df_raw = pd.read_csv(path, encoding='ISO-8859-1')
    df_raw.columns = df_raw.columns.str.strip().str.replace('\n', ' ').str.replace('\r', '').str.replace(' +', ' ', regex=True)
    df = df_raw.head(47).copy()
    df = df.replace(['N/A', 'N\\A', '#DIV/0!', '', ' '], np.nan)
    score_cols = [col for col in df.columns if col != 'County']
    for col in score_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['County'] = df['County'].apply(standardize_name)
   # Filtering (to prevent plotting zero-data counties)
    df_filtered = df.dropna(subset=score_cols, how='all').copy()
    df_county_clean = df_filtered.fillna(0).copy()
    
    pillar_dfs = group_columns_by_pillar(df_county_clean, PILLAR_KEYWORDS)
    return df_county_clean, pillar_dfs

@st.cache_data
def load_and_clean_pcn_csv(path):
    df = pd.read_csv(path, encoding='ISO-8859-1')
    df.columns = df.columns.str.strip().str.replace('\n', ' ').str.replace('\r', '').str.replace(' +', ' ', regex=True)
    # apply standardization to County and Subcounty if present
    if 'County' in df.columns:
        df['County'] = df['County'].apply(standardize_name)
    if 'Sub county' in df.columns:
        df['Sub county'] = df['Sub county'].apply(standardize_name)
    # coerce numeric columns where possible
    for col in df.columns:
        if col not in ['County', 'Sub county', 'Pillar', 'Indicator']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

# -------------------------
# 4. EXECUTION: load files and geodata (paths must exist in your app folder)
# -------------------------
# update these paths to match your environment
COUNTY_CSV = "county_lvl_data.csv"
PCN_CSV = "pcn_lvl_data.csv"
COUNTY_SHAPE = "ken_admbnda_adm1_iebc_20191031.shp"  # your shapefile for counties
SUBCOUNTY_SHAPE = "ken_admbnda_adm2_iebc_20191031.shp"  # optional, only if you have subcounty boundaries
# load county geojson
GEOJSON_COUNTY_KEY = "properties.County_Name_Key"

# load CSVs
df_county_raw, pillar_dfs = load_and_clean_county_csv(COUNTY_CSV)
pcn_lvl_df = load_and_clean_pcn_csv(PCN_CSV)


geojson_data = load_geodata(COUNTY_SHAPE)


# load subcounty geojson if available (optional)
subcounty_geojson = None
try:
    subcounty_geojson = load_subcounty_geodata(SUBCOUNTY_SHAPE)
except Exception:
    subcounty_geojson = None

# ============================
# 5. STREAMLIT UI: County-Level (your original working section)
# ============================
st.set_page_config(layout="wide", page_title="Kenya PCN Establishment Dashboard")
st.markdown(
    "<h1 style='text-align: center; font-size: 100px;'>Kenya PCN Establishment Dashboard</h1>",
    unsafe_allow_html=True
)
st.markdown("<h2 style='color:#1E90FF'>County-Level PCN Establishment Analysis</h2>", unsafe_allow_html=True)
st.markdown("---")

# sidebar controls for county-level (keeps your original behavior)
st.markdown("Select Performance Metric.", unsafe_allow_html=True)
pillar_keys = list(pillar_dfs.keys())

if not pillar_keys:
    st.warning("No county-level pillars detected. Check column names and PILLAR_KEYWORDS.")
else:
    selected_pillar = st.selectbox("1. Select Pillar:", options=pillar_keys, index=0)
    pillar_dfs = group_columns_by_pillar(df_county_raw, PILLAR_KEYWORDS)
    pillar_df = pillar_dfs[selected_pillar]
    indicator_options = [col for col in pillar_df.columns if col != 'County']
    selected_indicator = st.selectbox("2. Select Indicator/Metric:", options=indicator_options)

    # layout: bar + map
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Bar Chart")
        df_chart = pillar_df[['County', selected_indicator]].sort_values(by=selected_indicator, ascending=False)
        fig_bar = px.bar(
            df_chart,
            x='County',
            y=selected_indicator,
            color='County',
            text=selected_indicator,
            height=550,
            labels={selected_indicator: "Score (%)"},
            title=f"{selected_indicator}"
        )
        fig_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_bar.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("Geographic Map")
        KENYA_CENTER = {"lat": 0.5, "lon": 37.9}
        if geojson_data is None:
            st.error("County shapefile not loaded; can't render map.")
        else:
            # ensure we include all counties from geojson so borders render
            geojson_counties = [feature['properties']['County_Name_Key'] for feature in geojson_data['features']]
            df_all_counties = pd.DataFrame({'County': geojson_counties})
            df_score_data = pillar_df[['County', selected_indicator]].copy()
            df_map_data = df_all_counties.merge(df_score_data, on='County', how='left')

            # Convert to numeric, preserve NaN for missing; do NOT fill with 0
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

            # thin grey borders for all counties; NaNs will render as no fill
            fig_map.update_traces(marker_line={'width': 0.8, 'color': 'grey'}, selector=dict(type='choroplethmapbox'))
            # colorbar inside map, black ticks, labelled Score (%)
            fig_map.update_layout(
                coloraxis_colorbar=dict(
                    title=dict(text="Score (%)", font=dict(color="black", size=12)),
                    tickformat=".0f",
                    tickfont=dict(color="black", size=11),
                    x=0.97, xanchor="right", y=0.5, yanchor="middle", len=0.6, thickness=12,
                    bgcolor="rgba(255,255,255,0.6)", outlinecolor="rgba(0,0,0,0.2)", outlinewidth=1
                ),
                margin={"r":0, "t":30, "l":0, "b":0},
                mapbox=dict(bearing=0, pitch=0)
            )

            # title annotation inside map
            fig_map.add_annotation(
                text=f"{selected_indicator} by County",
                xref="paper", yref="paper", x=0.5, y=0.98, showarrow=False,
                font=dict(size=12, color="black", family="Arial Black"),
                bgcolor="rgba(255,255,255,0.7)", bordercolor="black", borderwidth=1, borderpad=6
            )
        #Manually make missing data appear white ---
        # Recolor counties with 0 (previously NaN) to white
            for feature in geojson_data["features"]:
                county_name = feature["properties"]["County_Name_Key"]
                if county_name in df_map_data["County"].values:
                    val = df_map_data.loc[df_map_data["County"] == county_name, selected_indicator].iloc[0]
                    if val == 0:
                        feature["properties"]["fill"] = "white"
            st.plotly_chart(fig_map, use_container_width=True)


st.markdown("""---""")

# ============================
# 6. PCN-LEVEL SECTION (new, built on your final script)
# ============================
st.markdown("<h2 style='color:#1E90FF'>Subcounty Level Analysis</h2>", unsafe_allow_html=True)
st.markdown("Use the filters below to drill down to PCN level.", unsafe_allow_html=True)

# Horizontal filters: independent of sidebar controls
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2,2,2,2])

# Build dictionary of PCN pillar groups from the PCN_PILLAR_KEYWORDS mapping (dynamic)
pcn_pillars_map = group_columns_by_pillar(pcn_lvl_df, PCN_PILLAR_KEYWORDS)
if not pcn_pillars_map:
    st.warning("No PCN-level pillars detected automatically. Please check PCN_PILLAR_KEYWORDS or column names in pcn_lvl_data.csv.")
else:
    with filter_col1:
        county_options_pcn = sorted(pcn_lvl_df['County'].dropna().unique())
        selected_county_pcn = st.selectbox("County (PCN data)", options=county_options_pcn)
       
    with filter_col2:
        subcounty_list = sorted(pcn_lvl_df[pcn_lvl_df['County'] == selected_county_pcn]['Sub county'].dropna().unique())
        subcounty_list = ["All"] + subcounty_list
        selected_subcounty_pcn = st.selectbox("Subcounty / PCN", options=subcounty_list)
        
    with filter_col3:
        # list unique standardized county names from PCN dataset
         selected_pillar_pcn = st.selectbox("PCN Pillar", options=list(pcn_pillars_map.keys()))
    with filter_col4:
        indicator_options_pcn = [col for col in pcn_pillars_map[selected_pillar_pcn].columns if col not in ['County','Subcounty']]
        selected_indicator_pcn = st.selectbox("PCN Indicator", options=indicator_options_pcn)
        # allow "All" option
        

    # filter pcn dataframe
    pcn_filtered = pcn_lvl_df[
        (pcn_lvl_df['County'] == selected_county_pcn)
    ].copy()

    # if a specific indicator was chosen, ensure its column exists in filtered frame
    if selected_indicator_pcn not in pcn_filtered.columns:
        st.warning(f"Indicator column '{selected_indicator_pcn}' not found in PCN dataset. Select another indicator.")
    else:
        # apply subcounty filter if not 'All'
        if selected_subcounty_pcn != "All":
            pcn_filtered_plot = pcn_filtered[pcn_filtered['Sub county'] == selected_subcounty_pcn]
        else:
            pcn_filtered_plot = pcn_filtered.copy()

        # ensure numeric conversion on the chosen indicator
        pcn_filtered_plot[selected_indicator_pcn] = pd.to_numeric(pcn_filtered_plot[selected_indicator_pcn], errors='coerce')

        # layout: bar + map (same style)
        colA, colB = st.columns([1,1])

        # BAR
        with colA:
            st.subheader(f"Bar Chart")
            df_bar_pcn = pcn_filtered_plot.sort_values(by=selected_indicator_pcn, ascending=False)
            # if there are many columns, guard against empty
            
            if df_bar_pcn.empty:
                st.info("No PCN data available for this selection.")
            else:
                fig_bar_pcn = px.bar(
                    df_bar_pcn,
                    x='Sub county',
                    y=selected_indicator_pcn,
                    color='Sub county',
                    text=selected_indicator_pcn,
                    labels={selected_indicator_pcn: "Score (%)"},
                    title=f"{selected_indicator_pcn} in {selected_subcounty_pcn} Subcounty"
                )
                fig_bar_pcn.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                fig_bar_pcn.update_layout(title_x=0, xaxis_tickangle=-180, margin={"r":0,"t":30,"l":0,"b":0})
                st.plotly_chart(fig_bar_pcn, use_container_width=True)

        # MAP
        with colB:
            st.subheader("Geographic Map by Sub County")
            if subcounty_geojson is None:
                st.info("No subcounty shapefile/geojson loaded (SUBCOUNTY_SHAPE). Map rendering is optional.")
            else:
                # prepare mapping dataframe: include all subcounties present in geojson
                geo_sub_names = [f['properties']['Subcounty_Name_Key'] for f in subcounty_geojson['features']]
                df_all_sub = pd.DataFrame({'Sub county': geo_sub_names})

                df_score = pcn_filtered[[ 'Sub county', selected_indicator_pcn ]].copy()
                df_score['Sub county'] = df_score['Sub county'].apply(standardize_name)
                df_map_pcn = df_all_sub.merge(df_score, left_on='Sub county', right_on='Sub county', how='left')

                # numeric coerced, keep NaN for missing
                df_map_pcn[selected_indicator_pcn] = pd.to_numeric(df_map_pcn[selected_indicator_pcn], errors='coerce')

                # create map
                fig_map_pcn = px.choropleth_mapbox(
                    df_map_pcn,
                    geojson=subcounty_geojson,
                    locations='Sub county',
                    featureidkey="properties.Subcounty_Name_Key",
                    color=selected_indicator_pcn,
                    hover_name='Sub county',
                    color_continuous_scale="RdYlGn",
                    mapbox_style="white-bg",
                    zoom=6.0,
                    center={"lat": 0.5, "lon": 37.9},
                    opacity=0.85,
                    labels={selected_indicator_pcn: "Score (%)"},
                )

                fig_map_pcn.update_traces(marker_line={'width':0.5,'color':'grey'}, selector=dict(type='choroplethmapbox'))
                fig_map_pcn.update_layout(
                    coloraxis_colorbar=dict(
                        tickformat=".0f",
                        tickfont=dict(color="black"),
                        x=0.95, xanchor="right", y=0.5, yanchor="middle", len=0.6, thickness=12,
                        bgcolor="rgba(255,255,255,0.6)"
                    ),
                    margin={"r":0,"t":30,"l":0,"b":0}
                )

                fig_map_pcn.add_annotation(
                    text=f"{selected_indicator_pcn} across PCNs in {selected_county_pcn}",
                    xref="paper", yref="paper", x=0.5, y=0.98, showarrow=False,
                    font=dict(size=11, color="black"), bgcolor="rgba(255,255,255,0.7)",
                    bordercolor="black", borderwidth=1, borderpad=6
                )

                st.plotly_chart(fig_map_pcn, use_container_width=True)

# -------------------------
# 7. Data Table Summary (optional) - show the filtered PCN data for transparency
# -------------------------
st.markdown("---")
st.header("PCN Data (Filtered)")
try:
    st.dataframe(pcn_filtered[[ 'County', 'Subcounty', selected_indicator_pcn ]].sort_values(by=selected_indicator_pcn, ascending=False), use_container_width=True)
except Exception:
    st.write("Select PCN Pillar/Indicator/County to view PCN table.")
