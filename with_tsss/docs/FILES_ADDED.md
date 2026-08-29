# File đã thêm

| File | Ý nghĩa |
|---|---|
| `README.md` | Phạm vi nhánh TSSS |
| `docs/PROGRESS.md` | Tiến độ |
| `docs/DECISIONS.md` | Nhật ký quyết định |
| `docs/ISSUES_AND_FIXES.md` | Nhật ký lỗi |
| `docs/FILES_ADDED.md` | Danh mục file |

## Config và dependency

| File | Ý nghĩa |
|---|---|
| `requirements.txt` | Phiên bản dependency dùng chung với pipeline cũ |
| `configs/pipeline.json` | Eligibility, cửa sổ, back-off, model, tuning, horizon và example input |

## Code

| File | Ý nghĩa |
|---|---|
| `src/property_price_forecasting_tsss/normalization.py` | Chuẩn hóa Unicode và nhãn nghiệp vụ |
| `src/property_price_forecasting_tsss/audit.py` | Audit ngày, giá, báo cáo và nguồn TSSS |
| `src/property_price_forecasting_tsss/market_features.py` | Clean TSSS, aggregate, back-off và comparable as-of |
| `src/property_price_forecasting_tsss/modeling.py` | Metric, Ridge, CatBoost và segment utilities |
| `src/property_price_forecasting_tsss/inference.py` | Input validation, base/market feature, interval, status và coverage |
| `src/property_price_forecasting_tsss/enhanced_market_features.py` | Comparable V2 và feature xu hướng TSSS as-of |
| `src/property_price_forecasting_tsss/retrieval_adjustment.py` | Tạo cặp TSTĐ–TSSS as-of, model chọn comparable, điều chỉnh giá và lấy trung bình ba comparable |
| `scripts/run_audit.py` | Chạy audit TSSS |
| `scripts/run_features.py` | Tạo 7.025×86 feature artifact |
| `scripts/run_benchmark.py` | Benchmark Ridge/ablation/CatBoost trên rolling folds |
| `scripts/run_tuning.py` | Sáu trial Optuna có SQLite resume |
| `scripts/run_finalize.py` | Tái tạo OOF, fit model full development và báo test cũ |
| `scripts/run_weighted_training_experiment.py` | Thí nghiệm CatBoost sample-weight theo dải giá hiếm trên rolling folds |
| `scripts/run_enhanced_features.py` | Tạo feature comparable V2 và temporal market riêng, không ghi đè feature chính |
| `scripts/run_enhanced_mape_benchmark.py` | Ablation feature và benchmark ba loss bằng pooled rolling MAPE |
| `scripts/run_learned_comparable_experiment.py` | Chạy rolling retrieval–adjustment ba TSSS và blend với CatBoost khóa |
| `scripts/run_package.py` | Tạo contract, calibration, importance, monitoring và example |
| `scripts/predict.py` | CLI batch inference có TSSS warehouse |
| `tests/test_with_tsss_pipeline.py` | Test audit, as-of, leakage, feature, model, metric và inference |

## Artifact

| File | Ý nghĩa |
|---|---|
| `artifacts/tsss_audit.json` | Audit 27.452 TSSS |
| `artifacts/market_features.jsonl.gz` | 86 feature as-of cho 7.025 TSTĐ |
| `artifacts/feature_manifest.json` | Feature contract và leakage guards |
| `artifacts/benchmark_results.json` | Benchmark và ablation rolling |
| `artifacts/optuna_study.db` | Study tuning có thể resume |
| `artifacts/tuning_trials.json` | Sáu trial dạng JSON |
| `artifacts/best_parameters.json` | Trial tốt nhất và best iterations theo fold |
| `artifacts/oof_predictions.jsonl.gz` | 3.334 prediction của model được chọn |
| `artifacts/oof_segment_metrics.json` | OOF metric theo phân khúc |
| `artifacts/reused_test_predictions.jsonl.gz` | Prediction test cũ không xác nhận |
| `artifacts/test_segment_metrics.json` | Phân khúc trên test cũ |
| `artifacts/final_results.json` | Kết quả cuối và so sánh pipeline cũ |
| `artifacts/model.cbm` | CatBoost fit trên 6.025 development rows |
| `artifacts/model_manifest.json` | Model checksum, feature và tham số |
| `artifacts/weighted_training_experiment.json` | So sánh OOF giữa baseline và CatBoost có sample-weight, không thay model chính |
| `artifacts/weighted_training_oof_predictions.jsonl.gz` | Prediction OOF của thí nghiệm sample-weight để phân tích dải giá |
| `artifacts/enhanced_market_features.jsonl.gz` | Feature comparable V2 và temporal cho 7.025 TSTĐ |
| `artifacts/enhanced_feature_manifest.json` | Danh sách feature V2 và leakage guard |
| `artifacts/enhanced_mape_benchmark.json` | Kết quả ablation và lựa chọn theo pooled rolling MAPE |
| `artifacts/enhanced_mape_oof_predictions.jsonl.gz` | OOF prediction của toàn bộ candidate V2 |
| `artifacts/learned_comparable_experiment.json` | Manifest pair, leakage policy, fold metric, OOF và test cũ của thí nghiệm retrieval–adjustment |
| `artifacts/learned_comparable_oof_predictions.jsonl.gz` | OOF prediction không PII của retrieval và các blend |
| `artifacts/learned_comparable_reused_test_predictions.jsonl.gz` | Prediction test cũ không xác nhận của retrieval và các blend |
| `artifacts/feature_importance.json` | CatBoost feature importance |
| `artifacts/model_package/inference_contract.json` | Input, market source và policy |
| `artifacts/model_package/calibration.json` | Conformal quantile từ OOF |
| `artifacts/model_package/monitoring_baseline.json` | Baseline drift và coverage |
| `artifacts/model_package/example_input.json` | Input TSTĐ mẫu |
| `artifacts/model_package/example_output.json` | Prediction, interval, status và TSSS coverage mẫu |
| `artifacts/model_package/deployment_manifest.json` | Version, checksum và trạng thái phát hành |

## Tài liệu phân tích

| File | Ý nghĩa |
|---|---|
| `docs/TSSS_AUDIT.md` | Kiểm toán TSSS |
| `docs/FEATURE_ENGINEERING.md` | 86 feature và comparable |
| `docs/LEAKAGE_AND_VALIDATION.md` | Hai trục thời gian, report guard và rolling folds |
| `docs/BENCHMARK_AND_MODEL_SELECTION.md` | Benchmark, Optuna, model và tham số |
| `docs/REUSED_TEST_ANALYSIS.md` | So sánh trên test đã mở, không xác nhận |
| `docs/INFERENCE_AND_MONITORING.md` | CLI, output, tối ưu production và drift |
| `docs/WEIGHTED_TRAINING_EXPERIMENT.md` | Mục tiêu, công thức, leakage guard và cách đọc thí nghiệm sample-weight |
| `docs/ENHANCED_WITH_TSSS_EXPERIMENT.md` | Luồng comparable V2, temporal feature, loss và kết quả MAPE |
| `docs/LEARNED_COMPARABLE_EXPERIMENT.md` | Luồng chọn ba comparable, điều chỉnh, kết quả và giới hạn promote |
| `docs/TEST_REPORT.md` | Phạm vi và kết quả test |
