# File đã thêm

| File | Ý nghĩa |
|---|---|
| `configs/pipeline.json` | Target, time split, CatBoost và cấu hình rare-band |
| `src/tsss_only/modeling.py` | Metric, log/raw CatBoost, sample-weight và oversampling |
| `scripts/run_stage2.py` | Tạo dữ liệu TSSS-only, contract và split |
| `scripts/run_stage3_benchmark.py` | Benchmark rolling các phương án xử lý imbalance |
| `scripts/run_stage4_finalize.py` | Fit model chọn và đánh giá temporal holdout |
| `scripts/run_external_tstd_test.py` | External test trên TSTĐ 05–07/2025, không dùng TSTĐ train/chọn model |
| `tests/test_tsss_only.py` | Test population, target, exclusion, benchmark và holdout |
| `docs/PIPELINE.md` | Luồng và leakage guard |
| `docs/PROGRESS.md` | Tiến độ |
| `docs/RESULTS.md` | Metric, model chọn và giới hạn đánh giá |
| `docs/ISSUES_AND_FIXES.md` | Vấn đề asset overlap và xử lý |
| `artifacts/stage_02/cleaned_tsss.jsonl.gz` | Dữ liệu TSSS đã chuẩn hóa |
| `artifacts/stage_03/benchmark_results.json` | Kết quả benchmark OOF |
| `artifacts/stage_03/final_results.json` | Model chọn và metric test |
| `artifacts/stage_03/external_tstd_test_results.json` | Metric external temporal test trên TSTĐ |
| `artifacts/stage_03/external_tstd_test_predictions.jsonl.gz` | Prediction external test TSTĐ không chứa PII |
