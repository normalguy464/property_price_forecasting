# Feature TSSS as-of

## Điều kiện cho từng TSTĐ

Một TSSS chỉ được nhìn thấy khi đồng thời:

- `market_date < t`.
- `availability_date < t`.
- Không cùng báo cáo TSTĐ.
- Tuổi market không âm và không quá 730 ngày tại thời điểm được ghi nhận.
- Diện tích dương; raw và estimated unit price nằm trong 5 triệu–2 tỷ VND/m².
- Nằm trong cửa sổ 90, 180 hoặc 365 ngày so với TSTĐ.

## Aggregate

Mỗi cửa sổ tạo count, raw median, estimated median, P25, P75 và ngày gần nhất theo ba cấp: cùng đường, cùng phường và cùng quận.

Back-off chọn cấp đầu tiên đủ bằng chứng:

- Đường: ít nhất 5 TSSS.
- Phường: ít nhất 10 TSSS.
- Quận: ít nhất 20 TSSS.
- Nếu vẫn thiếu: toàn thị trường đủ điều kiện trong cửa sổ.

Giá giao dịch và giá rao được tách ở cấp quận bằng trạng thái giao dịch. Do chỉ có 416 giao dịch, feature transaction thường thiếu và CatBoost xử lý missing trực tiếp.

## Comparable top-5

Candidate nằm trong cùng quận và 365 ngày. Khoảng cách gồm địa bàn, tuổi TSSS, VT1–VT4, lợi thế, mục đích đất, hình dáng và log-ratio diện tích/mặt tiền/chiều dài/khoảng cách/hẻm.

Trọng số là `exp(-distance)`. Output gồm weighted raw/estimated price, best distance, weighted age, tỷ lệ cùng đường/phường và weighted MAD.

## Kết quả coverage

- 7.025 TSTĐ có đủ 86 feature columns.
- 15 dòng không có TSSS nào trong 365 ngày.
- 1.010 dòng không có TSSS cùng đường trong 365 ngày.
- 3.334 OOF rows cuối đều có top-5 comparable trong cùng quận.

Artifact có 24.329 ô missing trong hơn 604 nghìn giá trị feature, chủ yếu do không đủ TSSS ở một cấp/cửa sổ hoặc không có giao dịch thật. Đây là missing có ý nghĩa; CatBoost xử lý trực tiếp. Artifact không có giá trị vô cực và không chứa PII/raw report.

Hai feature quan trọng nhất của CatBoost là comparable weighted estimated price và comparable weighted raw price, chiếm khoảng 23,15% và 22,18% feature importance.
