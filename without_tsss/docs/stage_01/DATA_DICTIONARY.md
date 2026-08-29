# Từ điển dữ liệu và chính sách feature

Ý nghĩa dưới đây được suy ra từ tên trường, phân phối và quan hệ giữa các cột. Những mục ghi “cần xác nhận” không được coi là data contract chính thức.

## Nhận dạng, vị trí và thuộc tính tài sản

| STT cột | Trường | Ý nghĩa trong bài toán | Chính sách dự kiến |
|---:|---|---|---|
| 0 | `STT` | Số thứ tự export; trùng 1.194 lần | Bỏ khỏi feature |
| 1 | `Mã kho` | Khóa duy nhất của dòng trong kho | Chỉ dùng lineage, không làm feature |
| 2 | `Phân loại kho` | TSSS hoặc TSTĐ | Dùng để tách schema và phân khúc; không trộn mù quáng |
| 3 | `Mã tài sản` | Mã tài sản TSTĐ; thiếu toàn bộ TSSS | Group/lineage, không làm feature trực tiếp |
| 4 | `Số báo cáo định giá` | Nhóm hồ sơ định giá chứa TSTĐ/TSSS | Group split bắt buộc; không categorical feature trực tiếp |
| 5 | `Phân loại tài sản` | QSDĐ và tài sản gắn liền với đất | Hằng số, bỏ trong tập hiện tại |
| 6 | `Đơn vị định giá` | Đơn vị MBAMC | Hằng số, bỏ; theo dõi drift nếu mở rộng nguồn |
| 7 | `Tỉnh/Thành phố` | Thành phố Hồ Chí Minh | Hằng số, bỏ trong tập hiện tại |
| 8 | `Thành phố/Quận/Huyện/Thị xã` | Địa giới cấp quận/thành phố | Categorical cốt lõi; chuẩn hóa theo hiệu lực thời gian |
| 9 | `Xã/Phường/Thị trấn` | Phường cũ | Categorical phân cấp; giữ missing flag |
| 10 | `Xã/Phường mới` | Phường sau ánh xạ hành chính | Cần xác nhận ngày hiệu lực mapping; tránh dùng mapping tương lai sai bối cảnh |
| 11 | `Đường phố` | Tên đường chính/đã chuẩn hóa hơn | Categorical cardinality cao; chuẩn hóa và back-off |
| 12 | `Đường phố1` | Biến thể/tên đường chi tiết hơn | Dùng để đối chiếu và xây canonical road, không dùng song song nếu trùng thông tin |
| 13 | `Đoạn đường` | Đoạn tuyến cụ thể | Thiếu 28.696; chỉ dùng khi đủ độ phủ, luôn có missing flag |
| 14 | `Chi tiết` | Địa chỉ/mô tả chi tiết tài sản | Không dùng nguyên văn; PII và singleton cao |
| 15 | `Khoảng cách đến đường chính (m)` | Khoảng cách BĐS tới đường chính | Numeric cốt lõi; kiểm tra 0, log/clip theo train và cờ cực trị |
| 16 | `Vị trí trong khung giá` | VT1–VT4 theo khả năng tiếp cận | Categorical/ordinal; không áp đặt khoảng cách tuyến tính nếu chưa xác nhận |
| 17 | `Độ rộng ngõ/ngách nhỏ nhất (Từ đường chính đến BĐS)` | Bề rộng đường/hẻm tiếp cận | Numeric; kiểm tra đơn vị và tương tác với vị trí |
| 18 | `Chi_so_ngo` | Chỉ số dẫn xuất từ độ rộng hẻm | Chỉ dùng nếu tái tạo từ raw trong pipeline; không tin file sẵn |
| 19 | `Mục đích sử dụng đất` | Đất ở đô thị/đất ở/nông thôn | Categorical; chuẩn hóa ba nhãn và xác minh 12 dòng nông thôn |
| 20 | `Diện tích (m2)` | Diện tích đất | Numeric cốt lõi; log, quan hệ hình học và cờ ngoài miền |
| 21 | `Chi_so_dientich` | Chỉ số điều chỉnh diện tích | Rebuild theo quy tắc train/nghiệp vụ hoặc bỏ |
| 22 | `Kích thước mặt tiền (m)` | Chiều rộng mặt tiền | Numeric cốt lõi; kiểm tra với diện tích và chiều dài |
| 23 | `Kích thước chiều dài` | Chiều sâu/chiều dài thửa | Numeric cốt lõi; kiểm tra với diện tích và mặt tiền |
| 24 | `Số mặt tiền tiếp giáp` | Số cạnh tiếp giáp đường, 1–3 | Numeric rời rạc/categorical; tương tác vị trí |
| 25 | `Hình dáng` | Cân đối, nở hậu, tóp hậu, chữ L và biến thể | Unicode NFC, trim, alias thành nhóm chuẩn |
| 26 | `Chi_so_hinhdang` | Chỉ số dẫn xuất hình dáng | Rebuild từ nhãn chuẩn hoặc bỏ |
| 27 | `Lợi thế kinh doanh` | Kém, Trung bình, Khá, Tốt | Categorical/ordinal; tương tác với vị trí và thời gian |
| 28 | `Chi_so_loithe` | Trọng số dẫn xuất lợi thế kinh doanh | Không chỉnh tay để tối ưu metric; rebuild nếu là quy tắc nghiệp vụ |
| 29 | `Thông tin quy hoạch` | Có/không hoặc chưa ghi nhận | Không đồng nhất với missing; tạo missing flag, cần bổ sung chất lượng nguồn |
| 30 | `Thông tin tranh chấp` | Thông tin pháp lý, chỉ có ở TSTĐ | Dùng cho TSTĐ sau xác nhận availability; missing theo loại kho |
| 31 | `Yếu tố khác` | Mô tả hẻm, công viên, đường đâm và yếu tố tự do | Chuẩn hóa rule-based thành multi-label; không dùng raw text trực tiếp ở bản đầu |
| 32 | `Phương pháp định giá` | Phương pháp so sánh | Hằng số, bỏ trong tập hiện tại |

