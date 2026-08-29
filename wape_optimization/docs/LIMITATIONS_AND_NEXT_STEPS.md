# Giới hạn và bước tiếp theo

## Vì sao chưa đạt 10%

- Tài sản từ 200 triệu VND/m² đóng góp sai số tuyệt đối rất lớn và có bias định giá thấp.
- `Lợi thế Tốt`, VT1 và các quận trung tâm có quan hệ giá phức tạp nhưng số mẫu hữu ích ít.
- Vị trí chỉ ở dạng phân cấp và mô tả; thiếu tín hiệu không gian chi tiết hoặc mã vùng pháp lý đủ nhỏ.
- TSSS là giá tham chiếu/ước tính, không phải lúc nào cũng là giao dịch đã xác nhận; anchor có thể mang bias nguồn.
- Dữ liệu chỉ bao phủ 17 tháng nên chưa học chắc chu kỳ, regime hoặc seasonality dài.
- Tài sản mới không có lịch sử cùng tài sản kém hơn đáng kể.

## Ưu tiên cải thiện

1. Thu thập test mới sau 31/07/2025 và khóa trước khi thử tiếp.
2. Bổ sung giao dịch đã xác nhận, thời điểm ghi nhận, trạng thái listing/giao dịch và độ tin cậy nguồn cho TSSS.
3. Dùng mã vùng pháp lý hoặc lưới không gian đã ẩn danh được phê duyệt, không cần lưu tọa độ thô; kiểm tra với bộ phận pháp lý trước khi triển khai.
4. Tăng mẫu ở quận trung tâm, VT1, `Lợi thế Tốt` và dải từ 200 triệu; kiểm tra định nghĩa nhãn và chất lượng thẩm định của các ca này.
5. Xây expert/gating cho phân khúc giá cao chỉ khi rolling OOF đủ mẫu và gating không dùng target thật.
6. Thêm reliability score cho market anchor, nguồn TSSS và độ gần comparable để mô hình biết khi nào không nên tin anchor.
7. Đặt review bắt buộc cho OOD, dải giá cao, anchor thiếu, comparable ít và khoảng dự báo quá rộng.

## Điều kiện production

Chỉ xem xét production khi có test thời gian mới độc lập, data contract đầu vào, SLA nhãn lịch sử, kiểm soát drift, kiểm thử inference và quy trình human review. Mục tiêu dưới 10% có thể được đặt cho luồng tự động an toàn sau khi định nghĩa coverage trước; không được đạt bằng cách nhìn target rồi loại ca khó.
