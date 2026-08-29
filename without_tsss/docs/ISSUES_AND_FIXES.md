# Nhật ký vấn đề và cách xử lý

## I-001: Code cũ không còn trong workspace

Phát hiện: workspace hiện chỉ có `Train_noi.xlsx`, `BAO_CAO_KIEM_TOAN_BAI_TOAN_BDS.md` và `Bao_cao_pipeline_du_doan_gia_BDS.docx`. Các file notebook và dữ liệu trung gian được báo cáo cũ nhắc tới không còn tồn tại.

Ảnh hưởng: không thể chạy lại hoặc xác minh pipeline cũ; báo cáo cũ đã lỗi thời về kiểm kê file.

Xử lý Stage 1: ghi nhận rõ, không suy diễn code chưa quan sát được. Tạo audit mới từ dataset hiện hữu.

## I-002: Mâu thuẫn đơn vị target

Phát hiện: tên hai cột target là `đ/m2`; `Tổng giá trị quyền sử dụng đất / Diện tích` khớp target trong 33.521 dòng ở sai số tương đối dưới `1e-6`; nhưng `Loại đơn giá` là `đ/m ngang` ở 34.477 dòng.

Ảnh hưởng: có thể huấn luyện sai đại lượng và so sánh thị trường sai đơn vị.

Xử lý đề xuất: yêu cầu data owner xác nhận data dictionary và công thức nghiệp vụ trước Stage 2. Không tự đổi tên hay quy đổi.

## I-003: Cột số lượng CTXD bị đổi nghĩa theo loại kho

Phát hiện: với toàn bộ 27.452 TSSS, `Số lượng CTXD` lớn hơn 100, trung vị 6,866 tỷ và gần bằng `Giá trị định giá` ở 26.903 dòng. Với 7.025 TSTĐ, giá trị nằm từ 0 đến 4.

Ảnh hưởng: cùng tên cột nhưng hai schema nghiệp vụ khác nhau; dùng trực tiếp gây tín hiệu giả và leakage.

Xử lý đề xuất: đặt trường này thành missing cho TSSS hoặc ánh xạ lại từ nguồn đúng; giữ số đếm chỉ cho TSTĐ sau xác nhận.

## I-004: Ngày giao dịch ngoài as-of date

Phát hiện: 26 TSSS có ngày giao dịch/rao bán sau ngày hiệu lực; một dòng ghi năm 2093. Một dòng ghi năm 1921.

Ảnh hưởng: leakage thời gian và lỗi nhập liệu.

Xử lý đề xuất: parse cố định `dd/mm/yyyy`; gắn cờ `transaction_after_as_of`; sửa hai lỗi thế kỷ khi có bằng chứng nguồn, nếu không loại khỏi tập lịch sử dùng cho feature tại thời điểm đó.

## I-005: Lần chạy audit đầu không tạo được thư mục output

Phát hiện: `PermissionError` khi script tự tạo `artifacts/stage_01` trong sandbox.

Xử lý: tạo sẵn thư mục và file bằng cơ chế ghi workspace được phép, sau đó chạy script với quyền ghi đã được phê duyệt. Lần chạy lại thành công.

## I-006: PowerShell không đọc được JSON do khóa chỉ khác hoa thường

Phát hiện: `ConvertFrom-Json` coi hai nhãn hình dáng chỉ khác hoa thường là khóa trùng, dù JSON hợp lệ và Python đọc được.

Xử lý: dùng Python để kiểm tra artifact. Stage 2 nên lưu top category dưới dạng danh sách đối tượng thay vì dictionary để tương thích công cụ case-insensitive.

## I-007: Công thức target không nhất quán ở một phần dữ liệu

Phát hiện: 933 dòng có sai số trên 1% giữa `Tổng giá trị quyền sử dụng đất / Diện tích` và target tạm thời. Trong đó 546 TSSS có tổng giá trị đất bằng 0. Ba TSSS cùng một báo cáo có hai cột target lệch trên 1%.

