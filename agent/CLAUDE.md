# SOCAR Hackathon 2026 — VFM + PTA

**Əvvəlcə oxu:** [AGENTS.md](AGENTS.md) (mühit, layout, data tələləri, modelləşdirmə qaydaları) və [PROJECT_STATE.md](PROJECT_STATE.md).

Komanda 3 agentlə işləyir: `ML-DATA`, `ML-PTA`, `UI`. Sessiyanın əvvəlində `Agentic chat/README.md`-ni oxu və protokola əməl et. Hansı agent olduğun bəlli deyilsə, insandan soruş. Agent tərifləri `.claude/agents/`-dədir.

- Tapşırıq: `docs/README.md`
- Data tələləri və plan: `docs/DATA_REPORT_TASK1_TASK2.md`, `ml/outputs/eda_summary.md`
- Fizika və düsturlar: `docs/PHYSICS_TASK1_TASK2.md`
- Baseline-lar: `python ml/eda/benchmark_vfm.py` (fizika modelləri), `ml/eda/validate_features.py` (time-forward)

Data repo-dadır: `data/` (`high_freq_data.csv` Git LFS ilə gəlir, `git lfs install` lazımdır). `data/processed/` gitignore-dadır. Ünsiyyət dili Azərbaycan dilidir, texniki terminlər ingiliscə yazılır.
