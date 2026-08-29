# Đối chứng test đã mở

Test 05–07/2025 gồm 1.000 dòng, được chạy sau khi giải pháp và trọng số đã khóa. Vì tập này đã được xem ở các pipeline trước, mọi số liệu dưới đây là non-confirmatory.

| Metric | Kết quả |
|---|---:|
| MAE | 14.971.066 VND/m² |
| WAPE | 13,17% |
| MdAPE | 8,25% |
| Trong 10% | 57,80% |
| Trong 20% | 84,00% |
| Trong 30% | 92,50% |
| Bias | -3.480.694 VND/m² |

Coverage interval 80%, 90%, 95% lần lượt là 81,6%, 90,7% và 94,2%. Coverage gần mức danh nghĩa nhưng không thay thế test xác nhận mới.

Các điểm yếu lặp lại: giá từ 200 triệu có WAPE 19,05%; `Lợi thế Tốt` 26,92% nhưng chỉ có 6 mẫu; tài sản mới chưa từng thấy trong development có WAPE 14,97%, trong khi tài sản đã thấy là 9,86%. Điều này cho thấy lịch sử cùng tài sản đem lại lợi ích lớn nhưng không được giả định luôn có ở production.
