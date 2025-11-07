import streamlit as st
import pandas as pd
from datetime import datetime, time
import json
import os

# Page configuration
st.set_page_config(
    page_title="Working Hours Tracker",
    page_icon="⏰",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# File to store data
DATA_FILE = 'timesheet_data.json'

# Initialize session state
if 'entries' not in st.session_state:
    st.session_state.entries = []
    # Load existing data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                st.session_state.entries = json.load(f)
        except:
            st.session_state.entries = []

def save_data():
    """Save data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(st.session_state.entries, f, indent=2)

def calculate_hours(start_time, end_time, break_minutes):
    """Calculate working hours"""
    if not start_time or not end_time:
        return 0
    
    start_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute
    
    total_minutes = end_minutes - start_minutes - break_minutes
    
    return round(total_minutes / 60, 2) if total_minutes > 0 else 0

def get_month_year(date_str):
    """Get month-year string from date"""
    d = datetime.strptime(date_str, '%Y-%m-%d')
    return d.strftime('%Y-%m')

def format_month_display(month_year):
    """Format month for display"""
    d = datetime.strptime(month_year, '%Y-%m')
    return d.strftime('%B %Y')

# Header
st.markdown("<h1 style='text-align: center; color: #667eea;'>⏰ Working Hours Tracker</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Track your daily working hours with ease</p>", unsafe_allow_html=True)
st.markdown("---")

# Input section
st.markdown("### 📝 Add New Entry")

col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1.5, 1.5])

with col1:
    entry_date = st.date_input("Date", datetime.now(), key="date_input")

with col2:
    start_time = st.time_input("Start Time", time(9, 0), key="start_time")

with col3:
    end_time = st.time_input("End Time", time(17, 0), key="end_time")

with col4:
    break_minutes = st.number_input("Break (mins)", min_value=0, value=30, step=5, key="break_mins")

with col5:
    st.markdown("<br>", unsafe_allow_html=True)
    add_button = st.button("➕ Add Entry", type="primary", use_container_width=True)

# Add entry logic
if add_button:
    hours = calculate_hours(start_time, end_time, break_minutes)
    
    if hours > 0:
        entry = {
            'id': len(st.session_state.entries) + 1,
            'date': entry_date.strftime('%Y-%m-%d'),
            'start_time': start_time.strftime('%H:%M'),
            'end_time': end_time.strftime('%H:%M'),
            'break_minutes': break_minutes,
            'hours': hours
        }
        
        st.session_state.entries.append(entry)
        # Sort by date
        st.session_state.entries.sort(key=lambda x: x['date'], reverse=True)
        save_data()
        st.success(f"✅ Entry added successfully! {hours} hours logged.")
        st.rerun()
    else:
        st.error("❌ End time must be after start time!")

st.markdown("---")

# Display last 5 entries
if st.session_state.entries:
    st.markdown("### 📋 Recent Entries (Last 5)")
    
    last_5 = st.session_state.entries[:5]
    
    for idx, entry in enumerate(last_5):
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 1.5, 1.5, 1, 1.5, 1])
            
            with col1:
                st.markdown(f"**📅 {entry['date']}**")
            with col2:
                st.write(f"🕐 {entry['start_time']}")
            with col3:
                st.write(f"🕔 {entry['end_time']}")
            with col4:
                st.write(f"☕ {entry['break_minutes']}m")
            with col5:
                st.markdown(f"**⏱️ {entry['hours']} hrs**")
            with col6:
                if st.button("🗑️", key=f"del_{entry['id']}", help="Delete entry"):
                    st.session_state.entries = [e for e in st.session_state.entries if e['id'] != entry['id']]
                    save_data()
                    st.rerun()
            
            if idx < len(last_5) - 1:
                st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Summary metrics
    st.markdown("### 📊 Summary")
    
    col1, col2, col3 = st.columns(3)
    
    total_entries = len(st.session_state.entries)
    total_hours = sum(e['hours'] for e in st.session_state.entries)
    months = len(set(get_month_year(e['date']) for e in st.session_state.entries))
    
    with col1:
        st.metric("Total Entries", total_entries, delta=None)
    
    with col2:
        st.metric("Total Hours", f"{total_hours:.2f} hrs", delta=None)
    
    with col3:
        st.metric("Months Tracked", months, delta=None)
    
    st.markdown("---")
    
    # Month selector and detailed view
    st.markdown("### 📅 View by Month")
    
    # Get unique months
    unique_months = sorted(list(set(get_month_year(e['date']) for e in st.session_state.entries)), reverse=True)
    
    selected_month = st.selectbox(
        "Select Month",
        unique_months,
        format_func=format_month_display,
        key="month_select"
    )
    
    # Filter entries by month
    month_entries = [e for e in st.session_state.entries if get_month_year(e['date']) == selected_month]
    month_total = sum(e['hours'] for e in month_entries)
    
    st.markdown(f"**{format_month_display(selected_month)} - Total: {month_total:.2f} hours**")
    
    # Create DataFrame for display
    df = pd.DataFrame(month_entries)
    df = df[['date', 'start_time', 'end_time', 'break_minutes', 'hours']]
    df.columns = ['Date', 'Start', 'End', 'Break (mins)', 'Hours']
    df = df.sort_values('Date', ascending=False)
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Download section
    st.markdown("### 💾 Download Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download current month
        csv_month = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Current Month",
            data=csv_month,
            file_name=f"timesheet_{selected_month}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Download all data
        df_all = pd.DataFrame(st.session_state.entries)
        df_all = df_all[['date', 'start_time', 'end_time', 'break_minutes', 'hours']]
        df_all.columns = ['Date', 'Start', 'End', 'Break (mins)', 'Hours']
        df_all = df_all.sort_values('Date', ascending=False)
        
        csv_all = df_all.to_csv(index=False)
        st.download_button(
            label="📥 Download All Data",
            data=csv_all,
            file_name=f"timesheet_all_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Clear all data option
    st.markdown("---")
    with st.expander("⚠️ Danger Zone"):
        st.warning("This will delete all your data permanently!")
        if st.button("🗑️ Clear All Data", type="secondary"):
            st.session_state.entries = []
            save_data()
            st.success("All data cleared!")
            st.rerun()

else:
    st.info("👋 No entries yet! Add your first working hours entry above.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #999; font-size: 12px;'>Made with ❤️ using Streamlit</p>", unsafe_allow_html=True)
