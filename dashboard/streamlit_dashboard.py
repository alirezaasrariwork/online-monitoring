# streamlit_dashboard.py
import streamlit as st
import pandas as pd
import os
from influxdb_client import InfluxDBClient
from influxdb_client.client.warnings import MissingPivotFunction
import warnings
from streamlit_autorefresh import st_autorefresh
import requests

warnings.simplefilter("ignore", MissingPivotFunction)

st.set_page_config(page_title="Monitoring Dashboard", layout="wide")
st.title("🖥️ Live & Historical Signal Monitoring")

# ────────────────────────────────────────────────
#               Configuration
# ────────────────────────────────────────────────
API_BASE_URL   = os.getenv("API_BASE_URL",   "http://localhost:8000")
INFLUX_HOST    = os.getenv("INFLUX_HOST",    "influxdb")           # ← use service name in docker-compose
INFLUX_PORT    = int(os.getenv("INFLUX_PORT", 8086))
INFLUX_BUCKET  = os.getenv("INFLUX_BUCKET",  "monitoring")
INFLUX_ORG     = os.getenv("INFLUX_ORG",     "my-org")
INFLUX_TOKEN   = os.getenv("INFLUX_TOKEN",   "my-token")

REFRESH_SEC    = 20
HISTORY_RANGE  = "-15m"           # adjust as needed: -1h, -6h, -24h, ...

# ────────────────────────────────────────────────
#               InfluxDB Client (cached)
# ────────────────────────────────────────────────
@st.cache_resource
def get_influx_client():
    url = f"http://{INFLUX_HOST}:{INFLUX_PORT}"
    return InfluxDBClient(url=url, token=INFLUX_TOKEN, org=INFLUX_ORG)

client = get_influx_client()
query_api = client.query_api()

# ────────────────────────────────────────────────
#               Color / Style helpers
# ────────────────────────────────────────────────
def style_status(val):
    colors = {
        "CRITICAL": "background-color: #dc3545; color: white; font-weight: bold;",
        "WARN":     "background-color: #fd7e14; color: black; font-weight: bold;",
        "OK":       "background-color: #198754; color: white;",
    }
    return colors.get(val, "")

def style_row(row):
    styles = [""] * len(row)
    level = row.get("Level", "OK")               # ← capital L
    try:
        level_col_idx = row.index.get_loc("Level")
        styles[level_col_idx] = style_status(level)
    except KeyError:
        pass  # silently skip if column missing (defensive)
    return styles

# ────────────────────────────────────────────────
#               LIVE section
# ────────────────────────────────────────────────
st.subheader("⚡ Live Signals (refreshes every 20s)")
st_autorefresh(interval=REFRESH_SEC * 1000, key="live_refresh")

signals = ["a", "b", "c"]
live_data = []

for sig in signals:
    try:
        r = requests.get(f"{API_BASE_URL}/signal/{sig}", timeout=3)
        r.raise_for_status()
        val = r.json().get("value", None)
    except:
        val = None

    if val is None:
        level, thresh, sugg = "—", "—", "API unreachable"
    else:
        val = round(float(val), 2)
        if sig == "a":
            level, alarm, sugg = "CRITICAL" if val > 80 else "WARN" if val > 60 else "OK", 80 if val > 80 else 60 if val > 60 else 0, "Cool down" if val > 80 else "Reduce load" if val > 60 else "Normal"
            thresh = 80 if val > 80 else 60
        elif sig == "b":
            level, alarm, sugg = "CRITICAL" if val > 120 else "WARN" if val > 90 else "OK", 120 if val > 120 else 90 if val > 90 else 0, "Release pressure" if val > 120 else "Monitor" if val > 90 else "Normal"
            thresh = 120 if val > 120 else 90
        else:  # c
            level, alarm, sugg = "CRITICAL" if val > 7 else "WARN" if val > 4 else "OK", 7 if val > 7 else 4 if val > 4 else 0, "Stop machine" if val > 7 else "Maintenance" if val > 4 else "Normal"
            thresh = 7 if val > 7 else 4

    live_data.append({
        "Signal": sig.upper(),
        "Value": val,
        "Threshold": thresh,
        "Level": level,
        "Suggestion": sugg
    })

live_df = pd.DataFrame(live_data)
st.dataframe(
    live_df.style.apply(style_row, axis=1),
    use_container_width=True,
    hide_index=True
)

# Quick metrics row (nice to have)
cols = st.columns(3)
for i, row in enumerate(live_data):
    with cols[i]:
        delta_color = "normal" if row["Level"] == "OK" else "inverse" if row["Level"] == "CRITICAL" else "off"
        st.metric(
            label=f"Signal {row['Signal']}",
            value=row["Value"] if row["Value"] is not None else "—",
            delta=row["Level"],
            delta_color=delta_color
        )

# ────────────────────────────────────────────────
#               HISTORICAL section
# ────────────────────────────────────────────────
st.subheader(f"📈 Historical Data (last {HISTORY_RANGE[1:]} window)")
st.caption("Data comes directly from InfluxDB — value + computed level/alarm/action")

try:
    flux = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: {HISTORY_RANGE})
      |> filter(fn: (r) => r["_measurement"] == "signals")
      |> pivot(rowKey:["_time", "source"], columnKey: ["_field"], valueColumn: "_value")
      |> keep(columns: ["_time", "source", "value", "level", "alarm", "action"])
      |> rename(columns: {{source: "Signal", value: "Value", level: "Level", alarm: "Alarm", action: "Suggestion"}})
      |> sort(columns: ["_time"], desc: true)
    '''

    tables = query_api.query_data_frame(flux)

    if isinstance(tables, list) and tables:
        df = pd.concat([t for t in tables if not t.empty], ignore_index=True)
    elif not isinstance(tables, list) and not tables.empty:
        df = tables
    else:
        df = pd.DataFrame()

    if df.empty:
        st.info("No data stored yet — run the simulator for a while")
    else:
        # Cleanup
        df["Signal"] = df["Signal"].str.upper()
        df["Value"]  = pd.to_numeric(df["Value"], errors="coerce").round(2)
        df["_time"]  = pd.to_datetime(df["_time"])
        df = df[["_time", "Signal", "Value", "Level", "Alarm", "Suggestion"]]

        # Optional: color whole row based on level
        st.dataframe(
            df.style.apply(style_row, axis=1, subset=["Level"]),
            use_container_width=True,
            hide_index=True
        )

        # Optional: simple line chart per signal
        if len(df) > 5:
            st.subheader("Trend (last values)")
            chart_df = df.pivot(index="_time", columns="Signal", values="Value").tail(200)
            st.line_chart(chart_df)

except Exception as e:
    st.error(f"Query failed: {e}")
    st.info("Check InfluxDB is running and credentials are correct (.env)")