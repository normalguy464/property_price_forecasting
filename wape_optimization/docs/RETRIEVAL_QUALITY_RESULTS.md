# Kết quả báo cáo chất lượng retrieval TSSS

## Phạm vi

Đánh giá lịch sử trên 7.025 TSTĐ và 27.425 TSSS đã làm sạch. Mỗi TSTĐ chỉ nhìn thấy TSSS có ngày thị trường, ngày có sẵn nghiêm ngặt trước thời điểm định giá, tối đa 365 ngày và khác báo cáo.

## Coverage

| Chỉ số | Kết quả |
|---|---:|
| TSTĐ có ít nhất một TSSS | 7.010 / 7.025 (99,79%) |
| TSTĐ có đủ Top-5 | 6.994 / 7.010 (99,77%) |
| TSTĐ không có TSSS | 15 |
| TSTĐ phải fallback ngoài quận | 20 |

## Phân phối score

| Metric | P25 | Trung vị | P75 | P90 |
|---|---:|---:|---:|---:|
| Score Top-1 | 66,59 | 83,77 | 91,07 | 94,83 |
| Score trung bình Top-5 | 58,46 | 75,24 | 86,63 | 91,77 |
| Score thấp nhất Top-5 | 52,49 | 67,61 | 83,78 | 89,93 |

| Nhóm score trung bình Top-5 | Số TSTĐ |
|---|---:|
| Dưới 60 | 1.892 |
| Từ 60 đến dưới 80 | 2.232 |
| Từ 80 trở lên | 2.886 |

## Chất lượng candidate

| Chỉ số | Kết quả |
|---|---:|
| Tuổi trung bình của TSSS được chọn | 101,10 ngày |
| Tỷ lệ TSSS cũ hơn 180 ngày | 19,44% |
| Tỷ lệ cùng đường | 78,76% |
| Tỷ lệ cùng phường nhưng khác đường | 20,12% |
| Tỷ lệ cùng quận nhưng khác phường | 1,05% |
| Tỷ lệ khác quận | 0,07% |
| Khớp vị trí trong khung giá | 85,17% |
| Khớp lợi thế kinh doanh | 92,92% |
| Khớp mục đích dùng đất | 85,55% |
| Khớp hình dáng | 91,53% |
| Tỷ lệ candidate duplicate cấu trúc trung bình | 5,38% |
| Độ phân tán giá raw tương đối trung bình | 15,44% |
| Độ phân tán giá estimated tương đối trung bình | 15,13% |

Duplicate cấu trúc nghĩa là các candidate trong cùng Top-5 trùng ngày, khu vực, thuộc tính, hình học và giá đơn vị sau làm tròn. Đây là tín hiệu cần review để không coi các listing gần trùng là năm quan sát độc lập.

## Backtest giá comparable

Chỉ trong bước đánh giá lịch sử, lấy weighted average theo rule distance của Top-5 rồi so với giá thật TSTĐ. Giá thật không được dùng để chọn TSSS.

| Baseline Top-5 | MAE | WAPE | MAPE | Within 10% |
|---|---:|---:|---:|---:|
| Weighted raw price | 29,73 triệu đ/m² | 27,67% | 31,01% | 19,90% |
| Weighted estimated price | 24,21 triệu đ/m² | 22,53% | 24,59% | 30,47% |

| Nhóm mean score | Estimated WAPE | Estimated MAPE | Within 10% |
|---|---:|---:|---:|
| Dưới 60 | 29,85% | 34,04% | 22,67% |
| 60 đến dưới 80 | 20,00% | 24,00% | 32,17% |
| Từ 80 trở lên | 17,76% | 18,86% | 34,27% |

## Kết luận

Score cao có quan hệ đúng chiều với chất lượng comparable: nhóm score từ 80 trở lên tốt hơn rõ rệt nhóm dưới 60. Tuy nhiên, ngay cả giá estimated weighted Top-5 ở nhóm tốt nhất vẫn có WAPE 17,76%, kém xa ensemble WAPE của nhánh này là 13,11%.

Vì vậy Top-5 TSSS phù hợp để tạo market feature, cung cấp bằng chứng cho chuyên viên và tạo cờ review; không nên lấy weighted average của chúng làm giá cuối. Các hướng cải thiện retrieval nên ưu tiên loại duplicate, thêm yếu tố nghiệp vụ chưa được score, đánh giá hoặc học lại trọng số distance bằng rolling validation, và đặt ngưỡng manual review cho score thấp hoặc giá phân tán cao.

## So sánh Top-3 và Top-5

Backtest Top-3 dùng đúng cùng 7.025 TSTĐ, cùng điều kiện as-of, scoring và trọng số khoảng cách; chỉ giảm số TSSS từ 5 xuống 3.

| Metric | Top-3 estimated weighted | Top-5 estimated weighted | Kết quả |
|---|---:|---:|---|
| MAE | 24,64 triệu đ/m² | 24,21 triệu đ/m² | Top-5 tốt hơn |
| WAPE | 22,93% | 22,53% | Top-5 tốt hơn 0,40 điểm % |
| MAPE | 24,85% | 24,59% | Top-5 tốt hơn |
| Within 10% | 30,46% | 30,47% | Gần như ngang nhau, Top-5 nhỉnh hơn |
| Mean score | 79,76 | 75,24 | Top-3 cao hơn |
| Tỷ lệ cùng đường | 82,89% | 78,76% | Top-3 cao hơn |
| Duplicate cấu trúc | 4,08% | 5,38% | Top-3 thấp hơn |

Kết luận: với bộ dữ liệu hiện tại, score cao hơn do chỉ giữ ba candidate tốt nhất không dẫn đến giá comparable chính xác hơn. Hai TSSS thứ tư và thứ năm giúp giảm phương sai giá, nên Top-5 được giữ làm cấu hình mặc định cho retrieval/market feature. Đây chỉ là kết luận cho baseline weighted comparable; không làm thay đổi ensemble WAPE.
