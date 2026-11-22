"""Headless check of the screens. Run before a demo:  python ui/check_app.py   (~2 min)

ui/check_pipeline.py checks the back end; this draws the pages. It runs the sample data through
the Load page, then opens every result page in English, Azerbaijani and Russian and fails on any
exception. One fresh AppTest per page, seeded with the session state the app itself would hold,
because AppTest cannot replay some of the app's widgets between runs. Sign-in is not exercised
(ui/store.py checks it). The per-user store goes to a temp folder, so real history stays clean.
"""
import os
import sys
import tempfile
import time
from pathlib import Path

UI = Path(__file__).resolve().parent
os.chdir(UI)
os.environ["RIZZML_HOME"] = tempfile.mkdtemp(prefix="rizzml_check_")
sys.path.insert(0, str(UI))

from streamlit.testing.v1 import AppTest  # noqa: E402

USER = "rizzman@socar.az"
VIEWS = ("rates", "quality", "pta", "field", "export", "graph", "help")


def fresh(**state) -> AppTest:
    at = AppTest.from_file("app.py", default_timeout=1500)
    for k, v in {"lang": "en", "user": USER, **state}.items():
        at.session_state[k] = v
    return at


def main() -> None:
    t0 = time.time()
    a = fresh(view="load", run=("sample", "sample dataset")).run()
    assert not a.exception, [e.value for e in a.exception]
    assert not a.error, [e.value for e in a.error]
    assert a.session_state["view"] == "rates", "the analysis did not land on Production Rates"
    held = {k: a.session_state[k] for k in ("result", "exports", "source", "data_key")}
    assert all(len(v) > 0 for v in held["exports"].values()), "an export is empty"
    print(f"Load page: sample analysis in {time.time() - t0:.0f} s; exports: "
          + ", ".join(f"{k} {len(v):,} B" for k, v in held["exports"].items()))

    for lang in ("en", "az", "ru"):
        for view in VIEWS:
            at = fresh(lang=lang, view=view, **held).run()
            assert not at.exception, (lang, view, [e.value for e in at.exception])
            if view == "quality":
                rows = len(at.dataframe[0].value)
                assert rows == len(held["result"]["quality"]), "Data Quality table lost rows"
        print(f"[{lang}] {', '.join(VIEWS)}: no errors")
    print(f"OK: Load page and {len(VIEWS)} result pages in 3 languages ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