Xử lý đề xuất: kiểm tra nguồn theo `Số báo cáo định giá`, tách lỗi thiếu tổng khỏi lỗi target, không dùng công thức hậu nghiệm làm feature.

## I-008: Cardinality và nhãn chưa chuẩn hóa

Phát hiện: `Hình dáng` có 51 nhãn, bao gồm khác biệt khoảng trắng, hoa thường và Unicode tổ hợp. Hai trường đường có 1.438 và 1.852 giá trị; `Chi tiết` có 11.008 giá trị và 7.486 giá trị chỉ xuất hiện một lần.

Xử lý đề xuất: Unicode NFC, trim, chuẩn hóa khoảng trắng/case có kiểm soát, từ điển alias, gộp đường hiếm theo fold và back-off đường đến phường rồi quận.

## I-009: Bỏ dấu không xử lý chữ đ

Phát hiện: artifact Stage 2 lần đầu gom 7.010/7.025 `Hình dáng` vào `khác` và 7.024/7.025 `Mục đích sử dụng đất` vào `khác`.

Nguyên nhân: Unicode NFD loại dấu kết hợp nhưng không chuyển `đ` thành `d`, làm các rule `can doi`, `dat o`, `duong dam` không khớp.

Xử lý: chuyển `đ` thành `d` trước khi loại dấu, sinh lại toàn bộ artifact. Kết quả cuối có bốn nhóm hình dáng, ba nhóm mục đích đất và các cờ văn bản có phân phối hợp lý. Test chuẩn hóa được thêm để chống tái phát.

## I-010: Tài sản lặp qua thời gian

Phát hiện: 910 mã tài sản xuất hiện hơn một lần; 836 tài sản trải qua nhiều tháng. Test cuối có 369/1.000 dòng thuộc tài sản từng xuất hiện trong development.

Ảnh hưởng: metric tổng trộn định giá tài sản mới và tái thẩm định; nhóm sau có thể dễ hơn dù ID không phải feature.

Xử lý: giữ nguyên test thời gian, không dùng ID làm feature, báo metric riêng cho 631 tài sản mới và 369 dòng tài sản đã thấy ở Stage 3.

## I-011: Cài dependency vượt thời gian và khóa file

Phát hiện: lần `pip install` đầu timeout 60 giây. Lần tiếp theo tải đủ gói nhưng kết thúc bằng `WinError 32` tại một file test của matplotlib.

Xử lý: kiểm tra import trực tiếp scikit-learn 1.9.0, CatBoost 1.2.10, Optuna 4.9.0 và chạy `pip check`. Tất cả import đúng phiên bản, `pip check` trả `No broken requirements found`.

## I-012: Hai benchmark CatBoost timeout

Phát hiện: cấu hình MAE 1.800 vòng và cấu hình log-target 1.200 vòng đều vượt 304 giây.

Nguyên nhân: loss MAE CPU và tổ hợp categorical cardinality cao quá tốn chi phí.

Xử lý: chuyển loss sang RMSE trên log target, giữ chọn model bằng raw MAE, đặt `max_ctr_complexity=1`, `rsm=0.8`, bốn thread, 400 vòng benchmark. Lần chạy thứ ba hoàn tất trong 84,9 giây.

## I-013: Tuning bị dừng giữa trial

Phát hiện: batch đầu không trả stdout trung gian; sau khoảng năm phút tiến trình được dừng để kiểm tra. SQLite cho thấy ba trial đã complete và một trial running.

Xử lý: giữ ba trial complete, đánh dấu trial dang dở `FAIL`, dùng SQLite để resume thay vì chạy lại từ đầu.

## I-014: Sampler resume lặp cấu hình

Phát hiện: khi resume với cùng seed 42, trial 4 và 5 lặp trial 0 và 1; trial tiếp theo đang chạy.

Xử lý: dừng batch, đánh dấu trial running `FAIL`, đổi seed theo số trial đã lưu. Study cuối có 14 record: 11 complete, hai fail, một pruned; khoảng 10 cấu hình hiệu dụng và không vượt phạm vi mô hình đã duyệt.

