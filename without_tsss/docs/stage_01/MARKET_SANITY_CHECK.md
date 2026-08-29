# Kiểm tra hợp lý so với thị trường và pháp lý Việt Nam

## Nguyên tắc so sánh

Bảng giá đất Nhà nước không phải giá thị trường. Giá căn hộ cũng không cùng đại lượng với đơn giá quyền sử dụng đất. Vì vậy các nguồn ngoài chỉ được dùng làm mốc phát hiện bản ghi cần xác minh, không dùng làm ngưỡng xóa tự động.

## Mốc chính thức

Quyết định 79/2024/QĐ-UBND của Thành phố Hồ Chí Minh được ban hành ngày 21/10/2024, có hiệu lực từ 31/10/2024 và hết hiệu lực cuối năm 2025 theo trang Công báo thành phố. [Nguồn Công báo TP.HCM](https://congbao.hochiminhcity.gov.vn/cong-bao/van-ban/quyet-dinh/so/79-2024-qd-ubnd/ngay/21-10-2024/47004?cbid=47104)

Bảng điều chỉnh nêu mức cao nhất 687,2 triệu đồng/m² tại Đồng Khởi, Lê Lợi và Nguyễn Huệ; một số tuyến trung tâm khác khoảng 430 triệu đồng/m², trong khi các khu ngoài trung tâm thấp hơn nhiều. [Nguồn Cổng Thông tin điện tử Chính phủ](https://xaydungchinhsach.chinhphu.vn/chi-tiet-bang-gia-dat-dieu-chinh-tai-tp-hcm-ap-dung-tu-31-10-119241022105804049.htm)

Bảng áp dụng từ 01/01/2026 vẫn nêu mức cao nhất 687,2 triệu đồng/m² ở địa bàn TP.HCM cũ và mức thấp nhất toàn thành phố mới 2,3 triệu đồng/m² tại Thiềng Liềng. Dataset không có huyện ngoại thành như Cần Giờ nên mức thấp nhất này không phải mốc trực tiếp cho mẫu hiện tại. [Nguồn Cổng Thông tin điện tử Chính phủ](https://xaydungchinhsach.chinhphu.vn/bang-gia-dat-tai-tphcm-ap-dung-tu-1-1-2026-tren-dia-ban-tphcm-119251227190324013.htm)

## So sánh với dataset

- Target tạm thời có trung vị 86,14 triệu và P95 259,31 triệu đồng trên đơn vị đang giả định là m².
- Quận 1 có trung vị 323,17 triệu, hợp lý về thứ tự tương đối so với Quận 12 là 57,82 triệu.
- Có 95 dòng trên 687,2 triệu; 72 ở Quận 1, 19 ở Thành phố Thủ Đức, hai ở Quận 3, một ở Phú Nhuận và một ở Bình Thạnh.
- Có 11 dòng trên một tỷ, đều ở Quận 1; max 1,81 tỷ.

Không thể kết luận 95 dòng này sai chỉ vì cao hơn bảng Nhà nước. Chúng có thể là giá thị trường, giá đã điều chỉnh theo lợi thế hoặc lỗi đơn vị. Tuy nhiên 19 dòng Thủ Đức vượt mốc cao nhất bảng chính thức trung tâm cần được kiểm tra theo đường, dự án và công thức nguồn.

## Bối cảnh biến động

Bộ Xây dựng báo cáo giá căn hộ chung cư trung bình tại TP.HCM khoảng 89 triệu đồng/m² trong quý II/2025 và tăng mạnh so với cùng kỳ. Đây chỉ là chỉ báo rằng mặt bằng bất động sản thay đổi theo thời gian; không thể dùng để xác nhận trực tiếp target đất của dataset. [Nguồn Bộ Xây dựng](https://moc.gov.vn/vn/tin-tuc/1269/87076/bo-xay-dung-cong-bo-thong-tin-ve-nha-o-va-thi-truong-bat-dong-san-trong-quy-ii-nam-2025.aspx)

## Quy tắc xử lý thực tế đề xuất

- Không dùng IQR toàn dataset để xóa các dòng giá cao ở Quận 1.
- Xác minh giá trong bối cảnh tháng, quận, phường, đường, vị trí khung giá và diện tích.
- Gắn các cờ `price_above_official_reference`, `price_extreme_within_location_time` và `unit_conflict`; cờ không đồng nghĩa với loại.
- Chỉ loại khỏi train khi có lỗi chắc chắn như năm 2093, sai schema hoặc công thức nguồn không thể giải thích.
- Giữ bản ghi cực trị hợp lệ để mô hình học thị trường cao cấp và đánh giá test trung thực.
