# Property Price Forecasting

Dự án được tách thành hai pipeline chính và một nhánh thử nghiệm độc lập:

- `without_tsss/`: pipeline đã nghiệm thu, chỉ học từ TSTĐ và không dùng TSSS.
- `with_tsss/`: TSTĐ vẫn là target còn TSSS quá khứ hợp lệ được dùng làm bối cảnh thị trường.
- `wape_optimization/`: thử history feature, residual learning và ensemble để kiểm tra mục tiêu WAPE dưới 10%; không sửa hai pipeline chính.

Môi trường Python dùng chung nằm tại `.venv/`. Dataset nguồn bất biến nằm tại `../Train_noi.xlsx`.

Luồng đầy đủ của nhánh mới được ghi trong `WITH_TSSS_PIPELINE_FLOW.md`.

## Kết quả so sánh rolling

| Pipeline | Model | MAE | WAPE | Trong biên 20% |
|---|---|---:|---:|---:|
| Không TSSS | Ridge | 15,88 triệu VND/m² | 14,91% | 77,35% |
| Có TSSS | CatBoost tuned | 14,83 triệu VND/m² | 13,93% | 80,71% |
| Tối ưu WAPE | Equal blend 3 CatBoost | 13,96 triệu VND/m² | 13,11% | 82,48% |

TSSS giảm rolling MAE khoảng 6,57%. Nhánh tối ưu giảm thêm 5,90% so với `with_tsss`, nhưng chưa đạt WAPE dưới 10% và chưa production-ready. Test 05–07/2025 chỉ là reused non-confirmatory vì đã mở trong pipeline cũ; model mới cần dữ liệu sau 07/2025 để có test xác nhận độc lập.

## Tài liệu điều hướng

- Luồng tổng: `WITH_TSSS_PIPELINE_FLOW.md`.
- Audit TSSS: `with_tsss/docs/TSSS_AUDIT.md`.
- Feature: `with_tsss/docs/FEATURE_ENGINEERING.md`.
- Leakage/validation: `with_tsss/docs/LEAKAGE_AND_VALIDATION.md`.
- Benchmark/model: `with_tsss/docs/BENCHMARK_AND_MODEL_SELECTION.md`.
- Đối chứng test cũ: `with_tsss/docs/REUSED_TEST_ANALYSIS.md`.
- Suy luận/monitoring: `with_tsss/docs/INFERENCE_AND_MONITORING.md`.
- Luồng tối ưu: `wape_optimization/docs/EXPERIMENT_FLOW.md`.
- Kết quả tối ưu: `wape_optimization/docs/RESULTS.md`.
- Giới hạn và bước tiếp: `wape_optimization/docs/LIMITATIONS_AND_NEXT_STEPS.md`.
