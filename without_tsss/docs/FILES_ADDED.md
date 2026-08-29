# Danh sách file đã thêm

## Stage 1

| File | Ý nghĩa |
|---|---|
| `.gitignore` | Ngăn lưu bytecode và thư mục cache Python |
| `AGENTS.md` | File tổng hợp mục tiêu, trạng thái, quyết định, rủi ro và quy tắc dự án |
| `README.md` | Hướng dẫn tổng quan và lệnh chạy Stage 1 |
| `requirements-stage1.txt` | Phiên bản dependency đã dùng để audit Excel |
| `artifacts/stage_01/.gitkeep` | Giữ cấu trúc thư mục artifact |
| `artifacts/stage_01/data_profile.json` | Snapshot thống kê máy đọc được của toàn bộ 90 cột, không xuất giá trị nhạy cảm |
| `docs/DECISIONS.md` | Nhật ký quyết định thiết kế và lý do |
| `docs/FILES_ADDED.md` | Danh mục mọi file mới và vai trò |
| `docs/ISSUES_AND_FIXES.md` | Nhật ký lỗi dữ liệu, lỗi chạy và cách xử lý |
| `docs/PROGRESS.md` | Tiến độ từng bước và cổng duyệt |
| `docs/PROJECT_TREE.md` | Cây thư mục dự án |
| `docs/STAGES.md` | Phạm vi, đầu ra và điều kiện hoàn tất bốn stage |
| `docs/stage_01/CODE_AUDIT.md` | Kiểm kê code/tài liệu cũ và giới hạn tái lập |
| `docs/stage_01/DATASET_AUDIT.md` | Phân tích sâu cấu trúc, target, thời gian, vị trí, thiếu, sai schema và leakage |
| `docs/stage_01/DATA_DICTIONARY.md` | Ý nghĩa và chính sách dự kiến cho đủ 90 trường |
| `docs/stage_01/FORECASTING_DESIGN.md` | Định nghĩa dự báo thời gian, rolling validation, feature, model, metric và triển khai |
| `docs/stage_01/MARKET_SANITY_CHECK.md` | Đối chiếu thận trọng với nguồn chính thức Việt Nam |
| `docs/stage_01/TEST_REPORT.md` | Lệnh, phạm vi và kết quả test cuối Stage 1 |
| `scripts/run_stage1_audit.py` | Điểm chạy tái tạo artifact kiểm toán |
| `src/property_price_forecasting/__init__.py` | Khai báo package audit |
| `src/property_price_forecasting/audit.py` | Logic đọc Excel, thống kê, kiểm tra thời gian, target, nhóm, PII và thị trường |
| `tests/test_stage1_audit.py` | Năm test tự động cho snapshot, schema, thời gian, PII và quy tắc code |

Không có file nào được thêm ngoài thư mục `property_price_forecasting`. Dataset nguồn và hai báo cáo cũ không bị sửa.

## Stage 2

