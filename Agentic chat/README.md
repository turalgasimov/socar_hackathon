# Agentic chat — 3 agentin ortaq iş sahəsi

Komandada 3 nəfər var, hər birinin öz Claude Code agenti olacaq. Agentlər bir-biri ilə **yalnız bu qovluqdakı fayllar vasitəsilə** danışır, fayllar da git ilə sinxronlaşdırılır.

| Agent ID | İnsan | Rol | Brif |
|---|---|---|---|
| `ML-DATA` | ML/Data #1 | Data təmizləmə + VFM modeli (Task 1) | [agents/ML_DATA_VFM.md](agents/ML_DATA_VFM.md) |
| `ML-PTA` | ML/Data #2 | PTA (Task 2) + fizika/validasiya + VFM↔PTA dövrəsi + tNavigator | [agents/ML_PTA_PHYSICS.md](agents/ML_PTA_PHYSICS.md) |
| `UI` | UI/Presentation | Streamlit tətbiqi (Phase 3) + təqdimat | [agents/UI_PRESENTATION.md](agents/UI_PRESENTATION.md) |

> **İnsan ↔ agent bölgüsü (təklif, komanda təsdiqləməlidir):**
> - Faig → `ML-DATA` (təmizləmə pipeline-ı və feature-ləri artıq onun işidir: `ml/src/`)
> - Rövşən → `ML-PTA` (PTA, fizika, tNavigator)
> - Tural → `UI` (`ui` branch-ı)
>
> Rollar dəyişdirilə bilər; dəyişikliyi [DECISIONS.md](DECISIONS.md)-də qeyd edin.
> İşə başlamaq üçün Claude Code-da: `/agents` (və ya "ml-data agenti kimi işlə") — təriflər `.claude/agents/`-dədir.

## Qovluq xəritəsi

| Fayl | Nə üçün | Kim yazır |
|---|---|---|
| `README.md` | protokol (bu fayl) | yalnız insanlar |
| `agents/*.md` | hər agentin rolu, sahəsi, tapşırıqları, "done" meyarı | sahibi (öz brifini yeniləyə bilər) |
| `CONTRACTS.md` | **interfeyslər**: fayl formatları, sütunlar, Python funksiya imzaları | provider yazır; dəyişiklik üçün consumer-in təsdiqi lazımdır |
| `TASKS.md` | tapşırıq lövhəsi (ID, sahib, status) | hər agent **yalnız öz sətirlərini** yeniləyir |
| `DECISIONS.md` | qəbul edilmiş qərarlar jurnalı (append-only) | təklif chat-da, insan təsdiqindən sonra yazılır |
| `chat/ml_data.md` | ML-DATA-nın mesajları | **yalnız ML-DATA** (append-only) |
| `chat/ml_pta.md` | ML-PTA-nın mesajları | **yalnız ML-PTA** (append-only) |
| `chat/ui.md` | UI-ın mesajları | **yalnız UI** (append-only) |
| `discussions/` | çox-agentli müzakirələrin moderator xülasələri və qərar təklifləri | moderator (insan və ya koordinator agent) |

**Niyə hər agentin ayrı chat faylı var?** Hər kəs yalnız öz faylına yazır, ona görə git merge conflict demək olar ki, olmur.

## Sessiya protokolu (hər agent üçün)

**Başlanğıcda:**
1. `git pull --rebase`
2. Oxu: bu README → öz brifin → `CONTRACTS.md` → `TASKS.md` → `DECISIONS.md`
3. Oxu: **digər iki agentin chat faylında** son oxuduğun mesajdan sonra gələn hər şeyi. Sənə ünvanlananlar `@ML-DATA` / `@ML-PTA` / `@UI` / `@ALL` ilə işarələnib.
4. Cavab lazımdırsa, **öz** chat faylına yaz və mesaj ID-sinə istinad et.

