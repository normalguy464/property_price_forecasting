# Kiểm toán dataset Stage 1

## Kết luận điều hành

Dataset đủ lớn để xây mô hình tabular theo thời gian trong phạm vi các quận nội thành Thành phố Hồ Chí Minh, nhưng chưa sẵn sàng huấn luyện. Ba rủi ro cao nhất là mâu thuẫn đơn vị target, schema thay đổi giữa TSSS và TSTĐ, và nhiều cột hậu nghiệm tái tạo trực tiếp giá. Chỉ riêng việc đạt metric tốt trên random split hiện không có giá trị chứng minh khả năng vận hành.

## Snapshot nguồn

| Thuộc tính | Giá trị |
|---|---:|
| File | `Train_noi.xlsx` |
| Sheet | `Sheet1` |
| Kích thước file | 20.450.165 byte |
| Số dòng | 34.477 |
| Số cột | 90 |
| Số tháng | 17 |
| Khoảng hiệu lực | 01/03/2024–31/07/2025 |
| Quận/thành phố thuộc TP.HCM | 17 |
| TSSS | 27.452 |
| TSTĐ | 7.025 |
| SHA-256 | `a07b30a2313d61460707049d78baf7cf36fc7206ff1a20501469ab97557fc297` |

## Cấu trúc nghiệp vụ

`TSSS` là tài sản so sánh. Nhóm này có ngày, giá và nguồn giao dịch/rao bán nhưng không có `Mã tài sản`. `TSTĐ` là tài sản thẩm định. Nhóm này có `Mã tài sản`, thông tin tranh chấp và tổng giá trị tài sản, nhưng không có ngày hoặc giá giao dịch/rao bán.

Có 13.554 số báo cáo. Kích thước báo cáo có trung vị 3 dòng, P90 là 4 và tối đa 9. Có 7.021 báo cáo chứa TSTĐ; 7.017 báo cáo có một TSTĐ và bốn báo cáo có hai TSTĐ. Không báo cáo nào trải qua nhiều `Thang_Nam`.

Điều này tạo phụ thuộc nhóm rất mạnh. Các TSSS trong cùng báo cáo có thể đã được chuyên viên chọn riêng cho TSTĐ. Nếu chia các dòng cùng báo cáo qua train và validation, hoặc dùng thống kê của chính báo cáo để dự đoán TSTĐ, kết quả sẽ lạc quan giả.

## Target tạm thời

Target đang được kiểm toán tạm thời là `Đơn giá quyền sử dụng đất (đ/m2)1`.

| Phân vị | Đồng trên đơn vị target |
|---|---:|
| Min | 17.043.802 |
| P0,1 | 21.698.698 |
| P1 | 32.407.385 |
| P5 | 43.162.506 |
| Median | 86.144.717 |
| P95 | 259.307.264 |
| P99 | 446.492.847 |
| P99,9 | 880.465.962 |
| Max | 1.809.729.730 |

Hai cột đơn giá có tương quan Pearson `0,999982`. Có 34.474 dòng sai số tương đối dưới `1e-6`, nhưng ba dòng cùng báo cáo `25.536459.AMC.0.H` lệch trên 1%; chênh lệch tuyệt đối tối đa là 59.433.963 đồng.

Mâu thuẫn chính:

- Tên hai cột đơn giá ghi `đ/m2`.
- 100% cột `Loại đơn giá` ghi `đ/m ngang`.
- `Tổng giá trị quyền sử dụng đất / Diện tích` khớp target ở 33.521 dòng với sai số tương đối dưới `1e-6`.
- 933 dòng lệch trên 1%; 546 trong số này là TSSS có tổng giá trị đất bằng 0.

Do đó bằng chứng nghiêng về đơn giá trên mét vuông, nhưng không đủ quyền để tự sửa metadata nghiệp vụ.

## Thời gian

