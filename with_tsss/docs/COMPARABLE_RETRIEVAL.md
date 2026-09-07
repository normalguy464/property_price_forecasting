# Đề xuất TSSS tham khảo

## Mục đích

Chức năng này nhận một TSTĐ tại thời điểm định giá và trả về 3 đến 5 TSSS lịch sử để chuyên viên tham khảo. Nó nằm trong `with_tsss` nhưng không thay đổi mô hình CatBoost, package suy luận hay metric hiện có.

Đây là truy xuất comparable để hỗ trợ nghiệp vụ, không phải mô hình dự báo giá cuối cùng và không tự động tạo giá đã điều chỉnh. Giá cuối cùng vẫn cần áp dụng quy tắc điều chỉnh, giới hạn và phê duyệt nghiệp vụ riêng.

## Luồng thực hiện

1. Chuẩn hoá TSTĐ bằng đúng hàm đầu vào của pipeline `with_tsss`.
2. Chỉ lấy TSSS có ngày thị trường và ngày có sẵn nhỏ hơn nghiêm ngặt ngày hiệu lực TSTĐ, tối đa 365 ngày.
3. Bỏ TSSS cùng báo cáo khi request có `report_reference`. Trường này chỉ dùng cho lọc candidate, bị bỏ trước bước chuẩn hoá model và không xuất ra output. Request mới không có mã này vẫn an toàn về thời gian, nhưng không thể áp dụng kiểm tra cùng báo cáo.
4. Ưu tiên candidate trong cùng quận/huyện; chỉ fallback ra toàn thị trường khi quận/huyện không có candidate nào.
5. Tính `rule_distance` từ độ mới, đường/phường/quận, vị trí khung giá, lợi thế kinh doanh, mục đích sử dụng, hình dáng, diện tích, mặt tiền, chiều dài, khoảng cách tới đường chính và độ rộng hẻm.
6. Sắp tăng dần theo `rule_distance`, trả tối đa 3 đến 5 TSSS. `rule_similarity_score_0_100` chỉ là thang diễn giải từ rule distance, không phải xác suất.
7. Trả mã tham chiếu nội bộ `TSSS-xxxxxx`, giá đơn vị raw/estimated, ngày thị trường, tuổi dữ liệu, mức khớp địa lý, các trường khớp và chênh lệch định lượng. Không trả mã tài sản, mã kho, số báo cáo, địa chỉ chi tiết, chi tiết hay thông tin liên hệ.

## Điều kiện kiểm soát

- Ngày ngoài khoảng dữ liệu đã kiểm chứng trong `configs/pipeline.json` hiện là 01/05/2025–31/07/2025 bị `reject`.
- Không đủ candidate, phải fallback khác quận/huyện, hoặc candidate có độ tương đồng rule thấp sẽ là `manual_review`.
- `TSSS-xxxxxx` là mã tham chiếu nội bộ theo dòng nguồn, không được đưa vào feature ML. Bảng ánh xạ sang hồ sơ gốc, nếu cần, phải được giữ ở hệ thống nghiệp vụ có phân quyền.
- Chức năng chỉ chọn comparable, chưa đảm bảo yêu cầu nghiệp vụ về 3 TSSS được điều chỉnh, giới hạn điều chỉnh ±20% hay bước kiểm tra độc lập ±15%.

## Cách chạy

```powershell
python scripts/retrieve_comparables.py artifacts/model_package/example_input.json ..\..\Train_noi.xlsx artifacts\comparable_retrieval_output.json --count 3
```

`input_json` là mảng bản ghi theo cùng contract với `scripts/predict.py`; có thể thêm `report_reference` chỉ để loại TSSS cùng báo cáo. `--count` chỉ nhận 3, 4 hoặc 5. File output không được commit nếu chứa kết quả truy xuất từ dữ liệu nghiệp vụ.
