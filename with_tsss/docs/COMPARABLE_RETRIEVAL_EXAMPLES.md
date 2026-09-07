# Năm ví dụ truy xuất TSSS

## Cách đọc tài liệu

Mỗi ví dụ lấy một TSTĐ thật trong `Train_noi.xlsx`, dùng ngày hiệu lực làm thời điểm `as-of`, loại TSSS cùng báo cáo và chỉ giữ TSSS có ngày thị trường, ngày có sẵn nghiêm ngặt trước thời điểm đó trong tối đa 365 ngày.

`Raw` và `estimated` trong bảng TSSS là giá đơn vị triệu đồng/m², được tính từ giá giao dịch/rao bán hoặc giá ước tính chia diện tích. `Score` là `rule_similarity_score_0_100`, chỉ phục vụ xếp hạng candidate. Nó không phải xác suất và không được dùng thay cho bước điều chỉnh giá nghiệp vụ.

Không có mã kho, mã tài sản, số báo cáo, chi tiết hay thông tin liên hệ trong tài liệu. Cột `Số lượng CTXD` không được trình bày vì nhiều dòng có giá trị hàng tỷ, không hợp lý về nghiệp vụ; retrieval không dùng trường này.

## Ví dụ 1: Quận Tân Bình

### TSTĐ

| Trường | Giá trị |
|---|---|
| Ngày hiệu lực | 07/05/2025 |
| Khu vực | Quận Tân Bình, Phường 14 → Phường Tân Bình, Trường Chinh |
| VT / khoảng cách / hẻm | VT3 / 200 m / 4 m |
| Đất và kích thước | Đất ở tại đô thị; 77,2 m²; 4,78 m × 15,65 m; 1 mặt tiền |
| Hình dáng / lợi thế / yếu tố khác | Không cân đối / Trung bình / Không |
| Đơn giá QSDĐ thực tế để đối chiếu | 109,10 triệu đ/m² |
| Tổng giá trị QSDĐ | 8,423 tỷ đồng |

### Năm TSSS

| Ref | Đường | Ngày / tuổi | VT | Diện tích; mặt tiền × dài | Cách đường / hẻm | Hình dáng / LT | Raw / estimated | Score | Cờ |
|---|---|---|---|---|---|---|---:|---:|---|
| TSSS-015949 | Trường Chinh | 27/05/2024 / 345 ngày | VT3 | 78; 4,45 × 17,5 | 200 / 5 | Cân đối / Trung bình | 134,62 / 128,21 | 85,73 | Cũ >180 ngày |
| TSSS-022691 | Trường Chinh | 15/01/2025 / 112 ngày | VT3 | 80; 4 × 20 | 100 / 3,5 | Cân đối / Trung bình | 136,25 / 126,88 | 83,54 | Không |
| TSSS-024286 | Trường Chinh | 12/02/2025 / 84 ngày | VT3 | 62; 4,2 × 14 | 250 / 3 | Cân đối / Trung bình | 120,97 / 109,68 | 82,96 | Không |
| TSSS-024303 | Trường Chinh | 12/02/2025 / 84 ngày | VT3 | 57; 4 × 14 | 220 / 5 | Cân đối / Trung bình | 131,58 / 119,30 | 81,72 | Không |
| TSSS-003092 | Trường Chinh | 19/08/2024 / 261 ngày | VT3 | 68; 4,3 × 16 | 100 / 5 | Cân đối / Trung bình | 145,59 / 135,29 | 80,99 | Cũ >180 ngày |

Tất cả cùng đường, VT, lợi thế và mục đích dùng đất; khác biệt lặp lại là hình dáng. Đây là một tập comparable khá tốt nhưng vẫn cần điều chỉnh hình dáng và thời gian cho các dòng cũ.

## Ví dụ 2: Quận 7

### TSTĐ

| Trường | Giá trị |
|---|---|
| Ngày hiệu lực | 09/05/2025 |
| Khu vực | Quận 7, Phường Tân Phong → Phường Tân Hưng, Lý Long Tường (H2105) |
| VT / khoảng cách / hẻm | VT2 / 180 m / 10 m |
| Đất và kích thước | Đất ở tại đô thị; 200 m²; 10 m × 20 m; 1 mặt tiền |
| Hình dáng / lợi thế / yếu tố khác | Cân đối / Trung bình / Không |
| Đơn giá QSDĐ thực tế để đối chiếu | 307,19 triệu đ/m² |
| Tổng giá trị QSDĐ | 61,437 tỷ đồng |

### Năm TSSS

