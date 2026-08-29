# Kiểm toán code và tài liệu hiện hữu

## Workspace trước khi tạo dự án mới

Tại thời điểm Stage 1 bắt đầu, workspace chỉ có ba file:

| File | Vai trò | Kết luận |
|---|---|---|
| `Train_noi.xlsx` | Dataset nguồn | Đã đọc và lập profile mới |
| `BAO_CAO_KIEM_TOAN_BAI_TOAN_BDS.md` | Báo cáo kiểm toán cũ | Có nhiều nhận định đúng về leakage và time split, nhưng phần kiểm kê code đã lỗi thời |
| `Bao_cao_pipeline_du_doan_gia_BDS.docx` | Báo cáo pipeline cũ | Đã đọc nội dung; đây là tài liệu mô tả, không phải pipeline thực thi |

Không còn notebook, package Python, file requirements cũ, dữ liệu Q2 hoặc thư mục `simple_cat-master`. Vì vậy Stage 1 không thể xác minh bằng thực thi các nhận định về cách outlier, split, encoding, CatBoost hoặc metric của pipeline trước đây.

## Những điểm giữ lại từ báo cáo cũ

- Cảnh báo loại ngoại lai trước split là đúng.
- Cảnh báo các cột `Don_gia_TB`, `Min`, `Max`, tổng giá trị và cột target trùng là leakage có cơ sở.
- Khuyến nghị validation theo thời gian phù hợp hướng triển khai mới.
- Khuyến nghị đánh giá theo phân khúc là cần thiết cho vận hành.

## Những điểm phải thay thế hoặc xác minh lại

- Danh sách file và code cũ không còn đúng với workspace.
- Dataset hiện phải được hiểu theo hai loại kho TSSS/TSTĐ; một số cột đổi nghĩa theo loại kho.
- Chưa có code tạo Q2 hoặc dữ liệu gốc trước `Train_noi.xlsx`; lineage trước file này vẫn thiếu.
- Chưa có bằng chứng metric, seed, tham số hay model artifact có thể tái lập.
- Chưa xác nhận target là đơn giá trên mét vuông dù tên cột gợi ý như vậy.

## Code mới ở Stage 1

Code mới chỉ làm kiểm toán read-only và xuất JSON. Nó không làm sạch, không split và không train. Toàn bộ file Python đã được test không chứa token comment.
