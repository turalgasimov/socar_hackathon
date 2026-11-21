# Agent brifi: `ML-DATA` — Data pipeline + VFM (Task 1)

**Mesajların:** `Agentic chat/chat/ml_data.md` · **Prefiks:** `ML-DATA-###`
**Bal payı:** VFM **50** (dəqiqlik 30 + metodologiya 20). Bu, komandanın ən böyük bal mənbəyidir.

## Missiya

10 quyu × 273 gün üçün gündəlik neft/su/qaz proqnozu verən, fizika strukturlu, reproduksiya olunan VFM modeli qurmaq. Model UI-a `VFMModel` kimi yüklənməli, Excel deliverable-ı isə C2 müqaviləsinə tam uyğun olmalıdır.

## Owned paths (yalnız sən dəyişirsən)

`ml/src/clean.py`, `ml/src/features.py`, `ml/src/config.py`, `ml/src/vfm.py`, `ml/models/`, `ml/outputs/vfm_*`, `.gitignore`, `requirements.txt` (ortaq: `ml/src/viz.py` — dəyişikliyi chat-da bildir)

## Başlamazdan əvvəl oxu

1. `docs/DATA_REPORT_TASK1_TASK2.md` — §1.3–1.5 (data tələləri), §2 (VFM planı)
2. `docs/PHYSICS_TASK1_TASK2.md` — Hissə A
3. `ml/eda/benchmark_vfm.py` — işləyən baseline-lar. **Buradan başla.**

## Tapşırıqlar (sıra ilə)

1. **D1 — əsası artıq var (`ml/src/clean.py`, `features.py` — Faig, commit 1dcd0ae).** Aşağıdakılardan çatışanları əlavə et:
   - sentinel `-999.25` → NaN; spike filtri (rolling median 61 dəq, 15%); dublikatları sil; sırala
   - choke step-merge; `is_test` (test pəncərəsi), `is_shut_in` (choke = 0); `qc_flag`
   - test repair: abs() + GL-06 ÷ 28.3168
   - C1 imzaları ilə
2. **D2 VFM v0** — ML-PTA və UI bunu gözləyir, **tez çıxar**:
   - E1 choke: $\ln q_L = a_w + b_1\ln S + b_2\ln\Delta p_c + b_3\ln p_{wh} + b_4\ln GLR(q_L)$, GLR implicit
   - WC(t): hər quyu üçün xətti trend; neft = q_L(1−WC), su = q_L·WC, qaz = neft·Rs/1000
   - HF-də (5 dəq) proqnoz → gündəlik orta. Shut-in-də q = 0 (S = 0 avtomatik verir)
   - Gap-lər: < 2 saat sensor interpolyasiyası; uzun gap-də gündəlik proqnozu qonşu günlərdən interpolyasiya et (GL-06 06-24 tamamilə boşdur)
   - `outputs/vfm_daily_v0.parquet` hazır olan kimi chat-a `update` yaz
3. **D3 VFM v1**
   - E2 IPR: $q_o = J_w(\bar p_r(t) - p_{wf})$. 6 quyuda J ML-PTA-dan gəlir (P3), 4 quyuda fit olunur; $\bar p_r(t)$ hamar funksiyadır
   - E3 termal: $q_o = a_w + b_w T_{gauge}$ (Joule-Thomson, LOO 2.09%)
   - Ansambl çəkiləri **nested CV** ilə (post-hoc seçim olmasın)
4. **D4** `outputs/vfm_predictions.xlsx` (2730 sətir) + `models/vfm.joblib`

## Done meyarı

- [ ] 2730 sətir, NaN yoxdur, ≥ 0, sütunlar C2-dəki kimidir
- [ ] Shut-in günləri (GL-01 04-15..18, GL-02 03-08, GL-04 06-03..05, GL-06 07-22, GL-08 08-19..22, GL-10 05-27/28) düzgün azalıb
- [ ] LOO metrikaları ML-PTA-nın `eval.py`-si ilə müstəqil təsdiqlənib (P2)
- [ ] `predict_daily()` UI-dan çağırılanda < 30 saniyə işləyir (cache ilə)

## Tələlər (unutma)

- GLR leakage (D-04); test-rejimi bias-ı — model sensorlarla idarə olunmalıdır, test debitlərini interpolyasiya etmə
- 06-14 10:20 sahə səviyyəli GL trip, 08-09 01:09–05:40 rabitə kəsilməsi
- Residual RF 85 nöqtədə overfit edir (2.11% > 1.82%)

## Kimə nə göndərirsən

- **→ ML-PTA:** gündəlik q_o (v0 hazır olan kimi), CV-ni müstəqil yoxlamaq üçün model factory
- **→ UI:** `VFMModel` API, nümunə çıxış faylları, təqdimat üçün şəkillər (model müqayisə cədvəli, fiziki eksponentlər)
- **← ML-PTA-dan:** J_Darcy cədvəli (P3), CV hesabatı (P2)
