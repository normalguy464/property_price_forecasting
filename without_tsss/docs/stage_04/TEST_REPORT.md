# Báo cáo kiểm thử Stage 4

## Lần chạy cuối

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
& .venv\Scripts\python.exe -m unittest discover -s tests -v
```

Kết quả: `28/28 PASSED`, exit code `0`, thời gian `0,975 giây`.

## Chín test Stage 4

- Manifest xác nhận 1.000 test rows và đúng thời gian.
- Frozen prediction có 1.000 row ID duy nhất và checksum đúng.
- Tất cả metric được tái tạo từ prediction artifact.
- Khoảng 80%, 90%, 95% bao point prediction và coverage khớp báo cáo.
- Nghiệm thu tổng nhất quán với từng điều kiện.
- Checksum model không đổi sau Stage 3.
- Input/output example chạy suy luận được và contract cấm TSSS/target.
- Phường hiếm luôn có cờ kiểm duyệt.
- Ngày ngoài horizon bị từ chối.

Năm test Stage 1, bảy test Stage 2, bảy test Stage 3 và chín test Stage 4 đều đạt. Test code không có comment Python.
