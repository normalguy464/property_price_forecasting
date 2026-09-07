# Báo cáo kiểm thử

## Bổ sung comparable retrieval

Lần chạy sau khi thêm backtest Top-3: 15/15 test đạt trong 0,690 giây.

- Candidate chỉ được lấy khi ngày thị trường và ngày có sẵn nhỏ hơn nghiêm ngặt ngày định giá.
- `report_reference` trùng bị loại, số lượng ngoài 3–5 và ngày ngoài phạm vi kiểm chứng bị từ chối.
- Output không có mã kho, mã tài sản, chi tiết hoặc thông tin liên hệ.
- Smoke test CLI với `Train_noi.xlsx` đã hoàn tất; không làm thay đổi model ensemble, metric hoặc artifact benchmark.
- Artifact báo cáo 7.025 TSTĐ tái tính được WAPE/MAPE từ audit row-level và không chứa trường định danh nhạy cảm.
- Artifact Top-3 tái tính được metric độc lập và không ghi đè artifact Top-5.

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
