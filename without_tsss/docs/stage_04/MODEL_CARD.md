# Model card

## Nhận dạng

- Tên: `property_price_forecasting_ridge_stage4`.
- Phiên bản package: `1.0.0-stage4`.
- Thuật toán: Ridge Regression.
- Target: đơn giá TSTĐ tại ngày hiệu lực, VND/m².
- Population: TSTĐ tại 17 quận/thành phố thuộc Thành phố Hồ Chí Minh có trong dữ liệu.
- Không dùng TSSS.

## Mục đích phù hợp

Model hỗ trợ ước lượng ban đầu ngay khi nhận thông tin bất động sản và phân luồng hồ sơ cần chuyên viên kiểm tra. Kết quả phải đi cùng khoảng dự báo, trạng thái và cờ lý do.

## Không phù hợp

- Không dự đoán tổng giá trị căn nhà hoặc giá trị công trình.
- Không thay thế quyết định thẩm định, tín dụng, pháp lý hoặc thuế.
- Không dùng khi thiếu `Lợi thế kinh doanh` hoặc `Vị trí trong khung giá`.
- Không dùng TSSS cùng báo cáo hoặc bất kỳ TSSS nào.
- Không dùng cho quận chưa thấy hoặc ngày sau 31/07/2025.
- Không suy ra tọa độ hay địa chỉ chi tiết.

## Dữ liệu và feature

Model fit trên 6.025 TSTĐ từ 03/2024 đến 04/2025 với 47 feature: chín categorical và 38 numeric/derived. ID tài sản, ID báo cáo, thông tin liên hệ, địa chỉ chi tiết, target-derived fields và TSSS không phải feature.

## Hiệu năng khóa

Trên 1.000 TSTĐ từ 04/05/2025 đến 31/07/2025: MAE 17,87 triệu VND/m², WAPE 15,72%, 79,90% trong biên 20% và 93,30% trong biên 30%. Model đạt ba ngưỡng kỹ thuật khóa trước test.

## Hạn chế quan trọng

- Dự đoán thấp ở phân khúc từ 200 triệu VND/m², lợi thế `Tốt`, Quận 1 và địa bàn chưa quen thuộc.
- Sai số thay đổi mạnh theo quận, vị trí và tháng; metric tổng không đại diện cho từng phân khúc.
- Dữ liệu chỉ dài 17 tháng và không có tọa độ, macro có ngày công bố, pháp lý chi tiết hoặc giao dịch thị trường độc lập.
- Ridge có thể ngoại suy thời gian tuyến tính không hợp lý nếu vượt horizon.
- Nhãn target là giá TSTĐ nội bộ, không nhất thiết bằng giá giao dịch thực tế.

## Trạng thái phát hành

`HISTORICAL_TEST_ACCEPTED_BUT_STALE_FOR_CURRENT_PRODUCTION`.

Model không được triển khai cho định giá hiện tại năm 2026. Phải bổ sung dữ liệu gần ngày triển khai, chạy lại toàn bộ rolling validation, tạo test khóa mới và phát hành package mới.

## Trách nhiệm vận hành

Owner nghiệp vụ phê duyệt ngưỡng sai số và chính sách human review. Owner dữ liệu đảm bảo schema và nhãn. Owner model theo dõi drift, metric có nhãn trễ, phiên bản và rollback. Mọi override của chuyên viên cần có reason code để phục vụ audit và tái huấn luyện.