## I-015: Nhóm giá cao và lợi thế Tốt còn yếu

Phát hiện: OOF Ridge có MAE 66,95 triệu ở target từ 200 triệu/m² trở lên và 113,66 triệu ở `Lợi thế kinh doanh = Tốt` nhưng nhóm này chỉ có 34 dòng.

Xử lý đề xuất Stage 4: báo riêng khoảng bất định, kiểm tra test phân khúc, cân nhắc cơ chế human review cho tài sản cao cấp thay vì tự động chấp nhận mọi dự đoán.

## I-016: Không xóa được Python bytecode sau test

Phát hiện: thao tác dọn `src/property_price_forecasting/__pycache__` bị Windows từ chối quyền truy cập đối với ba file `.pyc`.

Ảnh hưởng: không ảnh hưởng code, model hoặc kết quả test; thư mục này đã được loại khỏi phạm vi quản lý bởi `.gitignore`.

Xử lý: giữ nguyên file cache thay vì thay đổi quyền hệ thống. Các lần test dùng `PYTHONDONTWRITEBYTECODE=1` để không tạo thêm bytecode.

## I-017: PowerShell không in được Unicode khi kiểm tra mẫu suy luận

Phát hiện: lần đọc mode categorical kết thúc bằng `UnicodeEncodeError` do console dùng CP1252.

Xử lý: đặt `PYTHONIOENCODING=utf-8` và chạy lại. Kết quả mode và median được đọc đầy đủ; dữ liệu không bị thay đổi.

## I-018: Sandbox từ chối tạo thư mục Stage 4

Phát hiện: `New-Item` bị từ chối dù đích nằm trong workspace được phép ghi.

Xử lý: yêu cầu quyền ghi đúng phạm vi cho `artifacts/stage_04` và `docs/stage_04`; thao tác sau phê duyệt thành công, không ghi ra ngoài dự án.

## I-019: Guard nhầm cửa sổ test với ngày quan sát nhỏ nhất

Phát hiện: lần gọi evaluation đầu dừng trước dự đoán vì guard yêu cầu ngày nhỏ nhất bằng 01/05/2025, trong khi đây là ranh giới split và quan sát đầu tiên thực tế là 04/05/2025.

Ảnh hưởng: chưa tạo prediction, metric, calibration artifact hoặc manifest; test chưa tác động đến model hay lựa chọn nào.

Xử lý: thêm riêng `expected_test_date_min=2025-05-04` và `expected_test_date_max=2025-07-31` lấy từ split manifest Stage 2. Cửa sổ hỗ trợ vẫn bắt đầu 01/05/2025.

## I-020: Không ghi được artifact trong lần evaluation có prediction

Phát hiện: model đã tính prediction trong bộ nhớ nhưng `PermissionError` xảy ra ở lần ghi `calibration.json` đầu tiên vì thư mục Stage 4 thuộc phiên quyền nâng cao.

Ảnh hưởng: không có artifact hoặc metric nào được lưu, và không có model, threshold hay logic nào được thay đổi từ kết quả trong bộ nhớ.

Xử lý: chạy lại nguyên pipeline đã khóa với quyền ghi đúng thư mục. Manifest ghi một lần đánh giá hoàn tất; lần lỗi I/O được giữ trong nhật ký này để không che giấu việc prediction đã được tính lại kỹ thuật.

## I-021: Guard bỏ sót phường hiếm

Phát hiện: protocol yêu cầu kiểm duyệt địa bàn hiếm nhưng code ban đầu chỉ gắn `rare_road`; bốn dòng `rare ward` thiếu cờ lý do riêng dù đã được kiểm duyệt nhờ đồng thời có đường hiếm.

Xử lý: thêm `ward_rare_min_count=10`, cập nhật inference và bổ sung cờ trên prediction đã đóng băng, không gọi model lại. Checksum artifact được cập nhật; trạng thái và metric tổng không đổi.
