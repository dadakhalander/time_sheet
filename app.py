import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, time, date, timedelta
import io
import plotly.express as px
import plotly.graph_objects as go
import pdfkit

# --------------------------------------------------------------
# 1. PAGE CONFIG & THEMING
# --------------------------------------------------------------
st.set_page_config(
    page_title="Working Hours Tracker Pro",
    page_icon="⏰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark-mode toggle
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def switch_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

with st.sidebar:
    st.button("🌙 Toggle Dark Mode", on_click=switch_theme)

theme = st.session_state.theme
if theme == "dark":
    st.markdown(
        """
        <style>
        .css-1d391kg {background-color:#0e1117; color:#fafafa;}
        .css-1v0mbdj {background-color:#262730;}
        </style>
        """,
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------
# 2. DATABASE SETUP (SQLite)
# --------------------------------------------------------------
DB_FILE = "working_hours.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            break_minutes INTEGER NOT NULL,
            hours REAL NOT NULL
        )"""
    )
    return conn

def load_entries():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM entries ORDER BY date DESC, id DESC", conn)
    conn.close()
    return df

def add_entry(entry):
    conn = get_conn()
    conn.execute(
        """INSERT INTO entries (date, start_time, end_time, break_minutes, hours)
           VALUES (?,?,?,?,?)""",
        (entry["date"], entry["start_time"], entry["end_time"], entry["break_minutes"],
         entry["hours"]),
    )
    conn.commit()
    conn.close()

def update_entry(entry_id, entry):
    conn = get_conn()
    conn.execute(
        """UPDATE entries SET date=?, start_time=?, end_time=?, break_minutes=?, hours=?
           WHERE id=?""",
        (entry["date"], entry["start_time"], entry["end_time"], entry["break_minutes"],
         entry["hours"], entry_id),
    )
    conn.commit()
    conn.close()

def delete_entry(entry_id):
    conn = get_conn()
    conn.execute("DELETE FROM entries WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()

# --------------------------------------------------------------
# 3. HELPER FUNCTIONS
# --------------------------------------------------------------
def calculate_hours(start: time, end: time, break_min: int) -> float:
    s = start.hour * 60 + start.minute
    e = end.hour * 60 + end.minute
    total = e - s - break_min
    return round(total / 60, 2) if total > 0 else 0.0

def month_year(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m")

def format_month(my: str) -> str:
    return datetime.strptime(my, "%Y-%m").strftime("%B %Y")

def overtime_badge(total, target):
    diff = total - target
    if diff >= 0:
        return f"**+{diff:.1f}h**", "green"
    else:
        return f"**{diff:.1f}h**", "red"

def df_to_bytes(df: pd.DataFrame, fmt: str = "csv"):
    if fmt == "csv":
        return df.to_csv(index=False).encode("utf-8")
    if fmt == "xlsx":
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Timesheet")
        return out.getvalue()
    if fmt == "pdf":
        html = df.to_html(index=False, classes="table table-sm")
        css = """
        <style>
        table {width:100%; border-collapse:collapse; font-family:Arial; font-size:12px;}
        th, td {border:1px solid #ddd; padding:8px; text-align:center;}
        th {background:#f4f4f4; font-weight:bold;}
        </style>
        """
        return pdfkit.from_string(css + html, False)

# --------------------------------------------------------------
# 4. LOAD DATA
# --------------------------------------------------------------
df_entries = load_entries()
if df_entries.empty:
    df_entries = pd.DataFrame(
        columns=["id", "date", "start_time", "end_time", "break_minutes", "hours"]
    )

# --------------------------------------------------------------
# 5. SIDEBAR – SETTINGS & BULK UPLOAD
# --------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    monthly_target = st.number_input(
        "Monthly Target (hrs)", min_value=0.0, value=160.0, step=5.0
    )
    st.markdown("---")
    st.subheader("📥 Bulk Import")
    uploaded = st.file_uploader(
        "Upload CSV (Date,Start,End,Break)", type=["csv"], key="bulk"
    )
    if uploaded:
        try:
            up_df = pd.read_csv(uploaded)
            required = {"Date", "Start", "End", "Break"}
            if not required.issubset(up_df.columns):
                st.error(f"CSV must contain: {required}")
            else:
                for _, row in up_df.iterrows():
                    try:
                        hrs = calculate_hours(
                            time.fromisoformat(row["Start"]),
                            time.fromisoformat(row["End"]),
                            int(row["Break"]),
                        )
                        if hrs > 0:
                            add_entry({
                                "date": str(row["Date"]),
                                "start_time": row["Start"],
                                "end_time": row["End"],
                                "break_minutes": int(row["Break"]),
                                "hours": hrs
                            })
                    except:
                        continue
                st.success("Bulk import completed!")
                st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

# --------------------------------------------------------------
# 6. MAIN UI – ADD / EDIT ENTRY
# --------------------------------------------------------------
st.title("⏰ Working Hours Tracker **Pro**")
st.markdown("Track, visualise, and export your work time with power-user features.")

# Live Clock-In / Clock-Out
if "clocked_in" not in st.session_state:
    st.session_state.clocked_in = None

col_live1, col_live2 = st.columns([1, 3])
with col_live1:
    if st.button("⏱ Clock-In Now" if not st.session_state.clocked_in else "⏱ Clock-Out"):
        if not st.session_state.clocked_in:
            st.session_state.clocked_in = datetime.now()
            st.success("Clocked in!")
        else:
            end = datetime.now()
            hrs = (end - st.session_state.clocked_in).total_seconds() / 3600
            add_entry({
                "date": date.today().strftime("%Y-%m-%d"),
                "start_time": st.session_state.clocked_in.strftime("%H:%M"),
                "end_time": end.strftime("%H:%M"),
                "break_minutes": 0,
                "hours": round(hrs, 2)
            })
            st.session_state.clocked_in = None
            st.success(f"Clocked out – {hrs:.2f}h")
        st.rerun()
with col_live2:
    if st.session_state.clocked_in:
        elapsed = datetime.now() - st.session_state.clocked_in
        st.metric("Elapsed", str(elapsed).split('.')[0])

st.markdown("---")
st.subheader("📝 Add / Edit Entry")

col1, col2, col3, col4, col5, col6 = st.columns([2, 1.5, 1.5, 1, 1, 1.5])

edit_mode = st.session_state.get("edit_mode", False)
edit_id = st.session_state.get("edit_id", None)

with col1:
    entry_date = st.date_input(
        "Date",
        value=date.today() if not edit_mode else datetime.strptime(df_entries.loc[df_entries["id"] == edit_id, "date"].iloc[0], "%Y-%m-%d").date(),
        key="date_input",
    )
with col2:
    start_time = st.time_input(
        "Start",
        value=time(9, 0) if not edit_mode else time.fromisoformat(df_entries.loc[df_entries["id"] == edit_id, "start_time"].iloc[0]),
        key="start_input",
    )
with col3:
    end_time = st.time_input(
        "End",
        value=time(17, 0) if not edit_mode else time.fromisoformat(df_entries.loc[df_entries["id"] == edit_id, "end_time"].iloc[0]),
        key="end_input",
    )
with col4:
    break_min = st.number_input(
        "Break (mins)",
        min_value=0,
        value=30 if not edit_mode else int(df_entries.loc[df_entries["id"] == edit_id, "break_minutes"].iloc[0]),
        step=5,
        key="break_input",
    )
with col5:
    st.markdown("<br>", unsafe_allow_html=True)
    if edit_mode:
        if st.button("💾 Update", type="primary", use_container_width=True):
            hrs = calculate_hours(start_time, end_time, break_min)
            if hrs > 0:
                update_entry(
                    edit_id,
                    {
                        "date": entry_date.strftime("%Y-%m-%d"),
                        "start_time": start_time.strftime("%H:%M"),
                        "end_time": end_time.strftime("%H:%M"),
                        "break_minutes": break_min,
                        "hours": hrs,
                    },
                )
                st.session_state.edit_mode = False
                st.success("Entry updated!")
                st.rerun()
            else:
                st.error("End must be after start.")
    else:
        if st.button("➕ Add", type="primary", use_container_width=True):
            hrs = calculate_hours(start_time, end_time, break_min)
            if hrs > 0:
                add_entry(
                    {
                        "date": entry_date.strftime("%Y-%m-%d"),
                        "start_time": start_time.strftime("%H:%M"),
                        "end_time": end_time.strftime("%H:%M"),
                        "break_minutes": break_min,
                        "hours": hrs,
                    }
                )
                st.success(f"Added {hrs} hrs")
                st.rerun()
            else:
                st.error("End must be after start.")
with col6:
    st.markdown("<br>", unsafe_allow_html=True)
    if edit_mode:
        if st.button("❌ Cancel"):
            st.session_state.edit_mode = False
            st.rerun()

# --------------------------------------------------------------
# 7. RECENT ENTRIES (Last 7) + Inline Edit / Delete
# --------------------------------------------------------------
if not df_entries.empty:
    st.markdown("---")
    st.subheader("📋 Recent Entries (Last 7)")

    recent = df_entries.head(7)
    for idx, row in recent.iterrows():
        c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 1.3, 1.3, 1, 1.3, 0.8, 0.8])
        c1.write(f"**📅 {row['date']}**")
        c2.write(f"🕐 {row['start_time']}")
        c3.write(f"🕔 {row['end_time']}")
        c4.write(f"☕ {row['break_minutes']}m")
        c5.write(f"**⏱️ {row['hours']} hrs**")
        if c6.button("✏️", key=f"edit_{row['id']}"):
            st.session_state.edit_mode = True
            st.session_state.edit_id = row["id"]
            st.rerun()
        if c7.button("🗑️", key=f"del_{row['id']}"):
            delete_entry(row["id"])
            st.rerun()
        if idx < len(recent) - 1:
            st.markdown("---")

# --------------------------------------------------------------
# 8. SUMMARY METRICS
# --------------------------------------------------------------
if not df_entries.empty:
    st.markdown("---")
    st.subheader("📊 Summary")

    total_h = df_entries["hours"].sum()
    total_entries = len(df_entries)
    months = df_entries["date"].apply(month_year).nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Entries", total_entries)
    col2.metric("Total Hours", f"{total_h:.2f} hrs")
    col3.metric("Months Tracked", months)
    col4.metric("Avg Hours/Day", f"{total_h/total_entries:.2f}" if total_entries else "0")

    col_s2 = st.columns(1)[0]
    month_total = df_entries[df_entries["date"].apply(month_year) == month_year(date.today().strftime("%Y-%m-%d"))]["hours"].sum()
    badge, color = overtime_badge(month_total, monthly_target)
    col_s2.markdown(f"<h4 style='color:{color}; margin:0'>{badge} vs target</h4>", unsafe_allow_html=True)

# --------------------------------------------------------------
# 9. SEARCH & FILTER
# --------------------------------------------------------------
if not df_entries.empty:
    st.markdown("---")
    st.subheader("🔍 Search & Filter")
    search = st.text_input("Search date (YYYY-MM-DD) or keyword")
    filtered = df_entries
    if search:
        filtered = filtered[filtered["date"].str.contains(search, na=False)]

    # Month selector for detailed view
    months_list = sorted(df_entries["date"].apply(month_year).unique(), reverse=True)
    selected_month = st.selectbox(
        "View by Month", months_list, format_func=format_month, key="month_sel"
    )
    month_df = filtered[filtered["date"].apply(month_year) == selected_month].copy()
    month_total = month_df["hours"].sum()

    st.write(f"**{format_month(selected_month)} – {month_total:.2f} hrs**")

    # Table
    disp = month_df[["date", "start_time", "end_time", "break_minutes", "hours"]].copy()
    disp.columns = ["Date", "Start", "End", "Break (mins)", "Hours"]
    disp = disp.sort_values("Date", ascending=False)
    st.dataframe(disp, use_container_width=True, hide_index=True)

    # --------------------------------------------------------------
    # 10. CHARTS
    # --------------------------------------------------------------
    st.markdown("---")
    st.subheader("📈 Visualisations")

    # Daily hours
    daily = (
        df_entries.groupby("date")["hours"]
        .sum()
        .reset_index()
        .sort_values("date")
    )
    daily["date"] = pd.to_datetime(daily["date"])
    fig_daily = px.bar(
        daily,
        x="date",
        y="hours",
        title="Daily Working Hours",
        labels={"date": "Date", "hours": "Hours"},
        color="hours",
        color_continuous_scale="Viridis",
    )
    fig_daily.update_layout(showlegend=False)
    st.plotly_chart(fig_daily, use_container_width=True)

    # Weekly Heatmap
    df_heat = df_entries.copy()
    df_heat["date"] = pd.to_datetime(df_heat["date"])
    df_heat["weekday"] = df_heat["date"].dt.strftime("%a")
    df_heat["week"] = df_heat["date"].dt.isocalendar().week

    heatmap = df_heat.pivot_table(
        values="hours",
        index="week",
        columns="weekday",
        aggfunc="sum",
        fill_value=0
    )

    # Ensure all 7 days exist
    weekday_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for day in weekday_order:
        if day not in heatmap.columns:
            heatmap[day] = 0
    heatmap = heatmap[weekday_order]

    fig_heat = px.imshow(
        heatmap.values,
        labels=dict(x="Day", y="Week", color="Hours"),
        x=weekday_order,
        y=heatmap.index,
        color_continuous_scale="Blues",
        aspect="auto"
    )
    fig_heat.update_layout(title="Hours per Day (Weekly Heatmap)")
    st.plotly_chart(fig_heat, use_container_width=True)

    # Monthly progress vs target
    monthly = (
        df_entries.copy()
        .assign(month=lambda x: pd.to_datetime(x["date"]).dt.to_period("M").astype(str))
        .groupby("month")["hours"]
        .sum()
        .reset_index()
    )
    monthly["target"] = monthly_target
    fig_month = go.Figure()
    fig_month.add_trace(
        go.Bar(name="Actual", x=monthly["month"], y=monthly["hours"], marker_color="steelblue")
    )
    fig_month.add_trace(
        go.Scatter(
            name="Target",
            x=monthly["month"],
            y=monthly["target"],
            mode="lines+markers",
            line=dict(dash="dash", color="crimson"),
        )
    )
    fig_month.update_layout(
        title="Monthly Hours vs Target",
        xaxis_title="Month",
        yaxis_title="Hours",
        barmode="group",
    )
    st.plotly_chart(fig_month, use_container_width=True)

    # --------------------------------------------------------------
    # 11. DOWNLOADS
    # --------------------------------------------------------------
    st.markdown("---")
    st.subheader("💾 Export Data")

    col_d1, col_d2 = st.columns(2)

    # Current month CSV + Excel
    with col_d1:
        csv_month = df_to_bytes(disp, "csv")
        xlsx_month = df_to_bytes(disp, "xlsx")
        pdf_month = df_to_bytes(disp, "pdf")
        st.download_button(
            "📄 CSV – Current Month",
            csv_month,
            f"timesheet_{selected_month}.csv",
            "text/csv",
        )
        st.download_button(
            "📊 Excel – Current Month",
            xlsx_month,
            f"timesheet_{selected_month}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.download_button(
            "📊 PDF – Current Month",
            pdf_month,
            f"timesheet_{selected_month}.pdf",
            "application/pdf",
        )

    # All data
    with col_d2:
        all_disp = df_entries[["date", "start_time", "end_time", "break_minutes", "hours"]].copy()
        all_disp.columns = ["Date", "Start", "End", "Break (mins)", "Hours"]
        all_disp = all_disp.sort_values("Date", ascending=False)

        csv_all = df_to_bytes(all_disp, "csv")
        xlsx_all = df_to_bytes(all_disp, "xlsx")
        today_str = datetime.now().strftime("%Y-%m-%d")
        st.download_button(
            "📄 CSV – All Data",
            csv_all,
            f"timesheet_all_{today_str}.csv",
            "text/csv",
        )
        st.download_button(
            "📊 Excel – All Data",
            xlsx_all,
            f"timesheet_all_{today_str}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # --------------------------------------------------------------
    # 12. DANGER ZONE
    # --------------------------------------------------------------
    st.markdown("---")
    with st.expander("⚠️ Danger Zone"):
        st.warning("These actions **cannot be undone**.")
        col_z1, col_z2 = st.columns(2)
        with col_z1:
            if st.button("🗑️ Delete All Data"):
                conn = get_conn()
                conn.execute("DELETE FROM entries")
                conn.commit()
                conn.close()
                st.success("All data cleared!")
                st.rerun()
        with col_z2:
            if st.button("📥 Reset DB (keep schema)"):
                conn = get_conn()
                conn.execute("DELETE FROM entries")
                conn.commit()
                conn.close()
                st.success("Database reset!")
                st.rerun()

else:
    st.info("👋 No entries yet – add your first day above!")

# --------------------------------------------------------------
# 13. KEYBOARD SHORTCUTS
# --------------------------------------------------------------
st.markdown("""
<script>
const doc = window.parent.document;
doc.addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
        const btn = doc.querySelector('button[kind="primary"]');
        btn && btn.click();
    }
    if (e.key === 'Escape') {
        const cancel = Array.from(doc.querySelectorAll('button')).find(b => b.innerText.includes('Cancel'));
        cancel && cancel.click();
    }
});
</script>
""", unsafe_allow_html=True)

# --------------------------------------------------------------
# 13. FOOTER
# --------------------------------------------------------------
st.markdown("---")
st.caption("Made with ❤️ using **Streamlit** • Data stored locally in `working_hours.db`")
