# Cải thiện comparable, xu hướng thị trường và mục tiêu MAPE

## Phạm vi

Thí nghiệm giữ nguyên population TSTĐ, target đơn giá đất và 86 feature TSSS hiện tại. TSSS vẫn chỉ là nguồn lịch sử as-of. Model chính và test 05–07/2025 không được dùng để lựa chọn hoặc tự động thay thế.

## Bước 1: Comparable V2

Comparable V2 chọn tối đa 10 TSSS trong cùng quận, sau đó xếp hạng theo đường/phường, vị trí khung giá, lợi thế kinh doanh, mục đích sử dụng, hình dáng, diện tích, mặt tiền, chiều dài, khoảng cách đường chính, độ rộng ngõ và tuổi dữ liệu. Trọng số cuối giảm theo khoảng cách tương đồng và half-life thời gian 180 ngày; TSSS đã giao dịch được tăng trọng số 25%.

Mười lăm feature mới mô tả giá weighted, median, quantile, độ mới, độ tương đồng địa bàn, tỷ lệ giao dịch, effective sample size, MAD và tỷ lệ giá ước tính/giá raw.

## Bước 2: Xu hướng thị trường

Mười tám feature mới mô tả log-trend 90/365 và 180/365 ngày, tốc độ xuất hiện TSSS, tỷ lệ giao dịch, chênh giá giao dịch/rao bán, IQR tương đối và việc back-off thay đổi cấp địa bàn. Các feature đều được suy ra từ aggregate as-of hiện có nên không nhìn tương lai.

## Bước 3: Benchmark theo MAPE

Benchmark thay tám comparable cũ bằng comparable V2, thêm temporal riêng vào baseline, rồi dùng cả hai với RMSE, MAE và Huber. Tất cả dùng cùng CatBoost tuned và bốn expanding rolling folds. Model được xếp hạng theo pooled rolling MAPE; WAPE chỉ phá hòa. Test 05–07/2025 không được mở lại trong thí nghiệm.

## Kết quả

Baseline hiện tại đạt pooled rolling MAPE 12,60%, WAPE 13,93% và MAE 14.834.391 đồng/m².

| Candidate | MAPE | WAPE | Số fold cải thiện MAPE |
|---|---:|---:|---:|
| Comparable V2 thay comparable cũ, RMSE | 12,93% | 14,16% | 1/4 |
| Temporal market, RMSE | 12,94% | 14,24% | 0/4 |
| Comparable V2 + temporal, RMSE | 13,11% | 14,25% | 0/4 |
| Comparable V2 + temporal, MAE | 13,45% | 14,86% | 0/4 |
| Comparable V2 + temporal, Huber | 64,04% | 62,68% | 0/4 |

Huber trên log-target không hội tụ thành candidate hữu ích trong cấu hình này và bị loại. Candidate mới tốt nhất vẫn làm MAPE tăng 0,32 điểm phần trăm và WAPE tăng 0,23 điểm phần trăm. Vì vậy không promote model hoặc feature V2; package inference hiện tại giữ nguyên.

Kết quả cho thấy comparable cũ top-5 đang phù hợp dữ liệu này hơn công thức V2 top-10. Các trend 90/365 và 180/365 không tạo thêm tín hiệu ổn định, có thể do dữ liệu chỉ phủ khoảng 17 tháng và TSSS giao dịch thật chỉ có 416 dòng. Không nên tiếp tục tăng số trend hoặc tuning loss trên cùng OOF.
