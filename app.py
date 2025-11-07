import streamlit as st
import pandas as pd
from datetime import datetime, time

# Page configuration
st.set_page_config(page_title="Working Hours Tracker", page_icon="⏰", layout="wide")

# Initialize session state for entries
if 'entries' not in st.session_state:
    st.session_state.entries = []

def calculate_hours(start_time, end_time, break_minutes):
    """Calculate working hours"""
    start_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute
    total_minutes = end_minutes - start_minutes - break_minutes
    return round(total_minutes / 60, 2) if total_minutes > 0 else 0

def get_month_year(date_str):
    """Get month-year string"""
    d = datetime.strptime(date_str, '%Y-%m-%d')
    return d.strftime('%Y-%m')

def format_month(month_year):
    """Format month for display"""
    d = datetime.strptime(month_year, '%Y-%m')
    return d.strftime('%B %Y')

# Header
st.title("⏰ Working Hours Tracker")
st.markdown("Track your daily working hours with ease")
st.markdown("---")

# Input section
st.subheader("📝 Add New Entry")

col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1.5, 1.5])

with col1:
    entry_date = st.date_input("Date", datetime.now(), key="date")

with col2:
    start_time = st.time_input("Start Time", time(9, 0), key="start")

with col3:
    end_time = st.time_input("End Time", time(17, 0), key="end")

with col4:
    break_minutes = st.number_input("Break (mins)", min_value=0, value=30, step=5, key="break")

with col5:
    st.markdown("<br>", unsafe_allow_html=True)
    add_button = st.button("➕ Add Entry", type="primary", use_container_width=True)

# Add entry
if add_button:
    hours = calculate_hours(start_time, end_time, break_minutes)
    
    if hours > 0:
        new_entry = {
            'id': len(st.session_state.entries) + 1,
            'date': entry_date.strftime('%Y-%m-%d'),
            'start_time': start_time.strftime('%H:%M'),
            'end_time': end_time.strftime('%H:%M'),
            'break_minutes': break_minutes,
            'hours': hours
        }
        st.session_state.entries.append(new_entry)
        st.session_state.entries = sorted(st.session_state.entries, key=lambda x: x['date'], reverse=True)
        st.success(f"✅ Entry added successfully! {hours} hours logged.")
        st.rerun()
    else:
        st.error("❌ End time must be after start time!")

st.markdown("---")

# Display entries
if st.session_state.entries:
    # Last 5 entries
    st.subheader("📋 Recent Entries (Last 5)")
    
    last_5 = st.session_state.entries[:5]
    
    for i, entry in enumerate(last_5):
        c1, c2, c3, c4, c5, c6 = st.columns([2, 1.5, 1.5, 1, 1.5, 1])
        
        c1.write(f"**📅 {entry['date']}**")
        c2.write(f"🕐 {entry['start_time']}")
        c3.write(f"🕔 {entry['end_time']}")
        c4.write(f"☕ {entry['break_minutes']}m")
        c5.write(f"**⏱️ {entry['hours']} hrs**")
        
        if c6.button("🗑️", key=f"delete_{entry['id']}"):
            st.session_state.entries = [e for e in st.session_state.entries if e['id'] != entry['id']]
            st.rerun()
        
        if i < len(last_5) - 1:
            st.markdown("---")
    
    st.markdown("---")
    
    # Summary
    st.subheader("📊 Summary")
    
    col1, col2, col3 = st.columns(3)
    
    total_entries = len(st.session_state.entries)
    total_hours = sum(e['hours'] for e in st.session_state.entries)
    unique_months = len(set(get_month_year(e['date']) for e in st.session_state.entries))
    
    col1.metric("Total Entries", total_entries)
    col2.metric("Total Hours", f"{total_hours:.2f} hrs")
    col3.metric("Months Tracked", unique_months)
    
    st.markdown("---")
    
    # Month view
    st.subheader("📅 View by Month")
    
    months = sorted(list(set(get_month_year(e['date']) for e in st.session_state.entries)), reverse=True)
    
    selected_month = st.selectbox("Select Month", months, format_func=format_month)
    
    month_entries = [e for e in st.session_state.entries if get_month_year(e['date']) == selected_month]
    month_total = sum(e['hours'] for e in month_entries)
    
    st.write(f"**{format_month(selected_month)} - Total: {month_total:.2f} hours**")
    
    # Create table
    df_list = []
    for e in month_entries:
        df_list.append({
            'Date': e['date'],
            'Start': e['start_time'],
            'End': e['end_time'],
            'Break (mins)': e['break_minutes'],
            'Hours': e['hours']
        })
    
    df = pd.DataFrame(df_list)
    df = df.sort_values('Date', ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Download
    st.subheader("💾 Download Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_month = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Current Month",
            csv_month,
            f"timesheet_{selected_month}.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col2:
        all_data = []
        for e in st.session_state.entries:
            all_data.append({
                'Date': e['date'],
                'Start': e['start_time'],
                'End': e['end_time'],
                'Break (mins)': e['break_minutes'],
                'Hours': e['hours']
            })
        df_all = pd.DataFrame(all_data)
        csv_all = df_all.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download All Data",
            csv_all,
            f"timesheet_all_{datetime.now().strftime('%Y-%m-%d')}.csv",
            "text/csv",
            use_container_width=True
        )
    
    # Clear data
    st.markdown("---")
    with st.expander("⚠️ Danger Zone"):
        st.warning("This will delete all your data!")
        if st.button("🗑️ Clear All Data"):
            st.session_state.entries = []
            st.success("All data cleared!")
            st.rerun()

else:
    st.info("👋 No entries yet! Add your first entry above.")

# Footer
st.markdown("---")
st.caption("Made with ❤️ using Streamlit")