| Ref | Đường / mức địa lý | Ngày / tuổi | VT | Diện tích; mặt tiền × dài | Cách đường / hẻm | Hình dáng / LT | Raw / estimated | Score | Cờ |
|---|---|---|---|---|---|---|---:|---:|---|
| TSSS-029268 | Lâm Văn Bền / cùng phường | 21/04/2025 / 18 ngày | VT2 | 200; 10 × 20 | 150 / 10 | Cân đối / Trung bình | 140,00 / 132,50 | 59,78 | Không |
| TSSS-007453 | Lý Long Tường / cùng đường | 29/10/2024 / 192 ngày | VT1 | 218; 10,5 × 22 | 0 / 21 | Cân đối / Khá | 353,21 / 344,04 | 57,67 | Cũ >180 ngày |
| TSSS-001787 | Nguyễn Hữu Thọ / cùng phường | 26/07/2024 / 287 ngày | VT2 | 200; 10 × 20 | 200 / 10 | Cân đối / Trung bình | 132,50 / 127,50 | 57,37 | Cũ >180 ngày |
| TSSS-001788 | Nguyễn Hữu Thọ / cùng phường | 26/07/2024 / 287 ngày | VT2 | 200; 10 × 20 | 200 / 10 | Cân đối / Trung bình | 140,00 / 127,50 | 57,37 | Cũ >180 ngày |
| TSSS-001789 | Nguyễn Hữu Thọ / cùng phường | 26/07/2024 / 287 ngày | VT2 | 190; 10 × 20 | 200 / 10 | Cân đối / Trung bình | 157,89 / 142,11 | 56,63 | Cũ >180 ngày |

Tập này yếu hơn: chỉ một TSSS cùng đường nhưng khác VT, lợi thế và tiếp cận; các TSSS khớp hình học hơn lại khác đường hoặc cũ. Không nên lấy trung bình trực tiếp; cần manual review.

## Ví dụ 3: Thành phố Thủ Đức

### TSTĐ

| Trường | Giá trị |
|---|---|
| Ngày hiệu lực | 05/05/2025 |
| Khu vực | Phường Cát Lái, đường Nguyễn Thị Định |
| VT / khoảng cách / hẻm | VT2 / 1.900 m / 12 m |
| Đất và kích thước | Đất ở tại đô thị; 119 m²; 7 m × 17 m; 1 mặt tiền |
| Hình dáng / lợi thế / yếu tố khác | Cân đối / Trung bình / Không |
| Đơn giá QSDĐ thực tế để đối chiếu | 73,46 triệu đ/m² |
| Tổng giá trị QSDĐ | 8,742 tỷ đồng |

### Năm TSSS

| Ref | Mức địa lý | Ngày / tuổi | VT và thuộc tính categorical | Diện tích; mặt tiền × dài | Cách đường / hẻm | Raw / estimated | Score | Cờ |
|---|---|---|---|---|---|---:|---:|---|
| TSSS-006412 | Cùng đường | 03/10/2024 / 214 ngày | VT2, cân đối, Trung bình | 119; 7 × 17 | 2.000 / 12 | 89,08 / 80,67 | 96,09 | Cũ >180 ngày |
| TSSS-012627 | Cùng đường | 04/12/2024 / 152 ngày | VT2, cân đối, Trung bình | 119; 7 × 17 | 1.500 / 22 | 138,66 / 121,85 | 92,43 | Không |
| TSSS-012615 | Cùng đường | 04/12/2024 / 152 ngày | VT2, cân đối, Trung bình | 119; 7 × 17 | 1.400 / 22 | 134,45 / 121,01 | 92,04 | Không |
| TSSS-000400 | Cùng đường | 11/07/2024 / 298 ngày | VT2, cân đối, Trung bình | 119; 7 × 17 | 900 / 12 | 75,63 / 71,43 | 90,69 | Cũ >180 ngày |
| TSSS-028876 | Cùng đường | 23/04/2025 / 12 ngày | VT2, cân đối, Trung bình | 100; 5 × 20 | 1.800 / 12 | 68,00 / 65,00 | 90,38 | Không |

Đây là tập rất tốt về thuộc tính và cùng đường. Tuy vậy, giá raw phân tán 68,00–138,66 triệu đ/m², nên vẫn phải kiểm tra nguồn rao bán, điều chỉnh và độ mới thay vì trung bình cơ học.

## Ví dụ 4: Quận Bình Tân

### TSTĐ

| Trường | Giá trị |
|---|---|
| Ngày hiệu lực | 06/05/2025 |
| Khu vực | Phường Bình Hưng Hoà B → Phường Bình Tân, Liên Khu 4-5 |
| VT / khoảng cách / hẻm | VT3 / 215 m / 4,32 m |
| Đất và kích thước | Đất ở; 50,8 m²; 4,1 m × 13,59 m; 2 mặt tiền |
| Hình dáng / lợi thế | Cân đối / Trung bình |
| Yếu tố khác | CTXD thông vách, sử dụng cầu thang chung |
| Đơn giá QSDĐ thực tế để đối chiếu | 60,25 triệu đ/m² |
| Tổng giá trị QSDĐ | 3,061 tỷ đồng |

### Năm TSSS

