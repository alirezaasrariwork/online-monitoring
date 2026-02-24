# server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from fastapi.responses import JSONResponse
import time
import logging
import os

from alarm_logic import logic_a, logic_b, logic_c
from dga_diagnostics import DGADecisionEngine, GasSample

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

# DGA latest cache (for dashboard)
last_dga_result = None

# DGA engine
dga_engine = DGADecisionEngine()

class Signal(BaseModel):
    value: float

class DGASignal(BaseModel):
    H2: float
    CH4: float
    C2H6: float
    C2H4: float
    C2H2: float
    CO: float
    CO2: float

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

def write_dga_to_influx(dga_payload: dict):
    """
    dga_payload is the dict returned by dga_engine.get_four_suggestions()
    """
    if not write_api:
        raise RuntimeError("InfluxDB client not initialized")

    raw = dga_payload["raw_gases"]
    sugg = dga_payload["suggestions"]

    p = (
        Point("dga_signals")
        .tag("source", "DGA")
        .field("H2", float(raw["H2"]))
        .field("CH4", float(raw["CH4"]))
        .field("C2H6", float(raw["C2H6"]))
        .field("C2H4", float(raw["C2H4"]))
        .field("C2H2", float(raw["C2H2"]))
        .field("CO", float(raw["CO"]))
        .field("CO2", float(raw["CO2"]))
        .field("TDCG", float(dga_payload["tdcg"]))
        .field("IEEE_based", sugg["IEEE_based"])
        .field("Rogers_IEC_based", sugg["Rogers_IEC_based"])
        .field("Duval_based", sugg["Duval_based"])
        .field("Doernenburg_based", sugg["Doernenburg_based"])
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

@app.post("/signal/dga")
def signal_dga(sig: DGASignal):
    global last_dga_result
    try:
        sample = GasSample(
            timestamp=time.time(),
            H2=sig.H2,
            CH4=sig.CH4,
            C2H6=sig.C2H6,
            C2H4=sig.C2H4,
            C2H2=sig.C2H2,
            CO=sig.CO,
            CO2=sig.CO2
        )
        dga_engine.add_sample(sample)
        result = dga_engine.get_four_suggestions()
        last_dga_result = result

        # write to Influx
        write_dga_to_influx(result)

        return result
    except Exception:
        logger.exception("Error processing DGA signal")
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

@app.get("/signal/dga")
def get_dga():
    if last_dga_result is None:
        return JSONResponse({"error": "No DGA data yet"}, status_code=404)
    return JSONResponse(last_dga_result)
