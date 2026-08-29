import math

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

from property_price_forecasting_tsss.market_features import build_market_features
from property_price_forecasting_tsss.modeling import frame_for_catboost
from property_price_forecasting_tsss.normalization import canonical_business_advantage, canonical_land_use, canonical_shape, normalize_text, strip_accents


CATEGORICAL_FEATURES = ["district", "ward_old", "ward_new", "road", "road_segment", "price_position", "land_use", "plot_shape", "business_advantage"]


BASE_NUMERIC_FEATURES = [
    "area_m2", "frontage_m", "length_m", "frontage_count", "distance_to_main_road_m", "alley_width_m", "construction_count", "plot_rectangularity", "frontage_length_ratio",
    "log_area_m2", "log_frontage_m", "log_length_m", "log_distance_to_main_road_m", "log_alley_width_m", "is_direct_main_road", "ward_old_missing", "road_segment_missing",
    "other_is_none", "other_dead_end_alley", "other_road_or_alley_facing", "other_park_opposite", "other_near_tomb", "other_near_temple", "other_planning_issue", "other_unrecognized_area", "other_main_axis",
    "effective_year", "effective_month", "effective_quarter", "month_index", "month_sin", "month_cos", "quality_geometry_ratio_low", "quality_geometry_ratio_high", "quality_area_outside_review_range",
    "quality_frontage_outside_review_range", "quality_length_outside_review_range", "quality_access_outside_review_range",
]


REQUIRED_INPUTS = [
    "as_of_date", "district", "ward_new", "road", "price_position", "land_use", "plot_shape", "business_advantage", "area_m2", "frontage_m", "length_m", "frontage_count",
    "distance_to_main_road_m", "alley_width_m", "construction_count",
]


OPTIONAL_INPUTS = ["ward_old", "road_segment", "other_factors"]
FORBIDDEN_INPUTS = ["target_price_vnd_m2", "target_log1p", "TSSS", "Giá trị định giá", "Giá trị đề xuất", "Đơn giá quyền sử dụng đất (đ/m2)"]


def validate_record(record):
    missing = [name for name in REQUIRED_INPUTS if name not in record or record[name] is None]
    forbidden = [name for name in FORBIDDEN_INPUTS if name in record]
    unexpected = sorted(set(record) - set(REQUIRED_INPUTS + OPTIONAL_INPUTS))
    if missing:
        raise ValueError(f"Missing required inputs: {missing}")
    if forbidden:
        raise ValueError(f"Forbidden inputs: {forbidden}")
    if unexpected:
        raise ValueError(f"Unexpected inputs: {unexpected}")


def numeric(record, name):
    value = float(record[name])
    if not math.isfinite(value):
        raise ValueError(f"Non-finite input: {name}")
    return value