`Thời điểm hiệu lực` parse thành công 100% theo `dd/mm/yyyy` và khớp 100% với `Tháng`, `Năm`, `Thang_Nam`. Số dòng và trung vị target theo tháng:

| Tháng | Số dòng | Trung vị, triệu đồng |
|---|---:|---:|
| 2024-03 | 2.608 | 83,32 |
| 2024-04 | 2.094 | 85,88 |
| 2024-05 | 2.426 | 86,78 |
| 2024-06 | 2.339 | 84,69 |
| 2024-07 | 2.096 | 83,83 |
| 2024-08 | 2.002 | 86,71 |
| 2024-09 | 1.657 | 81,08 |
| 2024-10 | 2.323 | 84,57 |
| 2024-11 | 2.176 | 89,28 |
| 2024-12 | 2.402 | 85,27 |
| 2025-01 | 1.497 | 81,97 |
| 2025-02 | 1.980 | 86,58 |
| 2025-03 | 1.494 | 85,66 |
| 2025-04 | 2.677 | 86,98 |
| 2025-05 | 1.872 | 95,33 |
| 2025-06 | 1.035 | 87,67 |
| 2025-07 | 1.799 | 92,01 |

Các biến VNI, khối lượng VNI, lãi suất, GDP, CPI, vàng và USD có đúng một giá trị trong mỗi tháng. Tuy nhiên việc giá trị được gắn đúng theo tháng không chứng minh rằng chúng đã được công bố trước ngày dự báo. Stage 2 phải lag theo ngày công bố thực tế hoặc chỉ dùng biến đã biết.

Trong 27.452 TSSS có ngày giao dịch, 26 ngày nằm sau ngày hiệu lực. Một giá trị là `20/08/2093` và một giá trị là `09/02/1921`. Đây là lỗi thời gian rõ ràng hoặc dữ liệu chưa có tại as-of date.

## Vị trí và độ phủ

| Quận | Số dòng | Trung vị target, triệu đồng |
|---|---:|---:|
| Quận 1 | 689 | 323,17 |
| Quận 5 | 376 | 262,60 |
| Quận 3 | 537 | 195,55 |
| Quận 10 | 786 | 171,57 |
| Quận 4 | 200 | 161,70 |
| Phú Nhuận | 673 | 161,33 |
| Quận 11 | 414 | 147,99 |
| Tân Bình | 2.320 | 130,03 |
| Quận 7 | 1.536 | 128,83 |
| Quận 6 | 499 | 120,66 |
| Bình Thạnh | 1.627 | 119,64 |
| Tân Phú | 3.079 | 98,23 |
| Gò Vấp | 2.844 | 90,56 |
| Quận 8 | 978 | 81,43 |
| Thành phố Thủ Đức | 7.549 | 72,22 |
| Bình Tân | 5.190 | 69,55 |
| Quận 12 | 5.180 | 57,82 |

Phân bố này xác nhận nhãn “Tốt/Khá” không thể mang cùng tác động ở mọi nơi. Mô hình cần tương tác vị trí với lợi thế kinh doanh, vị trí khung giá, hẻm và thời gian.

Địa chỉ có 115 phường cũ, 80 phường mới, 1.438 nhãn `Đường phố`, 1.852 nhãn `Đường phố1`. Có 1.272 dòng thuộc đường có dưới năm mẫu theo trường đường chính. `Chi tiết` có 11.008 giá trị, 7.486 giá trị chỉ xuất hiện một lần. Trường này vừa dễ overfit vừa có rủi ro địa chỉ cá nhân, nên không dùng nguyên văn.

## Thiếu dữ liệu và hằng số

Ba cột thiếu 100% là `ty le dien tich`, `ty le mat tien`, `Ty le loi the`. Các thiếu lớn khác:

