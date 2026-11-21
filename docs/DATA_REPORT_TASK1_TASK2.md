# SOCAR Hackathon 2026 — Data Report + Task 1 (VFM) + Task 2 (PTA)

> Hazırlanıb: 2026-11-21 · Data: `data.zip` (5 CSV, 269 MB) · Bütün rəqəmlər real analizdən gəlir (skriptlər hazırdır, `ml/`-ə köçürülə bilər).

---

## 0. TL;DR — 8 əsas tapıntı

1. **Data sintetikdir, amma "raw as recorded" kimi korlanıb**: HF-də `-999.25` sentinel-lər (~11 000 dəyər), spike-lar (dh_pressure 9220 psia-ya qədər), 2 513 dublikat sətir, sıralanmamış sətirlər, 36 saata qədər gap-lər.
2. **Etiketlərdə (well_tests) 12 səhv sətir var**: 5 işarə səhvi (mənfi dəyər) + **GL-06-nın bütün qaz dəyərləri m³/d-dədir, mscf/d deyil** (×28.317). Düzəltməyən komanda GL-06 qazında ~28× səhv edəcək.
3. **Test dəyərləri = HF-in test pəncərəsi üzrə ortası** (fərq < 0.4 psi) → test anındakı sensorlar dəqiq bilinir, label-feature uyğunluğu mükəmməldir.
4. **GOR ≈ Rs** (completion faylındakı solution GOR; nisbət 0.989 ± 0.073). Bütün quyularda Pwf > Pb (min Pwf 2273 psia > max Pb 1595) → rezervuar doymamışdır (undersaturated) → **qaz = neft × Rs**.
5. **Choke fizika modeli** (q ∝ S²·√ΔP_choke·√WHP·GLR⁻⁰·⁶): dürüst LOO MAPE maye üçün **1.82%**. Saf ML: RF 5.2%, GBM 3.8%, Ridge 2.9%.
6. **Test rejimi effekti**: test zamanı downstream təzyiq ~24 psi, Pwf ~11 psi düşür → **test debitləri normal iş rejimindən 1–4% yüksəkdir**. Test debitlərini interpolyasiya edən model sistematik olaraq yuxarı proqnoz verir.
7. **Generator neft üçün Darcy IPR istifadə edir**: Horner-dən alınan k, S ilə Darcy PI = build-up-dan ölçülən J_oil (GL-01: 3.90 vs 3.86, GL-06: 5.80 vs 5.79). Bu, **VFM ↔ PTA qapalı dövrəsi** qurmağa imkan verir.
8. **6 shut-in hadisəsi** var (5.6–72 saat), build-up əyriləri təmizdir; ilkin Horner nəticələri hazırdır (§3.3).

---

## 1. DATA REPORT

### 1.1 Fayllar

