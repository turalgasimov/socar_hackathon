# Platform runbook — 22 Nov 2026

Task 2 (PTA) is submitted by Rovshan, Task 1 (VFM) by Faig. The files are in this folder, and
**alphabetical order is submission order**.

## Records to beat (exact, as the platform displayed them)

| task | record | the file that scored it |
|---|--:|---|
| Task 2 — PTA, out of 20 | **8.38397** | `ml/outputs/submitted/pta_model_match_8.3840_SHIPPED.csv` |
| Task 1 — VFM, out of 30 | **21.0200** | `ml/outputs/submitted/lam0.80_21.0200_SHIPPED.csv` (λ = 0.75 ties at 21.0200) |

## Rules for both tasks

1. **One change per submission.** Every file differs from its record file in one way only.
2. **"Won" means strictly greater than the record.** A tie keeps the record: no change is shipped
   for zero gain.
3. **Write down every score with all the decimals the platform shows,** next to the file name.
4. **Never rename or delete the two record files.** `ml/make_pta.py` reads the λ = 0.80 file as
   its rate input, and `ml/outputs/submitted/` is the audit trail.
5. **Times:**
   - decide by 11:45;
   - freeze at 12:15;
   - push by 12:45;
   - GitHub deadline 13:00.

## Task 2 — PTA (submitter: Rovshan)

Files: `pta_P0…`, `pta_P1…`, `pta_P2_down…` / `pta_P2_up…`, `pta_P3…`
(built by `python ml/eda/pta_probes.py`).

**If slots are limited:**
- 1 slot: submit P1 only.
- 2 slots: P1, then P2_up or P2_down.
- 3 or more: the full sequence.

**Step 1 — `pta_P0_skin_sign_abs.csv`** (|S| and |ΔP_skin| on GL-02, GL-04, GL-08). Skip it with
2 or fewer slots.
- **Score > 8.38397:** the platform uses a positive-skin convention. Keep P0 for the final
  combination (step 5). Go to step 2.
- **Score ≤ 8.38397:** the negative skins are confirmed. Write down the drop: (8.38397 − score) is
  what skin and ΔP_skin on those three rows were earning. Go to step 2.

**Step 2 — `pta_P1_k_from_IPR_rate.csv`** (k from the oil rate implied by the measured well tests).
- **Score > 8.38397:** step 3 with **P2_up**.
- **Score ≤ 8.38397:** step 3 with **P2_down**.

**Step 3a — `pta_P2_up_IPR_rate_x1.5.csv`** (only if P1 won).
- **Score > P1's score:** best = P2_up.
- **Otherwise:** best = P1.
- Either way, the rate ladder stops here.

**Step 3b — `pta_P2_down_IPR_rate_x-0.5.csv`** (only if P1 lost).
- **Score > 8.38397:** best = P2_down.
- **Otherwise:** the record file stays the answer. Stop.

**Step 4 — `pta_P3_IPR_rate_at_shutin_minute.csv`** (only if P1 won and a slot remains).
- **Score > best so far:** best = P3.
- **Otherwise:** keep the best.

**Step 5 — the combination** (only if P0 won **and** a rate file won). Rovshan's agent builds it
in one command: `python ml/eda/pta_probes.py --rate <best> --abs-skin --out …`.
- **Score > both:** it is final.
- **Otherwise:** the best single file is final.

**After the run, send Rovshan's agent** each file name with its exact score.
- **If a file beat 8.38397** (about 45 minutes of work), Rovshan's agent:
  1. ships the winner as a new record file named with its score;
  2. makes `ml/make_pta.py` reproduce it byte for byte;
  3. regenerates `notebooks/PTA_Phase2.ipynb`;
  4. updates the docs;
  5. hands Tural the matching `ui/pipeline.py` change.
- **If nothing beat it:** no code changes. The scores go into `agent/PROJECT_STATE.md` as tried and
  rejected, and 8.38397 is the final PTA answer.

## Task 1 — VFM (submitter: Faig)

*To be written by Faig's agent in the same format: files `vfm_V1…`, `vfm_V2…` in submission order,
each one change against 21.0200; a rule per step with the exact threshold; what to do after a win;
and the constraint that the λ = 0.80 file stays untouched because PTA reads it.*