| Trường | Số thiếu | Nhận định |
|---|---:|---|
| `Đoạn đường` | 28.696 | Không đủ độ phủ để dùng trực tiếp |
| `Thông tin tranh chấp` | 27.452 | Thiếu theo cấu trúc TSSS, không phải MCAR |
| `Mã tài sản` | 27.452 | Chỉ có ở TSTĐ |
| `Thông tin quy hoạch` | 20.107 | Missing có thể mang ý nghĩa chưa ghi nhận |
| `Thông tin liên hệ` | 12.911 | PII, phải loại khỏi model |
| Nhóm giao dịch, ngày, nguồn | 7.025 | Thiếu toàn bộ ở TSTĐ theo nghiệp vụ |
| `ty le ngo` | 3.482 | Feature dẫn xuất thiếu |
| Phường cũ | 1.799 | Có phường mới đầy đủ nhưng cần kiểm tra mapping theo thời gian |
| `ty le KC` | 349 | Feature dẫn xuất thiếu |
| Độ lệch chuẩn | 257 | Thường do nhóm ít mẫu |

Có 15 cột hằng số, gồm phạm vi thành phố, đơn vị định giá, phương pháp so sánh, ba trường cây trồng bằng 0, chi phí chuyển đổi bằng 0, ba chuẩn số học cố định và ba cột toàn null. Hằng số không mang thông tin dự đoán trong dataset hiện tại.

## Bất hợp lý và sai schema

`Số lượng CTXD` là lỗi nổi bật nhất. Toàn bộ 27.452 TSSS có giá trị trên 100; trung vị nhóm là 6,866 tỷ và tối đa 855 tỷ. Ở 26.903 TSSS, trường này gần bằng `Giá trị định giá`. Ngược lại, TSTĐ chỉ nhận 0–4. Không được winsorize lỗi này như một ngoại lai số lượng; phải sửa schema theo loại kho.

`Hình dáng` có 51 nhãn dù thực chất chỉ có một số nhóm, do khác biệt hoa thường, khoảng trắng và Unicode tổ hợp. `Yếu tố khác` có 2.191 nhãn tự do. Đây là dữ liệu cần chuẩn hóa ngôn ngữ có kiểm soát.

Diện tích 14,8–5.400 m², mặt tiền 1–68,32 m, chiều dài 3,05–250 m, khoảng cách đường chính 0–3.000 m và độ rộng đường/hẻm 0,7–90 m. Các cực trị không đủ để kết luận sai trong đô thị; phải kiểm tra bằng quan hệ hình học, nhóm vị trí và hồ sơ gốc, rồi gắn cờ thay vì xóa hàng loạt.

## Trùng lặp

- Không có dòng trùng hoàn toàn.
- `Mã kho` là duy nhất 34.477 dòng.
- `STT` trùng 1.194 lần, nên không phải khóa ổn định.
- `Số báo cáo định giá` lặp theo cấu trúc hồ sơ; đây là group key, không phải duplicate cần xóa.

## Leakage phải chặn

- Cột target còn lại.
- `Tổng giá trị quyền sử dụng đất`, tổng đề xuất đất và các giá trị định giá được hình thành sau khi biết giá.
- `Don_gia_TB`, `Min`, `Max`, `Độ lệch chuẩn`, `Số lượng mẫu` nếu chúng được tính cả tương lai hoặc gồm chính dòng cần dự đoán.
- `ghep` và các feature tỷ lệ nếu không có code lineage để chứng minh chỉ dùng đầu vào có sẵn.
- Giá giao dịch/rao bán của chính dòng nếu mục tiêu là dự đoán giá trước giao dịch.
- TSSS được chọn cùng báo cáo nếu chế độ triển khai không có bước chuyên viên cung cấp các so sánh này trước dự đoán.

## Kết luận Stage 1

Dataset có tín hiệu vị trí và tài sản mạnh, nhưng metric tốt có thể đạt rất dễ bằng leakage. Stage 2 chỉ nên bắt đầu sau khi người dùng xác nhận ba câu hỏi trong `AGENTS.md`.
