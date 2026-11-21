# Agent brifi: `ML-PTA` — PTA (Task 2) + fizika/validasiya + tNavigator

**Mesajların:** `Agentic chat/chat/ml_pta.md` · **Prefiks:** `ML-PTA-###`
**Bal payı:** PTA **30** (plot-lar 10 + parametrlər 20). Bundan əlavə VFM metodologiyasının (20) validasiya hissəsi də sənindir.

## Missiya

1. 6 shut-in üçün avtomatik build-up analizi (Horner + Bourdet), bütün plot-lar və parametrlərlə.
2. VFM-in **müstəqil yoxlayıcısı** olmaq: CV protokolları, baseline-lar, ablation, UQ.
3. VFM ↔ PTA fizika dövrəsini qurmaq və tNavigator ilə verifikasiya etmək.

## Owned paths

`ml/src/pta.py`, `ml/src/physics.py`, `ml/src/eval.py`, `tnav/`, `ml/outputs/pta_*`, `ml/outputs/figures/pta_*`

## Başlamazdan əvvəl oxu

1. `docs/PHYSICS_TASK1_TASK2.md` — Hissə B (bütün düsturlar), Hissə C
2. `docs/DATA_REPORT_TASK1_TASK2.md` — §3 (ilkin Horner nəticələri, tələlər)

## Shut-in hadisələri

| Quyu | Başlanğıc | Bitmə | Müddət | Xüsusiyyət |
|---|---|---|---|---|
| GL-01 | 2025-04-15 08:00 | 04-18 08:00 | 72 saat | sərhəd / plato 3511.5 psia |
| GL-02 | 2025-03-08 14:23 | 03-08 20:02 | 5.6 saat | qısa |
| GL-04 | 2025-06-03 08:00 | 06-05 08:00 | 48 saat | uzun WBS, radial ~14 saatdan |
| GL-06 | 2025-07-22 03:11 | 07-22 11:11 | 8 saat | təmiz |
| GL-08 | 2025-08-19 09:00 | 08-22 09:00 | 72 saat | ideal infinite-acting |
| GL-10 | 2025-05-27 21:04 | 05-28 06:04 | 9 saat | qısa + sərhəd |

## Tapşırıqlar (sıra ilə)

1. **P1 `pta.py`** — VFM-i gözləmə: əvvəlcə q_o üçün test interpolyasiyası (mock) ilə başla, sonra v0-a keç
   - Δt, Pws (dəqiqəlik), Pwf(Δt=0) = son 10 dəqiqənin medianı
   - t_p = 24·N_p/q_o (D-06); Bourdet derivative (Agarwal Δt_e, L = 0.15)
   - Avtomatik radial pəncərə: WBS bitdikdən sonra + derivative CV minimal + r_i < r_e
   - m, k, P_1hr, S, ΔP_skin, p*, FE, r_i (düsturlar PHYSICS B6-da); 5 plot üçün DataFrame (C3)
2. **P2 `eval.py`** — LOTO, blocked-time (yan–iyun → iyul–sen), LOWO, trivial baseline (test interpolyasiyası), ablation (label fix, test-rejimi, dəqiqəlik vs gündəlik), cross-conformal 90% (Research-ML `uq.py` məntiqi)
3. **P3 Dövrə:** $J = 0.00708kh/(\mu B(\ln(r_e/r_w) - 0.75 + S))$ → ML-DATA-ya ötür. QC: test olmayan günlərdə E1/E2/E3 estimatorlarının uyğunluğu
4. **P4** Model-based PTA (Stehfest: WBS + skin + radial + dairəvi sərhəd) — Horner-i QC etmək üçün; sintetik benchmark (məlum k/S ilə)
5. **P5 tNavigator:** GL-08 və GL-01 üçün tək quyulu radial model, VFM rate history ilə → simulyasiya edilmiş və ölçülmüş build-up-ın müqayisəsi

## Done meyarı

- [ ] `outputs/pta_results.xlsx` 6 sətir, C3 sütunları
- [ ] Hər hadisə üçün 5 plot datası, radial pəncərə UI-da dəyişdirilə bilir
- [ ] Final q_o VFM v1-dən gəlir (test interpolyasiyasından yox)
- [ ] CV cədvəli: hər model × protokol × faza; baseline-ı keçmə göstərilib
- [ ] J_Darcy vs J_BU cədvəli + təqdimat üçün 1 slayd

## Tələlər

- k ∝ q: VFM-də 2% xəta k-da 2% xəta deməkdir (B10). Final nəticəni VFM v1 ilə yenilə.
- GL-01-də p* (3606) ≫ plato (3511): p̄-ni ayrıca göstər
- GL-04-də WBS radial pəncərəni gec başladır; GL-02/06/10 qısadır

## Kimə nə göndərirsən

- **→ ML-DATA:** J_Darcy cədvəli, CV hesabatları, fiziki QC xəbərdarlıqları
- **→ UI:** `analyze_buildup()` API, plot DataFrame-ləri, şəkillər
- **← ML-DATA-dan:** gündəlik q_o (v0 → v1)