| File | Ý nghĩa |
|---|---|
| `requirements-stage2.txt` | Dependency dùng cho pipeline dữ liệu Stage 2 |
| `configs/stage2.json` | Cấu hình target, population, ngày, test và chính sách không dùng TSSS |
| `artifacts/stage_02/.gitkeep` | Giữ cấu trúc artifact Stage 2 |
| `artifacts/stage_02/cleaned_tstd.jsonl.gz` | Dataset TSTĐ sạch gồm 7.025 dòng, 57 cột, định dạng JSON Lines nén |
| `artifacts/stage_02/data_contract.json` | Danh sách feature, metadata, target, diagnostic, leakage và PII máy đọc được |
| `artifacts/stage_02/quality_report.json` | Thống kê chất lượng, missing, cardinality, cờ lỗi và checksum |
| `artifacts/stage_02/split_manifest.json` | Định nghĩa development, test và bốn rolling folds |
| `docs/stage_02/BUSINESS_CONTRACT.md` | Hợp đồng target, đối tượng, inference và đầu vào vận hành |
| `docs/stage_02/CLEANING_AND_FEATURES.md` | Chi tiết chuẩn hóa, làm sạch, feature và cột bị loại |
| `docs/stage_02/DATA_QUALITY_REPORT.md` | Báo cáo số dòng/cột, target, missing, cờ chất lượng và hạn chế |
| `docs/stage_02/SPLIT_REPORT.md` | Phân chia thời gian, số mẫu, giao tài sản và quy tắc Stage 3 |
| `docs/stage_02/TEST_REPORT.md` | Kết quả 12 kiểm thử cuối Stage 2 |
| `scripts/run_stage2_pipeline.py` | Điểm chạy tái tạo toàn bộ artifact Stage 2 |
| `src/property_price_forecasting/cleaning.py` | Logic lọc TSTĐ, chuẩn hóa, feature, PII/leakage guard và xuất dữ liệu |
| `src/property_price_forecasting/splitting.py` | Định nghĩa và kiểm tra expanding-window folds |
| `tests/test_stage2_pipeline.py` | Bảy kiểm thử cho hợp đồng, dữ liệu sạch, split và chuẩn hóa |

## Stage 3

| File hoặc thư mục | Ý nghĩa |
|---|---|
| `.venv/` | Môi trường Python riêng; được ignore, không liệt kê từng file dependency |
| `requirements-stage3.txt` | Phiên bản pandas, openpyxl, scikit-learn, CatBoost và Optuna |
| `configs/stage3.json` | Metric chính, benchmark, CatBoost, Optuna, seed và ngân sách CPU |
| `artifacts/stage_03/benchmark_metrics.json` | Metric pooled/fold cho baseline, ba Ridge và CatBoost mặc định |
| `artifacts/stage_03/best_params.json` | Trial CatBoost tốt nhất, tham số và iterations theo fold |
| `artifacts/stage_03/optuna_study.db` | SQLite study có khả năng resume và lịch sử trial |
| `artifacts/stage_03/optuna_trials.json` | Bản JSON audit 14 trial records |
| `artifacts/stage_03/rolling_metrics.json` | Metric Ridge cuối theo tổng, fold và so sánh finalist |
| `artifacts/stage_03/segment_metrics.json` | Metric theo tháng, quận, lợi thế, vị trí, giá, road rarity, asset history |
| `artifacts/stage_03/oof_predictions.jsonl.gz` | 3.334 dự đoán OOF của Ridge cùng lỗi và nhãn phân khúc |
| `artifacts/stage_03/selected_model.json` | Manifest model, tham số, feature, metric, checksum và test guard |
| `artifacts/stage_03/feature_importance.json` | Hệ số tổng hợp 47 feature và top 200 transformed features |
| `artifacts/stage_03/runtime_versions.json` | Python và phiên bản thư viện thực tế |
| `artifacts/stage_03/model/ridge_model.joblib` | Model candidate fit trên toàn bộ development |
| `docs/stage_03/MODEL_BENCHMARK.md` | Thiết kế và kết quả benchmark giới hạn |
| `docs/stage_03/OPTUNA_TUNING.md` | Search space, ngân sách, trial tốt nhất và lỗi resume |
| `docs/stage_03/MODEL_SELECTION.md` | Quy tắc chọn, so sánh finalist và tham số Ridge |
| `docs/stage_03/ROLLING_VALIDATION_RESULTS.md` | Metric tổng, fold và tháng của model được chọn |
| `docs/stage_03/SEGMENT_ERROR_ANALYSIS.md` | Phân tích vùng yếu và hành động thực tế |
| `docs/stage_03/FEATURE_IMPORTANCE.md` | Cách đọc và kết quả hệ số Ridge |
| `docs/stage_03/TEST_REPORT.md` | Kết quả 19 kiểm thử cuối Stage 3 |
| `scripts/run_stage3_benchmark.py` | Chạy benchmark trên rolling folds |
| `scripts/run_stage3_tuning.py` | Tuning/resume CatBoost bằng Optuna |
| `scripts/run_stage3_finalize.py` | So sánh finalist, sinh OOF, phân khúc và model candidate |
| `src/property_price_forecasting/modeling.py` | Metric, baseline, Ridge, CatBoost, fold và segment utilities |
| `tests/test_stage3_modeling.py` | Bảy test test-guard, OOF, tuning, selection và model integrity |

