# server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from fastapi.responses import JSONResponse
import time
import logging
import os

# -------------------------------
# Import your logic functions
# -------------------------------
def logic_a(value):
    if value > 80:
        return "CRITICAL", 1, "Cool down system"
    elif value > 60:
        return "WARN", 1, "Reduce load"
    return "OK", 0, "Normal"

def logic_b(value):
    if value > 120:
        return "CRITICAL", 1, "Release pressure"
    elif value > 90:
        return "WARN", 1, "Monitor pressure"
    return "OK", 0, "Normal"

def logic_c(value):
    if value > 7:
        return "CRITICAL", 1, "Stop machine"
    elif value > 4:
        return "WARN", 1, "Schedule maintenance"
    return "OK", 0, "Normal"

# -------------------------------
# InfluxDB config
# -------------------------------
INFLUX_HOST = os.getenv("INFLUX_HOST", "localhost")
INFLUX_PORT = int(os.getenv("INFLUX_PORT", 8086))
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "monitoring")
INFLUX_ORG = os.getenv("INFLUX_ORG", "my-org")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "my-token")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

# -------------------------------
# InfluxDB client
# -------------------------------
try:
    client = InfluxDBClient(
        url=f"http://{INFLUX_HOST}:{INFLUX_PORT}",
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    )
    write_api = client.write_api(write_options=SYNCHRONOUS)
except Exception as e:
    logger.exception("Failed to connect to InfluxDB")
    client = None
    write_api = None

# -------------------------------
# FastAPI setup
# -------------------------------
app = FastAPI()
last_values = {"A": 0, "B": 0, "C": 0}

class Signal(BaseModel):
    value: float

def write_signal(name, value, level, alarm, action):
    if not write_api:
        raise RuntimeError("InfluxDB client not initialized")
    p = (
        Point("signals")
        .tag("source", name)
        .field("value", value)
        .field("level", level)
        .field("alarm", alarm)
        .field("action", action)
        .time(time.time_ns())
    )
    write_api.write(bucket=INFLUX_BUCKET, record=p)

# -------------------------------
# POST endpoints (send signal)
# -------------------------------
@app.post("/signal/a")
def signal_a(sig: Signal):
    try:
        level, alarm, action = logic_a(sig.value)
        last_values["A"] = sig.value
        write_signal("A", sig.value, level, alarm, action)
        return {"value": sig.value, "level": level, "alarm": alarm, "action": action}
    except Exception:
        logger.exception("Error processing signal A")
        raise HTTPException(status_code=500, detail="Internal error")

@app.post("/signal/b")
def signal_b(sig: Signal):
    try:
        level, alarm, action = logic_b(sig.value)
        last_values["B"] = sig.value
        write_signal("B", sig.value, level, alarm, action)
        return {"value": sig.value, "level": level, "alarm": alarm, "action": action}
    except Exception:
        logger.exception("Error processing signal B")
        raise HTTPException(status_code=500, detail="Internal error")

@app.post("/signal/c")
def signal_c(sig: Signal):
    try:
        level, alarm, action = logic_c(sig.value)
        last_values["C"] = sig.value
        write_signal("C", sig.value, level, alarm, action)
        return {"value": sig.value, "level": level, "alarm": alarm, "action": action}
    except Exception:
        logger.exception("Error processing signal C")
        raise HTTPException(status_code=500, detail="Internal error")

# -------------------------------
# GET endpoints (for live dashboard)
# -------------------------------
@app.get("/signal/a")
def get_a():
    return JSONResponse({"value": last_values["A"]})

@app.get("/signal/b")
def get_b():
    return JSONResponse({"value": last_values["B"]})

@app.get("/signal/c")
def get_c():
    return JSONResponse({"value": last_values["C"]})