| Ref | Mức địa lý | Ngày / tuổi | VT và thuộc tính categorical | Diện tích; mặt tiền × dài | Cách đường / hẻm | Raw / estimated | Score | Cờ |
|---|---|---|---|---|---|---:|---:|---|
| TSSS-028181 | Cùng đường | 22/04/2025 / 14 ngày | VT3, cân đối, Trung bình | 59,8; 4 × 15 | 200 / 4,5 | 80,27 / 75,25 | 94,22 | Không |
| TSSS-028125 | Cùng đường | 22/04/2025 / 14 ngày | VT3, cân đối, Trung bình | 59,8; 4 × 15 | 200 / 4,5 | 80,27 / 75,25 | 94,22 | Không |
| TSSS-028124 | Cùng đường | 22/04/2025 / 14 ngày | VT3, cân đối, Trung bình | 63; 4,5 × 14 | 200 / 5 | 87,30 / 80,95 | 92,00 | Không |
| TSSS-028155 | Cùng đường | 22/04/2025 / 14 ngày | VT3, cân đối, Trung bình | 63; 4,5 × 14 | 200 / 5 | 87,30 / 80,95 | 92,00 | Không |
| TSSS-028163 | Cùng đường | 22/04/2025 / 14 ngày | VT3, cân đối, Trung bình | 64; 4 × 16 | 100 / 6 | 101,56 / 90,63 | 86,78 | Không |

Tập TSSS rất mới và cùng đường, nhưng có hai cặp dòng gần như giống nhau. Trước khi chọn ba TSSS chính thức, cần kiểm tra duplicate hoặc các tài sản có liên hệ thực tế với nhau; không coi năm dòng như năm quan sát độc lập.

## Ví dụ 5: Quận 12

### TSTĐ

| Trường | Giá trị |
|---|---|
| Ngày hiệu lực | 13/05/2025 |
| Khu vực | Phường Thạnh Lộc → Phường An Phú Đông, đường Hà Huy Giáp, đoạn Ngã Tư Ga – Cầu Phú Long |
| VT / khoảng cách / hẻm | VT3 / 500 m / 3,4 m |
| Đất và kích thước | Đất ở tại đô thị; 80 m²; 5 m × 16,01 m; 1 mặt tiền |
| Hình dáng / lợi thế | Cân đối / Trung bình |
| Yếu tố khác | Gần thổ mộ |
| Đơn giá QSDĐ thực tế để đối chiếu | 50,59 triệu đ/m² |
| Tổng giá trị QSDĐ | 4,047 tỷ đồng |

### Năm TSSS

| Ref | Mức địa lý | Ngày / tuổi | VT và thuộc tính categorical | Diện tích; mặt tiền × dài | Cách đường / hẻm | Raw / estimated | Score | Cờ |
|---|---|---|---|---|---|---:|---:|---|
| TSSS-003774 | Cùng quận | 30/08/2024 / 256 ngày | VT3, cân đối, Trung bình | 80; 4,5 × 19 | 500 / 3,5 | 43,75 / 40,00 | 93,28 | Cũ >180 ngày |
| TSSS-003773 | Cùng quận | 30/08/2024 / 256 ngày | VT3, cân đối, Trung bình | 84,5; 4,8 × 17,6 | 500 / 3,5 | 43,20 / 39,05 | 93,21 | Cũ >180 ngày |
| TSSS-025735 | Cùng đường | 11/03/2025 / 63 ngày | VT3, cân đối, Trung bình | 78; 4 × 18 | 580 / 4 | 44,87 / 42,31 | 93,07 | Không |
| TSSS-025736 | Cùng đường | 11/03/2025 / 63 ngày | VT3, cân đối, Trung bình | 82; 4 × 20 | 600 / 4 | 46,34 / 43,90 | 92,28 | Không |
| TSSS-029001 | Cùng đường | 14/04/2025 / 29 ngày | VT3, cân đối, Trung bình | 100; 5 × 17 | 500 / 4,5 | 67,00 / 64,99 | 92,13 | Không |

Ba TSSS cùng đường đều khá mới và khớp categorical. Yếu tố `gần thổ mộ` chỉ có ở TSTĐ trong ví dụ này, chưa nằm trong rule xếp hạng retrieval hiện tại; chuyên viên phải xem đây là yếu tố điều chỉnh hoặc tạo cờ review riêng.

## Tổng kết so sánh

| Ví dụ | Chất lượng candidate | Điểm cần xem xét trước khi định giá |
|---|---|---|
| Quận Tân Bình | Khá tốt | Khác hình dáng; hai TSSS cũ |
| Quận 7 | Yếu | Khác đường hoặc khác VT/lợi thế; đa số cũ; giá phân tán |
| Thủ Đức | Tốt | Giá raw phân tán dù thuộc tính khớp |
| Bình Tân | Tốt nhưng cần audit | Candidate gần trùng nhau, nguy cơ duplicate/không độc lập |
| Quận 12 | Khá tốt | Yếu tố gần thổ mộ chưa được score; hai candidate cùng quận đã cũ |
