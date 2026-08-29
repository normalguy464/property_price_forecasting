from hashlib import sha256
from pathlib import Path
import json
import math
import re
import unicodedata

import numpy as np
import pandas as pd


CATEGORICAL_FEATURES = [
    "district",
    "ward_old",
    "ward_new",
    "road",
    "road_segment",
    "price_position",
    "land_use",
    "plot_shape",
    "business_advantage",
]


NUMERIC_FEATURES = [
    "area_m2",
    "frontage_m",
    "length_m",
    "frontage_count",
    "distance_to_main_road_m",
    "alley_width_m",
    "construction_count",
    "plot_rectangularity",
    "frontage_length_ratio",
    "log_area_m2",
    "log_frontage_m",
    "log_length_m",
    "log_distance_to_main_road_m",
    "log_alley_width_m",
    "is_direct_main_road",
    "ward_old_missing",
    "road_segment_missing",
    "other_is_none",
    "other_dead_end_alley",
    "other_road_or_alley_facing",
    "other_park_opposite",
    "other_near_tomb",
    "other_near_temple",
    "other_planning_issue",
    "other_unrecognized_area",
    "other_main_axis",
    "effective_year",
    "effective_month",
    "effective_quarter",
    "month_index",
    "month_sin",
    "month_cos",
    "quality_geometry_ratio_low",
    "quality_geometry_ratio_high",
    "quality_area_outside_review_range",
    "quality_frontage_outside_review_range",
    "quality_length_outside_review_range",
    "quality_access_outside_review_range",
]


METADATA_COLUMNS = [
    "source_excel_row",
    "asset_group_id",
    "report_group_id",
    "as_of_date",
    "split",
    "asset_seen_in_development",
]


TARGET_COLUMNS = [
    "target_price_vnd_m2",
    "target_log1p",
]


DIAGNOSTIC_COLUMNS = [
    "quality_target_formula_mismatch",
    "quality_target_above_official_reference",
]


LEAKAGE_SOURCE_COLUMNS = [
    "Đơn giá quyền sử dụng đất (đ/m2)",
    "Giá trị định giá",
    "Giá trị đề xuất",
    "Tổng giá trị quyền sử dụng đất",
    "Tổng giá trị đề xuất quyền sử dụng đất",
    "Tổng giá trị định giá công trình xây dựng",
    "Tổng giá trị đề xuất công trình xây dựng",
    "Tổng giá trị định giá cây trồng",
    "Tổng giá trị đề xuất cây trồng",
    "Tổng giá trị tài sản",
    "Giá giao dịch/rao bán (đ)",
    "Giá ước tính (đ)",
    "Don_gia_TB",
    "Min",
    "Max",
    "Độ lệch chuẩn",
    "Số lượng mẫu",
]


SENSITIVE_SOURCE_COLUMNS = [
    "Mã kho",
    "Mã tài sản",
    "Số báo cáo định giá",
    "Chi tiết",
    "Thông tin liên hệ",
]


def normalize_text(value):
    if pd.isna(value):
        return "__missing__"
    text = unicodedata.normalize("NFC", str(value)).replace("\u00a0", " ")
    text = re.sub(r"[–—]", "-", text)
    text = re.sub(r"\s+", " ", text).strip().casefold()
    return text if text else "__missing__"


def strip_accents(value):
    text = normalize_text(value).replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    return "".join(character for character in text if unicodedata.category(character) != "Mn")


def canonical_shape(value):
    text = strip_accents(value)
    if "khong can doi" in text:
        return "khong_can_doi"
    if "kha can doi" in text:
        return "kha_can_doi"
    if "can doi" in text or "vuong vuc" in text:
        return "can_doi"
    if "no hau" in text:
        return "no_hau"
    if "top hau" in text:
        return "top_hau"
    if "chu l" in text or "hinh l" in text:
        return "hinh_chu_l"
    if "phuc tap" in text or "da giac" in text:
        return "phuc_tap"
    return "khac"


def canonical_land_use(value):
    text = strip_accents(value)
    if "nong thon" in text:
        return "dat_o_nong_thon"
    if "do thi" in text:
        return "dat_o_do_thi"
    if "dat o" in text:
        return "dat_o"
    return "khac"


