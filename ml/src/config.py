"""Shared paths and physical constants for the SOCAR VFM/PTA pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
PROC = DATA / "processed"
OUT = ROOT / "ml" / "outputs"
FIGS = OUT / "figures"
for _d in (PROC, OUT, FIGS):
    _d.mkdir(parents=True, exist_ok=True)

# Raw inputs
F_HIGH_FREQ = DATA / "high_freq_data.csv"
F_WELL_TESTS = DATA / "well_tests.csv"
F_CHOKE = DATA / "choke_events.csv"
F_PVT = DATA / "reservoir_pvt.csv"
F_COMPLETION = DATA / "well_completion.csv"
F_HF_PARQUET = PROC / "high_freq.parquet"          # raw -> parquet cache
F_HF_CLEAN = PROC / "high_freq_clean.parquet"      # cleaned 1-min series
F_WT_CLEAN = PROC / "well_tests_clean.parquet"     # cleaned labels

# LAS/Petrel-style absent-value code used throughout the high-frequency file
NULL_SENTINEL = -999.25

SENSORS = [
    "whp_psia",
    "whp_downstream_psia",
    "dh_pressure_psia",
    "dh_temperature_degf",
    "annulus_pressure_psia",
    "gas_lift_rate_mscfd",
]

# Noise floors: a deviation smaller than this is never called a spike.
# Calibrated against the measured minute-to-minute noise -- the spike
# population is bimodal (noise at 1-3 psi, real glitches above 25 psi with an
# empty gap between), and spike counts plateau at these values, so the floors
# sit in the gap rather than inside the noise. Dropping them to ~1 psi
# misclassifies ~7000 ordinary noise samples as spikes.
SPIKE_FLOOR = {
    "whp_psia": 15.0,
    "whp_downstream_psia": 10.0,
    "dh_pressure_psia": 10.0,
    "dh_temperature_degf": 1.0,
    "annulus_pressure_psia": 20.0,
    "gas_lift_rate_mscfd": 100.0,
}

# 1 Mscf = 28.3168 m3. GL-06's gas columns were logged in m3/d under an
# Mscf/d header; this is the exact factor recovered from its GOR/GLR columns.
MSCF_TO_M3 = 28.3168

# Gaps up to this many minutes are bridged by interpolation; longer outages
# are left as NaN so that daily aggregates can report true coverage.
MAX_INTERP_GAP_MIN = 5
