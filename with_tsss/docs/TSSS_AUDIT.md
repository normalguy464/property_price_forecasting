# Kiểm toán TSSS

## Quy mô

- Tổng nguồn: 34.477 dòng.
- TSSS: 27.452 dòng, 13.094 báo cáo.
- TSTĐ: 7.025 dòng, 7.021 báo cáo.
- 14.122 TSSS thuộc báo cáo cũng có TSTĐ; đây là vùng rủi ro leakage nếu dùng TSSS cùng báo cáo.

## Ngày

Tất cả TSSS parse được cả ngày thị trường và ngày hiệu lực. Có 9.387 dòng có market date trước ngày hiệu lực, 18.039 dòng cùng ngày và 26 dòng market date sau ngày hiệu lực. Một dòng có năm 1921; ngày lớn nhất là năm 2093.

Eligibility loại 26 dòng market date sau availability và một dòng cũ hơn 730 ngày. Còn 27.425 dòng làm nguồn feature.

Điểm hạn chế: không có ingestion timestamp thật. `Thời điểm hiệu lực` chỉ là proxy thời điểm TSSS đã có trong hệ thống; production nên bổ sung `available_at` bất biến từ data warehouse.

## Giá

Median giá giao dịch/rao bán trên diện tích là 105,88 triệu VND/m². Median giá ước tính trên diện tích là 98,80 triệu; median đơn giá đất đã điều chỉnh là 86,44 triệu.

27.036/27.452 TSSS là `Chưa giao dịch`, chỉ 416 là `Đã giao dịch`; 27.131 dòng lấy từ Internet. Vì vậy tín hiệu chủ đạo là giá rao bán, không phải giá giao dịch thực.

Median tỷ lệ raw/estimated là 1,0694, cho thấy giá ước tính thường điều chỉnh giảm khoảng 6,5% so với mức rao. Hai tín hiệu được giữ riêng.

## Chính sách cột

- Dùng: tổng giá raw/diện tích, giá ước tính/diện tích, trạng thái giao dịch, ngày, nguồn và thuộc tính vật lý/vị trí.
- Không dùng: đơn giá đất đã điều chỉnh vì chưa biết chính xác quy trình tạo.
- Không dùng: `Don_gia_TB`, `Min`, `Max`, độ lệch chuẩn và số lượng mẫu vì có thể đã tính từ tập so sánh cùng báo cáo/toàn dữ liệu.
- Không xuất: liên hệ, địa chỉ chi tiết, mã tài sản, mã kho hoặc số báo cáo raw.