| Fayl | Sətir | Granularity | Dövr | Məzmun |
|---|---:|---|---|---|
| `high_freq_data.csv` | 3 917 073 | 1 dəqiqə × 10 quyu | 2025-01-01 → 2025-09-30 (273 gün) | 6 sensor (aşağıda) |
| `well_tests.csv` | 85 | hər test 12/16/24 saat | təxminən aylıq, quyu başına 7–9 test | ölçülmüş oil/water/gas + sensorların test ortası + fluid xassələri |
| `choke_events.csv` | 66 | hadisə (step function) | 2025-01-01 başlanğıc dəyərlər | `choke_opening_pct` (0 = shut-in) |
| `reservoir_pvt.csv` | 10 | statik | — | h, φ, ct, rw, Bo, μo, Pb, T_res, datum TVD, drainage area, Sw |
| `well_completion.csv` | 10 | statik | — | gauge TVD, GL valve TVD/port, tubing OD/ID, manifold (A/B), lift-gas SG, Rs, Bw, choke max (128/64"), first production, **cum oil @ 2025-01-01** |

**Quyular:** GL-01…GL-10, hamısı gas-lift. Manifold A: GL-01…05, Manifold B: GL-06…10.

### 1.2 Sütunlar (tip + məna)

**high_freq_data** (hamısı float64, `timestamp` datetime, `well_name` kateqoriya):

| Sütun | Vahid | Fiziki məna | VFM üçün dəyəri |
|---|---|---|---|
| `whp_psia` | psia | wellhead pressure (choke upstream) | choke tənliyi |
| `whp_downstream_psia` | psia | choke downstream / flowline | ΔP_choke = whp − downstream; test rejimi indikatoru |
| `dh_pressure_psia` | psia | downhole gauge (= Pwf gauge dərinliyində) | IPR: q = J·(Pr − Pwf); PTA build-up |
| `dh_temperature_degf` | °F | gauge temperaturu | termal siqnal: debit ↑ → T ↑ (shut-in-də 3–6 °F düşür) |
| `annulus_pressure_psia` | psia | casing/annulus (lift-gas injection) | gas-lift vəziyyəti |
| `gas_lift_rate_mscfd` | Mscf/d | injected lift gas | GLR, VLP |

**well_tests**: `oil_rate_stbd`, `water_rate_stbd`, `gas_rate_mscfd` (**hədəflər**); `total_gas_rate_mscfd` = gas + lift gas; `liquid_rate_stbd`, `water_cut_pct`, `gor_scf_stb`, `glr_scf_stb`, `bsw_pct` (törəmə); `separator_pressure/temperature`; `oil_gravity_api`, `gas_sg`, `water_salinity_ppm` (fluid).

> **Vacib:** `gas_rate_mscfd` = formasiya qazı (lift qazı **daxil deyil**). Yoxlanıb: gas + GL = total_gas.

### 1.3 HF data keyfiyyəti — problemlər və təmizləmə

| Problem | Miqyas | Təmizləmə |
|---|---|---|
| `-999.25` sentinel (LAS null) | quyu/sensor başına 45–680, cəmi ~11 000 | → NaN |
| Spike-lar | quyu/sensor başına 0–21; dh_pressure 9220, WHP 1219, GL 3990-a qədər | rolling median (61 dəq), \|x − med\| > 15% → NaN |
| Tam dublikat sətirlər | 2 513 | `drop_duplicates()` |
| Sıralanmamış timestamp-lər | quyu başına 388–1 209 | `sort_values(['well_name','timestamp'])` |
| Gap-lər | quyu başına 315–3 630 dəqiqə yoxdur | qısa: interpolyasiya; uzun: proqnozu interpolyasiya et |
| **Sahə səviyyəli rabitə kəsilməsi** | **2025-08-09 01:09 → 05:40, 10 quyunun hamısı** | interpolyasiya |
| Uzun gap-lər | GL-04 09-21→09-22 (36 saat), GL-06 06-23→06-25 (36 saat), GL-03/05/09/10 1 günlük | GL-06-da 06-24 tamamilə boşdur → proqnoz interpolyasiya |
| GL=0 "flatline" | 6 quyu | sensor xətası **deyil**, shut-in-dir (choke=0) |

### 1.4 Etiket (well_tests) səhvləri — 12 sətir

Redundant sütunlarla (liquid = oil + water, GOR = gas/oil, total_gas = gas + GL, GLR, WC) avtomatik aşkarlanıb:

| Quyu | Test tarixi | Səhv | Düzəliş |
|---|---|---|---|
| GL-04 | 2025-07-12 | `total_gas_rate` = −1753.5 | abs() |
| GL-06 | **bütün 9 test** | `gas_rate`, `total_gas_rate` **m³/d** vahidindədir (5493 vs gözlənilən 194) | ÷ 28.3168 |
| GL-06 | 2025-06-18 | `gas_lift_rate` = −717.5 | abs() |
| GL-06 | 2025-08-18 | `water_rate` = −572.2 | abs() |
| GL-08 | 2025-09-24 | `gas_rate` = −479.5 | abs() |
| GL-09 | 2025-07-27 | `gas_lift_rate` = −1010.5 | abs() |

Bundan başqa: test ayları əskikdir (GL-02 mart, GL-05 iyun, GL-08 avqust, GL-10 may — əksəriyyəti shut-in ayları ilə üst-üstə düşür).

### 1.5 Əməliyyat hadisələri

- **Shut-in-lər (choke = 0) — PTA üçün:** 6 hadisə (§3.1). Hamısında GL → 0 və HF ilə choke loqu dəqiqəsinədək uyğundur.
- **Choke dəyişiklikləri:** 66 hadisə. Shut-in-dən sonra pilləli açılma var (məs. GL-01: 21.9 → 29.7 → 37.5%, ~2.5 saat ara ilə). Test pəncərələrinin heç birində choke dəyişməyib.
- **Sahə səviyyəli gas-lift trip:** 2025-06-14 ~10:20, 10 quyunun hamısında GL ~50% düşür (kompressor) → həmin gün debit azalır.
- **Test rejimi:** hər test zamanı quyu test separatoruna keçir (aşağıdakı cədvəl, 85 testin ortası):

| | Δ downstream | Δ WHP | Δ Pwf (dh) | Δ T |
|---|---:|---:|---:|---:|
| test − (testdən 6 saat əvvəl) | **−24.2 psi** | −12.2 psi | **−11.2 psi** | +0.04 °F |

→ Pwf düşür → drawdown artır → **test zamanı debit normaldan 1–4% yüksəkdir** (GL-01: 3.86 bpd/psi × 10 psi ≈ 39 bpd ≈ 3.8%).

### 1.6 Quyu xülasəsi (test-lərdən, təmizlənmiş)

| Quyu | Mani-fold | Test sayı | Neft (yanvar→sentyabr) stb/d | WC % | GOR test / Rs | Choke % | Pwf psia | GL Mscf/d |
|---|---|---:|---|---|---|---|---|---|
| GL-01 | A | 9 | 1158 → 791 | 41.8 → 47.4 | 273 / 278 | 35.9–40.6 | 3219–3233 | 758–830 |
| GL-02 | A | 8 | 1432 → 1149 | 50.1 → 57.7 | 302 / 301 | 51.6–60.9 | 2838–2867 | 835–961 |
| GL-03 | A | 9 | 756 → 734 | 32.1 → 36.3 | 221 / 222 | 28.1–50.0 | 2479–2608 | 558–663 |
| GL-04 | A | 9 | 823 → 578 | 30.2 → 34.7 | 245 / 238 | 25.0–32.8 | 2277–2509 | 1436–1598 |
| GL-05 | A | 8 | 880 → 733 | 31.8 → 36.1 | 309 / 326 | 35.9–42.2 | 2826–2946 | 819–990 |
| GL-06 | B | 9 | 806 → 695 | 38.6 → 44.5 | 209 / 217 | 26.6–32.8 | 2649–2724 | 718–870 |
| GL-07 | B | 9 | **4696 → 3920** | 26.5 → 34.8 | 261 / 268 | 64.1–71.9 | 2728–2751 | 871–1122 |
| GL-08 | B | 8 | 1593 → 1480 | 17.1 → 23.9 | 332 / 336 | 32.8–43.8 | 2626–2696 | 468–549 |
| GL-09 | B | 9 | 1346 → 1070 | 18.0 → 26.5 | 162 / 160 | 29.7–37.5 | 2610–2719 | 848–1039 |
| GL-10 | B | 7 | 2278 → 1603 | 22.1 → 27.6 | 228 / 230 | 35.9–42.2 | 3663–3675 | 963–1022 |

Ümumi trend: neft azalır (deplesiya), WC hamar şəkildə artır (+4…+8 faiz bəndi / 9 ay), GOR sabitdir (= Rs).

### 1.7 Fiziki tapıntılar (modelləşdirmə üçün açar)

| # | Tapıntı | Sübut | Nəticə |
|---|---|---|---|
| F1 | Test sensor dəyərləri = HF test pəncərəsinin ortası | 6 sensorun hamısında fərq < 0.4 psi (gas-lift-də fərq yalnız işarə səhvlərindən) | feature-lər dəqiqdir, label noise yalnız rate-lərdədir |
| F2 | GOR = Rs | test GOR / Rs = 0.989 ± 0.073 | qaz modelə ehtiyac yoxdur: gas = oil × Rs |
| F3 | Undersaturated | min Pwf 2273 > max Pb 1595 | xətti PI (Vogel lazım deyil) |
| F4 | Choke tənliyi güclüdür | LOO 1.82% | Pr bilinmədən debit hesablanır |
| F5 | Neft üçün Darcy IPR | J_Darcy(k, S) ≈ J_oil(build-up), §3.6 | PTA → VFM əlaqəsi |
| F6 | Pr hamar azalır | build-up J ilə hesablanmış Pr: GL-01 3519 → 3435, GL-06 2841 → 2772 psia | Pr(t) üçün hamar model (MB / polinom) |
| F7 | **Joule-Thomson qızması**: T_gauge − T_res = η·(Pr − Pwf), η = 2.6–3.5 mF/psi (6 quyuda); shut-in-də T geotermal dəyərə düşür (qradiyent 1.1–1.44 °F/100ft) | per-well q_o = a + b·T → LOO **2.09%** (korrelyasiya 0.95–0.99) | 3-cü müstəqil estimator (E3) |
| F8 | Test rejimi bias-ı | §1.5 | sensor-əsaslı model avtomatik düzəldir |

---

## 2. TASK 1 — VIRTUAL FLOW METERING (50 bal: 20 metodologiya + 30 dəqiqlik)

### 2.1 Problem

- **Çıxış:** 10 quyu × 273 gün = **2 730 sətir**: `date, well_name, oil_rate_stbd, water_rate_stbd, gas_rate_mscfd` (Excel).
- **Etiket:** cəmi **85 test** (quyu başına 7–9) — çox az data → **fizika strukturu mütləqdir** (Research-ML-dən dərs: kiçik n-də tip-əyri > GBM > LSTM).
- Gizli "həqiqət" çox güman generatorun gündəlik debitləridir; test etiketlərinin özündə küy var (GOR küyü ~6–7%).

### 2.2 Aparılmış eksperimentlər (dürüst leave-one-test-out, maye debiti)

| Model | LOO MAPE | Qeyd |
|---|---:|---|
| RandomForest (raw sensorlar + quyu one-hot) | 5.19% | overfit |
| HistGradientBoosting (raw + statik, quyu ID-siz) | 3.80% | LOWO (görünməmiş quyu): **69.7%** |
| Ridge (raw + quyu one-hot) | 2.93% | |
| IPR per-well: q = a + b·t + c·Pwf | 2.10% | 3 parametr/quyu |
| **Choke fizikası (pooled, quyu intercept-ləri)** | **1.82%** | 14 parametr cəmi |
| Ensemble 0.7·choke + 0.3·IPR | **1.78%** | |
| Choke + RF residual | 2.11% | residual ML 85 nöqtədə overfit edir |
| *(Choke, GLR-də həqiqi q ilə — LEAKAGE)* | *1.02%* | *yalançı nəticə, tələ!* |

Maye → faza (LOO): **neft 2.35%** (R² 0.9987), **su 3.25%** (R² 0.9971), **qaz 5.33%** (R² 0.9953; xətanın çoxu test qazının öz küyüdür).
Termal estimator (neft birbaşa, hər quyu üçün q_o = a + b·T_gauge): **2.09%**.

Reproduksiya: `python ml/eda/benchmark_vfm.py` — bütün rəqəmləri eyni şəkildə çıxarır. Qeyd: 0.7/0.3 çəkiləri nəticəyə baxdıqdan sonra seçilib (post-hoc). Əvvəlcədən təyin olunmuş 0.5/0.5 ansamblı 1.80% verir.

Choke modelinin öyrənilmiş eksponentləri fiziki məna daşıyır: S^2.06 (≈ sahə ∝ d²), ΔP_choke^0.47 (≈ √ΔP), WHP^0.47 (qaz sıxlığı ∝ P), GLR^−0.61.

### 2.3 Tövsiyə olunan arxitektura — "Physics-structured hybrid VFM"

```
HF raw ──► Cleaning (sentinel, spike, dup, sort, gap) ──► choke merge (step) ──► 1-5 dəq resample
                                                                │
         ┌──────────────────────────────────────────────────────┼─────────────────────┐
         ▼                                                      ▼                     ▼
  [E1] Choke model                                 [E2] IPR model             [E3] Termal / GL
  ln q_L = a_w + b1 ln S + b2 ln ΔPc               q_o = J_w·(Pr_w(t) − Pwf)   (köməkçi, residual)
       + b3 ln WHP + b4 ln GLR(q)  (implicit)      J_w: PTA-dan (6 quyu) /
                                                   fit (4 quyu); Pr(t): hamar
         └──────────────► inverse-variance ensemble / stacking ◄──────────────┘
                                      │
                       q_L(t) dəqiqəlik ──► WC_w(t) (hamar trend) ──► q_o, q_w
                                      │                               q_g = q_o · Rs_w
                                      ▼
                          gündəlik orta (shut-in = 0, trip, start-up daxil) ──► Excel
```

### 2.4 Rəqiblərdən daha dəqiq olmaq üçün tryuklar (təsir sırası ilə)

1. **Etiket təmizliyi** (§1.4): GL-06 qaz vahidi + 5 işarə səhvi. Ən böyük "pulsuz" qazanc.
2. **HF təmizliyi** (§1.3): spike-lar və `-999.25` gündəlik ortanı korlayır.
3. **Fiziki dekompozisiya**: maye → WC(t) → neft/su; **qaz = neft × Rs**. Kütlə balansı avtomatik qorunur (oil + water = liquid, gas/oil = Rs). Qazı ayrıca ML ilə öyrənən rəqib küylü etiketləri əzbərləyəcək.
4. **Dəqiqəlik proqnoz + gündəlik aqreqasiya**: gündəlik orta sensorlardan proqnoz qeyri-xətti olduğuna görə bias verir; shut-in günləri (məs. GL-02 03-08: 5.6 saat dayanma → gün ~77%), pilləli start-up, 06-14 trip düzgün tutulur. Choke modelində S = 0 → q = 0 avtomatik alınır.
5. **Test rejimi bias-ını nəzərə almaq**: model sensorlarla (Pwf, ΔPc) idarə olunmalıdır; test debitlərinin sadə interpolyasiyası hər gün +1–4% səhv verir.
6. **GLR leakage-dən qaçmaq**: GLR = (GL + q_o·Rs)/q_L hədəfi ehtiva edir → implicit həll (brentq). Leakage CV-ni 1.82% → 1.02% kimi yalandan yaxşı göstərir.
7. **Çoxlu müstəqil fiziki estimator + ansambl** (choke, IPR, termal): fərqli sensor küyləri → ansambl dispersiyanı azaldır.
8. **PTA → VFM**: 6 quyuda J = Darcy(k, S) sabitlənir, p*/P̄ Pr(t)-ni anker edir → IPR estimatorunun sərbəst parametrləri azalır.
9. **Partial pooling**: eksponentlər bütün quyular üçün ümumi, yalnız intercept quyu-spesifik → 85 nöqtəyə 14 parametr.
10. **WC modeli**: hamar trend (zaman və ya kumulyativ maye üzrə) — LOO xəta 0.94 faiz bəndi; əlavə olaraq tubing qradiyenti (dh − WHP)/TVD sıxlıq → WC siqnalı ola bilər (yoxlanmalı).

### 2.5 Validasiya protokolu (metodologiya 20 bal üçün)

- **LOTO** (leave-one-test-out, quyu daxilində) — əsas metrika (gizli test eyni quyu + eyni dövrdür).
- **Blocked time CV**: yanvar–iyun train → iyul–sentyabr test (ekstrapolyasiya).
- **LOWO** (leave-one-well-out): ümumiləşdirmə üçün (saf ML 70% → fizikanın üstünlüyünü göstərir).
- Metrikalar: faza üzrə MAPE, R², bias; **trivial baseline** (test interpolyasiyası) ilə müqayisə — Research-ML-də olduğu kimi "baseline-ı keçmə" şərti.
- **Ablation**: etiket təmizliyi olmadan / test rejimi düzəlişi olmadan / dəqiqəlik vs gündəlik.
- **UQ**: cross-conformal 90% interval (Research-ML `uq.py` məntiqi) → UI-də proqnoz zolağı.
- **Fiziki QC**: q ≥ 0, choke = 0 → q = 0, gas/oil = Rs, J_VFM ≈ J_Darcy(PTA).

---

## 3. TASK 2 — AUTOMATED PTA / BUILD-UP (30 bal: 10 plot + 20 parametr)

### 3.1 Shut-in hadisələri

| # | Quyu | Shut-in | Açılma | Müddət | Qeyd |
|---|---|---|---|---:|---|
| 1 | GL-01 | 2025-04-15 08:00 | 04-18 08:00 | 72.0 saat | P plato ~3511.5 → sərhəd (A = 110 acre), derivative düşür |
| 2 | GL-02 | 2025-03-08 14:23 | 03-08 20:02 | 5.6 saat | qısa, radial axın ~1.8 saatdan |
| 3 | GL-04 | 2025-06-03 08:00 | 06-05 08:00 | 48.0 saat | **uzun wellbore storage** (hump ~0.5 saat), radial ~14 saatdan |
| 4 | GL-06 | 2025-07-22 03:11 | 07-22 11:11 | 8.0 saat | təmiz radial |
| 5 | GL-08 | 2025-08-19 09:00 | 08-22 09:00 | 72.0 saat | böyük A (620 acre) → tam infinite-acting, ən təmiz hadisə |
| 6 | GL-10 | 2025-05-27 21:04 | 05-28 06:04 | 9.0 saat | derivative gecdə düşür (A = 100 acre) |

### 3.2 Metod (README tələbi: single-phase oil, proqnozlaşdırılmış gündəlik Qo)

- **Δt, Pws**: shut-in-dən sonrakı dəqiqəlik `dh_pressure` (gauge dərinliyində; m, k, S üçün datum düzəlişi lazım deyil, p* datuma düzəldilir).
- **Pwf(Δt=0)**: shut-in-dən əvvəlki son 10 dəqiqənin medianı.
- **q_o**: shut-in-dən əvvəlki tam günün **VFM proqnozu**.
- **t_p (Horner pseudo-time)** = 24·N_p / q_o, N_p = `cum_oil_at_2025_01_01` + Σ(VFM gündəlik neft, 01-01 → shut-in). ← cum oil məhz buna görə verilib; VFM iki dəfə istifadə olunur.
- **Radial axın pəncərəsi — avtomatik**: Bourdet derivative (superposition time, L = 0.15) → 0.7 log-dövr uzunluğunda ən sabit derivative pəncərəsi.
- Düsturlar (oilfield vahidləri):
  - m = Horner xəttinin mütləq slope-u (psi/cycle)
  - **k = 162.6·q_o·B_o·μ_o / (m·h)**
  - P_1hr — Horner xəttinin Δt = 1 saatdakı qiyməti
  - **S = 1.151·[(P_1hr − Pwf)/m − log₁₀(k/(φ·μ·c_t·r_w²)) + 3.2275]**
  - **ΔP_skin = 0.869·m·S**
  - əlavə: p*, FE = (p* − Pwf − ΔPs)/(p* − Pwf), r_inv = 0.029·√(k·Δt/(φμc_t)), C (unit slope-dan)

### 3.3 İlkin nəticələr (q_o hələlik test interpolyasiyasıdır → VFM proqnozu ilə əvəzlənəcək)

| Quyu | q_o stb/d | t_p saat | Pwf psia | Radial pəncərə, saat | **m psi/cycle** | P_1hr | p* | **k md** | **Skin** | **ΔP_skin psi** | FE |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| GL-01 | 1040 | 232 513 | 3240.4 | 1.4–7.1 | 23.42 | 3480.8 | 3606.5* | 110.4 | 5.64 | 114.8 | 0.69 |
| GL-02 | 1348 | 209 194 | 2883.2 | 1.8–8.9 | 52.45 | 3125.5 | 3404.6 | 59.6 | −0.53 | −24.0 | 1.05 |
| GL-04 | 811 | 136 861 | 2307.2 | 14.1–70.8 | 144.26 | 2902.5 | 3643.5 | 56.0 | −1.23 | −154.1 | 1.12 |
| GL-06 | 715 | 170 202 | 2680.1 | 2.5–12.6 | 14.94 | 2786.0 | 2864.1 | 313.4 | 1.98 | 25.7 | 0.86 |
| GL-08 | 1405 | 91 090 | 2636.5 | 22.4–112 | 92.59 | 2986.6 | 3445.8 | 41.5 | −1.59 | −128.0 | 1.16 |
| GL-10 | 1929 | 196 997 | 3686.0 | 0.8–4.0 | 28.31 | 3888.7 | 4038.6* | 196.4 | 2.11 | 51.9 | 0.85 |

\* GL-01 və GL-10-da sərhəd effekti var — p* drenaj sahəsinin orta təzyiqindən yüksəkdir (GL-01-də ölçülən plato 3511.5); MBH düzəlişi və ya P̄ ayrıca göstərilməlidir.

**Diqqət:** k ∝ q_o → VFM-də 2% xəta k-da 2% xəta verir. Skin log(k)-dan asılıdır (az həssasdır). Yəni **VFM dəqiqliyi PTA balını da birbaşa müəyyən edir.**

### 3.4 UI-də olmalı plot-lar (hər shut-in üçün)

1. **Rate + pressure history** (Cartesian): proqnoz q_o (gündəlik) + dh_pressure, shut-in zonası rənglənmiş.
2. **Log-log diagnostic**: ΔP və Bourdet derivative; WBS unit slope, radial (flat), sərhəd bölgələri annotasiya ilə; seçilmiş pəncərə.
3. **Horner plot**: Pws vs log₁₀((t_p + Δt)/Δt), fit xətti, m, P_1hr, p* işarəli.
4. **MDH plot** (Pws vs log Δt) — t_p ≫ Δt olduğu üçün Horner ilə praktiki eynidir, QC kimi.
5. **Cartesian build-up** (Pws vs Δt) + nəticə cədvəli (Excel export).

### 3.5 Tələlər və təkmilləşdirmələr

- **Radial pəncərə seçimi** parametr dəqiqliyinin əsas mənbəyidir: GL-01 (sərhəd 1.4–7 saatda derivative-i əyir), GL-10 (qısa + sərhəd), GL-04 (WBS 10 saatdan çox). Avtomatik seçimə fiziki şərtlər əlavə edilməlidir: WBS bitməsi (unit-slope-dan ≥ 1.5 log-dövr, "1.5-cycle rule"), r_inv < r_e.
- **Model-based regressiya (güclü əlavə)**: analitik model (WBS + skin + radial + closed circle) Stehfest inversiyası ilə + nonlinear least squares → k, S, C, r_e. Horner (tələb olunan) nəticə + model match = QC. Rəqiblərin çoxu yalnız əl ilə Horner edəcək.
- **Superposition**: rate history (pilləli choke) Horner-dən daha düzgün olar; README Horner istəyir, ona görə əsas çıxış Horner, superposition yalnız QC.
- **Gauge → datum**: p* üçün qradiyent düzəlişi (datum − gauge = 280–1810 ft).

### 3.6 VFM ↔ PTA qapalı dövrəsi (təqdimat üçün "wow" məqamı)

PTA-dan alınan k, S ilə Darcy PI: **J = 0.00708·k·h / (μ_o·B_o·(ln(r_e/r_w) − 0.75 + S))**, və build-up-dan birbaşa J_oil = q_o / (P_end − Pwf):

| Quyu | J_Darcy (PTA-dan) | J_oil (build-up) | Qeyd |
|---|---:|---:|---|
| GL-01 | **3.90** | **3.86** | BU stabilləşib → dəqiq uyğunluq |
| GL-02 | 4.02 | 4.65 | BU qısa (P_end < Pr → J_oil yuxarıdır) |
| GL-04 | 0.89 | 0.95 | eyni səbəb |
| GL-06 | **5.80** | **5.79** | |
| GL-08 | 2.49 | 2.72 | infinite-acting |
| GL-10 | 8.22 | 8.42 | |

→ Generator neft üçün Darcy IPR istifadə edir. Dövrə: **VFM q_o → PTA k, S → J_Darcy → IPR VFM estimatoru (E2) → yenidən q_o**. Konsistentlik VFM və PTA-nı bir-biri ilə yoxlayır.

---

## 4. Research-ML-dən götürüləcək dərslər

| Research-ML tapıntısı | Burada tətbiqi |
|---|---|
| Kiçik n-də **fizika tip-əyrisi > GBM > LSTM** (MAPE 2.87 vs 3.00 vs 5.43) | burada da: choke 1.82 < Ridge 2.93 < GBM 3.80 < RF 5.19. LSTM etmirik |
| "GBM öyrənmirdi" (səhv lr) — hər modeli trivial baseline ilə yoxla | hər model test-interpolyasiyası baseline-ı ilə müqayisə olunur |
| Ümumi proqnoz üfüqü / leakage səhvi | GLR leakage (1.02% yalançı) — implicit həll |
| Hibrid: fizika + ML residual | residual RF hələlik overfit edir (2.11%) → residual yalnız güclü regularizasiya ilə |
| Dimensionless normalizasiya (kh, t_D) | J/kh, q/(kh·Δp) ilə quyular arası pooling |
| Cross-conformal UQ (coverage 0.83–0.90) | UI-də 90% proqnoz zolağı |
| Xam geologiya LSTM-ə ziyan verir | statik feature-ləri birbaşa yox, fiziki qruplar kimi ver |

---

## 5. tNavigator — necə istifadə edək (real, vaxta uyğun)

| # | İstifadə | Dəyər | Vaxt |
|---|---|---|---|
| T1 | **Numerical well test**: hər shut-in quyusu üçün tək quyulu radial model (h, φ, c_t, B_o, μ_o, r_w, r_e = PVT-dən; k, S = Horner-dən), VFM proqnoz rate history ilə run → simulyasiya edilmiş build-up vs ölçülmüş | k, S, q-nun üçünü birlikdə təsdiqləyir; təqdimat üçün güclü | 2–3 saat (GL-08 və GL-01 ilə başla) |
| T2 | **Auto-PTA benchmark-ı**: məlum k/S/C/r_e ilə 20–30 sintetik build-up generasiya et → bizim avtomatik Horner alqoritminin xətasını ölç | "alqoritmimiz məlum cavablarda k xətası X%" — metodologiya balı | Python analitik modellə daha sürətli; tNavigator 2–3 case üçün |
| T3 | **Pr(t) material balance**: tək quyulu model + VFM debitləri → P̄(t) | IPR estimatorunda Pr(t)-ni sabitləyir | T1 ilə birlikdə |
| T4 | VFP / lift curve (Well Designer): tubing ID, valve depth, GLR → BHP(q) | 4-cü fiziki estimator, sintetik augmentasiya | aşağı prioritet: generator tNavigator korrelyasiyasından istifadə etmir, mismatch riski |

**Data artırma haqqında açıq fikir:** VFM-də ən faydalı "artırma" tNavigator deyil, **dəqiqəlik HF + fiziki strukturdur** (85 etiket → 3.9 M sensor nöqtəsində fizika ilə proqnoz). tNavigator-un ən böyük dəyəri **PTA verifikasiyasında** (T1, T2).

---

## 6. Növbəti addımlar (təklif olunan iş bölgüsü)

| Prioritet | İş | Çıxış |
|---|---|---|
| P0 | `ml/data_prep.py`: HF + test təmizləmə, choke merge, parquet | təmiz data |
| P0 | `ml/vfm.py`: E1 choke + E2 IPR + WC + Rs, dəqiqəlik → gündəlik, LOTO/blocked/LOWO CV | `vfm_predictions.xlsx` (2730 sətir) |
| P0 | `ml/pta.py`: avtomatik Horner + Bourdet + 5 plot, VFM q_o və N_p ilə | `pta_results.xlsx` + PNG/Plotly |
| P1 | VFM ↔ PTA dövrəsi (J_Darcy), ansambl çəkiləri, conformal UQ | dəqiqlik + təqdimat |
| P1 | tNavigator T1 (GL-08, GL-01) | verifikasiya slaydı |
| P2 | Model-based PTA regressiya (Stehfest), T2 benchmark | PTA dəqiqliyi |
| P2 | UI (Streamlit + Plotly): upload → clean → VFM → PTA → export | Phase 3 |

**Mühit:** `pip install openpyxl streamlit plotly` (hazırda quraşdırılmayıb; pandas 2.2.3, sklearn 1.9, scipy 1.15, torch var).
**Git:** `data/high_freq_data.csv` Git LFS ilə izlənir (Faig, 1dcd0ae); `data/processed/` gitignore-dadır.
