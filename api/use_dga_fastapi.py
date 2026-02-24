from datetime import datetime
from fastapi import FastAPI
from dga_diagnostics import DGADecisionEngine, GasSample

app = FastAPI()
engine = DGADecisionEngine()

@app.post("/diagnose")
async def diagnose_signal(payload: dict):
    # payload example: {"H2":85, "CH4":210, ..., "timestamp":"2025-04-10T14:30:00"}
    sample = GasSample(
        timestamp = payload.get("timestamp", datetime.utcnow().isoformat()),
        H2   = payload.get("H2",   0.0),
        CH4  = payload.get("CH4",  0.0),
        C2H6 = payload.get("C2H6", 0.0),
        C2H4 = payload.get("C2H4", 0.0),
        C2H2 = payload.get("C2H2", 0.0),
        CO   = payload.get("CO",   0.0),
        CO2  = payload.get("CO2",  0.0),
    )
    engine.add_sample(sample)
    result = engine.get_four_suggestions()
    return result