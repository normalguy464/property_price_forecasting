# Phân tích test theo phân khúc

## Nhóm cần ưu tiên xử lý

| Nhóm | Số dòng | MAE | WAPE | Trong biên 20% | Mean error |
|---|---:|---:|---:|---:|---:|
| Giá thật ≥ 200 triệu/m² | 77 | 85,17 triệu | 25,15% | 61,04% | -67,51 triệu |
| Lợi thế kinh doanh `Tốt` | 6 | 150,17 triệu | 28,04% | 50,00% | -122,97 triệu |
| Đường chưa thấy trong development | 66 | 43,12 triệu | 25,55% | 71,21% | -28,47 triệu |
| Đường hiếm | 247 | 21,61 triệu | 16,13% | 78,95% | -3,19 triệu |
| Phường hiếm | 4 | 158,70 triệu | 49,90% | 0,00% | -151,20 triệu |
| Tài sản mới | 631 | 19,48 triệu | 16,67% | 79,56% | -8,45 triệu |

Nhóm `Tốt` và phường hiếm có rất ít mẫu nên metric có phương sai cao, nhưng mức sai số đủ lớn để không cho tự động chấp nhận.

## Vị trí trong khung giá

| Vị trí | Số dòng | MAE | WAPE | Trong biên 20% |
|---|---:|---:|---:|---:|
| VT1 | 244 | 32,72 triệu | 18,87% | 72,54% |
| VT2 | 453 | 15,82 triệu | 15,64% | 79,25% |
| VT3 | 184 | 8,51 triệu | 10,12% | 88,04% |
| VT4 | 119 | 9,69 triệu | 11,49% | 84,87% |

VT1 khó hơn đáng kể do chứa nhiều bất động sản mặt đường và giá cao.

## Quận có ít nhất 20 mẫu

| Quận | Số dòng | MAE | WAPE | Trong biên 20% |
|---|---:|---:|---:|---:|
| Quận 1 | 22 | 58,67 triệu | 17,45% | 68,18% |
| Quận 7 | 55 | 35,63 triệu | 20,84% | 72,73% |
| Phú Nhuận | 20 | 26,82 triệu | 14,18% | 70,00% |
| Bình Thạnh | 48 | 25,24 triệu | 18,36% | 79,17% |
| Thành phố Thủ Đức | 226 | 23,27 triệu | 22,09% | 69,47% |

Các quận giá cao và Thành phố Thủ Đức cần mô hình/feature địa phương tốt hơn, nhiều dữ liệu mới hơn và có thể cần mô hình phân tầng trong lần phát triển tiếp theo.

## Tài sản mới và tái thẩm định

| Nhóm | Số dòng | MAE | WAPE | Trong biên 20% |
|---|---:|---:|---:|---:|
| Tài sản mới | 631 | 19,48 triệu | 16,67% | 79,56% |
| Tài sản đã thấy | 369 | 15,12 triệu | 13,97% | 80,49% |

Mô hình không dùng ID tài sản nhưng vẫn tốt hơn ở tài sản tái thẩm định, có thể do nhóm này nằm trong khu vực quen thuộc hơn. Metric production phải tiếp tục tách hai nhóm.

## Chất lượng dữ liệu

28 dòng có cờ quy tắc chất lượng đạt MAE 11,93 triệu, không xấu hơn nhóm sạch. Điều này không chứng minh cờ vô ích: các rule hiện tại chủ yếu là cờ rà soát rộng và nhóm nhỏ. Không được loại hàng loạt chỉ dựa trên kết quả này.

## Hiệu quả của cổng kiểm duyệt

| Trạng thái | Số dòng | MAE | WAPE | Trong biên 20% |
|---|---:|---:|---:|---:|
| Tự động | 616 | 11,79 triệu | 12,80% | 82,95% |
| Kiểm duyệt thủ công | 384 | 27,62 triệu | 18,63% | 75,00% |

Cổng guard đã tập trung phần lớn trường hợp khó vào nhóm kiểm duyệt. Không có dòng test nào bị từ chối vì tất cả ngày/quận đều nằm trong miền đã kiểm chứng.
