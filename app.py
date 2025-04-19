import streamlit as st
import pandas as pd
import plotly.express as px
import os
from data_storage import load_activity_data, DATA_FILE, DATA_DIR
from screenshot_capture import SCREENSHOT_DIR # To build image paths

st.set_page_config(layout="wide")

st.title("AI Task Tracker Analysis")

# --- Load Data ---
st.header("Activity Log")
df = load_activity_data()

if df.empty:
    st.warning(f"No activity data found in '{DATA_FILE}'. Run the main tracker script (`main.py`) first.")
    st.stop() # Stop execution if no data

# Convert Timestamp if it's not already datetime (might happen if load fails partially)
if 'Timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['Timestamp']):
     df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
     df = df.dropna(subset=['Timestamp']) # Remove rows where conversion failed

# --- Display Raw Data ---
st.dataframe(df.sort_values(by="Timestamp", ascending=False))

# --- Data Filtering ---
st.sidebar.header("Filters")
# Date Range Filter
min_date = df['Timestamp'].min().date()
max_date = df['Timestamp'].max().date()
selected_date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(selected_date_range) == 2:
    start_date = pd.to_datetime(selected_date_range[0]).normalize() # Start of the day
    end_date = pd.to_datetime(selected_date_range[1]) + pd.Timedelta(days=1) # End of the day
    df_filtered = df[(df['Timestamp'] >= start_date) & (df['Timestamp'] < end_date)].copy() # Use .copy()
else:
    st.sidebar.warning("Please select a valid date range (start and end).")
    df_filtered = df.copy() # Show all data if range is invalid

# Main Topic Filter
topics = sorted(df_filtered['MainTopic'].unique())
topics_with_all = ["Select All"] + topics  # Add "Select All" option
selected_topics = st.sidebar.multiselect("Filter by Main Topic", options=topics_with_all, default=["Select All"])

if "Select All" in selected_topics:
    # Keep all topics if "Select All" is selected
    pass
else:
    # Filter by selected topics
    df_filtered = df_filtered[df_filtered['MainTopic'].isin(selected_topics)]


if df_filtered.empty and not df.empty:
     st.warning("No data matches the selected filters.")
     st.stop()
elif df_filtered.empty:
     st.warning("No data available.") # Should have been caught earlier, but just in case
     st.stop()


# Create tabs for analysis and screenshot viewer
analysis_tab, screenshot_tab = st.tabs(["Analysis", "Screenshot Viewer"])

# --- Visualizations ---
with analysis_tab:
    st.header("Analysis")

    # 1. Time Spent per Topic (Approximate)
    st.subheader("Approximate Time Spent per Topic")
    # Calculate time difference between consecutive entries for the *same* topic
    # This is an approximation, assuming continuous work between screenshots of the same topic
    df_filtered = df_filtered.sort_values(by=['MainTopic', 'Timestamp'])
    df_filtered['TimeDiff'] = df_filtered.groupby('MainTopic')['Timestamp'].diff()

    # Define a reasonable max duration between screenshots to consider it "continuous"
    MAX_CONTINUOUS_MINUTES = 10 # Adjust as needed
    df_filtered['Duration'] = df_filtered['TimeDiff'].apply(
        lambda x: x.total_seconds() / 60 if pd.notnull(x) and x <= pd.Timedelta(minutes=MAX_CONTINUOUS_MINUTES) else 0
    )

    topic_time = df_filtered.groupby('MainTopic')['Duration'].sum().reset_index()
    topic_time = topic_time[topic_time['Duration'] > 0] # Filter out topics with no calculated duration
    topic_time = topic_time.sort_values(by='Duration', ascending=False)

    if not topic_time.empty:
        fig_topic_time = px.bar(topic_time, x='MainTopic', y='Duration', title="Time per Topic (Minutes)",
                              labels={'Duration': 'Total Minutes (Approx.)', 'MainTopic': 'Topic'})
        st.plotly_chart(fig_topic_time, use_container_width=True)
    else:
        st.info("Not enough consecutive data points to estimate time spent per topic with current filters.")


    # 2. Activity Count per Main Topic
    st.subheader("Activity Count per Main Topic")
    topic_counts = df_filtered['MainTopic'].value_counts().reset_index()
    topic_counts.columns = ['MainTopic', 'Count']
    topic_counts = topic_counts.sort_values(by='Count', ascending=False)

    if not topic_counts.empty:
        fig_topic_counts = px.pie(topic_counts, names='MainTopic', values='Count', title="Activities per Main Topic")
        st.plotly_chart(fig_topic_counts, use_container_width=True)
    else:
         st.info("No topic data available for the selected filters.")


    # 3. Timeline of Activities
    st.subheader("Activity Timeline")
    if not df_filtered.empty:
        # Ensure ScreenshotFile column exists
        if 'ScreenshotFile' not in df_filtered.columns:
            df_filtered['ScreenshotFile'] = None # Add dummy column if missing

        # Create hover text
        df_filtered['HoverText'] = df_filtered.apply(
            lambda row: f"Time: {row['Timestamp'].strftime('%H:%M:%S')}<br>"
                        f"App: {row['AppName']}<br>"
                        f"Topic: {row['MainTopic']}<br>"
                        f"Desc: {row['CrispDescription']}",
            axis=1
        )
        fig_timeline = px.scatter(df_filtered, x='Timestamp', y='MainTopic', 
                                  title="Activity Timeline by Main Topic",
                                  hover_data=['HoverText'],
                                  labels={'MainTopic': 'Topic', 'Timestamp': 'Time'})
        fig_timeline.update_layout(xaxis_title="Time", yaxis_title="Topic")
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No data points available for the timeline with current filters.")


# --- Screenshot Viewer ---
with screenshot_tab:
    st.header("Screenshot Viewer")
    if 'ScreenshotFile' in df_filtered.columns and not df_filtered['ScreenshotFile'].isnull().all():
        # Select a record to view screenshot
        record_options = df_filtered.apply(lambda row: f"{row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {row['AppName']} ({row['MainTopic']})", axis=1)
        selected_record = st.selectbox("Select activity record to view screenshot:", options=record_options)

        if selected_record:
            # Find the corresponding row
            selected_row = df_filtered[record_options == selected_record].iloc[0]
            screenshot_filename = selected_row['ScreenshotFile']
            if screenshot_filename and isinstance(screenshot_filename, str):
                screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_filename)
                if os.path.exists(screenshot_path):
                    st.image(screenshot_path, caption=f"Screenshot for: {selected_record}", use_container_width=True)
                    st.write(f"**Crisp Description:** {selected_row['CrispDescription']}")
                    st.write(f"**Short Description:** {selected_row['ShortDescription']}")
                else:
                    st.warning(f"Screenshot file not found: {screenshot_path}")
            else:
                st.info("No screenshot file recorded for this entry.")

    else:
        st.info("No screenshots available or 'ScreenshotFile' column missing in the filtered data.")

