# Báo cáo kiểm thử Stage 2

## Lần chạy cuối

Lệnh:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
& C:\Users\ACER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Kết quả lần chạy cuối: `12/12 PASSED`, exit code `0`, thời gian `0,456 giây`.

## Phạm vi

Năm test Stage 1 tiếp tục đạt. Bảy test Stage 2 kiểm tra:

- Hợp đồng VND/m², TSTĐ tại ngày hiệu lực và không dùng TSSS.
- `Lợi thế kinh doanh` và `Vị trí trong khung giá` được ghi nhận là đầu vào inference.
- Đúng 7.025 dòng, development 6.025 và test 1.000.
- Checksum dataset sạch khớp quality report.
- Không còn raw PII hoặc leakage trong đầu ra.
- Đủ 47 feature, categorical không null và numeric hữu hạn.
- Train luôn kết thúc trước validation/test; không giao số báo cáo.
- Chuẩn hóa Unicode và chữ `đ` hoạt động đúng.
- Target/diagnostic không nằm trong feature contract.
- Toàn bộ code Python tiếp tục không có token comment.

Dataset sạch được sinh hai lần liên tiếp với cùng SHA-256 `2b0d4b3db2ba22913e3c007c031f01c9a22a4ee3dca8bf4970969539f019200c`.

## Chưa được kiểm thử trong Stage 2

Chưa có model, metric dự đoán, tuning, SHAP hoặc model artifact. Những phần này thuộc Stage 3 sau khi người dùng duyệt.
