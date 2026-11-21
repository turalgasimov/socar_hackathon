# Agent brifi: `UI` — İnteqrasiya olunmuş interfeys (Phase 3) + Təqdimat

**Mesajların:** `Agentic chat/chat/ui.md` · **Prefiks:** `UI-###`
**Bal payı:** UI **10** (funksionallıq 4 + workflow 6) + Təqdimat **10**. Bundan əlavə VFM və PTA nəticələri münsiflərə **sənin interfeysindən** göstəriləcək.

## Missiya

İstifadəçini xam datadan son interpretasiyaya qədər addım-addım aparan bir tətbiq qurmaq. Tətbiq ML modulunu (`ml.*`) çağırır, ML məntiqini təkrar yazmır (C4). Paralel olaraq təqdimatı hazırlamaq.

## Owned paths

`ui/` (app, səhifələr, `ui/mock/`), `presentation/`

## Texnologiya (təklif)

- **Streamlit** + **Plotly**, Excel üçün **openpyxl**: `pip install streamlit plotly openpyxl`
- Başqa seçim etsən (Dash, React), `decision-proposal` göndər.

## README tələbləri → səhifələr

| README tələbi | Səhifə / funksiya |
|---|---|
| Upload well data | 1. **Upload**: CSV/ZIP yüklə, və ya default dataset |
| Visualize field measurements | 2. **Data QC**: sensor time series; shut-in, test, 06-14 trip, 08-09 outage işarələri; QC xülasəsi (sentinel/spike/gap sayları, etiket düzəlişləri) |
| Use trained models / Predict rates | 3. **VFM**: yüklənmiş model; gündəlik neft/su/qaz; test nöqtələri ilə overlay; p10–p90 zolağı; model metrikaları |
| Generate well-test plots | 4. **PTA**: hadisə seçimi → 5 plot (history, log-log + derivative, Horner, MDH/Cartesian), radial pəncərə slayderi |
| Estimate reservoir properties / Interpret | 4. **PTA**: m, k, S, ΔPskin, p*, FE cədvəli + avtomatik şərh mətni (məs. "S < 0 → stimulyasiya") |
| Export results and reports | 5. **Export**: `vfm_predictions.xlsx`, `pta_results.xlsx`, HTML/PDF hesabat |

**Workflow (6 bal):** yuxarıda stepper/progress göstər; hər addım əvvəlkinin nəticəsini istifadə etsin (`st.session_state`); "Run all" düyməsi olsun.

## Tapşırıqlar

1. **U1** Skelet + **mock data** (`web/mock/`, CONTRACTS C2/C3 sxemləri ilə). ML-i gözləmə.
2. **U2** Plotly plot-ları
3. **U3** Export
4. **U4 Təqdimat** (10–12 slayd, təklif olunan storyline):
   1. Problem: VFM + PTA niyə lazımdır
   2. Data: 3.9 M sətir, 85 etiket, 6 shut-in
   3. **Data tələləri**: GL-06 m³, işarə səhvləri, spike-lar, test-rejimi bias-ı — "biz bunları tapdıq"
   4. Fizika: quyu = təzyiq zənciri (PHYSICS §0 diaqramı)
   5. Model: grey-box choke + IPR + termal ansambl; müqayisə cədvəli (fizika > ML)
   6. Validasiya: LOTO / blocked / LOWO, leakage tələsi, UQ
   7. VFM nəticələri (dəqiqlik, gündəlik plot)
   8. PTA: avtomatik Horner + derivative, 6 hadisənin nəticələri
   9. **VFM ↔ PTA dövrəsi** (J_Darcy = J_BU) — "wow" slaydı
   10. tNavigator verifikasiyası
   11. UI demo
   12. Nəticə + növbəti addımlar
5. **U5** Demo ssenarisi (3–5 dəq)

## Done meyarı

- [ ] Tətbiq təmiz mühitdə `streamlit run ui/app.py` ilə açılır
- [ ] Upload → Export bütün axın real ML ilə işləyir
- [ ] İki Excel fayl UI-dan yüklənir və CONTRACTS sxeminə uyğundur
- [ ] Təqdimat + demo məşq olunub

## Kimə nə göndərirsən

- **→ ML-DATA / ML-PTA:** API-də çatışmayan şeylər üçün `request`, təqdimat üçün şəkil sorğuları, performans problemləri
- **← onlardan:** API, real çıxışlar, şəkillər, rəqəmlər
