# Kết quả thử nghiệm

## Kết quả rolling quyết định

| Hướng | MAE VND/m² | WAPE | MdAPE | Trong 10% | Trong 20% | Trong 30% |
|---|---:|---:|---:|---:|---:|---:|
| `without_tsss` khóa | 15.877.093 | 14,91% | 9,98% | 50,03% | 77,35% | 91,21% |
| `with_tsss` khóa | 14.834.391 | 13,93% | 9,21% | 53,51% | 80,71% | 92,38% |
| Equal blend được chọn | 13.959.391 | 13,11% | 8,38% | 56,48% | 82,48% | 92,68% |

Equal blend giảm MAE/WAPE 5,90% so với `with_tsss` và 12,08% so với `without_tsss`. Tuy nhiên WAPE vẫn cao hơn mục tiêu 3,11 điểm phần trăm; muốn từ 13,11% xuống 10% cần giảm thêm khoảng 23,71% tổng sai số tuyệt đối hiện tại.

## Mô hình đơn và blend đáng chú ý

| Candidate | WAPE | MAE VND/m² |
|---|---:|---:|
| Direct history | 13,61% | 14.499.656 |
| Residual market log | 13,25% | 14.113.745 |
| Residual hybrid log | 13,99% | 14.897.961 |
| Residual market raw-MAE | 13,62% | 14.500.433 |
| Equal blend cuối | 13,11% | 13.959.391 |

## Sai số theo thời gian

| Phân khúc | Số dòng | WAPE | MAE VND/m² |
|---|---:|---:|---:|
| Fold 1 | 834 | 12,56% | 12.906.350 |
| Fold 2 | 992 | 14,57% | 16.521.701 |
| Fold 3 | 697 | 12,23% | 12.738.612 |
| Fold 4 | 811 | 12,48% | 12.957.303 |

Tháng 11 và 12/2024 khó nhất, WAPE lần lượt 14,59% và 14,54%. Kết quả không suy giảm đều theo thời gian; đây là biến động regime và mix dữ liệu, không chỉ là trend một chiều.

## Sai số theo nghiệp vụ

| Phân khúc | Số dòng | WAPE | MAE VND/m² | Bias VND/m² |
|---|---:|---:|---:|---:|
| Giá từ 200 triệu | 266 | 17,76% | 56.344.591 | -26.178.571 |
| Lợi thế `Tốt` | 34 | 19,87% | 88.525.812 | -26.331.030 |
| VT1 | 798 | 14,25% | 24.664.734 | -2.623.236 |
| Quận 1 | 70 | 18,56% | 67.055.671 | -1.931.321 |
| Quận 10 | 60 | 17,11% | 31.815.559 | -2.491.439 |
| Bình Thạnh | 154 | 16,44% | 21.136.113 | -8.886.331 |
| Thành phố Thủ Đức | 912 | 16,10% | 14.070.038 | -2.892.065 |

Nút thắt chính là tài sản giá rất cao, vị trí thương mại mạnh và một số địa bàn giá cao. Nhóm `Lợi thế Tốt` chỉ có 34 dòng OOF nên vừa khó vừa thiếu mẫu. Nhóm `Kém` chỉ có một dòng, không đủ để kết luận.

## Kết luận

Thử nghiệm chứng minh TSSS anchor, residual learning và ensemble còn cải thiện được pipeline, nhưng dữ liệu hiện tại không cung cấp bằng chứng trung thực rằng WAPE dưới 10% là đạt được trên toàn population. Không nên dùng kết quả phân khúc để loại các ca khó khỏi metric; nên dùng chúng để thiết kế luồng review và kế hoạch bổ sung dữ liệu.
