# CONTRACTS — modullar arası interfeyslər (v0.2)

> Provider bu faylı yazır. Dəyişiklik üçün əvvəlcə chat-da `contract-change` göndərilir və consumer `ack` verməlidir.
> Məqsəd: UI mock data ilə **dərhal** işə başlaya bilsin, ML-PTA isə VFM bitməsini gözləmədən işləsin.
> Layout [AGENTS.md](../AGENTS.md)-dəki kimidir: kod `ml/src/` (modullar bir-birini bare name ilə import edir), yollar `ml/src/config.py`-da.

## C1. Təmiz data — provider: ML-DATA → consumer: ML-PTA, UI — **mövcuddur** (`ml/src/clean.py`)

```python
clean.clean_high_freq(use_cache=True) -> (pd.DataFrame, dict)
    # sentinel -> NaN, dublikatlar, Hampel despike, ≤5 dəq gap interpolasiyası,
    # choke join, shut-in flag; report dict hər düzəlişi saxlayır
clean.clean_well_tests() -> (pd.DataFrame, dict)
    # 5 işarə səhvi + GL-06 m3 -> Mscf
features.static_table(), features.* -> train_table (85 × 147), daily_table (2729 × 143)
```

Artifaktlar (gitignore, yenidən yaradılır): `config.F_HF_CLEAN`, `config.F_WT_CLEAN`, `data/processed/train_table.parquet`, `daily_table.parquet`.

**Açıq sual (ML-DATA):** `is_test` flag-i (test separatoru rejimi) və `qc_flag` bitmask-ı əlavə olunsunmu? (1 = sentinel, 2 = spike, 4 = interpolasiya, 8 = sahə hadisəsi: 06-14 trip, 08-09 outage)

## C2. VFM proqnozları — provider: ML-DATA → consumer: ML-PTA, UI

`ml/src/vfm.py`

```python
class VFMModel:
    def fit(self, tests_clean: pd.DataFrame, hf_clean: pd.DataFrame) -> "VFMModel"
    def predict_hf(self, hf_clean: pd.DataFrame, freq: str = "5min") -> pd.DataFrame
        # sütunlar: timestamp, well_name, liquid_rate_stbd, oil_rate_stbd, water_rate_stbd,
        #           gas_rate_mscfd, est_choke, est_ipr, est_thermal, p10_oil, p90_oil
    def predict_daily(self, hf_clean: pd.DataFrame) -> pd.DataFrame
        # sütunlar: date, well_name, oil_rate_stbd, water_rate_stbd, gas_rate_mscfd
        #           (+ isteğe bağlı: liquid_rate_stbd, wc, uptime_frac, p10_oil, p90_oil)
    def save(self, path) / @classmethod load(cls, path)

def cv_report(model_factory, tests_clean, hf_clean) -> pd.DataFrame
    # protocol (loto | time_forward | lowo), phase, mape, r2, bias
```

**Deliverable fayl** `ml/outputs/vfm_predictions.xlsx` — README-dəki dəqiq sütunlar, bu sıra ilə:

| date | well_name | oil_rate_stbd | water_rate_stbd | gas_rate_mscfd |
|---|---|---|---|---|

- 10 quyu × 273 gün = **2730 sətir**. `daily_table`-da 2729 var: GL-06 2025-06-24 günü tamamilə boşdur və imputasiya olunmalıdır.
- NaN yoxdur, hamısı ≥ 0. Shut-in günlərində debit uptime-a mütənasib azalır.
- Model faylı: `ml/models/vfm.joblib`.

## C3. PTA — provider: ML-PTA → consumer: UI

`ml/src/pta.py`

```python
@dataclass
class ShutIn: well_name: str; start: pd.Timestamp; end: pd.Timestamp

def detect_shutins(choke: pd.DataFrame, hf_clean: pd.DataFrame) -> list[ShutIn]

def analyze_buildup(ev: ShutIn, hf_clean, daily_pred, pvt, completion,
                    radial_window: tuple[float, float] | None = None) -> dict
    # "results": dict (aşağıdakı sütunlar)
    # "plots":   {"history": df, "loglog": df, "horner": df, "horner_line": df, "cartesian": df}
    #   loglog  df: dt_h, dp_psi, dp_deriv_psi, regime ("wbs"|"radial"|"boundary"|"")
    #   horner  df: horner_x (=(tp+dt)/dt), pws_psia, in_radial (bool)
    # radial_window=None -> avtomatik seçim; UI istifadəçiyə əl ilə dəyişmək imkanı verir

def run_all(hf_clean, daily_pred, choke, pvt, completion) -> pd.DataFrame
```

**Deliverable fayl** `ml/outputs/pta_results.xlsx`:

| well_name | shut_in_start | shut_in_end | duration_h | qo_stbd | np_stb | tp_h | pwf_psia | radial_start_h | radial_end_h | horner_slope_psi_cycle | permeability_md | skin | delta_p_skin_psi | p1hr_psia | p_star_psia | p_star_datum_psia | flow_efficiency | r_inv_ft |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

README-də tələb olunan minimum: **Horner slope, skin, permeability (md), delta P skin (psi)**.

## C4. UI ↔ ML qaydaları

- UI kodu `ui/` qovluğundadır (`ui` branch-ı `web/` adını `ui/` olaraq dəyişir).
- UI **heç vaxt** ML məntiqini təkrar yazmır; yalnız `ml/src` funksiyalarını çağırır.
- ML funksiyaları **plot obyekti yox, DataFrame qaytarır**. Plotly ilə render UI-ın işidir.
- ML hazır olmayana qədər UI `ui/mock/` qovluğunda bu sxemlərə uyğun mock fayllarla işləyir.
- Proqnoz/PTA 10 saniyədən uzun çəkirsə, UI `st.cache_data` istifadə edir. ML tərəfi funksiyaları deterministik saxlayır.

## Versiya tarixi

| Versiya | Tarix | Dəyişiklik | Təsdiq |
|---|---|---|---|
| v0.1 | 2026-11-21 | ilkin layihə | — |
| v0.2 | 2026-11-21 | Faig-in `ml/src` layout-una və `ui/` qovluğuna uyğunlaşdırıldı; C1 mövcud koda bağlandı | gözləyir: ML-DATA, ML-PTA, UI |
