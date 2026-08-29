# Thí nghiệm chọn và điều chỉnh ba TSSS

## Mục tiêu

Kiểm tra hướng retrieval–adjustment: với mỗi TSTĐ, lấy tối đa 30 TSSS lịch sử trong 365 ngày, học chọn ba comparable phù hợp nhất, dự báo phần điều chỉnh giá cho từng comparable rồi lấy trung bình ba giá đã điều chỉnh. Kết quả được blend với CatBoost TSTĐ–TSSS hiện tại theo các trọng số cố định 0%, 25%, 50%, 75% và 100% retrieval.

## Luồng an toàn thời gian

1. TSSS chỉ hợp lệ khi cả ngày thị trường và ngày sẵn có đều nghiêm ngặt trước ngày hiệu lực TSTĐ.
2. TSSS cùng báo cáo bị loại.
3. Candidate ban đầu được xếp theo đường, phường, quận, vị trí khung giá, lợi thế kinh doanh, mục đích sử dụng, hình dáng, diện tích, mặt tiền, chiều dài, khoảng cách và độ rộng hẻm.
4. Trong mỗi rolling fold, model chọn comparable và model điều chỉnh chỉ fit từ các TSTĐ của train fold.
5. Giá điều chỉnh từng comparable bị giới hạn trong khoảng -20% đến +20% so với đơn giá rao bán/giao dịch của comparable.
6. Test 05–07/2025 không dùng chọn trọng số hoặc tham số.

Không có Mã tài sản, mã kho, số báo cáo, địa chỉ chi tiết hoặc liên hệ trong prediction artifact.

## Dữ liệu cặp

- 7.025 TSTĐ được xét.
- 208.596 cặp TSTĐ–TSSS được tạo.
- 7.010 TSTĐ có ít nhất một TSSS hợp lệ; 15 dòng không có comparable và dùng median train làm fallback.
- Mỗi TSTĐ có tối đa 30 candidate trước khi chọn ba comparable.
- 20 TSTĐ không có candidate cùng quận nên dùng fallback toàn kho TSSS hợp lệ.

## Kết quả rolling OOF

| Phương án | MAE đồng/m² | WAPE | MAPE | Trong 10% | P90 APE |
|---|---:|---:|---:|---:|---:|
| CatBoost with-TSSS khóa | 14.834.391 | 13,93% | 12,60% | 53,51% | 26,67% |
| Chỉ three-comparable đã điều chỉnh | 16.820.313 | 15,79% | 14,60% | 47,24% | 31,86% |
| 75% CatBoost + 25% comparable | **14.310.600** | **13,44%** | **12,24%** | **54,35%** | **26,15%** |

Blend 25% retrieval giảm MAE 523.791 đồng/m², tương đương 3,53%; WAPE giảm 0,49 điểm %, MAPE giảm 0,37 điểm % và `within_10pct` tăng 0,84 điểm % so với CatBoost khóa.

## Test cũ không xác nhận

Trên 1.000 TSTĐ 05–07/2025 đã từng được mở, blend 25% retrieval đạt MAE 15.874.155 đồng/m², WAPE 13,97% và `within_10pct` 56,30%, tốt hơn CatBoost khóa lần lượt 1,39%, 0,20 điểm % và 0,80 điểm %. Đây chỉ là tín hiệu nhất quán, không phải test xác nhận độc lập.

## Quyết định

Thí nghiệm cho tín hiệu cải thiện nhưng chưa thay model/package phát hành. Lý do: trọng số blend được chọn trên cùng OOF và test 05–07/2025 đã bị mở. Cần test thời gian mới sau 31/07/2025 trước khi promote.