def build_base_features(records):
    rows = []
    for index, record in enumerate(records):
        validate_record(record)
        timestamp = pd.to_datetime(record["as_of_date"], format="%Y-%m-%d", errors="raise")
        area = numeric(record, "area_m2")
        frontage = numeric(record, "frontage_m")
        length = numeric(record, "length_m")
        frontage_count = numeric(record, "frontage_count")
        distance = numeric(record, "distance_to_main_road_m")
        alley = numeric(record, "alley_width_m")
        construction_count = numeric(record, "construction_count")
        if area <= 0 or frontage <= 0 or length <= 0:
            raise ValueError("Area, frontage and length must be positive")
        if frontage_count < 0 or distance < 0 or alley < 0 or construction_count < 0:
            raise ValueError("Counts, distance and alley width must be non-negative")
        other = strip_accents(record.get("other_factors"))
        rectangle = area / (frontage * length)
        month_index = (timestamp.year - 2024) * 12 + timestamp.month - 3
        rows.append({
            "source_excel_row": -(index + 1),
            "as_of_date": timestamp.strftime("%Y-%m-%d"),
            "district": normalize_text(record["district"]),
            "ward_old": normalize_text(record.get("ward_old")),
            "ward_new": normalize_text(record["ward_new"]),
            "road": normalize_text(record["road"]),
            "road_segment": normalize_text(record.get("road_segment")),
            "price_position": normalize_text(record["price_position"]),
            "land_use": canonical_land_use(record["land_use"]),
            "plot_shape": canonical_shape(record["plot_shape"]),
            "business_advantage": canonical_business_advantage(record["business_advantage"]),
            "area_m2": area,
            "frontage_m": frontage,
            "length_m": length,
            "frontage_count": frontage_count,
            "distance_to_main_road_m": distance,
            "alley_width_m": alley,
            "construction_count": construction_count,
            "plot_rectangularity": rectangle,
            "frontage_length_ratio": frontage / length,
            "log_area_m2": math.log1p(area),
            "log_frontage_m": math.log1p(frontage),
            "log_length_m": math.log1p(length),
            "log_distance_to_main_road_m": math.log1p(distance),
            "log_alley_width_m": math.log1p(alley),
            "is_direct_main_road": int(distance == 0),
            "ward_old_missing": int(record.get("ward_old") is None),
            "road_segment_missing": int(record.get("road_segment") is None),
            "other_is_none": int(other in ["khong", "binh thuong"]),
            "other_dead_end_alley": int("hem cut" in other or "cuoi hem cut" in other),
            "other_road_or_alley_facing": int(any(value in other for value in ["duong dam", "dam duong", "dam hem", "hem dam", "hem huong vao"])),
            "other_park_opposite": int("doi dien cong vien" in other),
            "other_near_tomb": int(any(value in other for value in ["gan mo", "lan can mo", "tho mo"])),
            "other_near_temple": int("gan chua" in other or "lan can chua" in other),
            "other_planning_issue": int("quy hoach" in other),
            "other_unrecognized_area": int("khong cong nhan" in other),
            "other_main_axis": int("truc chinh" in other),
            "effective_year": timestamp.year,
            "effective_month": timestamp.month,
            "effective_quarter": timestamp.quarter,
            "month_index": month_index,
            "month_sin": math.sin(2 * math.pi * timestamp.month / 12),
            "month_cos": math.cos(2 * math.pi * timestamp.month / 12),
            "quality_geometry_ratio_low": int(rectangle < 0.5),
            "quality_geometry_ratio_high": int(rectangle > 2),
            "quality_area_outside_review_range": int(area < 20 or area > 2000),
            "quality_frontage_outside_review_range": int(frontage < 2 or frontage > 30),
            "quality_length_outside_review_range": int(length < 5 or length > 80),
            "quality_access_outside_review_range": int(distance > 2000 or alley > 60),
        })
    return pd.DataFrame(rows)


def predict_records(records, market_source, model_path, model_manifest, config, calibration=None):
    base = build_base_features(records)
    market, _ = build_market_features(base, market_source, config, [f"__request_{index}" for index in range(len(base))])
    frame = pd.concat([base.reset_index(drop=True), market.drop(columns=["source_excel_row"]).reset_index(drop=True)], axis=1)
    features = model_manifest["categorical_features"] + model_manifest["base_numeric_features"] + model_manifest["market_numeric_features"]
    model = CatBoostRegressor()
    model.load_model(model_path)
    pool = Pool(frame_for_catboost(frame, features, model_manifest["categorical_features"]), cat_features=model_manifest["categorical_features"])
    predictions = np.maximum(np.expm1(model.predict(pool)), 1.0)
    outputs = []
    start = pd.Timestamp(config["supported_as_of_start"])
    end = pd.Timestamp(config["supported_as_of_end"])
    for index, prediction in enumerate(predictions):
        flags = []
        reject = []
        date = pd.Timestamp(base.loc[index, "as_of_date"])
        if date < start or date > end:
            reject.append("unsupported_as_of_date")
        road_count = float(frame.loc[index, "market_road_count_365d"])
        comparable_count = float(frame.loc[index, "comparable_count_365d"])
        if road_count == 0:
            flags.append("no_same_road_tsss_365d")
        elif road_count < config["road_min_count"]:
            flags.append("low_same_road_tsss_365d")
        if comparable_count < config["comparable_top_k"]:
            flags.append("insufficient_comparable_tsss_365d")
        if float(frame.loc[index, "market_backoff_count_365d"]) == 0:
            flags.append("no_tsss_365d")
        status = "reject" if reject else "manual_review" if flags else "automatic"
        output = {
            "prediction_vnd_m2": float(prediction),
            "status": status,
            "flags": sorted(set(flags + reject)),
            "tsss_coverage": {
                "same_road_count_365d": road_count,
                "backoff_count_365d": float(frame.loc[index, "market_backoff_count_365d"]),
                "comparable_count_365d": comparable_count,
                "backoff_level_365d": int(frame.loc[index, "market_backoff_level_365d"]),
            },
        }
        if calibration is not None:
            intervals = {}
            log_prediction = math.log1p(float(prediction))
            for level, values in calibration["levels"].items():
                qhat = float(values["qhat_log"])
                intervals[level] = {"lower_vnd_m2": max(math.expm1(log_prediction - qhat), 1.0), "upper_vnd_m2": math.expm1(log_prediction + qhat)}
            output["prediction_intervals"] = intervals
        outputs.append(output)
    return outputs