## Target, giá trị định giá và thông tin giao dịch

| STT cột | Trường | Ý nghĩa trong bài toán | Chính sách dự kiến |
|---:|---|---|---|
| 33 | `Đơn giá quyền sử dụng đất (đ/m2)` | Target bản làm tròn hoặc phiên bản song song | Không làm feature; đối chiếu chất lượng target |
| 34 | `Đơn giá quyền sử dụng đất (đ/m2)1` | Target tạm thời có độ chính xác thập phân | Chỉ dùng làm y sau khi xác nhận đơn vị |
| 35 | `Loại đơn giá` | Metadata đơn vị, hiện 100% `đ/m ngang` | Hằng số nhưng là lỗi chặn; cần data owner xác nhận |
| 36 | `Mục đích sử dụng đất có giá trị cao nhất` | Bản sao mục đích sử dụng trong tập hiện tại | Giữ tối đa một trong cột 19/36 sau kiểm tra |
| 37 | `Giá trị định giá` | Giá trị được định giá/hậu nghiệm | Leakage, bỏ khỏi feature |
| 38 | `Giá trị đề xuất` | Giá trị đề xuất cuối quy trình | Leakage, bỏ khỏi feature |
| 39 | `Tổng giá trị quyền sử dụng đất` | Diện tích nhân đơn giá đất ở phần lớn dòng | Leakage trực tiếp, chỉ dùng kiểm tra chất lượng |
| 40 | `Tổng giá trị đề xuất quyền sử dụng đất` | Tổng đất đề xuất | Leakage trực tiếp, chỉ dùng kiểm tra |
| 41 | `Số lượng CTXD` | Số công trình ở TSTĐ nhưng mang giá trị tiền ở TSSS | Tách theo loại kho; TSSS đặt missing/sửa mapping, TSTĐ cần xác nhận |
| 42 | `Tổng giá trị định giá công trình xây dựng` | Giá trị công trình | Hậu nghiệm; bỏ nếu dự đoán trước định giá |
| 43 | `Tổng giá trị đề xuất công trình xây dựng` | Giá trị công trình đề xuất | Hậu nghiệm; bỏ |
| 44 | `Số lượng cây trồng` | Số cây | Hằng số 0, bỏ |
| 45 | `Tổng giá trị định giá cây trồng` | Giá trị cây | Hằng số 0, bỏ |
| 46 | `Tổng giá trị đề xuất cây trồng` | Giá trị cây đề xuất | Hằng số 0, bỏ |
| 47 | `Tổng giá trị tài sản` | Tổng cuối chỉ có ý nghĩa ở TSTĐ, TSSS bằng 0 | Leakage, bỏ khỏi feature |
| 48 | `Tình trạng giao dịch` | Chưa/đã giao dịch, chỉ có TSSS | Có thể dùng cho kho so sánh lịch sử; không có ở TSTĐ |
| 49 | `Thời điểm giao dịch/rao bán (đ)` | Ngày giao dịch/rao bán TSSS | Trục availability của comparable; phải không sau as-of date |
| 50 | `Giá giao dịch/rao bán (đ)` | Giá tổng quan sát/rao bán TSSS | Dùng để xây lịch sử nếu mục tiêu phù hợp; không làm feature của chính target cần dự đoán |
| 51 | `Giá ước tính (đ)` | Giá đã điều chỉnh/ước tính cho TSSS | Nguy cơ leakage/hậu nghiệm; cần xác nhận công thức trước khi dùng |
| 52 | `Chi phí chuyển đổi sang đất ở (đ)` | Chi phí chuyển mục đích | Hằng số 0, bỏ trong tập hiện tại |
| 53 | `Nguồn thông tin` | Internet, thực địa và nguồn TSSS | Categorical chất lượng nguồn; missing theo TSTĐ |
| 54 | `Thông tin liên hệ` | Tên/số điện thoại/người cung cấp | PII, loại hoàn toàn khỏi model và artifact |
| 55 | `Thời điểm hiệu lực` | Ngày hiệu lực báo cáo | As-of date tạm thời; trục split và feature availability |

