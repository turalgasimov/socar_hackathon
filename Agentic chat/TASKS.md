# TASKS — tapşırıq lövhəsi

Status: `todo` · `doing` · `review` · `done` · `blocked`. Hər agent **yalnız öz sətirlərini** yeniləyir. Yeni tapşırıq əlavə etmək olar (ID-ni öz prefiksinlə ver).

| ID | Tapşırıq | Sahib | Status | Asılıdır | Çıxış |
|---|---|---|---|---|---|
| T0 | `requirements.txt` (`.gitignore` artıq var) | ML-DATA | todo | — | repo |
| D1 | `ml/src/clean.py` + `features.py`: HF təmizləmə + test repair + choke join + shut-in flag + feature-lər (Faig, 1dcd0ae) | ML-DATA | **done** | — | C1 |
| D1b | `is_test` (test separatoru rejimi) flag-i + test-rejimi bias-ının ölçülməsi | ML-DATA | todo | D1 | C1 |
| D0 | **Fizika modeli (choke/IPR/termal) vs Ridge-58 feature — eyni time-forward protokolu ilə müqayisə** | ML-DATA | todo | D1 | qərar |
| D2 | VFM v0: E1 choke modeli (implicit GLR) + WC trend + qaz = neft×Rs, dəqiqəlik→gündəlik | ML-DATA | todo | D1 | C2 v0 |
| D3 | VFM v1: E2 IPR + E3 termal + ansambl (nested CV ilə çəkilər) | ML-DATA | todo | D2, P3 | C2 v1 |
| D4 | Gap / shut-in / trip günlərinin düzgün aqreqasiyası, `vfm_predictions.xlsx` | ML-DATA | todo | D2 | deliverable |
| P1 | `ml/pta.py`: shut-in aşkarlama, Bourdet, avto radial pəncərə, Horner, 5 plot üçün DataFrame | ML-PTA | todo | D1 (mock ilə başlaya bilər) | C3 |
| P2 | `ml/eval.py`: LOTO / blocked-time / LOWO, baseline-lar, ablation, conformal UQ (müstəqil yoxlayıcı) | ML-PTA | todo | D2 | metrika cədvəli |
| P3 | VFM↔PTA dövrəsi: J_Darcy(k,S) → ML-DATA-ya ötür; normal günlərdə E1/E2/E3 uyğunluq QC | ML-PTA | todo | P1, D2 | J cədvəli |
| P4 | Model-based PTA (Stehfest: WBS + skin + radial + sərhəd) QC + sintetik benchmark | ML-PTA | todo | P1 | metodologiya slaydı |
| P5 | tNavigator numerical well test (GL-08, GL-01) | ML-PTA | todo | P1, D2 | verifikasiya slaydı |
| U1 | Streamlit skelet: Upload → Data QC → VFM → PTA → Export (mock data ilə) | UI | todo | — | web/app.py |
| U2 | Plotly plotlar: sensor time series (shut-in/test/hadisə işarələri), VFM vs test, PTA 5 plot | UI | todo | U1 | web/ |
| U3 | Export: 2 Excel + HTML/PDF hesabat | UI | todo | C2, C3 | web/ |
| U4 | Təqdimat: storyline + slaydlar, şəkilləri ML agentlərdən istə | UI | todo | D2, P1 | presentation/ |
| U5 | Demo ssenarisi (3–5 dəq) və məşq | UI | todo | U1–U4 | — |
