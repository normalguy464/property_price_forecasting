# Đối chứng trên test đã mở

## Cảnh báo diễn giải

Đây không phải test xác nhận độc lập vì 1.000 dòng 05–07/2025 đã được xem trong pipeline cũ. Model TSSS không dùng chúng để chọn thiết kế hoặc tham số, nhưng người phát triển đã biết hiệu năng baseline trên giai đoạn này.

| Metric | Không TSSS | Có TSSS | Thay đổi |
|---|---:|---:|---:|
| MAE | 17,87 triệu | 16,10 triệu | giảm 9,92% |
| RMSE | 46,21 triệu | 38,57 triệu | giảm 16,53% |
| RMSLE | 0,1924 | 0,1716 | tốt hơn |
| WAPE | 15,72% | 14,16% | giảm 1,56 điểm % |
| MdAPE | 9,97% | 8,50% | giảm 1,47 điểm % |
| Trong biên 10% | 50,0% | 55,5% | tăng 5,5 điểm % |
| Trong biên 20% | 79,9% | 83,3% | tăng 3,4 điểm % |
| Trong biên 30% | 93,3% | 91,7% | giảm 1,6 điểm % |

Within 30% giảm dù các metric khác tốt hơn, cho thấy vẫn có một số lỗi đuôi và không nên chỉ nhìn MAE.

Theo tháng, MAE có TSSS là 15,29 triệu tháng 5, 14,39 triệu tháng 6 và 18,33 triệu tháng 7. Tháng 7 vẫn xấu nhất, củng cố yêu cầu dữ liệu mới và giám sát drift.

## Kết luận

TSSS cho tín hiệu nhất quán giữa rolling validation và giai đoạn test cũ, nhưng bằng chứng phát hành cuối cùng vẫn cần một test mới sau 31/07/2025 chưa từng được mở.
