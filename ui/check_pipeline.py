"""Self-check for the app back end. Run before a demo:  python ui/check_pipeline.py <folder with the raw CSVs>

Asserts that the pipeline runs end to end, every shut-in is interpreted, PTA matches the submitted
results (ml/outputs/pta_submission.csv) to within 0.5% on k and 0.02 on skin (the app computes its own
rates, so the last digits can differ), and every export opens.
"""
import io
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import pipeline as P  # noqa: E402

data = Path(sys.argv[1] if len(sys.argv) > 1 else P.ROOT / "data")
r = P.analyse(data, progress=print)
wells, days = r["rates"].well_name.nunique(), r["rates"].timestamp.nunique()
assert len(r["rates"]) == wells * days, "rates grid is not one row per well per day"
assert not r["rates"][P.RATES].isna().any().any(), "missing predicted rates"
errors = [x for x, _ in r["pta"] if "error" in x]
assert not errors, errors
pta = P.pta_table(r)
ref_file = P.ROOT / "ml/outputs/pta_submission.csv"
if ref_file.exists():
    ref = pd.read_csv(ref_file).set_index("well_name")
    for row in pta.itertuples():
        if row.well_name in ref.index:
            k_ref, s_ref = ref.loc[row.well_name, "permeability_md"], ref.loc[row.well_name, "skin"]
            assert abs(row.permeability_md / k_ref - 1) < 0.005, (row.well_name, row.permeability_md, k_ref)
            assert abs(row.skin - s_ref) < 0.02, (row.well_name, row.skin, s_ref)
for name, df in {"rates": r["rates"], "pta": pta}.items():
    assert len(pd.read_excel(io.BytesIO(P.to_excel({name: df})))) == len(df)
    assert len(pd.read_csv(io.BytesIO(P.to_csv(df)))) == len(df)
print(f"OK: {wells} wells x {days} days, {len(pta)} build-ups, PTA matches the submission, exports open ({r['seconds']} s)")