## Stage 4

| File | Ý nghĩa |
|---|---|
| `requirements-stage4.txt` | Dependency cố định cho đánh giá và suy luận |
| `configs/stage4.json` | Test scope, calibration, nghiệm thu, OOD, drift và example input |
| `artifacts/stage_04/.gitkeep` | Giữ cấu trúc artifact Stage 4 |
| `artifacts/stage_04/calibration.json` | Quantile conformal 80%, 90%, 95% từ rolling OOF |
| `artifacts/stage_04/domain_profile.json` | Category support và numeric range fit chỉ từ development |
| `artifacts/stage_04/evaluation_manifest.json` | Thời điểm đánh giá, test scope, checksum và cam kết test usage |
| `artifacts/stage_04/test_metrics.json` | Metric tổng, interval coverage và nghiệm thu khóa |
| `artifacts/stage_04/segment_metrics.json` | Metric test theo 12 chiều phân khúc |
| `artifacts/stage_04/test_predictions.jsonl.gz` | 1.000 frozen test predictions không chứa ID nguồn hoặc địa chỉ chi tiết |
| `artifacts/stage_04/model_package/.gitkeep` | Giữ cấu trúc package |
| `artifacts/stage_04/model_package/deployment_manifest.json` | Model version, checksum, đường dẫn và horizon hỗ trợ |
| `artifacts/stage_04/model_package/inference_contract.json` | Trường input bắt buộc/tùy chọn/cấm và hành động ngoài miền |
| `artifacts/stage_04/model_package/monitoring_baseline.json` | Baseline input/prediction/status và ngưỡng drift |
| `artifacts/stage_04/model_package/example_input.json` | Payload mẫu không có target hoặc TSSS |
| `artifacts/stage_04/model_package/example_output.json` | Point prediction, interval, status và flags mẫu |
| `docs/stage_04/EVALUATION_PROTOCOL.md` | Protocol và ngưỡng được khóa trước test |
| `docs/stage_04/FINAL_TEST_RESULTS.md` | Metric tổng, tháng, đuôi sai số và nghiệm thu |
| `docs/stage_04/SEGMENT_ANALYSIS.md` | Phân tích vị trí, giá, rarity, asset history và guard cohort |
| `docs/stage_04/CALIBRATION_AND_GUARDRAILS.md` | Coverage interval và quy tắc auto/review/reject |
| `docs/stage_04/MODEL_CARD.md` | Intended use, giới hạn, hiệu năng và trạng thái phát hành |
| `docs/stage_04/MONITORING_AND_RETRAINING.md` | Drift, delayed-label metric, alert, retrain và rollback |
| `docs/stage_04/DEPLOYMENT_RUNBOOK.md` | Input/output, lệnh batch, xử lý trạng thái và audit |
| `docs/stage_04/TEST_REPORT.md` | Kết quả 28 kiểm thử tích hợp cuối |
| `scripts/run_stage4_evaluation.py` | Entry point đánh giá test khóa, có guard chống chạy lại |
| `scripts/predict_stage4.py` | CLI dự đoán batch từ JSON |
| `scripts/refresh_stage4_policy.py` | Bổ sung cờ phường hiếm trên frozen prediction, không gọi model lại |
| `src/property_price_forecasting/evaluation.py` | Calibration, profile, metric, segment, artifact và package logic |
| `src/property_price_forecasting/inference.py` | Validation input, tạo 47 feature, prediction interval và OOD guard |
| `tests/test_stage4_delivery.py` | Chín test khóa, metric, interval, checksum, inference và staleness |