## Feature tổng hợp, thời gian, vĩ mô và hệ số điều chỉnh

| STT cột | Trường | Ý nghĩa trong bài toán | Chính sách dự kiến |
|---:|---|---|---|
| 56 | `ghep` | Chuỗi ghép phường, đường, vị trí và có thể yếu tố khác | Không dùng bản có sẵn; rebuild key rõ delimiter và lineage |
| 57 | `Don_gia_TB` | Đơn giá trung bình theo nhóm | Leakage nếu tính toàn bộ dữ liệu; rebuild out-of-fold và lagged |
| 58 | `Min` | Giá nhỏ nhất theo nhóm | Leakage nếu tính toàn bộ; rebuild lịch sử hoặc bỏ |
| 59 | `Max` | Giá lớn nhất theo nhóm | Leakage nếu tính toàn bộ; rebuild lịch sử hoặc bỏ |
| 60 | `Độ lệch chuẩn` | Độ phân tán giá theo nhóm | Rebuild lịch sử với minimum count; missing khi ít mẫu |
| 61 | `Số lượng mẫu` | Cỡ mẫu của nhóm tổng hợp | Rebuild theo train quá khứ; dùng cho smoothing/back-off |
| 62 | `Tháng` | Tháng của ngày hiệu lực | Rebuild từ cột 55 |
| 63 | `Tháng1` | Bản sao tháng | Bỏ bản trùng, rebuild một cột duy nhất |
| 64 | `Năm` | Năm hiệu lực | Rebuild từ cột 55 |
| 65 | `Quý` | Quý hiệu lực | Rebuild từ cột 55 |
| 66 | `Quý_Năm` | Khóa quý-năm | Rebuild từ cột 55 |
| 67 | `Thang_Nam` | Khóa tháng-năm | Rebuild từ cột 55; dùng chia fold |
| 68 | `VNI_Chi_So` | Chỉ số VN-Index theo tháng | Chỉ dùng lag/giá trị đã công bố tại as-of date |
| 69 | `VNI_khoi_luong` | Khối lượng giao dịch chứng khoán theo tháng | Chỉ dùng lag; kiểm tra nguồn và ngày công bố |
| 70 | `Lai_suat` | Lãi suất theo tháng | Chỉ dùng giá trị biết trước; ghi nguồn/version |
| 71 | `GDP` | GDP gắn theo tháng dù thường công bố theo quý | Rủi ro forward-fill và công bố trễ; lag theo release date |
| 72 | `CPI` | CPI theo tháng | Lag theo ngày công bố, không dùng tương lai |
| 73 | `Gold` | Giá vàng theo tháng | Xác nhận cách tổng hợp và availability |
| 74 | `ghep usd` | Khóa ghép tháng cho USD | Bỏ, rebuild join key từ ngày |
| 75 | `USD` | Tỷ giá USD theo tháng | Lag/as-of join, ghi nguồn |
| 76 | `DT_chuan` | Diện tích chuẩn 60 | Hằng số tham chiếu; chỉ dùng trong rule được xác nhận |
| 77 | `MT_chuan` | Mặt tiền chuẩn 5 | Hằng số tham chiếu; chỉ dùng trong rule được xác nhận |
| 78 | `CD_chuan` | Chiều dài chuẩn 12 | Hằng số tham chiếu; chỉ dùng trong rule được xác nhận |
| 79 | `LT_chuan` | Mức chuẩn lợi thế 1–4 | Feature dẫn xuất; rebuild từ nhãn nếu quy tắc hợp lệ |
| 80 | `KC_chuan` | Mức khoảng cách chuẩn | Feature dẫn xuất; rebuild từ khoảng cách/vị trí |
| 81 | `Ngo_chuan` | Mức độ rộng ngõ chuẩn | Feature dẫn xuất; rebuild từ raw |
| 82 | `ty le dien tich` | Tỷ lệ điều chỉnh diện tích | Thiếu 100%, bỏ |
| 83 | `ty le mat tien` | Tỷ lệ điều chỉnh mặt tiền | Thiếu 100%, bỏ |
| 84 | `Ty le chieu dai` | Hệ số điều chỉnh chiều dài | Rebuild từ raw nếu có công thức nghiệp vụ |
| 85 | `Ty le loi the` | Tỷ lệ điều chỉnh lợi thế | Thiếu 100%, bỏ |
| 86 | `ty le KC` | Hệ số điều chỉnh khoảng cách | Rebuild; hiện thiếu 349 và có giá trị âm |
| 87 | `ty le ngo` | Hệ số điều chỉnh độ rộng ngõ | Rebuild; thiếu 3.482 và phần lớn âm |
| 88 | `ty le so mat` | Hệ số điều chỉnh số mặt tiền | Rebuild; dấu âm cần xác nhận quy ước |
| 89 | `hinh dang` | Hệ số/nhóm số hóa hình dáng | Rebuild từ nhãn chuẩn, không dùng cùng cột 26 nếu trùng |

## Nhóm trường được phép dùng trực tiếp ở bản đầu

Sau khi xác nhận availability, nhóm cốt lõi gồm quận, phường, đường chuẩn hóa, diện tích, mặt tiền, chiều dài, số mặt tiếp giáp, hình dáng chuẩn, lợi thế kinh doanh, vị trí khung giá, khoảng cách đường chính, độ rộng hẻm, mục đích đất, nguồn TSSS và feature thời gian đã rebuild.

Mọi feature tổng hợp giá phải được tạo trong pipeline theo từng train fold và chỉ nhìn quá khứ.
