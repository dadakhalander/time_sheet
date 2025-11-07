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

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
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
                data = json.load(f)
                st.session_state.entries = data if isinstance(data, list) else []
        except Exception as e:
            st.session_state.entries = []

def save_data():
    """Save data to JSON file"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(st.session_state.entries, f, indent=2)
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")

def calculate_hours(start_time, end_time, break_minutes):
    """Calculate working hours"""
    try:
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute
        
        total_minutes = end_minutes - start_minutes - break_minutes
        
        return round(total_minutes / 60, 2) if total_minutes > 0 else 0
    except:
        return 0

def get_month_year(date_str):
    """Get month-year string from date"""
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d')
        return d.strftime('%Y-%m')
    except:
        return "Unknown"

def format_month_display(month_year):
    """Format month for display"""
    try:
        d = datetime.strptime(month_year, '%Y-%m')
        return d.strftime('%B %Y')
    except:
        return month_year

# Header
st.title("⏰ Working Hours Tracker")
st.markdown("Track your daily working hours with ease")
st.divider()

# Input section
st.subheader("📝 Add New Entry")

col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1.5, 1.5])

with col1:
    entry_date = st.date_input("Date", datetime.now())

with col2:
    start_time = st.time_input("Start Time", time(9, 0))

with col3:
    end_time = st.time_input("End Time", time(17, 0))

with col4:
    break_minutes = st.number_input("Break (mins)", min_value=0, value=30, step=5)

with col5:
    st.write("")
    st.write("")
    add_button = st.button("➕ Add Entry", type="primary")

# Add entry logic
if add_button:
    hours = calculate_hours(start_time, end_time, break_minutes)
    
    if hours > 0:
        entry = {
            'id': int(datetime.now().timestamp() * 1000),
            'date': entry_date.strftime('%Y-%m-%d'),
            'start_time': start_time.strftime('%H:%M'),
            'end_time': end_time.strftime('%H:%M'),
            'break_minutes': int(break_minutes),
            'hours': float(hours)
        }
        
        st.session_state.entries.append(entry)
        st.session_state.entries.sort(key=lambda x: x['date'], reverse=True)
        save_data()
        st.success(f"✅ Entry added! {hours} hours logged.")
        st.rerun()
    else:
        st.error("❌ End time must be after start time!")

st.divider()

# Display last 5 entries
if st.session_state.entries:
    st.subheader("📋 Recent Entries (Last 5)")
    
    last_5 = st.session_state.entries[:5]
    
    for idx, entry in enumerate(last_5):
        col1, col2, col3, col4, col5, col6 = st.columns([2, 1.5, 1.5, 1, 1.5, 1])
        
        with col1:
            st.write(f"**📅 {entry['date']}**")
        with col2:
            st.write(f"🕐 {entry['start_time']}")
        with col3:
            st.write(f"🕔 {entry['end_time']}")
        with col4:
            st.write(f"☕ {entry['break_minutes']}m")
        with col5:
            st.write(f"**⏱️ {entry['hours']} hrs**")
        with col6:
            if st.button("🗑️", key=f"del_{entry['id']}"):
                st.session_state.entries = [e for e in st.session_state.entries if e['id'] != entry['id']]
                save_data()
                st.rerun()
        
        if idx < len(last_5) - 1:
            st.markdown("---")
    
    st.divider()
    
    # Summary metrics
    st.subheader("📊 Summary")
    
    col1, col2, col3 = st.columns(3)
    
    total_entries = len(st.session_state.entries)
    total_hours = sum(e['hours'] for e in st.session_state.entries)
    months = len(set(get_month_year(e['date']) for e in st.session_state.entries))
    
    with col1:
        st.metric("Total Entries", total_entries)
    
    with col2:
        st.metric("Total Hours", f"{total_hours:.2f} hrs")
    
    with col3:
        st.metric("Months Tracked", months)
    
    st.divider()
    
    # Month selector
    st.subheader("📅 View by Month")
    
    unique_months = sorted(list(set(get_month_year(e['date']) for e in st.session_state.entries)), reverse=True)
    
    if unique_months:
        selected_month = st.selectbox(
            "Select Month",
            unique_months,
            format_func=format_month_display
        )
        
        # Filter entries by month
        month_entries = [e for e in st.session_state.entries if get_month_year(e['date']) == selected_month]
        month_total = sum(e['hours'] for e in month_entries)
        
        st.write(f"**{format_month_display(selected_month)} - Total: {month_total:.2f} hours**")
        
        # Create DataFrame
        df_data = []
        for e in month_entries:
            df_data.append({
                'Date': e['date'],
                'Start': e['start_time'],
                'End': e['end_time'],
                'Break (mins)': e['break_minutes'],
                'Hours': e['hours']
            })
        
        if df_data:
            df = pd.DataFrame(df_data)
            df = df.sort_values('Date', ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Download section
        st.subheader("💾 Download Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if df_data:
                csv_month = pd.DataFrame(df_data).to_csv(index=False)
                st.download_button(
                    label="📥 Download Current Month",
                    data=csv_month,
                    file_name=f"timesheet_{selected_month}.csv",
                    mime="text/csv"
                )
        
        with col2:
            # All data
            all_data = []
            for e in st.session_state.entries:
                all_data.append({
                    'Date': e['date'],
                    'Start': e['start_time'],
                    'End': e['end_time'],
                    'Break (mins)': e['break_minutes'],
                    'Hours': e['hours']
                })
            
            if all_data:
                csv_all = pd.DataFrame(all_data).to_csv(index=False)
                st.download_button(
                    label="📥 Download All Data",
                    data=csv_all,
                    file_name=f"timesheet_all_{datetime.now().strftime('%Y-%m-%d')}.csv",
                    mime="text/csv"
                )
        
        # Clear data
        st.divider()
        with st.expander("⚠️ Danger Zone"):
            st.warning("This will delete all your data permanently!")
            if st.button("🗑️ Clear All Data"):
                st.session_state.entries = []
                save_data()
                st.success("All data cleared!")
                st.rerun()

else:
    st.info("👋 No entries yet! Add your first working hours entry above.")

# Footer
st.divider()
st.markdown("<p style='text-align: center; color: #999;'>Made with ❤️ using Streamlit</p>", unsafe_allow_html=True)
