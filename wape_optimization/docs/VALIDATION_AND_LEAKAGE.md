# Validation và leakage

## Rolling validation

Bốn fold giữ nguyên trật tự thời gian. Mỗi validation chỉ dùng các tháng sau train của chính fold. Pooled OOF gồm 3.334 dòng; metric cuối được tính một lần trên toàn bộ dự đoán OOF, không lấy trung bình đơn giản giữa bốn WAPE.

## Rào leakage

- Test 05–07/2025 không dùng để fit, early stopping, chọn iteration, trọng số hoặc correction.
- Feature TSSS chỉ dùng dữ liệu có availability date nghiêm ngặt trước ngày dự báo và loại cùng báo cáo.
- Feature lịch sử TSTĐ yêu cầu `ngày nhãn + 7 ngày < ngày dự báo` theo cách cài đặt `age > 7`.
- TSTĐ cùng báo cáo với dòng hiện tại bị loại khỏi lịch sử.
- Mọi thống kê lịch sử bị giới hạn tối đa 365 ngày.
- Xu hướng tài sản dùng hai nhãn quá khứ; không dùng target hiện tại.
- Không fit outlier threshold trên toàn dữ liệu và không loại dòng khó khỏi validation.
- OOF của mọi component được căn đúng theo `row_index` trước khi blend.

## Vì sao test cũ không còn xác nhận độc lập

Test 05–07/2025 đã được xem trong pipeline trước. Dù nhánh này không dùng nó để lựa chọn, con người đã biết kết quả nên vẫn tồn tại rủi ro thích nghi gián tiếp. Bằng chứng production cần một test theo thời gian mới hơn 31/07/2025 được khóa trước khi phát triển tiếp.
