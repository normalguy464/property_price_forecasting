# Benchmark mô hình Stage 3

## Phạm vi

Benchmark chỉ dùng 6.025 dòng development và bốn rolling folds. Tổng OOF validation là 3.334 dòng. Test 05–07/2025 không được dùng.

Các ứng viên được giới hạn:

1. Trung vị vị trí phân cấp trong cửa sổ sáu tháng: đường → phường → quận → toàn cục.
2. Ridge one-hot với alpha 1, 10, 100; target log1p.
3. CatBoost categorical native với cấu hình mặc định đã giới hạn CPU; target log1p.

## Kết quả pooled

| Model | MAE, triệu VND/m² | RMSE, triệu | RMSLE | WAPE | Trong ±20% |
|---|---:|---:|---:|---:|---:|
| Hierarchical median | 30,995 | 58,677 | 0,3564 | 29,10% | 51,86% |
| Ridge alpha 1 | 15,877 | 32,262 | 0,1861 | 14,91% | 77,35% |
| Ridge alpha 10 | 16,512 | 34,946 | 0,1909 | 15,50% | 77,59% |
| Ridge alpha 100 | 22,937 | 49,645 | 0,2543 | 21,54% | 65,24% |
| CatBoost mặc định | 16,845 | 34,983 | 0,1950 | 15,82% | 76,66% |

Ridge alpha 1 giảm MAE 48,77% so với baseline. Alpha lớn làm underfit rõ rệt. CatBoost mặc định chạm 399–400 vòng ở cả bốn fold, nên được đưa sang Optuna.

## Cấu hình Ridge

- Categorical: OneHotEncoder, `handle_unknown=ignore`, `min_frequency=5`.
- Numeric: StandardScaler.
- Target: `log1p`, dự đoán hoàn nguyên bằng `expm1`.
- Solver: `lsqr`.
- `max_iter=5000`, `tol=1e-4`.

## Kết luận benchmark

Ridge alpha 1 dẫn đầu benchmark ban đầu. CatBoost được tuning vì khoảng cách chưa lớn và có khả năng học tương tác phi tuyến vị trí–lợi thế–thời gian.
