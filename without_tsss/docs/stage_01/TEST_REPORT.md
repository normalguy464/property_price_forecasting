# Báo cáo kiểm thử Stage 1

## Kết quả cuối stage

Lệnh:

```powershell
& C:\Users\ACER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Thời điểm chạy: 09/08/2026, múi giờ Asia/Saigon.

Kết quả lần chạy cuối: `5/5 PASSED`, exit code `0`, thời gian test `0,024 giây`.

| Test | Mục đích | Kết quả |
|---|---|---|
| `test_source_snapshot` | File nguồn tồn tại, đúng 34.477 × 90 và checksum không đổi | Passed |
| `test_schema_is_complete` | Profile đủ 90 cột, tên cột không trùng | Passed |
| `test_temporal_scope` | Có 17 tháng, parse ngày hiệu lực thành công và khớp tháng/năm | Passed |
| `test_privacy_guard` | Artifact không xuất top value của các cột nhạy cảm | Passed |
| `test_python_files_have_no_comments` | Toàn bộ code Python không có token comment | Passed |

## Chạy audit

Lần chạy thành công cuối cùng đọc 34.477 dòng, 90 cột và ghi `artifacts/stage_01/data_profile.json`.

Trước đó có hai lần thất bại vì sandbox không cho script tạo/ghi output. Sau khi tạo sẵn đường dẫn và được cấp quyền ghi trong workspace, audit chạy thành công. Chi tiết được lưu ở `docs/ISSUES_AND_FIXES.md`.

## Phạm vi test

Test Stage 1 xác nhận công cụ audit và tính toàn vẹn snapshot. Nó không chứng minh pipeline làm sạch hoặc mô hình dự đoán đúng vì các thành phần đó chưa được phép xây ở stage này.
