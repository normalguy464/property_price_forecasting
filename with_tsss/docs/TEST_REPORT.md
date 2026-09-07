# Báo cáo test

## Nhánh không TSSS sau di chuyển

`28/28 PASSED` bằng môi trường dùng chung. Điều này xác nhận việc gom thư mục không làm thay đổi artifact hoặc pipeline cũ.

## Nhánh có TSSS

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
& ..\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Kết quả sau thí nghiệm chọn và điều chỉnh ba TSSS: `15/15 PASSED`, exit code 0. Test inference smoke chạy riêng đạt trong 23,080 giây; 14 test còn lại đạt trong 0,821 giây. Bộ test kiểm tra audit counts, 7.025×86 feature contract, 7.025×33 enhanced feature contract, as-of/same-report fixture, TSSS không là target, rolling selection, sáu trial Optuna, OOF scope/metric, benchmark V2 không promote model xấu hơn, test reuse flag, checksum, inference interval/stale guard, retrieval–adjustment OOF tái lập được, không PII và quy tắc code không comment.

Nhánh không TSSS được chạy lại sau cùng: `28/28 PASSED`, exit code 0, thời gian 0,465 giây.
# Bổ sung kiểm thử comparable retrieval

Lần chạy sau khi bổ sung truy xuất TSSS: 17/17 test thành công, 23,548 giây.

- Kiểm thử TSSS history vẫn giữ điều kiện ngày thị trường, ngày có sẵn và loại cùng báo cáo.
- Kiểm thử retrieval mới xác minh chỉ trả candidate as-of, loại `report_reference` trùng, xếp hạng đúng theo rule và không có mã kho, mã tài sản, chi tiết hoặc thông tin liên hệ trong output.
- Kiểm thử input đảm bảo ngày không được hỗ trợ bị reject và số lượng ngoài 3–5 bị từ chối.
