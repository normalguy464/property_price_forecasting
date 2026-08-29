# Báo cáo kiểm thử Stage 3

## Lần chạy cuối

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
& .venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Kết quả: `19/19 PASSED`, exit code `0`, thời gian `0,444 giây`.

## Bảy test Stage 3

- Công thức MAE, WAPE và tỷ lệ trong biên đúng trên ví dụ nhỏ.
- Benchmark chỉ có năm variant: baseline, ba Ridge alpha và một CatBoost mặc định.
- Benchmark, tuning, rolling và selected model đều ghi test rows used bằng 0.
- Optuna có đúng 14 audit records và lưu đủ tham số tốt nhất.
- OOF có 3.334 source rows duy nhất, không vượt 30/04/2025.
- Model được chọn đúng là ứng viên có pooled rolling MAE thấp nhất.
- Model artifact tồn tại và checksum khớp manifest.
- Toàn bộ code Python vẫn không có token comment.

## Chưa kiểm thử

Chưa chạy metric trên 1.000 dòng test, chưa calibration khoảng dự báo và chưa kiểm tra drift production. Đây là phạm vi Stage 4 sau phê duyệt.
