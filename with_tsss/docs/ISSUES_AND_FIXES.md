# Lỗi và cách xử lý

## I-TSSS-001: PowerShell làm hỏng tên cột Unicode trong here-string

Lần audit ad-hoc đầu tiên biến `Phân loại kho` thành ký tự `?` và gây `KeyError`.

Xử lý: truy cập tên cột bằng chỉ số trong kiểm tra ad-hoc và viết code chính thức bằng file UTF-8 qua patch.

## I-TSSS-002: Sandbox chặn ghi artifact audit

Audit đã tính xong trong bộ nhớ nhưng không ghi được `tsss_audit.json`.

Xử lý: chạy lại nguyên script với quyền ghi đúng nhánh `with_tsss`; không thay đổi rule hay dữ liệu.

## I-TSSS-003: Feature builder mất khoảng bảy phút

Nguyên nhân là quantile và comparable được tính as-of cho từng TSTĐ trên 27.425 TSSS hợp lệ.

Xử lý hiện tại: giữ cách tính minh bạch để bảo đảm đúng thời gian. Khi production nên lập index theo ngày/địa bàn và cache rolling aggregate.

## I-TSSS-004: Asset history OOF ban đầu dùng cờ toàn development

Phân tích đầu tiên gán mọi OOF row là tài sản đã thấy vì dùng cờ được tạo so với toàn development.

Xử lý: tái tạo OOF của model đã chọn và xác định tài sản mới/đã thấy riêng theo train của từng fold. Metric tổng không đổi; phân khúc cuối có 2.931 tài sản mới và 403 tài sản đã thấy.

## I-TSSS-005: Số iterations trong manifest chưa đồng nhất

Cấu hình tuning còn giữ 675 iterations trong khi median best iteration là 311.

Xử lý: model và manifest cuối đều ghi effective iterations bằng 311; checksum được tạo lại.

## I-TSSS-006: Sai chính tả tên cột availability trong market source

Hai test as-of và inference không chạy được vì `clean_market_source` tham chiếu `availaility_date`, trong khi cột được tạo là `availability_date`.

Xử lý: sửa đúng tên cột. Quy tắc eligibility và artifact feature không thay đổi.

## I-TSSS-007: Cấu hình benchmark Huber sơ bộ không cùng điều kiện baseline

Lần chạy nháp dùng `Huber:delta=0.1` trên log-target làm model hội tụ không hợp lệ và dùng seed khác model baseline, nên không thể dùng kết quả để kết luận.

Xử lý: đổi Huber sang `delta=1.0`, đọc đúng seed của trial CatBoost đã chọn và dùng cùng seed cho mọi candidate trước khi chạy lại toàn bộ benchmark.

Lần chạy hợp lệ vẫn cho MAPE 64,04%, xác nhận Huber không phù hợp với log-target và hyperparameter hiện tại; candidate bị loại, không tuning tiếp trên cùng OOF.
