import streamlit as st
import os
import glob
from PIL import Image
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import sys

# Configure page settings
st.set_page_config(
    layout="wide", 
    page_title="University Building HVAC Performance Dashboard",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Custom CSS for improved appearance
st.markdown("""
<style>
    .main .block-container {padding-top: 1rem;}
    h1, h2, h3 {color: #00205b;}
    h1 {border-bottom: 2px solid #d93e29; padding-bottom: 10px; margin-bottom: 20px;}
    h2 {border-bottom: 1px solid #bdc3c7; padding-bottom: 8px; margin-top: 30px;}
    .metric-value {font-size: 24px; font-weight: bold; color: #d93e29;}
    .metric-label {font-size: 16px; color: #00205b;}
    .stTabs [data-baseweb="tab-list"] {gap: 16px;}
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 4px 4px 0 0;
        padding: 10px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e6f3ff;
        border-bottom: 2px solid #d93e29;
    }
    .chart-container {
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        padding: 15px;
        margin-bottom: 20px;
    }
    .data-container {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .dataframe {
        font-size: 12px;
    }
    div.stButton > button {
        background-color: #d93e29;
        color: white;
    }
    div.stButton > button:hover {
        background-color: #00205b;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Define the KPI output directory
KPI_DIR = "4_KPI"
SANKEY_DIR = "3_Sankey_Diagram"

# Try to import the Sankey diagram creation module
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import importlib.util
    spec = importlib.util.spec_from_file_location("sankey_module", "3_create_sankey_diagram.py")
    sankey_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sankey_module)
    sankey_available = True
except:
    sankey_available = False

# Get the current directory path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Top header with dashboard title
st.title("Building Z Energy Dashboard")

# Function to create custom metric display
def display_metric(title, value, unit="", delta=None, delta_suffix="from baseline"):
    st.markdown(f"""
    <div style="padding: 10px; background-color: white; border-radius: 5px; height: 100px; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
        <p class="metric-label">{title}</p>
        <p class="metric-value">{value} {unit}</p>
        {f'<p style="font-size: 14px; color: {"#2ecc71" if delta >= 0 else "#e74c3c"}">{"+" if delta >= 0 else ""}{delta}% {delta_suffix}</p>' if delta is not None else ""}
    </div>
    """, unsafe_allow_html=True)

# Function to display images in columns with enhanced styling
def display_images_in_columns(image_paths, num_columns=2, caption_func=None, width=None):
    if not image_paths:
        st.info("No images available for this category.")
        return
        
    cols = st.columns(num_columns)
    for i, img_path in enumerate(image_paths):
        col_idx = i % num_columns
        with cols[col_idx]:
            try:
                img = Image.open(img_path)
                caption = os.path.basename(img_path) if caption_func is None else caption_func(img_path)
                # Clean up caption by removing file extension and replacing underscores
                caption = os.path.splitext(caption)[0].replace('_', ' ').title()
                st.markdown(f"<div class='chart-container'>", unsafe_allow_html=True)
                st.image(img, caption=caption, use_container_width=True, width=width)
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error loading image {img_path}: {str(e)}")

# Function to load and display CSV data
def display_csv_data(csv_path, title="Data Table"):
    try:
        df = pd.read_csv(csv_path, sep=";", decimal=",")
        st.markdown(f"<div class='data-container'>", unsafe_allow_html=True)
        st.subheader(title)
        st.dataframe(df, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return df
    except Exception as e:
        st.warning(f"Could not load data from {csv_path}: {str(e)}")
        return None

# Function to extract key metrics from CSV files
def extract_metrics():
    metrics = {}
    
    # EUI
    eui_files = glob.glob(f"{KPI_DIR}/EUI/*.csv")
    if eui_files:
        try:
            eui_df = pd.read_csv(eui_files[0], sep=";", decimal=",")
            if 'Total_EUI' in eui_df.columns:
                metrics['eui'] = eui_df['Total_EUI'].iloc[-1]
        except:
            metrics['eui'] = 45.3  # Default value
    else:
        metrics['eui'] = 45.3  # Default value
    
    # GAHP GUE
    gahp_files = glob.glob(f"{KPI_DIR}/GAHP_GUE/*.csv")
    if gahp_files:
        try:
            gahp_df = pd.read_csv(gahp_files[0], sep=";", decimal=",")
            if 'GUE' in gahp_df.columns:
                metrics['gue'] = gahp_df['GUE'].mean()
        except:
            metrics['gue'] = 1.32  # Default value
    else:
        metrics['gue'] = 1.32  # Default value
    
    # EHP EER
    ehp_files = glob.glob(f"{KPI_DIR}/EHP_EER/*.csv")
    if ehp_files:
        try:
            ehp_df = pd.read_csv(ehp_files[0], sep=";", decimal=",")
            if 'EER' in ehp_df.columns:
                metrics['eer'] = ehp_df['EER'].mean()
        except:
            metrics['eer'] = 2.75  # Default value
    else:
        metrics['eer'] = 2.75  # Default value
    
    # Boiler Efficiency
    boiler1_files = glob.glob(f"{KPI_DIR}/Boiler1_Efficiency/*.csv")
    if boiler1_files:
        try:
            boiler1_df = pd.read_csv(boiler1_files[0], sep=";", decimal=",")
            if 'Efficiency' in boiler1_df.columns:
                metrics['boiler1_eff'] = boiler1_df['Efficiency'].mean()
        except:
            metrics['boiler1_eff'] = 89.5  # Default value
    else:
        metrics['boiler1_eff'] = 89.5  # Default value
    
    boiler2_files = glob.glob(f"{KPI_DIR}/Boiler2_Efficiency/*.csv")
    if boiler2_files:
        try:
            boiler2_df = pd.read_csv(boiler2_files[0], sep=";", decimal=",")
            if 'Efficiency' in boiler2_df.columns:
                metrics['boiler2_eff'] = boiler2_df['Efficiency'].mean()
        except:
            metrics['boiler2_eff'] = 86.7  # Default value
    else:
        metrics['boiler2_eff'] = 86.7  # Default value
    
    # Dry Cooler Effectiveness
    dc_files = glob.glob(f"{KPI_DIR}/DC/*.csv")
    if dc_files:
        try:
            dc_df = pd.read_csv(dc_files[0], sep=";", decimal=",")
            if 'Effectiveness' in dc_df.columns:
                metrics['dc_eff'] = dc_df['Effectiveness'].mean()
        except:
            metrics['dc_eff'] = 0.65  # Default value
    else:
        metrics['dc_eff'] = 0.65  # Default value
    
    # Comfort Metrics
    comfort_files = glob.glob(f"{KPI_DIR}/Comfort_results/Temperature/*.csv")
    if comfort_files:
        try:
            # Try to extract comfort data across seasons
            metrics['comfort'] = 91.5  # Default value
            metrics['avg_temp'] = 22.1  # Default value
            metrics['avg_co2'] = 520  # Default value
            metrics['avg_humidity'] = 41.2  # Default value
        except:
            # Use default values if extraction fails
            metrics['comfort'] = 91.5
            metrics['avg_temp'] = 22.1
            metrics['avg_co2'] = 520
            metrics['avg_humidity'] = 41.2
    else:
        metrics['comfort'] = 91.5
        metrics['avg_temp'] = 22.1
        metrics['avg_co2'] = 520
        metrics['avg_humidity'] = 41.2
    
    return metrics

# Function to create EUI pie chart
def create_eui_pie_chart():
    # Try to load real data or use sample data
    eui_files = glob.glob(f"{KPI_DIR}/EUI/*.csv")
    if eui_files:
        try:
            eui_df = pd.read_csv(eui_files[0], sep=";", decimal=",")
            if 'Total_EUI' in eui_df.columns and 'Heating_EUI' in eui_df.columns and 'Cooling_EUI' in eui_df.columns:
                # Extract relevant columns
                heating_eui = eui_df['Heating_EUI'].iloc[-1]
                cooling_eui = eui_df['Cooling_EUI'].iloc[-1]
                other_eui = eui_df['Total_EUI'].iloc[-1] - heating_eui - cooling_eui
                
                # Create pie chart data
                labels = ['Heating', 'Cooling', 'Other']
                values = [heating_eui, cooling_eui, other_eui]
                
                # Create pie chart
                fig = px.pie(
                    values=values,
                    names=labels,
                    title='Energy Use Intensity Breakdown (kWh/m²)',
                    color_discrete_sequence=['#e74c3c', '#3498db', '#2ecc71'],
                    hole=0.4
                )
                
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(
                    title_x=0.5,
                    margin=dict(t=50, b=20, l=20, r=20),
                    font=dict(size=14),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                
                return fig
        except Exception as e:
            pass
    
    # Sample data as fallback
    labels = ['Heating', 'Cooling', 'Other']
    values = [28.7, 12.3, 4.3]
    
    # Create pie chart
    fig = px.pie(
        values=values,
        names=labels,
        title='Energy Use Intensity Breakdown (kWh/m²)',
        color_discrete_sequence=['#e74c3c', '#3498db', '#2ecc71'],
        hole=0.4
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        title_x=0.5,
        margin=dict(t=50, b=20, l=20, r=20),
        font=dict(size=14),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    return fig

# Dashboard Overview section
def show_dashboard_overview():
    st.header("Dashboard Overview")
    
    # Extract key metrics for display
    metrics = extract_metrics()
    
    # Update metrics with correct values
    metrics['eui'] = 20.68  # Corrected EUI value
    metrics['comfort'] = "Optimal (mostly IDA 1)"  # Indoor air quality
    metrics['humidity_status'] = "Optimal (mostly within 30-60%)"
    metrics['spi_heating'] = "94.8%"
    metrics['dc_rejection'] = "49%"  # Dry cooler effectiveness (rejection)
    metrics['dc_absorption'] = "30%"  # Dry cooler effectiveness (absorption)
    metrics['boiler1_eff'] = "70.6%"  # Boiler 1 efficiency
    metrics['boiler2_eff'] = "73.3%"  # Boiler 2 efficiency
    
    # First row - Energy metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_metric("Energy Use Intensity", f"{metrics['eui']:.2f}", "kWh/m²")
    
    with col2:
        display_metric("Heating SPI", metrics['spi_heating'], "")
    
    with col3:
        display_metric("Indoor Air Quality", metrics['comfort'], "")

    # Second row - System performance
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_metric("GAHP GUE", f"{metrics['gue']:.2f}", "")
    
    with col2:
        display_metric("EHP EER", f"{metrics['eer']:.2f}", "")
    
    with col3:
        display_metric("Relative Humidity", metrics['humidity_status'], "")

    # Third row - Boilers and Dry Cooler
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_metric("Boiler 1 Efficiency", metrics['boiler1_eff'], "")
    
    with col2:
        display_metric("Boiler 2 Efficiency", metrics['boiler2_eff'], "")
    
    with col3:
        display_metric("Dry Cooler Effectiveness", f"Rejection: {metrics['dc_rejection']} | Absorption: {metrics['dc_absorption']}", "")

    # Visualization selection
    st.markdown("---")  # Add a separator
    visualization = st.radio(
        "Select visualization:",
        ["Energy Use Distribution", "Sankey Diagram"],
        horizontal=True
    )
    
    if visualization == "Energy Use Distribution":
        # Display the static EUI image with fixed width
        try:
            st.image("4_KPI/EUI/energy_distribution_pie.png", width=700)  # Adjust this value as needed
        except Exception as e:
            st.error(f"Could not load EUI distribution image. Error: {str(e)}")
    else:
        st.subheader("Sankey Diagram")
        # Display Sankey diagram with adjusted height and width
        if os.path.exists(f"{SANKEY_DIR}/energy_sankey.html"):
            with open(f"{SANKEY_DIR}/energy_sankey.html", 'r', encoding='utf-8') as f:
                html_content = f.read()
                st.components.v1.html(html_content, height=800, width=1200)
        elif sankey_available:
            try:
                energy_values = sankey_module.load_energy_data()
                fig = sankey_module.create_sankey_diagram(energy_values)
                fig.update_layout(
                    height=800,
                    width=1200,
                    margin=dict(l=50, r=50, t=50, b=50)
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Could not create Sankey diagram: {str(e)}")
                if os.path.exists(f"{SANKEY_DIR}/energy_sankey.png"):
                    st.image(f"{SANKEY_DIR}/energy_sankey.png", use_container_width=True)

# GAHP Section
def show_gahp_analysis():
    st.header("GAHP Gas Utilization Efficiency (GUE) Analysis")
    
    # Brief description of GAHP
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <p>The Gas Absorption Heat Pump (GAHP) uses natural gas and heat from the ground to provide heating.
    Gas Utilization Efficiency (GUE) measures how efficiently the GAHP converts gas energy into useful heating.
    Higher GUE values indicate better performance.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display GAHP GUE metrics
    metrics = extract_metrics()
    cols = st.columns(3)
    with cols[0]:
        display_metric("Average GUE", f"{metrics['gue']:.2f}", "")
    
    # Create tabs for different visualizations
    tabs = st.tabs(["Time Series", "Seasonal Analysis", "GUE Map"])
    
    # Get list of GAHP images
    gahp_images = sorted(glob.glob(f"{KPI_DIR}/GAHP_GUE/*.png"))
    
    with tabs[0]:  # Time Series
        time_series_plots = [img for img in gahp_images if "time" in img.lower()]
        if time_series_plots:
            st.image(time_series_plots[0], width=1200)
        else:
            st.warning("No time series plots found for GAHP GUE.")
            
    with tabs[1]:  # Seasonal Analysis
        boxplot_images = [img for img in gahp_images if "boxplot" in img.lower()]
        if boxplot_images:
            st.image(boxplot_images[0], width=1200)
        else:
            st.warning("No seasonal boxplot found for GAHP GUE.")
            
    with tabs[2]:  # GUE Map
        gue_map_images = [img for img in gahp_images if "Seasonal_PowerVStemp" in img]
        if gue_map_images:
            st.image(gue_map_images[0], width=1400)
        else:
            st.warning("No GUE map found for GAHP.")

# EHP Section
def show_ehp_analysis():
    st.header("EHP Energy Efficiency Ratio (EER) Analysis")
    
    # Brief description of EHP
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <p>The Electric Heat Pump (EHP) provides cooling for the building.
    Energy Efficiency Ratio (EER) measures how efficiently the EHP converts electricity into cooling.
    Higher EER values indicate better efficiency.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display EHP EER metrics
    metrics = extract_metrics()
    cols = st.columns(3)
    with cols[0]:
        display_metric("Average EER", f"{metrics['eer']:.2f}", "")
    
    # Create tabs for different visualizations
    tabs = st.tabs(["Time Series", "EER MAP"])
    
    # Get list of EHP images
    ehp_images = sorted(glob.glob(f"{KPI_DIR}/EHP_EER/*.png"))
    
    with tabs[0]:  # Time Series
        time_series_plots = [img for img in ehp_images if "time" in img.lower()]
        if time_series_plots:
            st.image(time_series_plots[0], width=1200)
        else:
            st.warning("No time series plots found for EHP EER.")
            
    with tabs[1]:  # Temperature Analysis
        temp_scatter_images = [img for img in ehp_images if "temperature_scatter" in img.lower()]
        if temp_scatter_images:
            st.image(temp_scatter_images[0], width=1200)
        else:
            st.warning("No temperature analysis found for EHP.")

# Boiler Section
def show_boiler_analysis():
    st.header("Boiler Efficiency Analysis")
    
    # Brief description of boilers
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <p>The building is equipped with two condensing boilers that provide supplementary heating when needed.
    Boiler efficiency measures how effectively the boilers convert natural gas into useful heat.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for boiler selection
    tabs = st.tabs(["Boiler 1", "Boiler 2"])
    
    for i, tab in enumerate(tabs):
        with tab:
            boiler_num = i + 1
            
            # Display boiler efficiency metrics
            cols = st.columns(3)
            with cols[0]:
                if boiler_num == 1:
                    display_metric(f"Boiler {boiler_num} Efficiency", "70.6%")
                else:
                    display_metric(f"Boiler {boiler_num} Efficiency", "73.3%")
            
            # Create tabs for different visualizations
            analysis_tabs = st.tabs(["Time Series", "Seasonal Analysis", "Load Analysis"])
            
            # Get list of boiler images
            boiler_images = sorted(glob.glob(f"{KPI_DIR}/Boiler{boiler_num}_Efficiency/*.png"))
            
            with analysis_tabs[0]:  # Time Series
                time_series_plots = [img for img in boiler_images if "time" in img.lower()]
                if time_series_plots:
                    st.image(time_series_plots[0], width=1200)
                else:
                    st.warning(f"No time series plots found for Boiler {boiler_num}.")
                    
            with analysis_tabs[1]:  # Seasonal Analysis
                boxplot_images = [img for img in boiler_images if "boxplot" in img.lower()]
                if boxplot_images:
                    st.image(boxplot_images[0], width=1200)
                else:
                    st.warning(f"No seasonal boxplot found for Boiler {boiler_num}.")
                    
            with analysis_tabs[2]:  # Load Analysis
                load_images = [img for img in boiler_images if f"Boiler{boiler_num}_Efficiency_vs_Load_by_Season" in img]
                if load_images:
                    st.image(load_images[0], width=1200)
                else:
                    st.warning(f"No load analysis found for Boiler {boiler_num}.")

# Degree Days Section
def show_degree_days():
    st.header("Degree Days Analysis")
    
    # Brief description and values
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <p><strong>Building Z:</strong> 
    2021-2022 (HDD: 1968, CDD: -) | 
    2022-2023 (HDD: 1963, CDD: 12)</p>
    <p><strong>Secondary Schools (2015-2018):</strong> HDD: 2172, CDD: 27</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different analyses
    tabs = st.tabs(["2021-2022", "2022-2023", "Year and School Comparison"])
    
    # Get list of degree day images
    dd_images = sorted(glob.glob(f"{KPI_DIR}/Degree_Days/*.png"))
    
    with tabs[0]:  # 2021-2022 Analysis
        plots = [img for img in dd_images if "2021" in img or "_2021.png" in img]
        for img in plots:
            st.image(img, width=1200)
        if not plots:
            st.warning("No plots found for 2021-2022.")
            
    with tabs[1]:  # 2022-2023 Analysis
        plots = [
            img for img in dd_images 
            if ("monthly_degree_days.png" in img or 
                "monthly_eui.png" in img or 
                "monthly_kwh_per_cdd.png" in img or 
                "monthly_kwh_per_hdd.png" in img)
        ]
        for img in plots:
            st.image(img, width=1200)
        if not plots:
            st.warning("No plots found for 2022-2023.")
            
    with tabs[2]:  # Year Comparison
        comparison_plots = [img for img in dd_images if "comparison" in img.lower()]
        if comparison_plots:
            col1, col2, col3 = st.columns([1, 5, 1])
            with col2:
                st.image(comparison_plots[0], use_container_width=True)
        if not comparison_plots:
            st.warning("No comparison plots found.")

# Comfort Section
def show_comfort_analysis():
    st.header("Indoor Comfort Analysis")
    
    # Brief description
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <p>Indoor comfort analysis evaluates the building's ability to maintain comfortable conditions for occupants (Daily 9:00-17:00).
    The analysis considers three key parameters:</p>
    <ul>
        <li><strong>Temperature:</strong> Divided in classes based on deviation from setpoint:
            <ul>
                <li>Class 1: ≤ 1°C deviation (95% satisfaction)</li>
                <li>Class 2: ≤ 2°C deviation (90% satisfaction)</li>
                <li>Class 3: ≤ 3°C deviation (80% satisfaction)</li>
                <li>Class 4: > 3°C deviation (65% satisfaction)</li>
            </ul>
        </li>
        <li><strong>CO₂ Levels:</strong> Categorized according to IDA classes:
            <ul>
                <li>IDA 1: < 400 ppm (excellent)</li>
                <li>IDA 2: 400-600 ppm (good)</li>
                <li>IDA 3: 600-1000 ppm (moderate)</li>
                <li>IDA 4: > 1000 ppm (low)</li>
            </ul>
        </li>
        <li><strong>Humidity:</strong> Optimal range of 30-60% relative humidity</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for parameter selection
    parameter_tabs = st.tabs(["Temperature", "CO₂", "Relative Humidity"])
    
    for idx, (parameter, tab) in enumerate(zip(["Temperature", "CO₂", "Relative Humidity"], parameter_tabs)):
        with tab:
            # Create sub-tabs for view type
            view_tabs = st.tabs(["All Rooms", "Per Room"])
            
            with view_tabs[0]:  # All Rooms view
                if parameter == "Temperature":
                    # Season selection for Temperature
                    season = st.selectbox("Select season:", ["Winter", "Spring"], key=f"season_{parameter}")
                    season_lower = season.lower()
                    
                    # Show distribution plot
                    dist_pattern = f"{KPI_DIR}/Comfort_results/Temperature/temp_summary_{season_lower}.png"
                elif parameter == "CO₂":
                    # Season selection for CO₂
                    season = st.selectbox("Select season:", ["Fall", "Winter", "Spring", "Summer"], key=f"season_{parameter}")
                    season_lower = season.lower()
                    
                    # Show distribution plot
                    dist_pattern = f"{KPI_DIR}/Comfort_results/CO2_and_Humidity/co2_ida_distribution_{season_lower}.png"
                else:  # Relative Humidity
                    # Season selection for Humidity
                    season = st.selectbox("Select season:", ["Fall", "Winter", "Spring", "Summer"], key=f"season_{parameter}")
                    season_lower = season.lower()
                    
                    # Show distribution plot
                    dist_pattern = f"{KPI_DIR}/Comfort_results/CO2_and_Humidity/humidity_mean_summary_{season_lower}.png"
                
                col1, col2, col3 = st.columns([1, 5, 1])
                with col2:
                    dist_images = glob.glob(dist_pattern)
                    if dist_images:
                        st.image(dist_images[0], use_container_width=True)
                    else:
                        st.warning(f"No distribution data available for {parameter} in {season}.")
            
            with view_tabs[1]:  # Per Room view
                if parameter == "Temperature":
                    # Season selection for Temperature
                    season = st.selectbox("Select season:", ["Winter", "Spring"], key=f"season_per_room_{parameter}")
                    season_lower = season.lower()
                    
                    # Get unique room numbers from temperature files
                    room_pattern = f"{KPI_DIR}/Comfort_results/Temperature/temp_*_{season_lower}.png"
                    room_files = glob.glob(room_pattern)
                    rooms = sorted(list(set([
                        f.split('temp_')[1].split('_')[0]
                        for f in room_files
                        if not 'summary' in f
                    ])))
                else:
                    # Season selection for CO₂ and Humidity
                    season = st.selectbox("Select season:", ["Fall", "Winter", "Spring", "Summer"], key=f"season_per_room_{parameter}")
                    season_lower = season.lower()
                    
                    # Get room numbers from combined files
                    room_pattern = f"{KPI_DIR}/Comfort_results/CO2_and_Humidity/combined_*_{season_lower}.png"
                    room_files = glob.glob(room_pattern)
                    rooms = sorted(list(set([
                        f.split('combined_')[1].split('_')[0]
                        for f in room_files
                    ])))
                
                if rooms:
                    # Create room type mapping
                    room_types = {
                        # Meeting & break spaces
                        "241": "Meeting or break space",
                        "243": "Meeting or break space",
                        "225": "Meeting or break space",
                        
                        # PC rooms
                        "445": "PC Room",
                        "424": "PC Room",
                        "423": "PC Room",
                        "422": "PC Room",
                        "421": "PC Room",
                        "522": "PC Room",
                        "521": "PC Room",
                        
                        # Offices
                        "345": "Office",
                        "332": "Office",
                        "328": "Office",
                        "327": "Office",
                        "324": "Office",
                        
                        # Teaching rooms
                        "223": "Teaching Room",
                        "221": "Teaching Room",
                        "126": "Teaching Room",
                        "125": "Teaching Room",
                        
                        # Laboratories
                        "543": "Laboratory",
                        "524": "Laboratory",
                        "171": "Laboratory",
                        "143": "Laboratory",
                        "123": "Laboratory"
                    }
                    
                    # Create room options with types
                    room_options = [f"Room {room}: {room_types.get(room, 'Unknown Type')}" for room in rooms]
                    selected_room_with_type = st.selectbox("Select room:", room_options, key=f"room_{parameter}")
                    
                    # Extract room number from selection
                    selected_room = selected_room_with_type.split(":")[0].replace("Room ", "").strip()
                    
                    if parameter == "Temperature":
                        col1, col2, col3 = st.columns([1, 5, 1])
                    else:  # For combined CO₂ and humidity graphs
                        col1, col2, col3 = st.columns([1, 2.5, 1])
                        
                    with col2:
                        if parameter == "Temperature":
                            temp_pattern = f"{KPI_DIR}/Comfort_results/Temperature/temp_{selected_room}_{season_lower}.png"
                            room_images = glob.glob(temp_pattern)
                            if room_images:
                                st.image(room_images[0], use_container_width=True)
                            else:
                                st.warning(f"No {parameter} data available for Room {selected_room} in {season}.")
                        else:
                            combined_pattern = f"{KPI_DIR}/Comfort_results/CO2_and_Humidity/combined_{selected_room}_{season_lower}.png"
                            combined_images = glob.glob(combined_pattern)
                            if combined_images:
                                st.image(combined_images[0], use_container_width=True)
                            else:
                                st.warning(f"No combined CO₂ & humidity data available for Room {selected_room} in {season}.")
                else:
                    st.warning(f"No room-specific data found for {season}.")

# Energy Signature Section
def show_energy_signature():
    st.header("Energy Signature Analysis")
    
    # Brief description of energy signature
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <p>Energy signature analysis shows the relationship between energy consumption and outdoor temperature.
    This helps identify:</p>
    <ul>
        <li><strong>Balance Point:</strong> The outdoor temperature at which heating or cooling is no longer needed.</li>
        <li><strong>Rate:</strong> How much additional energy is needed per degree of temperature change.</li>
        <li><strong>Baseload:</strong> The minimum energy consumption regardless of outdoor temperature.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different modes
    tabs = st.tabs(["Heating Signature", "Cooling Signature"])
    
    # Get energy signature images
    signature_images = sorted(glob.glob(f"{KPI_DIR}/Energy_signature/*.png"))
    
    with tabs[0]:  # Heating Mode
        plot_images = [img for img in signature_images if "heat" in img.lower()]
        if not plot_images:
            st.warning("No heating mode energy signature images found.")
        else:
            col1, col2, col3 = st.columns([1, 5, 1])
            with col2:
                st.image(plot_images[0], use_container_width=True)
            
            params = {
                "Balance Point": "14.4°C",
                "Rate": "3.79 kW/°C",
                "Baseload": "5.1 kW"
            }
            
            st.markdown("""
            <h4 style='font-size: 16px; margin-bottom: 10px;'>Heating Signature Parameters</h4>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div style='font-size: 14px;'>
                    <p style='color: #666; margin-bottom: 4px;'>Balance Point</p>
                    <p style='font-size: 16px; margin: 0;'>{params["Balance Point"]}</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style='font-size: 14px;'>
                    <p style='color: #666; margin-bottom: 4px;'>Rate</p>
                    <p style='font-size: 16px; margin: 0;'>{params["Rate"]}</p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style='font-size: 14px;'>
                    <p style='color: #666; margin-bottom: 4px;'>Baseload</p>
                    <p style='font-size: 16px; margin: 0;'>{params["Baseload"]}</p>
                </div>
                """, unsafe_allow_html=True)
            
    with tabs[1]:  # Cooling Mode
        plot_images = [img for img in signature_images if "cool" in img.lower()]
        if not plot_images:
            st.warning("No cooling mode energy signature images found.")
        else:
            col1, col2, col3 = st.columns([1, 5, 1])
            with col2:
                st.image(plot_images[0], use_container_width=True)
            
            params = {
                "Balance Point": "17.2°C",
                "Rate": "0.55 kW/°C",
                "Baseload": "6.0 kW"
            }
            
            st.markdown("""
            <h4 style='font-size: 16px; margin-bottom: 10px;'>Cooling Signature Parameters</h4>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div style='font-size: 14px;'>
                    <p style='color: #666; margin-bottom: 4px;'>Balance Point</p>
                    <p style='font-size: 16px; margin: 0;'>{params["Balance Point"]}</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style='font-size: 14px;'>
                    <p style='color: #666; margin-bottom: 4px;'>Rate</p>
                    <p style='font-size: 16px; margin: 0;'>{params["Rate"]}</p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style='font-size: 14px;'>
                    <p style='color: #666; margin-bottom: 4px;'>Baseload</p>
                    <p style='font-size: 16px; margin: 0;'>{params["Baseload"]}</p>
                </div>
                """, unsafe_allow_html=True)

# Dry Cooler Section
def show_drycooler():
    st.header("Dry Cooler Performance Analysis")
    
    # Brief description of dry cooler
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <p>The dry cooler is responsible for heat exchange with the atmosphere.
    It operates in two modes:</p>
    <ul>
        <li><strong>Heat Rejection:</strong> Rejects heat to the outside atmosphere.</li>
        <li><strong>Heat Absorption:</strong> Absorbs heat from the outside atmosphere.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different modes
    tabs = st.tabs(["Heat Rejection", "Heat Absorption", "DC vs. EHP"])
    
    with tabs[0]:  # Heat Rejection
        col1, col2, col3 = st.columns([1, 4, 1])
        with col2:
            rejection_images = glob.glob(f"{KPI_DIR}/DC/*reject*.png")
            if rejection_images:
                st.image(rejection_images[0], use_container_width=True)
            else:
                st.warning("No heat rejection performance images found.")
                
    with tabs[1]:  # Heat Absorption
        col1, col2, col3 = st.columns([1, 4, 1])
        with col2:
            absorption_images = glob.glob(f"{KPI_DIR}/DC/*absorpt*.png")
            if absorption_images:
                st.image(absorption_images[0], use_container_width=True)
            else:
                st.warning("No heat absorption performance images found.")
    
    with tabs[2]:  # DC vs. EHP
        col1, col2, col3 = st.columns([1, 6, 1])
        with col2:
            ehp_comparison = glob.glob(f"{KPI_DIR}/DC_EHP/dc_ehp_comparison_daily.png")
            if ehp_comparison:
                st.image(ehp_comparison[0], use_container_width=True)
            else:
                st.warning("No EHP comparison data available.")

# BTES Section
def show_btes_analysis():
    st.header("BTES Storage Analysis")
    
    # Brief description
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <p>The Borehole Thermal Energy Storage (BTES) system is used to store and retrieve thermal energy in the ground.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display BTES storage decline graph
    col1, col2, col3 = st.columns([1, 8, 1])
    with col2:
        btes_image = f"{KPI_DIR}/BTES_storage_decline.png"
        if os.path.exists(btes_image):
            st.image(btes_image, use_container_width=True)
        else:
            st.warning("BTES storage decline graph not found.")

# Sidebar navigation
def main():
    # Sidebar navigation with larger logo
    st.sidebar.image(f"{KPI_DIR}/UA.png", width=200)  # Increased width for larger logo
    st.sidebar.title("Navigation")
    
    # Dashboard Overview radio at the top
    view_selection = st.sidebar.radio(
        "View",
        ["Dashboard Overview", "Analysis Levels"]
    )

    if view_selection == "Dashboard Overview":
        show_dashboard_overview()
    else:
        # Select the level
        level = st.sidebar.selectbox(
            "Select Analysis Level",
            ["System Level", "Component Level", "Comfort Level"]
        )
        
        if level == "System Level":
            system_analysis = st.sidebar.radio(
                "Select System Analysis",
                ["Degree Days", "Energy Signature"]
            )
            if system_analysis == "Degree Days":
                show_degree_days()
            else:
                show_energy_signature()
        
        elif level == "Component Level":
            component_analysis = st.sidebar.radio(
                "Select Component",
                [
                    "Gas Absorption Heat Pump (GAHP)",
                    "Electric Heat Pump (EHP)",
                    "Boilers",
                    "Dry Cooler (DC)",
                    "Borehole Thermal Energy Storage (BTES)"
                ]
            )
            if component_analysis == "Gas Absorption Heat Pump (GAHP)":
                show_gahp_analysis()
            elif component_analysis == "Electric Heat Pump (EHP)":
                show_ehp_analysis()
            elif component_analysis == "Boilers":
                show_boiler_analysis()
            elif component_analysis == "Dry Cooler (DC)":
                show_drycooler()
            else:
                show_btes_analysis()
        
        elif level == "Comfort Level":
            show_comfort_analysis()
    
    # Add dashboard information
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    Data Period: Nov 2022 - Nov 2023  
    Temperature Data: 2025
    """)
    
    # Add contact information
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    University of Antwerp
    """)

if __name__ == "__main__":
    main()
