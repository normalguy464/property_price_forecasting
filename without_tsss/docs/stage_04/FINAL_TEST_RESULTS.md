# Kết quả test khóa

## Kết luận

Ridge candidate đạt cả ba ngưỡng nghiệm thu kỹ thuật đã khóa trước test. Kết quả này xác nhận khả năng dự báo ngoài thời gian cho giai đoạn 04/05/2025–31/07/2025, không chứng minh model còn phù hợp sau giai đoạn đó.

## Metric tổng

| Metric | Test khóa | Rolling OOF Stage 3 |
|---|---:|---:|
| Số dòng | 1.000 | 3.334 |
| MAE | 17.871.591 VND/m² | 15.877.093 VND/m² |
| RMSE | 46.209.151 VND/m² | 32.262.101 VND/m² |
| RMSLE | 0,1924 | 0,1861 |
| WAPE | 15,72% | 14,91% |
| MdAPE | 9,97% | 9,98% |
| Trong biên 10% | 50,00% | 50,03% |
| Trong biên 20% | 79,90% | 77,35% |
| Trong biên 30% | 93,30% | 91,21% |
| Mean error | -4.889.773 VND/m² | -3.446.987 VND/m² |

MAE tăng khoảng 12,6% so với OOF nhưng vẫn dưới guardrail 19.052.512 VND/m². RMSE tăng mạnh hơn MAE, cho thấy một số lỗi cực lớn trong test. Mean error âm xác nhận xu hướng dự đoán thấp.

## Nghiệm thu

| Điều kiện khóa trước test | Kết quả | Đạt |
|---|---:|---|
| MAE ≤ 19.052.512 VND/m² | 17.871.591 | Có |
| WAPE ≤ 18% | 15,72% | Có |
| Trong biên 20% ≥ 70% | 79,90% | Có |

Trạng thái: `TECHNICALLY_ACCEPTED_ON_HISTORICAL_LOCKED_TEST`.

## Theo tháng

| Tháng | Số dòng | MAE | WAPE | Trong biên 20% | Mean error |
|---|---:|---:|---:|---:|---:|
| 05/2025 | 450 | 16,65 triệu | 14,54% | 81,56% | -6,11 triệu |
| 06/2025 | 219 | 13,71 triệu | 12,60% | 83,11% | -3,44 triệu |
| 07/2025 | 331 | 22,29 triệu | 19,25% | 75,53% | -4,19 triệu |

Tháng 07/2025 xấu hơn rõ rệt và vượt ngưỡng MAE/WAPE tổng. Đây là tín hiệu suy giảm theo thời gian cần theo dõi khi bổ sung dữ liệu mới.

## Đuôi sai số

- Median absolute error: 8,73 triệu VND/m².
- P90 absolute error: 34,17 triệu VND/m².
- P95 absolute error: 50,62 triệu VND/m².
- P99 absolute error: 181,58 triệu VND/m².
- P95 absolute percentage error: 33,79%.

Không được diễn giải MAE tổng như bảo đảm cho từng bất động sản; đuôi sai số vẫn rất lớn.

## Tính độc lập của test

- Model, encoder và scaler được fit trước Stage 4.
- Test không dùng cho fit, tuning, chọn model hoặc conformal calibration.
- Test chỉ dùng để tính đánh giá cuối và phân tích rủi ro.
- Prediction artifact được đóng băng và có checksum trong evaluation manifest.
