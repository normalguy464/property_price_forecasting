# Làm sạch và tạo feature Stage 2

## Nguyên tắc

- Không sửa `Train_noi.xlsx`.
- Lọc TSTĐ trước mọi thống kê.
- Không fit quy tắc theo target toàn dữ liệu.
- Không xóa outlier.
- Không đưa ID, PII, địa chỉ chi tiết hoặc cột hậu nghiệm vào feature.
- Mọi feature hiếm, target encoding hoặc thống kê vị trí cần học dữ liệu sẽ được fit lại trong từng fold ở Stage 3.

## Luồng xử lý

1. Đọc `Sheet1`, giữ dòng `Phân loại kho = TSTĐ`.
2. Parse `Thời điểm hiệu lực` theo `dd/mm/yyyy`.
3. Ép target về số và kiểm tra target dương.
4. Chuẩn hóa văn bản theo Unicode NFC, khoảng trắng, casefold và dấu gạch.
5. Tạo bản không dấu dùng riêng cho rule; xử lý riêng chữ `đ`.
6. Chuẩn hóa nhãn hình dáng, mục đích đất và lợi thế kinh doanh.
7. Chuyển các mô tả `Yếu tố khác` thành cờ nghiệp vụ giới hạn.
8. Tạo feature hình học, log, tiếp cận và lịch.
9. Tạo cờ chất lượng không dùng để xóa hàng.
10. Tạo ID nhóm số cho tài sản/báo cáo, không đưa vào feature.
11. Khóa split thời gian và xuất JSON Lines nén.

## Kết quả chuẩn hóa categorical

| Feature | Cardinality cuối | Ghi chú |
|---|---:|---|
| `district` | 17 | Không thiếu |
| `ward_old` | 114 | Gồm token missing, 331 dòng thiếu |
| `ward_new` | 78 | Từ 80 nhãn raw sau hợp nhất biến thể Unicode/case |
| `road` | 1.102 | Từ 1.112 nhãn raw |
| `road_segment` | 774 | Gồm token missing, 1.244 dòng thiếu |
| `price_position` | 4 | VT1–VT4 |
| `land_use` | 3 | Đất ở đô thị, đất ở, đất ở nông thôn |
| `plot_shape` | 4 | Cân đối, khá cân đối, không cân đối, phức tạp |
| `business_advantage` | 4 | Kém, trung bình, khá, tốt |

Đường hiếm chưa được gộp trên toàn dataset. Stage 3 phải fit vocabulary trên train của từng fold và back-off đường → phường → quận để validation không ảnh hưởng cách gộp.

## Feature số

Có 38 feature số:

- Raw: diện tích, mặt tiền, chiều dài, số mặt tiếp giáp, khoảng cách đường chính, độ rộng hẻm và số công trình.
- Hình học: `area/(frontage×length)` và `frontage/length`.
- Log: diện tích, mặt tiền, chiều dài, khoảng cách và độ rộng hẻm.
- Tiếp cận/missing: mặt đường trực tiếp, thiếu phường cũ, thiếu đoạn đường.
- Tám cờ từ `Yếu tố khác`.
- Thời gian: năm, tháng, quý, chỉ số tháng, sin/cos mùa vụ.
- Sáu cờ kiểm tra phạm vi hình học và tiếp cận.

Không dùng các chỉ số điều chỉnh có sẵn như `Chi_so_loithe`, `ty le ngo`, `ty le KC`, `Don_gia_TB`, `Min`, `Max`. Các feature này thiếu lineage hoặc có nguy cơ chứa quy tắc hậu nghiệm.

## Xử lý văn bản tự do

`Yếu tố khác` có 1.123 nhãn trong TSTĐ nên không đưa raw text vào model. Các cờ cuối gồm:

| Cờ | Số dòng bật |
|---|---:|
| Hẻm cụt | 296 |
| Đường/hẻm đâm vào tài sản | 523 |
| Đối diện công viên | 139 |
| Gần/lân cận mộ | 206 |
| Gần/lân cận chùa | 83 |
| Có mô tả quy hoạch | 81 |
| Có diện tích không công nhận | 75 |
| Thuộc trục chính | 32 |

Những cờ này là rule ban đầu, cần chuyên viên nghiệp vụ rà soát ở cổng Stage 2.

## Cột bị loại

- Toàn bộ TSSS và nhóm giao dịch/rao bán.
- Target trùng và mọi tổng giá trị định giá/đề xuất.
- Thống kê giá nhóm có sẵn.
- `Mã kho`, mã tài sản, số báo cáo, địa chỉ chi tiết, thông tin liên hệ.
- Cột hằng số, toàn null và các hệ số dẫn xuất thiếu lineage.
- Macro do chưa có nguồn và ngày công bố.

Danh sách máy đọc được nằm trong `artifacts/stage_02/data_contract.json`.
