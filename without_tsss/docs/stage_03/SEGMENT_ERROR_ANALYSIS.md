# Phân tích sai số theo phân khúc

## Vị trí

Các quận có MAE tuyệt đối cao nhất:

| Quận | Số dòng | MAE, triệu | WAPE | Trong ±20% |
|---|---:|---:|---:|---:|
| Quận 1 | 70 | 73,88 | 20,45% | 61,43% |
| Quận 3 | 39 | 39,86 | 18,07% | 66,67% |
| Quận 4 | 20 | 35,63 | 17,19% | 75,00% |
| Quận 10 | 60 | 34,87 | 18,75% | 63,33% |
| Quận 5 | 31 | 33,19 | 13,94% | 67,74% |

MAE cao một phần do mặt bằng giá cao, nên phải đọc cùng WAPE và cỡ mẫu. Quận 1 vẫn là vùng rủi ro rõ ràng.

## Khoảng giá

| Target | Số dòng | MAE, triệu | WAPE | Mean error, triệu |
|---|---:|---:|---:|---:|
| Dưới 60 triệu | 794 | 6,25 | 13,02% | +3,08 |
| 60–100 triệu | 1.331 | 8,77 | 11,21% | +0,23 |
| 100–200 triệu | 943 | 19,61 | 14,40% | -3,26 |
| Từ 200 triệu | 266 | 66,95 | 21,10% | -42,01 |

Model chuyển từ overpredict ở giá thấp sang underpredict mạnh ở giá cao. Không nên calibration toàn cục bằng một hằng số.

## Lợi thế kinh doanh

| Nhóm | Số dòng | MAE, triệu | WAPE | Trong ±20% |
|---|---:|---:|---:|---:|
| Tốt | 34 | 113,66 | 25,51% | 52,94% |
| Khá | 315 | 32,36 | 16,18% | 67,30% |
| Trung bình | 2.984 | 13,03 | 14,04% | 78,69% |
| Kém | 1 | 5,51 | 12,39% | 100% |

Nhóm Tốt rất yếu và hiếm. Kết quả này xác nhận một nhãn lợi thế không đủ mô tả tài sản cao cấp nếu thiếu thêm dữ liệu vị trí/chất lượng.

## Vị trí khung giá

- VT1: MAE 29,10 triệu, WAPE 16,81%.
- VT2: MAE 13,08 triệu.
- VT3: MAE 9,27 triệu.
- VT4: MAE 10,33 triệu.

VT1 thường đi cùng mặt bằng giá cao nên sai số tuyệt đối lớn hơn.

## Đường hiếm và tài sản mới

- Đường hiếm/chưa thấy trong train fold: 1.184 dòng, MAE 22,19 triệu.
- Đường phổ biến: 2.150 dòng, MAE 12,40 triệu.
- Tài sản mới trong fold: 2.931 dòng, MAE 16,07 triệu.
- Tài sản đã từng thấy: 403 dòng, MAE 14,47 triệu.

Stage 4 cần báo test theo hai nhóm tài sản. Với đường hiếm, inference nên kèm cảnh báo confidence thấp hoặc back-off về phường/quận.

## Hành động đề xuất

- Thiết lập human review cho target dự đoán cao, Quận 1, lợi thế Tốt và đường chưa thấy.
- Dùng prediction interval thay vì chỉ điểm dự đoán.
- Thu thập thêm TSTĐ cao cấp; quyết định không dùng TSSS làm giới hạn khả năng bổ sung tín hiệu thị trường.
- Không chỉnh trọng số `Lợi thế kinh doanh` bằng tay; cần thêm mẫu hoặc feature xác định hơn.
