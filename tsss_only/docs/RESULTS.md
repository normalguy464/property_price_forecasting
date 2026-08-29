# Kết quả TSSS-only

Target là `Đơn giá quyền sử dụng đất (đ/m2)1` của TSSS. Không dùng `Tình trạng giao dịch`, tổng giá trị quyền sử dụng đất, giá trị định giá, giá rao/giao dịch hay các cột leakage làm feature.

## Population

- 27.452 TSSS hợp lệ.
- 23.746 development và 3.706 temporal holdout.
- Không loại outlier.
- Target median 86,44 triệu đồng/m².

## Rolling benchmark

| Model | MAPE | WAPE | MAE đồng/m² |
|---|---:|---:|---:|
| Hierarchical median | 24,65% | 27,05% | 29.697.964 |
| Ridge log | 11,66% | 12,55% | 13.774.647 |
| CatBoost log | 2,67% | 3,27% | 3.588.069 |
| CatBoost raw | 3,70% | 4,16% | 4.567.107 |
| CatBoost log + sample-weight | 2,83% | 3,43% | 3.766.606 |
| CatBoost log + oversampling | 2,74% | 3,31% | 3.634.171 |

CatBoost log được chọn. Sample-weight và oversampling đều làm MAPE/WAPE xấu hơn nên không dùng.

## Temporal holdout

CatBoost log đạt MAPE 2,91%, WAPE 4,10% và MAE 4.920.847 đồng/m² trên 3.706 dòng test.

## Giới hạn bắt buộc

Toàn bộ 3.706 tài sản test đã xuất hiện trong development theo `Mã tài sản`. Vì vậy metric này chỉ phù hợp kịch bản định giá lại tài sản đã có lịch sử TSSS; không được báo cáo là độ chính xác cho tài sản mới hoàn toàn. Không thực hiện tuning thêm trên split này. Muốn đánh giá tài sản mới cần group split theo `Mã tài sản` hoặc một tập TSSS mới có tài sản chưa từng xuất hiện.

## External test trên TSTĐ

Model TSSS-only được test đúng một lần trên 1.000 TSTĐ từ 05–07/2025. Không có TSTĐ nào được dùng để train, benchmark hoặc chọn model.

- MAPE: 60,45%.
- WAPE: 67,09%.
- MAE: 76.257.470 đồng/m².
- Median dự đoán: 33,31 triệu đồng/m², trong khi median target TSTĐ là 91,20 triệu đồng/m².

Kết luận: TSSS-only không thể dùng trực tiếp để dự đoán TSTĐ. Hai population có khác biệt phân phối/lineage nhãn rất lớn; TSSS-only chỉ dùng cho bài toán dự đoán hoặc định giá lại TSSS, còn dự đoán TSTĐ phải giữ pipeline TSTĐ hoặc with-TSSS ban đầu.
