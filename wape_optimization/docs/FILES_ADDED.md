# File đã thêm

Tất cả file dưới đây chỉ thuộc `wape_optimization`; hai pipeline chính không bị ghi đè.

## Cấu hình và code

| File | Ý nghĩa |
|---|---|
| `configs/experiments.json` | Nguồn khóa, cửa sổ lịch sử, CatBoost và mục tiêu WAPE |
| `src/property_price_forecasting_wape/history_features.py` | Tạo feature lịch sử TSTĐ as-of có lag và back-off |
| `src/property_price_forecasting_wape/experiments.py` | Metric, anchor, fit và predict các biến thể CatBoost |
| `scripts/run_history_features.py` | Sinh feature lịch sử và manifest |
| `scripts/run_experiments.py` | Chạy direct/residual rolling và blend ban đầu |
| `scripts/run_additional_experiments.py` | Thử residual raw-MAE và correction tuần tự |
| `scripts/run_finalize.py` | Fit component toàn development, test không xác nhận và đóng gói |
| `tests/test_wape_optimization.py` | 10 kiểm tra artifact, leakage, metric và model |

## Artifact

| File | Ý nghĩa |
|---|---|
| `artifacts/history_features.jsonl.gz` | 58 feature lịch sử cho 7.025 TSTĐ |
| `artifacts/history_manifest.json` | Hợp đồng feature và leakage guard |
| `artifacts/component_oof_predictions.npz` | Dự đoán OOF của các component |
| `artifacts/selected_oof_predictions.jsonl.gz` | OOF của giải pháp được chọn |
| `artifacts/experiment_results.json` | Candidate, metric, iteration và quyết định chọn |
| `artifacts/oof_segments.json` | Metric rolling theo fold, tháng, quận, lợi thế, vị trí và dải giá |
| `artifacts/components/residual_market_log.cbm` | Component residual log fit toàn development |
| `artifacts/components/residual_market_raw.cbm` | Component residual raw-MAE fit toàn development |
| `artifacts/solution_manifest.json` | Trọng số, feature, đường dẫn và checksum model |
| `artifacts/calibration.json` | Quantile conformal từ rolling OOF |
| `artifacts/reused_test_predictions.jsonl.gz` | Dự đoán test cũ, sai số và interval |
| `artifacts/reused_test_segments.json` | Phân khúc trên test cũ không xác nhận |
| `artifacts/final_results.json` | Kết quả cuối và so sánh ba hướng |

## Tài liệu

| File | Ý nghĩa |
|---|---|
| `README.md` | Tổng quan và cách chạy |
| `docs/EXPERIMENT_FLOW.md` | Luồng dữ liệu và thí nghiệm |
| `docs/MODEL_DESIGN.md` | Feature, mô hình và tham số đã chọn |
| `docs/VALIDATION_AND_LEAKAGE.md` | Rolling validation và rào leakage |
| `docs/RESULTS.md` | Kết quả tổng và theo phân khúc |
| `docs/REUSED_TEST.md` | Đối chứng test 05–07/2025 |
| `docs/LIMITATIONS_AND_NEXT_STEPS.md` | Giới hạn và điều kiện để tiến gần 10% |
| `docs/TEST_REPORT.md` | Kết quả kiểm thử cuối |
| `docs/PROGRESS.md` | Tiến độ |
| `docs/DECISIONS.md` | Nhật ký quyết định |
| `docs/ISSUES_AND_FIXES.md` | Lỗi, rủi ro và cách xử lý |
| `docs/FILES_ADDED.md` | Danh sách file và ý nghĩa |
