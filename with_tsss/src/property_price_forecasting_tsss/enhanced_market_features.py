from pathlib import Path
import json
import math

import numpy as np
import pandas as pd

from property_price_forecasting_tsss.market_features import clean_market_source, safe_log_ratio


COMPARABLE_V2_FEATURES = [
    "comparable_v2_count_365d",
    "comparable_v2_weighted_raw_price_365d",
    "comparable_v2_weighted_estimated_price_365d",
    "comparable_v2_raw_median_365d",
    "comparable_v2_estimated_median_365d",
    "comparable_v2_estimated_p25_365d",
    "comparable_v2_estimated_p75_365d",
    "comparable_v2_best_distance_365d",
    "comparable_v2_weighted_age_days_365d",
    "comparable_v2_same_road_share_365d",
    "comparable_v2_same_ward_share_365d",
    "comparable_v2_transaction_share_365d",
    "comparable_v2_effective_sample_size_365d",
    "comparable_v2_estimated_mad_365d",
    "comparable_v2_estimated_to_raw_ratio_365d",
]


TEMPORAL_MARKET_FEATURES = [
    "market_backoff_raw_log_trend_90_365",
    "market_backoff_estimated_log_trend_90_365",
    "market_backoff_raw_log_trend_180_365",
    "market_backoff_estimated_log_trend_180_365",
    "market_district_raw_log_trend_90_365",
    "market_district_estimated_log_trend_90_365",
    "market_district_raw_log_trend_180_365",
    "market_district_estimated_log_trend_180_365",
    "market_road_estimated_log_trend_90_365",
    "market_ward_estimated_log_trend_90_365",
    "market_road_activity_rate_ratio_90_365",
    "market_ward_activity_rate_ratio_90_365",
    "market_district_activity_rate_ratio_90_365",
    "market_district_transaction_share_365",
    "market_district_transaction_listing_log_gap_365",
    "market_district_estimated_iqr_ratio_90",
    "market_district_estimated_iqr_ratio_365",
    "market_backoff_level_changed_90_365",
]


def weighted_comparable_values(indices, target, arrays, age, config):
    if len(indices) == 0:
        return [0.0] + [np.nan] * (len(COMPARABLE_V2_FEATURES) - 1)
    settings = config["enhanced_comparable"]
    current_age = age[indices].astype(float)
    same_road = arrays["road"][indices] == target["road"]
    same_ward = arrays["ward"][indices] == target["ward_new"]
    distance = current_age / 365.0 * settings["recency_distance_weight"]
    distance += np.where(same_road, 0.0, np.where(same_ward, 1.5, 3.0))
    distance += (arrays["price_position"][indices] != target["price_position"]) * 1.25
    distance += (arrays["business_advantage"][indices] != target["business_advantage"]) * 0.75
    distance += (arrays["land_use"][indices] != target["land_use"]) * 0.5
    distance += (arrays["plot_shape"][indices] != target["plot_shape"]) * 0.25
    specifications = [
        ("area", "area_m2", 1.5),
        ("frontage", "frontage_m", 0.75),
        ("length", "length_m", 0.4),
        ("distance", "distance_to_main_road_m", 0.5),
        ("alley", "alley_width_m", 0.5),
    ]
    for name, target_name, weight in specifications:
        differences = np.asarray([safe_log_ratio(value, float(target[target_name])) for value in arrays[name][indices]])
        distance += differences * weight
    order = np.argsort(distance)[:settings["top_k"]]
    chosen = indices[order]
    chosen_distance = distance[order]
    chosen_age = age[chosen].astype(float)
    weights = np.exp(-chosen_distance / settings["distance_temperature"])
    weights *= np.exp(-math.log(2.0) * chosen_age / settings["recency_half_life_days"])
    weights *= 1.0 + arrays["is_transaction"][chosen] * settings["transaction_weight_boost"]
    weights = weights / weights.sum()
    raw_values = arrays["raw_unit"][chosen].astype(float)
    estimated_values = arrays["estimated_unit"][chosen].astype(float)
    weighted_raw = float(np.sum(raw_values * weights))
    weighted_estimated = float(np.sum(estimated_values * weights))
    estimated_mad = float(np.sum(np.abs(estimated_values - weighted_estimated) * weights))
    ratio = weighted_estimated / weighted_raw if weighted_raw > 0 else np.nan
    return [
        float(len(chosen)),
        weighted_raw,
        weighted_estimated,
        float(np.median(raw_values)),
        float(np.median(estimated_values)),
        float(np.quantile(estimated_values, 0.25)),
        float(np.quantile(estimated_values, 0.75)),
        float(chosen_distance.min()),
        float(np.sum(chosen_age * weights)),
        float(np.sum((arrays["road"][chosen] == target["road"]) * weights)),
        float(np.sum((arrays["ward"][chosen] == target["ward_new"]) * weights)),
        float(np.sum(arrays["is_transaction"][chosen] * weights)),
        float(1.0 / np.sum(weights ** 2)),
        estimated_mad,
        float(ratio),
    ]


