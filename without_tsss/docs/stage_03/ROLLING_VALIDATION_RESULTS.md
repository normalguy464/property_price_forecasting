# Kết quả rolling validation của Ridge

## Tổng thể

| Metric | Giá trị |
|---|---:|
| Số OOF rows | 3.334 |
| MAE | 15.877.093 VND/m² |
| RMSE | 32.262.101 VND/m² |
| RMSLE | 0,1861 |
| WAPE | 14,91% |
| MdAPE | 9,98% |
| Trong ±10% | 50,03% |
| Trong ±20% | 77,35% |
| Trong ±30% | 91,21% |
| Mean error | -3.446.987 VND/m² |

Mean error âm cho thấy xu hướng dự đoán thấp hơn target, nhất là ở phân khúc cao. Stage 4 cần kiểm tra bias này trên test trước khi cân nhắc calibration.

## Theo fold

| Fold | Validation | Số dòng | MAE, triệu | WAPE | Trong ±20% | Mean error, triệu |
|---|---|---:|---:|---:|---:|---:|
| 1 | 09–10/2024 | 834 | 13,886 | 13,51% | 80,82% | -3,739 |
| 2 | 11–12/2024 | 992 | 18,176 | 16,02% | 75,00% | -3,041 |
| 3 | 01–02/2025 | 697 | 15,136 | 14,53% | 80,63% | -6,956 |
| 4 | 03–04/2025 | 811 | 15,749 | 15,17% | 73,86% | -0,627 |

Fold 2 yếu nhất theo MAE; fold 4 có tỷ lệ trong ±20% thấp nhất. Không có fold nào sụp hoàn toàn, nhưng độ dao động MAE 13,89–18,18 triệu là đáng kể và phải được so với test cuối.

## Theo tháng nổi bật

- 11/2024: MAE 18,62 triệu, cao nhất.
- 12/2024: MAE 17,78 triệu.
- 04/2025: MAE 16,60 triệu.
- 02/2025: MAE 15,78 triệu và xu hướng underpredict khoảng 7,62 triệu.

Metric pooled được tính trực tiếp trên toàn bộ OOF rows, không phải trung bình đơn giản metric của bốn fold.