def canonical_business_advantage(value):
    text = strip_accents(value)
    mapping = {
        "kem": "kem",
        "trung binh": "trung_binh",
        "kha": "kha",
        "tot": "tot",
    }
    return mapping.get(text, "khac")


def contains_any(series, phrases):
    pattern = "|".join(re.escape(phrase) for phrase in phrases)
    return series.str.contains(pattern, regex=True, na=False).astype("int8")


def stable_group_ids(series):
    values = series.astype("string").fillna("__missing__")
    mapping = {value: index + 1 for index, value in enumerate(sorted(values.unique().tolist()))}
    return values.map(mapping).astype("int32")


def source_file_sha256(path):
    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def output_file_sha256(path):
    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_tstd(source, config):
    dataframe = source.copy()
    source_rows = dataframe.index.to_series() + 2
    eligible = dataframe["Phân loại kho"].eq(config["eligible_warehouse_class"])
    dataframe = dataframe.loc[eligible].copy()
    source_rows = source_rows.loc[eligible]
    as_of_date = pd.to_datetime(dataframe[config["as_of_column"]], format=config["date_format"], errors="coerce")
    target = pd.to_numeric(dataframe[config["target_column"]], errors="coerce")
    valid = as_of_date.notna() & target.notna() & target.gt(0)
    removed_invalid = int((~valid).sum())
    dataframe = dataframe.loc[valid].copy()
    source_rows = source_rows.loc[valid]
    as_of_date = as_of_date.loc[valid]
    target = target.loc[valid]
    test_start = pd.Timestamp(config["test_start"])
    test_end = pd.Timestamp(config["test_end"])
    if as_of_date.max() > test_end:
        raise ValueError("Source contains rows after configured test_end")
    split = pd.Series(np.where(as_of_date < test_start, "development", "test"), index=dataframe.index)
    development_assets = set(dataframe.loc[split.eq("development"), "Mã tài sản"].astype("string"))
    asset_seen = dataframe["Mã tài sản"].astype("string").isin(development_assets)
    normalized_other = dataframe["Yếu tố khác"].map(strip_accents)
    area = pd.to_numeric(dataframe["Diện tích (m2)"], errors="coerce")
    frontage = pd.to_numeric(dataframe["Kích thước mặt tiền (m)"], errors="coerce")
    length = pd.to_numeric(dataframe["Kích thước chiều dài"], errors="coerce")
    distance = pd.to_numeric(dataframe["Khoảng cách đến đường chính (m)"], errors="coerce")
    alley = pd.to_numeric(dataframe["Độ rộng ngõ/ngách nhỏ nhất (Từ đường chính đến BĐS)"], errors="coerce")
    rectangle = area / (frontage * length)
    land_formula = pd.to_numeric(dataframe["Tổng giá trị quyền sử dụng đất"], errors="coerce") / area
    formula_error = (land_formula - target).abs() / np.maximum(np.maximum(land_formula.abs(), target.abs()), 1)
    base_month = pd.Timestamp("2024-03-01")
    month_index = (as_of_date.dt.year - base_month.year) * 12 + as_of_date.dt.month - base_month.month
    clean = pd.DataFrame(index=dataframe.index)
    clean["source_excel_row"] = source_rows.astype("int32")
    clean["asset_group_id"] = stable_group_ids(dataframe["Mã tài sản"])
    clean["report_group_id"] = stable_group_ids(dataframe["Số báo cáo định giá"])
    clean["as_of_date"] = as_of_date.dt.strftime("%Y-%m-%d")
    clean["split"] = split
    clean["asset_seen_in_development"] = asset_seen.astype("int8")
    clean["district"] = dataframe["Thành phố/Quận/Huyện/Thị xã"].map(normalize_text)
    clean["ward_old"] = dataframe["Xã/Phường/Thị trấn"].map(normalize_text)
    clean["ward_new"] = dataframe["Xã/Phường mới"].map(normalize_text)
    clean["road"] = dataframe["Đường phố"].map(normalize_text)
    clean["road_segment"] = dataframe["Đoạn đường"].map(normalize_text)
    clean["price_position"] = dataframe["Vị trí trong khung giá"].map(normalize_text)
    clean["land_use"] = dataframe["Mục đích sử dụng đất"].map(canonical_land_use)
    clean["plot_shape"] = dataframe["Hình dáng"].map(canonical_shape)
    clean["business_advantage"] = dataframe["Lợi thế kinh doanh"].map(canonical_business_advantage)
    clean["area_m2"] = area.astype("float64")
    clean["frontage_m"] = frontage.astype("float64")
    clean["length_m"] = length.astype("float64")
    clean["frontage_count"] = pd.to_numeric(dataframe["Số mặt tiền tiếp giáp"], errors="coerce").astype("float64")
    clean["distance_to_main_road_m"] = distance.astype("float64")
    clean["alley_width_m"] = alley.astype("float64")
    clean["construction_count"] = pd.to_numeric(dataframe["Số lượng CTXD"], errors="coerce").astype("float64")
    clean["plot_rectangularity"] = rectangle.astype("float64")
    clean["frontage_length_ratio"] = (frontage / length).astype("float64")
    clean["log_area_m2"] = np.log1p(area)
    clean["log_frontage_m"] = np.log1p(frontage)
    clean["log_length_m"] = np.log1p(length)
    clean["log_distance_to_main_road_m"] = np.log1p(distance)
    clean["log_alley_width_m"] = np.log1p(alley)
    clean["is_direct_main_road"] = distance.eq(0).astype("int8")
    clean["ward_old_missing"] = dataframe["Xã/Phường/Thị trấn"].isna().astype("int8")
    clean["road_segment_missing"] = dataframe["Đoạn đường"].isna().astype("int8")
    clean["other_is_none"] = normalized_other.isin(["khong", "binh thuong"]).astype("int8")
    clean["other_dead_end_alley"] = contains_any(normalized_other, ["hem cut", "cuoi hem cut"])
    clean["other_road_or_alley_facing"] = contains_any(normalized_other, ["duong dam", "dam duong", "dam hem", "hem dam", "hem huong vao"])
    clean["other_park_opposite"] = contains_any(normalized_other, ["doi dien cong vien"])
    clean["other_near_tomb"] = contains_any(normalized_other, ["gan mo", "lan can mo", "tho mo"])
    clean["other_near_temple"] = contains_any(normalized_other, ["gan chua", "lan can chua"])
    clean["other_planning_issue"] = contains_any(normalized_other, ["quy hoach"])
    clean["other_unrecognized_area"] = contains_any(normalized_other, ["khong cong nhan"])
    clean["other_main_axis"] = contains_any(normalized_other, ["truc chinh"])
    clean["effective_year"] = as_of_date.dt.year.astype("int16")
    clean["effective_month"] = as_of_date.dt.month.astype("int8")
    clean["effective_quarter"] = as_of_date.dt.quarter.astype("int8")
    clean["month_index"] = month_index.astype("int16")
    clean["month_sin"] = np.sin(2 * math.pi * as_of_date.dt.month / 12)
    clean["month_cos"] = np.cos(2 * math.pi * as_of_date.dt.month / 12)
    clean["quality_geometry_ratio_low"] = rectangle.lt(0.5).astype("int8")
    clean["quality_geometry_ratio_high"] = rectangle.gt(2).astype("int8")
    clean["quality_area_outside_review_range"] = (area.lt(20) | area.gt(2000)).astype("int8")
    clean["quality_frontage_outside_review_range"] = (frontage.lt(2) | frontage.gt(30)).astype("int8")
    clean["quality_length_outside_review_range"] = (length.lt(5) | length.gt(80)).astype("int8")
    clean["quality_access_outside_review_range"] = (distance.gt(2000) | alley.gt(60)).astype("int8")
    clean["target_price_vnd_m2"] = target.astype("float64")
    clean["target_log1p"] = np.log1p(target)
    clean["quality_target_formula_mismatch"] = formula_error.gt(0.01).astype("int8")
    clean["quality_target_above_official_reference"] = target.gt(config["official_reference_vnd_m2"]).astype("int8")
    ordered = METADATA_COLUMNS + CATEGORICAL_FEATURES + NUMERIC_FEATURES + TARGET_COLUMNS + DIAGNOSTIC_COLUMNS
    clean = clean[ordered].reset_index(drop=True)
    return clean, removed_invalid


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_clean_jsonl(path, dataframe):
    compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
    dataframe.to_json(path, orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