def log_ratio(left, right):
    left = pd.to_numeric(left, errors="coerce").to_numpy(dtype=float)
    right = pd.to_numeric(right, errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(left) & np.isfinite(right) & (left > 0) & (right > 0)
    output = np.full(len(left), np.nan, dtype=float)
    output[valid] = np.log(left[valid] / right[valid])
    return output


def rate_ratio(recent_count, historical_count, recent_days, historical_days):
    recent = pd.to_numeric(recent_count, errors="coerce").to_numpy(dtype=float)
    historical = pd.to_numeric(historical_count, errors="coerce").to_numpy(dtype=float)
    output = np.full(len(recent), np.nan, dtype=float)
    valid = historical > 0
    output[valid] = np.clip((recent[valid] / recent_days) / (historical[valid] / historical_days), 0.0, 4.0)
    return output


def iqr_ratio(p25, p75, median):
    p25_values = pd.to_numeric(p25, errors="coerce").to_numpy(dtype=float)
    p75_values = pd.to_numeric(p75, errors="coerce").to_numpy(dtype=float)
    median_values = pd.to_numeric(median, errors="coerce").to_numpy(dtype=float)
    output = np.full(len(median_values), np.nan, dtype=float)
    valid = np.isfinite(p25_values) & np.isfinite(p75_values) & (median_values > 0)
    output[valid] = (p75_values[valid] - p25_values[valid]) / median_values[valid]
    return output


def build_temporal_market_features(market_features):
    source = market_features
    output = pd.DataFrame({"source_excel_row": source["source_excel_row"].to_numpy()})
    for level in ["backoff", "district"]:
        for price_type in ["raw", "estimated"]:
            for recent in [90, 180]:
                name = f"market_{level}_{price_type}_log_trend_{recent}_365"
                output[name] = log_ratio(source[f"market_{level}_{price_type}_median_{recent}d"], source[f"market_{level}_{price_type}_median_365d"])
    output["market_road_estimated_log_trend_90_365"] = log_ratio(source["market_road_estimated_median_90d"], source["market_road_estimated_median_365d"])
    output["market_ward_estimated_log_trend_90_365"] = log_ratio(source["market_ward_estimated_median_90d"], source["market_ward_estimated_median_365d"])
    for level in ["road", "ward", "district"]:
        output[f"market_{level}_activity_rate_ratio_90_365"] = rate_ratio(source[f"market_{level}_count_90d"], source[f"market_{level}_count_365d"], 90.0, 365.0)
    transactions = source["market_district_transaction_count_365d"].to_numpy(dtype=float)
    listings = source["market_district_listing_count_365d"].to_numpy(dtype=float)
    total = transactions + listings
    output["market_district_transaction_share_365"] = np.divide(transactions, total, out=np.zeros_like(transactions), where=total > 0)
    output["market_district_transaction_listing_log_gap_365"] = log_ratio(source["market_district_transaction_raw_median_365d"], source["market_district_listing_raw_median_365d"])
    for window in [90, 365]:
        output[f"market_district_estimated_iqr_ratio_{window}"] = iqr_ratio(
            source[f"market_district_estimated_p25_{window}d"],
            source[f"market_district_estimated_p75_{window}d"],
            source[f"market_district_estimated_median_{window}d"],
        )
    output["market_backoff_level_changed_90_365"] = (source["market_backoff_level_90d"].to_numpy() != source["market_backoff_level_365d"].to_numpy()).astype(float)
    return output[["source_excel_row"] + TEMPORAL_MARKET_FEATURES]


def build_enhanced_market_features(base, source, current_market_features, config, target_reports=None):
    market = clean_market_source(source, config)
    raw_reports = pd.Series(source["Số báo cáo định giá"].astype(str).to_numpy(), index=source.index.to_numpy() + 2)
    arrays = {name: market[name].to_numpy() for name in market.columns}
    availability_days = market["availability_date"].to_numpy(dtype="datetime64[D]").astype("int64")
    market_days = market["market_date"].to_numpy(dtype="datetime64[D]").astype("int64")
    rows = []
    maximum_availability_used = None
    for position, target in base.iterrows():
        target_day = np.datetime64(target["as_of_date"], "D").astype("int64")
        target_report = raw_reports.loc[int(target["source_excel_row"])] if target_reports is None else str(target_reports[position])
        age = target_day - market_days
        eligible = availability_days < target_day
        eligible &= market_days < target_day
        eligible &= age <= 365
        eligible &= arrays["report"] != target_report
        eligible &= arrays["district"] == target["district"]
        indices = np.flatnonzero(eligible)
        if len(indices):
            current_max = int(availability_days[indices].max())
            maximum_availability_used = current_max if maximum_availability_used is None else max(maximum_availability_used, current_max)
        values = weighted_comparable_values(indices, target, arrays, age, config)
        rows.append({"source_excel_row": int(target["source_excel_row"]), **dict(zip(COMPARABLE_V2_FEATURES, values))})
        if (position + 1) % 500 == 0:
            print(f"enhanced_feature_rows={position + 1}")
    comparable = pd.DataFrame(rows)
    temporal = build_temporal_market_features(current_market_features)
    if not comparable["source_excel_row"].equals(temporal["source_excel_row"]):
        raise RuntimeError("Enhanced comparable and temporal feature alignment failed")
    features = comparable.merge(temporal, on="source_excel_row", validate="one_to_one")
    names = COMPARABLE_V2_FEATURES + TEMPORAL_MARKET_FEATURES
    manifest = {
        "base_rows": int(len(base)),
        "eligible_tsss_rows": int(len(market)),
        "enhanced_feature_count": int(len(names)),
        "comparable_v2_feature_count": int(len(COMPARABLE_V2_FEATURES)),
        "temporal_market_feature_count": int(len(TEMPORAL_MARKET_FEATURES)),
        "comparable_v2_features": COMPARABLE_V2_FEATURES,
        "temporal_market_features": TEMPORAL_MARKET_FEATURES,
        "enhanced_features": names,
        "maximum_availability_date_used": None if maximum_availability_used is None else str(np.datetime64(maximum_availability_used, "D")),
        "rows_without_comparable_v2": int(features["comparable_v2_count_365d"].eq(0).sum()),
        "leakage_guards": ["availability_date_strictly_before_target", "market_date_strictly_before_target", "same_report_excluded", "maximum_365_day_market_window"],
    }
    return features[["source_excel_row"] + names], manifest


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_features(path, dataframe):
    compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
    dataframe.to_json(path, orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
