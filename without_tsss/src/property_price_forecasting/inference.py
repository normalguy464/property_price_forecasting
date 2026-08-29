from pathlib import Path
import json
import math

import joblib
import numpy as np
import pandas as pd

from property_price_forecasting.cleaning import CATEGORICAL_FEATURES, NUMERIC_FEATURES, canonical_business_advantage, canonical_land_use, canonical_shape, normalize_text, strip_accents


REQUIRED_INPUTS = [
    "as_of_date",
    "district",
    "ward_new",
    "road",
    "price_position",
    "land_use",
    "plot_shape",
    "business_advantage",
    "area_m2",
    "frontage_m",
    "length_m",
    "frontage_count",
    "distance_to_main_road_m",
    "alley_width_m",
    "construction_count",
]


OPTIONAL_INPUTS = ["ward_old", "road_segment", "other_factors"]


FORBIDDEN_INPUTS = [
    "target_price_vnd_m2",
    "target_log1p",
    "TSSS",
    "Giá trị định giá",
    "Giá trị đề xuất",
    "Đơn giá quyền sử dụng đất (đ/m2)",
]


BASE_NUMERIC_INPUTS = [
    "area_m2",
    "frontage_m",
    "length_m",
    "frontage_count",
    "distance_to_main_road_m",
    "alley_width_m",
    "construction_count",
]


QUALITY_FEATURES = [
    "quality_geometry_ratio_low",
    "quality_geometry_ratio_high",
    "quality_area_outside_review_range",
    "quality_frontage_outside_review_range",
    "quality_length_outside_review_range",
    "quality_access_outside_review_range",
]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_record(record):
    missing = [name for name in REQUIRED_INPUTS if name not in record or record[name] is None]
    forbidden = [name for name in FORBIDDEN_INPUTS if name in record]
    allowed = set(REQUIRED_INPUTS + OPTIONAL_INPUTS)
    unexpected = sorted(set(record) - allowed)
    if missing:
        raise ValueError(f"Missing required inputs: {missing}")
    if forbidden:
        raise ValueError(f"Forbidden target or leakage inputs: {forbidden}")
    if unexpected:
        raise ValueError(f"Unexpected inputs: {unexpected}")


def numeric_value(record, name):
    value = float(record[name])
    if not math.isfinite(value):
        raise ValueError(f"Non-finite numeric input: {name}")
    return value


def build_feature_frame(records):
    rows = []
    for record in records:
        validate_record(record)
        timestamp = pd.to_datetime(record["as_of_date"], format="%Y-%m-%d", errors="raise")
        area = numeric_value(record, "area_m2")
        frontage = numeric_value(record, "frontage_m")
        length = numeric_value(record, "length_m")
        frontage_count = numeric_value(record, "frontage_count")
        distance = numeric_value(record, "distance_to_main_road_m")
        alley = numeric_value(record, "alley_width_m")
        construction_count = numeric_value(record, "construction_count")
        if area <= 0 or frontage <= 0 or length <= 0:
            raise ValueError("Area, frontage and length must be positive")
        if frontage_count < 0 or distance < 0 or alley < 0 or construction_count < 0:
            raise ValueError("Counts, distance and alley width must be non-negative")
        other = strip_accents(record.get("other_factors"))
        rectangle = area / (frontage * length)
        base_month = pd.Timestamp("2024-03-01")
        month_index = (timestamp.year - base_month.year) * 12 + timestamp.month - base_month.month
        row = {
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
        }
        rows.append(row)
    return pd.DataFrame(rows)[CATEGORICAL_FEATURES + NUMERIC_FEATURES]


def prediction_intervals(predictions, calibration):
    log_prediction = np.log1p(np.maximum(np.asarray(predictions, dtype=float), 1.0))
    intervals = {}
    for level, values in calibration["levels"].items():
        qhat = float(values["qhat_log"])
        intervals[level] = {
            "lower": np.maximum(np.expm1(log_prediction - qhat), 1.0),
            "upper": np.expm1(log_prediction + qhat),
        }
    return intervals


def assess_feature_frame(frame, as_of_dates, predictions, primary_lower, primary_upper, profile, settings):
    results = []
    start = pd.Timestamp(settings["supported_as_of_start"])
    end = pd.Timestamp(settings["supported_as_of_end"])
    for index, row in frame.reset_index(drop=True).iterrows():
        reject = []
        review = []
        date = pd.Timestamp(as_of_dates[index])
        if date < start or date > end:
            reject.append("unsupported_as_of_date")
        if profile["category_counts"]["district"].get(str(row["district"]), 0) == 0:
            reject.append("unseen_district")
        for name in ["ward_new", "road", "price_position", "business_advantage"]:
            count = profile["category_counts"][name].get(str(row[name]), 0)
            if count == 0:
                review.append(f"unseen_{name}")
        road_count = profile["category_counts"]["road"].get(str(row["road"]), 0)
        if 0 < road_count < settings["road_rare_min_count"]:
            review.append("rare_road")
        ward_count = profile["category_counts"]["ward_new"].get(str(row["ward_new"]), 0)
        if 0 < ward_count < settings["ward_rare_min_count"]:
            review.append("rare_ward")
        for name, bounds in profile["numeric_limits"].items():
            value = float(row[name])
            if value < bounds["lower"] or value > bounds["upper"]:
                review.append(f"numeric_tail_{name}")
        if any(int(row[name]) == 1 for name in QUALITY_FEATURES):
            review.append("quality_rule_flag")
        if str(row["business_advantage"]) == "tot":
            review.append("sparse_business_advantage_tot")
        if float(predictions[index]) >= settings["high_price_review_vnd_m2"]:
            review.append("high_predicted_price")
        width_ratio = float((primary_upper[index] - primary_lower[index]) / max(predictions[index], 1.0))
        if width_ratio > settings["wide_interval_ratio"]:
            review.append("wide_prediction_interval")
        flags = sorted(set(reject + review))
        status = "reject" if reject else "manual_review" if review else "automatic"
        results.append({"status": status, "flags": flags, "interval_width_ratio": width_ratio})
    return results


def predict_records(records, model_path, profile_path, calibration_path, settings):
    frame = build_feature_frame(records)
    model = joblib.load(model_path)
    predictions = np.maximum(np.expm1(model.predict(frame)), 1.0)
    calibration = read_json(calibration_path)
    profile = read_json(profile_path)
    intervals = prediction_intervals(predictions, calibration)
    primary = str(settings["primary_interval_level"])
    decisions = assess_feature_frame(frame, [record["as_of_date"] for record in records], predictions, intervals[primary]["lower"], intervals[primary]["upper"], profile, settings)
    outputs = []
    for index, prediction in enumerate(predictions):
        interval_output = {}
        for level, values in intervals.items():
            interval_output[level] = {"lower_vnd_m2": float(values["lower"][index]), "upper_vnd_m2": float(values["upper"][index])}
        outputs.append({"prediction_vnd_m2": float(prediction), "prediction_intervals": interval_output, **decisions[index]})
    return outputs
