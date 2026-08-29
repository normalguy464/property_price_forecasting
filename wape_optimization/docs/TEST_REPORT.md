# Báo cáo kiểm thử

Ngày chạy: 13/08/2026.

Lệnh:

```text
../.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Kết quả nhánh này: 10/10 test đạt trong 0,535 giây.

Kiểm thử hồi quy sau khi tách nhánh:

- `without_tsss`: 28/28 đạt.
- `with_tsss`: 11/11 đạt.
- Tổng cả ba nhánh: 49/49 đạt.

Phạm vi kiểm tra:

- Shape, feature count, uniqueness và infinity của history artifact.
- Quy tắc lag nhãn, loại cùng báo cáo và không dùng target hiện tại.
- Đường dẫn chỉ đọc tới hai pipeline khóa.
- Tái tính toàn bộ rolling metric từ selected OOF.
- Giải pháp cuối tốt hơn cả hai baseline nhưng chưa đạt 10%.
- Tổng trọng số bằng 1 và SHA-256 của ba model đúng manifest.
- Test cũ được đánh dấu không dùng cho selection và metric tái lập được.
- Prediction interval có thứ tự hợp lệ.
- Artifact dự đoán không chứa các cột định danh/địa chỉ nhạy cảm.
- Toàn bộ file Python của nhánh không có comment.

Kết luận: artifact nội bộ nhất quán và pipeline thử nghiệm chạy được. Test kỹ thuật đạt không đồng nghĩa model đã production-ready.
