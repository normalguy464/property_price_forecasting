# Truy xuất 3–5 TSSS trong nhánh WAPE

## Phạm vi

Nhánh `wape_optimization` có thêm retrieval TSSS tham khảo cho một TSTĐ input. Chức năng này không làm thay đổi ba model ensemble, artifact, WAPE, MAE hoặc kết quả benchmark của nhánh.

Retrieval dùng cùng nguyên tắc với `with_tsss`: ngày thị trường và ngày có sẵn của TSSS phải nhỏ hơn nghiêm ngặt ngày định giá, cửa sổ tối đa 365 ngày, và TSSS có `report_reference` trùng sẽ bị loại.

## Xếp hạng

Candidate được ưu tiên theo tổng rule distance gồm độ mới, đường/phường/quận, vị trí trong khung giá, lợi thế kinh doanh, mục đích đất, hình dáng, diện tích, mặt tiền, chiều dài, khoảng cách tới đường chính và độ rộng hẻm. Kết quả trả 3–5 mã tham chiếu nội bộ, giá raw/estimated đơn vị, ngày, mức khớp, khác biệt định lượng và cờ review.

Mã tham chiếu không phải feature của ensemble WAPE. Output không có mã kho, mã tài sản, số báo cáo, chi tiết hoặc thông tin liên hệ.

## Chạy

```powershell
python scripts/retrieve_comparables.py input.json comparable_output.json --market-xlsx ..\..\Train_noi.xlsx --count 5
```

`input.json` dùng contract TSTĐ như nhánh `with_tsss`; có thể thêm `report_reference` chỉ để loại TSSS cùng báo cáo. Retrieval không tự tạo giá điều chỉnh hoặc thay thế giá dự báo ensemble.