**İş zamanı:**
- Yalnız öz sahəndəki kodu dəyiş (brifdəki "Owned paths" bölməsi). Başqasının sahəsinə dəyişiklik lazımdırsa, chat-da `request` göndər.
- Interfeys dəyişirsə: əvvəlcə chat-da `contract-change` təklifi göndər. Consumer `ack` verəndən sonra `CONTRACTS.md`-ni yenilə.
- Fiziki və ya rəqəmsal iddia yazanda **sübut** göstər: rəqəm + skript/fayl yolu.

**Sonda:**
1. `TASKS.md`-də öz sətirlərinin statusunu yenilə.
2. Chat-a `handoff` mesajı yaz: nə bitdi, nə qaldı, kim nəyi gözləyir.
3. `git add "Agentic chat" <öz fayllarin>` → `git commit -m "chat(ML-DATA): ..."` → `git push`.

## Mesaj formatı

```markdown
### ML-DATA-007 · 2026-11-21 15:40 (Baku) · → @ML-PTA @UI · type: update
**Mövzu:** v0 gündəlik proqnozlar hazırdır
**Məzmun:** outputs/vfm_daily_v0.parquet (2730 sətir). LOO neft MAPE 2.3%.
**Lazım olan:** @ML-PTA — shut-in-lər üçün q_o və N_p götürə bilərsən. @UI — demo üçün real fayl.
**Fayllar:** ml/vfm.py, outputs/vfm_daily_v0.parquet
**Cavab verir:** ML-PTA-004
```

- **ID:** `<AGENT>-<3 rəqəmli sıra nömrəsi>`, hər agent öz sayğacını aparır.
- **type:** `update` | `question` | `answer` | `request` | `contract-change` | `ack` | `decision-proposal` | `blocker` | `handoff`
- Qısa yaz. Uzun izahat lazımdırsa, `docs/`-a fayl yaz və ona link ver.
- `blocker` → insan da baxmalıdır: mövzunun əvvəlinə **[BLOCKER]** yaz.

## Qaydalar

1. **Son söz insanlarındır.** Agentlər təklif edir, `decision-proposal`-ı insan təsdiqləyir, sonra `DECISIONS.md`-yə yazılır.
2. Raw data `data/`-dadır (`high_freq_data.csv` Git LFS ilə; `git lfs install` lazımdır). `data/processed/` gitignore-dadır, pipeline ilə yenidən yaradılır. Yeni böyük fayl əlavə etmə: LFS kvotası 1 GB-dır.
3. Parquet artifaktları commit olunmur. Excel deliverable-ları (`ml/outputs/*.xlsx`) və kiçik modellər (`ml/models/`) commit olunur.
4. Hər nəticə reproduksiya oluna bilməlidir: skript + seed + data versiyası.
5. Vaxt zonası: Asia/Baku (UTC+4).

## Ballar (prioritet üçün)

VFM **50** (metodologiya 20 + dəqiqlik 30) · PTA **30** (plot-lar 10 + parametrlər 20) · UI **10** (funksionallıq 4 + workflow 6) · Təqdimat **10**

## Bilik bazası (hər agent oxumalıdır)

- [AGENTS.md](../AGENTS.md) — mühit, layout, data faktları, modelləşdirmə qaydaları (Faig)
- [PROJECT_STATE.md](../PROJECT_STATE.md) — cari status
- [ml/outputs/eda_summary.md](../ml/outputs/eda_summary.md), [feature_report.md](../ml/outputs/feature_report.md) — EDA və time-forward feature nəticələri
- [docs/DATA_REPORT_TASK1_TASK2.md](../docs/DATA_REPORT_TASK1_TASK2.md) — data tələləri, fizika modelləri, plan
- [docs/PHYSICS_TASK1_TASK2.md](../docs/PHYSICS_TASK1_TASK2.md) — bütün fizika və düsturlar
- [ml/eda/benchmark_vfm.py](../ml/eda/benchmark_vfm.py) — reproduksiya olunan benchmark
- [docs/README.md](../docs/README.md) — rəsmi tapşırıq
