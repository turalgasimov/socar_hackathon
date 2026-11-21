# DECISIONS — qərarlar jurnalı (append-only)

Format: `D-<nömrə> · tarix · qərar · səbəb/sübut · təklif edən · təsdiq edən`.
Qərarı dəyişmək lazımdırsa, köhnəsini silmə; yeni qərar yaz və "D-xx-i əvəz edir" qeyd et.

| ID | Tarix | Qərar | Səbəb / sübut | Təklif | Təsdiq |
|---|---|---|---|---|---|
| D-01 | 2026-11-21 | Etiket düzəlişi: işarə səhvləri → abs(); GL-06 qazı ÷ 28.3168 | redundant sütunlar (liquid, GOR, total gas), DATA_REPORT §1.4 | setup | insan |
| D-02 | 2026-11-21 | Qaz = neft × Rs (completion faylından); ayrıca qaz modeli yoxdur | GOR/Rs = 0.989 ± 0.073; Pwf > Pb hər yerdə | setup | insan |
| D-03 | 2026-11-21 | Proqnoz HF səviyyəsində (1–5 dəq) aparılır, sonra gündəlik ortalanır | shut-in, start-up, trip, test-rejimi düzgün tutulur | setup | insan |
| D-04 | 2026-11-21 | GLR feature-u implicit həll olunur (leakage qadağandır) | leakage CV-ni 1.82% → 1.02% kimi yalandan yaxşı göstərir | setup | insan |
| D-05 | 2026-11-21 | Əsas model fizika strukturlu grey-box-dur; saf GBM/RF yalnız baseline-dır | LOO: choke 1.82%, Ridge 2.93%, GBM 3.80%, RF 5.19% | setup | insan |
| D-06 | 2026-11-21 | Horner t_p = 24·N_p/q_o; N_p = cum_oil_2025-01-01 + Σ VFM | README + verilmiş cum_oil sütunu | setup | insan |
| D-07 | 2026-11-21 | Qapalı-tank material balance istifadə edilmir; p̄r(t) datadan öyrənilir | MB 11.7 psi/gün proqnozlaşdırır, müşahidə ~0.3 (PHYSICS A2.2) | setup | insan |
