# dga_diagnostics.py
"""
Enhanced DGA Diagnostic Decision Module
Now includes Doernenburg method and 4 separate method-based suggestions.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List
from datetime import datetime

@dataclass
class GasSample:
    timestamp: str | datetime
    H2: float   = 0.0
    CH4: float  = 0.0
    C2H6: float = 0.0
    C2H4: float = 0.0
    C2H2: float = 0.0
    CO: float   = 0.0
    CO2: float  = 0.0
    oil_volume_liters: Optional[float] = None

    def tdcg(self) -> float:
        return self.H2 + self.CH4 + self.C2H6 + self.C2H4 + self.C2H2

    def ratios(self) -> Dict[str, float]:
        r = {}
        safe_div = lambda a, b: a / b if b > 0.1 else float('inf')
        r["CH4_H2"]     = safe_div(self.CH4, self.H2)
        r["C2H2_C2H4"]  = safe_div(self.C2H2, self.C2H4)
        r["C2H4_C2H6"]  = safe_div(self.C2H4, self.C2H6)
        r["C2H2_CH4"]   = safe_div(self.C2H2, self.CH4)
        r["C2H6_C2H2"]  = safe_div(self.C2H6, self.C2H2)   # Doernenburg R4
        return r


class DGADecisionEngine:
    def __init__(self):
        self.history: List[GasSample] = []

    def add_sample(self, sample: GasSample):
        self.history.append(sample)
        if len(self.history) > 10:
            self.history = self.history[-10:]

    def latest(self) -> Optional[GasSample]:
        return self.history[-1] if self.history else None

    # ────────────────────────────────────────────────
    # IEEE Condition (table 8 style)
    # ────────────────────────────────────────────────
    def ieee_condition(self, sample: GasSample) -> Dict:
        t = sample.tdcg()
        if t < 720:
            level, desc = 1, "Normal – routine sampling"
        elif t <= 1920:
            level, desc = 2, "Above normal – monthly sampling + trend watch"
        elif t <= 4630:
            level, desc = 3, "Abnormal – investigate + plan repairs"
        else:
            level, desc = 4, "Critical – urgent action, consider de-energize"

        return {
            "level": level,
            "tdcg_ppm": round(t, 1),
            "description": desc
        }
 
    # ────────────────────────────────────────────────
    # Duval Triangle 1
    # ────────────────────────────────────────────────
    def duval_triangle(self, sample: GasSample) -> Dict:
        total = sample.CH4 + sample.C2H4 + sample.C2H2
        if total < 0.1:
            return {"zone": "Insufficient data", "percentages": {}}

        pCH4  = 100 * sample.CH4 / total
        pC2H4 = 100 * sample.C2H4 / total
        pC2H2 = 100 * sample.C2H2 / total

        if pC2H2 > 13 and pC2H4 > 23:
            zone = "D2 – High energy discharge / arcing"
        elif pC2H2 > 13:
            zone = "D1 – Low energy discharge"
        elif pCH4 > 98:
            zone = "PD – Partial discharge"
        elif pC2H4 > 50 and pCH4 < 15:
            zone = "T3 – Thermal >700°C"
        elif pC2H4 > 10 and pCH4 > 50:
            zone = "T2 – Thermal 300–700°C"
        elif pCH4 > 50 and pC2H4 < 10:
            zone = "T1 – Thermal <300°C"
        else:
            zone = "Mixed / DT / uncertain"

        return {
            "zone": zone,
            "percentages": {
                "%CH4": round(pCH4, 1),
                "%C2H4": round(pC2H4, 1),
                "%C2H2": round(pC2H2, 1)
            }
        }

    # ────────────────────────────────────────────────
    # IEC / Rogers 3-ratio diagnosis (table 19 style)
    # ────────────────────────────────────────────────
    def iec_rogers_diagnosis(self, sample: GasSample) -> Dict:
        r = sample.ratios()
        ch4_h2    = r["CH4_H2"]
        c2h2_c2h4 = r["C2H2_C2H4"]
        c2h4_c2h6 = r["C2H4_C2H6"]

        if ch4_h2 < 0.1 and c2h4_c2h6 < 0.2:
            fault = "PD – Partial Discharge"
        elif c2h2_c2h4 > 1 and 0.1 <= ch4_h2 <= 0.5 and c2h4_c2h6 > 1:
            fault = "D1 – Low energy discharge"
        elif 0.6 <= c2h2_c2h4 <= 2.5 and 0.1 <= ch4_h2 <= 1 and c2h4_c2h6 > 2:
            fault = "D2 – High energy discharge / arcing"
        elif c2h2_c2h4 < 0.1 and ch4_h2 > 1 and 1 <= c2h4_c2h6 <= 4:
            fault = "T2 – Thermal fault 300–700°C"
        elif c2h2_c2h4 < 0.02 and ch4_h2 > 1 and c2h4_c2h6 > 4:
            fault = "T3 – Thermal fault >700°C"
        elif ch4_h2 > 1 and c2h4_c2h6 < 1:
            fault = "T1 – Thermal fault <300°C (possible)"
        else:
            fault = "Unclear / mixed"

        return {"fault_type": fault, "ratios_used": r}

    # ────────────────────────────────────────────────
    # Doernenburg method (L1 + 4 ratios – approximate from tables 16–18)
    # ────────────────────────────────────────────────
    def doernenburg_diagnosis(self, sample: GasSample) -> Dict:
        # L1 significant thresholds (approximate from table 16)
        l1_thresholds = {
            "H2": 100, "CH4": 120, "CO": 350,
            "C2H2": 5, "C2H4": 50, "C2H6": 65
        }

        significant = any(
            getattr(sample, gas) > thresh
            for gas, thresh in l1_thresholds.items()
        )

        if not significant:
            return {
                "status": "Below L1 thresholds → no significant fault indicated",
                "doernenburg_code": "Normal / no code"
            }

        r = sample.ratios()

        # Simplified 4-ratio Doernenburg logic (table 17/18 style – approximate mapping)
        # R1 = CH4/H2, R2 = C2H2/C2H4, R3 = C2H2/CH4?, R4 = C2H6/C2H2
        code = "Unclear"

        if r["C2H2_C2H4"] > 1 and r["CH4_H2"] > 0.1:
            code = "High energy electrical + thermal"
        elif r["C2H2_C2H4"] > 1 and r["C2H6_C2H2"] < 0.2:
            code = "Electrical discharge dominant"
        elif r["CH4_H2"] > 0.1 and r["C2H2_C2H4"] < 0.1 and r["C2H4_C2H6"] > 1:
            code = "Thermal fault with cellulose involvement"
        elif r["CH4_H2"] < 0.1:
            code = "Partial discharge / corona likely"

        return {
            "status": "Above L1 → ratios applied",
            "doernenburg_code": code,
            "ratios": {k: round(v, 3) for k,v in r.items()}
        }

    # ────────────────────────────────────────────────
    # Four different suggestions (one per method)
    # ────────────────────────────────────────────────
    def get_four_suggestions(self) -> Dict:
        sample = self.latest()
        if not sample:
            return {"error": "No sample available"}

        ieee_res   = self.ieee_condition(sample)
        duval_res  = self.duval_triangle(sample)
        rogers_res = self.iec_rogers_diagnosis(sample)
        doern_res  = self.doernenburg_diagnosis(sample)

        suggestions = {
            "IEEE_based": f"Condition {ieee_res['level']} – {ieee_res['description']}. "
                          f"{'Urgent attention needed.' if ieee_res['level'] >= 3 else 'Continue monitoring.'}",

            "Rogers_IEC_based": f"Main diagnosis: {rogers_res['fault_type']}. "
                                f"Follow-up: {'Detailed electrical tests recommended.' if 'D' in rogers_res['fault_type'] else 'Thermal inspection / paper analysis advised.'}",

            "Duval_based": f"Duval zone: {duval_res['zone']}. "
                           f"{'High priority – arcing suspected.' if 'D' in duval_res['zone'] else 'Thermal issue likely – check hotspots / cooling system.'}",

            "Doernenburg_based": f"Doernenburg: {doern_res['doernenburg_code']}. "
                                 f"{'Significant fault above L1 – immediate verification needed.' if 'Above L1' in doern_res['status'] else 'No strong indication – routine check sufficient.'}"
        }

        return {
            "suggestions": suggestions,
            "latest_timestamp": str(sample.timestamp),
            "tdcg": round(sample.tdcg(), 1),
            "raw_gases": {
                "H2": sample.H2, "CH4": sample.CH4, "C2H6": sample.C2H6,
                "C2H4": sample.C2H4, "C2H2": sample.C2H2, "CO": sample.CO, "CO2": sample.CO2
            }
        }


# Example usage / test
if __name__ == "__main__":
    engine = DGADecisionEngine()

    # Example signal
    sample = GasSample(
        timestamp="2025-04-10T14:30:00",
        H2=120, CH4=320, C2H6=130, C2H4=280, C2H2=45, CO=950, CO2=7200
    )
    engine.add_sample(sample)

    result = engine.get_four_suggestions()
    import json
    print(json.dumps(result, indent=2))
# ────────────────────────────────────────────────
#   Example usage in FastAPI endpoint
# ────────────────────────────────────────────────

# engine = DGADecisionEngine()

# @app.post("/diagnose")
# async def diagnose(data: dict):
#     sample = GasSample(
#         timestamp = data.get("timestamp", datetime.utcnow().isoformat()),
#         H2   = data.get("H2", 0),
#         CH4  = data.get("CH4", 0),
#         C2H6 = data.get("C2H6", 0),
#         C2H4 = data.get("C2H4", 0),
#         C2H2 = data.get("C2H2", 0),
#         CO   = data.get("CO", 0),
#         CO2  = data.get("CO2", 0),
#     )
#     engine.add_sample(sample)
#     report = engine.diagnose_latest()
#     return report
# {
#   "suggestions": {
#     "IEEE_based": "Condition 3 – Abnormal – investigate + plan repairs. Urgent attention needed.",
#     "Rogers_IEC_based": "Main diagnosis: T2 – Thermal fault 300–700°C. Follow-up: Thermal inspection / paper analysis advised.",
#     "Duval_based": "Duval zone: T2 – Thermal 300–700°C. Thermal issue likely – check hotspots / cooling system.",
#     "Doernenburg_based": "Doernenburg: Thermal fault with cellulose involvement. Significant fault above L1 – immediate verification needed."
#   },
#   ...
# }