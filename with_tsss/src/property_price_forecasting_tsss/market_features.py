from pathlib import Path
import json
import math

import numpy as np
import pandas as pd

from property_price_forecasting_tsss.normalization import canonical_business_advantage, canonical_land_use, canonical_shape, normalize_text


LEVELS = ["road", "ward", "district"]
AGGREGATE_METRICS = ["count", "raw_median", "estimated_median", "estimated_p25", "estimated_p75", "age_min"]


def clean_market_source(source, config):
    frame = source.loc[source["Phân loại kho"].eq("TSSS")].copy()
    frame["market_date"] = pd.to_datetime(frame["Thời điểm giao dịch/rao bán (đ)"], format=config["market_date_format"], errors="coerce")
    frame["availability_date"] = pd.to_datetime(frame["Thời điểm hiệu lực"], format=config["market_date_format"], errors="coerce")
    frame["age_at_collection"] = (frame["availability_date"] - frame["market_date"]).dt.days
    frame["area"] = pd.to_numeric(frame["Diện tích (m2)"], errors="coerce")
    frame["raw_unit"] = pd.to_numeric(frame["Giá giao dịch/rao bán (đ)"], errors="coerce") / frame["area"]
    frame["estimated_unit"] = pd.to_numeric(frame["Giá ước tính (đ)"], errors="coerce") / frame["area"]
    valid = frame["market_date"].notna() & frame["availability_date"].notna()
    valid &= frame["age_at_collection"].between(0, config["maximum_market_age_at_collection_days"])
    valid &= frame["area"].gt(0)
    valid &= frame["raw_unit"].between(config["market_unit_price_min"], config["market_unit_price_max"])
    valid &= frame["estimated_unit"].between(config["market_unit_price_min"], config["market_unit_price_max"])
    frame = frame.loc[valid].copy()
    frame["report"] = frame["Số báo cáo định giá"].astype(str)
    frame["district"] = frame["Thành phố/Quận/Huyện/Thị xã"].map(normalize_text)
    frame["ward"] = frame["Xã/Phường mới"].map(normalize_text)
    frame["road"] = frame["Đường phố"].map(normalize_text)
    frame["price_position"] = frame["Vị trí trong khung giá"].map(normalize_text)
    frame["land_use"] = frame["Mục đích sử dụng đất"].map(canonical_land_use)
    frame["plot_shape"] = frame["Hình dáng"].map(canonical_shape)
    frame["business_advantage"] = frame["Lợi thế kinh doanh"].map(canonical_business_advantage)
    frame["frontage"] = pd.to_numeric(frame["Kích thước mặt tiền (m)"], errors="coerce")
    frame["length"] = pd.to_numeric(frame["Kích thước chiều dài"], errors="coerce")
    frame["distance"] = pd.to_numeric(frame["Khoảng cách đến đường chính (m)"], errors="coerce")
    frame["alley"] = pd.to_numeric(frame["Độ rộng ngõ/ngách nhỏ nhất (Từ đường chính đến BĐS)"], errors="coerce")
    frame["is_transaction"] = frame["Tình trạng giao dịch"].eq("Đã giao dịch").astype("int8")
    columns = [
        "market_date", "availability_date", "report", "district", "ward", "road", "price_position", "land_use", "plot_shape", "business_advantage",
        "area", "frontage", "length", "distance", "alley", "raw_unit", "estimated_unit", "is_transaction",
    ]
    return frame[columns].reset_index(drop=True)


def feature_names(config):
    names = []
    for window in config["windows_days"]:
        for level in LEVELS:
            for metric in AGGREGATE_METRICS:
                names.append(f"market_{level}_{metric}_{window}d")
        names.extend([
            f"market_backoff_raw_median_{window}d",
            f"market_backoff_estimated_median_{window}d",
            f"market_backoff_count_{window}d",
            f"market_backoff_level_{window}d",
            f"market_district_transaction_count_{window}d",
            f"market_district_transaction_raw_median_{window}d",
            f"market_district_listing_count_{window}d",
            f"market_district_listing_raw_median_{window}d",
        ])
    names.extend([
        "comparable_count_365d",
        "comparable_weighted_raw_price_365d",
        "comparable_weighted_estimated_price_365d",
        "comparable_best_distance_365d",
        "comparable_weighted_age_days_365d",
        "comparable_same_road_share_365d",
        "comparable_same_ward_share_365d",
        "comparable_estimated_mad_365d",
    ])
    return names


def aggregate_values(indices, age, raw, estimated):
    if len(indices) == 0:
        return {"count": 0.0, "raw_median": np.nan, "estimated_median": np.nan, "estimated_p25": np.nan, "estimated_p75": np.nan, "age_min": np.nan}
    estimated_values = estimated[indices]
    return {
        "count": float(len(indices)),
        "raw_median": float(np.median(raw[indices])),
        "estimated_median": float(np.median(estimated_values)),
        "estimated_p25": float(np.quantile(estimated_values, 0.25)),
        "estimated_p75": float(np.quantile(estimated_values, 0.75)),
        "age_min": float(np.min(age[indices])),
    }


def safe_log_ratio(left, right):
    if not np.isfinite(left) or not np.isfinite(right) or left <= 0 or right <= 0:
        return 1.0
    return abs(math.log(left / right))


def comparable_values(indices, target, arrays, age, top_k):
    if len(indices) == 0:
        return [0.0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
    distance = age[indices] / 365.0 * 0.25
    same_road = arrays["road"][indices] == target["road"]
    same_ward = arrays["ward"][indices] == target["ward_new"]
    distance += np.where(same_road, 0.0, np.where(same_ward, 2.0, 4.0))
    distance += (arrays["price_position"][indices] != target["price_position"]) * 1.0
    distance += (arrays["business_advantage"][indices] != target["business_advantage"]) * 0.5
    distance += (arrays["land_use"][indices] != target["land_use"]) * 0.25
    distance += (arrays["plot_shape"][indices] != target["plot_shape"]) * 0.25
    for name, target_name, weight in [("area", "area_m2", 1.0), ("frontage", "frontage_m", 0.5), ("length", "length_m", 0.25), ("distance", "distance_to_main_road_m", 0.25), ("alley", "alley_width_m", 0.25)]:
        distance += np.asarray([safe_log_ratio(value, float(target[target_name])) for value in arrays[name][indices]]) * weight
    order = np.argsort(distance)[:top_k]
    chosen = indices[order]
    chosen_distance = distance[order]
    weights = np.exp(-np.minimum(chosen_distance, 20.0))
    weights = weights / weights.sum()
    raw_price = float(np.sum(arrays["raw_unit"][chosen] * weights))
    estimated_price = float(np.sum(arrays["estimated_unit"][chosen] * weights))
    weighted_age = float(np.sum(age[chosen] * weights))
    road_share = float(np.sum((arrays["road"][chosen] == target["road"]) * weights))
    ward_share = float(np.sum((arrays["ward"][chosen] == target["ward_new"]) * weights))
    estimated_mad = float(np.sum(np.abs(arrays["estimated_unit"][chosen] - estimated_price) * weights))
    return [float(len(chosen)), raw_price, estimated_price, float(chosen_distance.min()), weighted_age, road_share, ward_share, estimated_mad]


def build_market_features(base, source, config, target_reports=None):
    market = clean_market_source(source, config)
    raw_reports = pd.Series(source["Số báo cáo định giá"].astype(str).to_numpy(), index=source.index.to_numpy() + 2)
    arrays = {name: market[name].to_numpy() for name in market.columns}
    availability_days = market["availability_date"].to_numpy(dtype="datetime64[D]").astype("int64")
    market_days = market["market_date"].to_numpy(dtype="datetime64[D]").astype("int64")
    raw = market["raw_unit"].to_numpy(dtype=float)
    estimated = market["estimated_unit"].to_numpy(dtype=float)
    rows = []
    same_report_candidates_excluded = 0
    maximum_availability_used = None
    for position, target in base.iterrows():
        target_day = np.datetime64(target["as_of_date"], "D").astype("int64")
        target_report = raw_reports.loc[int(target["source_excel_row"])] if target_reports is None else str(target_reports[position])
        age = target_day - market_days
        available = availability_days < target_day
        historical = market_days < target_day
        within_maximum = age <= max(config["windows_days"])
        report_different = arrays["report"] != target_report
        same_report_candidates_excluded += int(np.sum(available & historical & within_maximum & ~report_different))
        eligible = available & historical & within_maximum & report_different
        eligible_indices = np.flatnonzero(eligible)
        if len(eligible_indices):
            current_max = int(availability_days[eligible_indices].max())
            maximum_availability_used = current_max if maximum_availability_used is None else max(maximum_availability_used, current_max)
        result = {"source_excel_row": int(target["source_excel_row"])}
        level_indices_by_window = {}
        for window in config["windows_days"]:
            window_indices = eligible_indices[age[eligible_indices] <= window]
            road_indices = window_indices[(arrays["district"][window_indices] == target["district"]) & (arrays["ward"][window_indices] == target["ward_new"]) & (arrays["road"][window_indices] == target["road"])]
            ward_indices = window_indices[(arrays["district"][window_indices] == target["district"]) & (arrays["ward"][window_indices] == target["ward_new"])]
            district_indices = window_indices[arrays["district"][window_indices] == target["district"]]
            level_indices_by_window[window] = {"road": road_indices, "ward": ward_indices, "district": district_indices, "global": window_indices}
            level_values = {}
            for level in LEVELS:
                values = aggregate_values(level_indices_by_window[window][level], age, raw, estimated)
                level_values[level] = values
                for metric, value in values.items():
                    result[f"market_{level}_{metric}_{window}d"] = value
            thresholds = {"road": config["road_min_count"], "ward": config["ward_min_count"], "district": config["district_min_count"], "global": 1}
            selected_level = "global"
            for level in ["road", "ward", "district", "global"]:
                if len(level_indices_by_window[window][level]) >= thresholds[level]:
                    selected_level = level
                    break
            selected_indices = level_indices_by_window[window][selected_level]
            selected_values = aggregate_values(selected_indices, age, raw, estimated)
            result[f"market_backoff_raw_median_{window}d"] = selected_values["raw_median"]
            result[f"market_backoff_estimated_median_{window}d"] = selected_values["estimated_median"]
            result[f"market_backoff_count_{window}d"] = selected_values["count"]
            result[f"market_backoff_level_{window}d"] = float({"road": 0, "ward": 1, "district": 2, "global": 3}[selected_level])
            district_indices = level_indices_by_window[window]["district"]
            transaction_indices = district_indices[arrays["is_transaction"][district_indices] == 1]
            listing_indices = district_indices[arrays["is_transaction"][district_indices] == 0]
            result[f"market_district_transaction_count_{window}d"] = float(len(transaction_indices))
            result[f"market_district_transaction_raw_median_{window}d"] = float(np.median(raw[transaction_indices])) if len(transaction_indices) else np.nan
            result[f"market_district_listing_count_{window}d"] = float(len(listing_indices))
            result[f"market_district_listing_raw_median_{window}d"] = float(np.median(raw[listing_indices])) if len(listing_indices) else np.nan
        comparable_pool = level_indices_by_window[max(config["windows_days"])]["district"]
        comparable = comparable_values(comparable_pool, target, arrays, age, config["comparable_top_k"])
        for name, value in zip(feature_names(config)[-8:], comparable):
            result[name] = value
        rows.append(result)
        if (position + 1) % 500 == 0:
            print(f"feature_rows={position + 1}")
    features = pd.DataFrame(rows)
    names = feature_names(config)
    features = features[["source_excel_row"] + names]
    manifest = {
        "base_rows": int(len(base)),
        "eligible_tsss_rows": int(len(market)),
        "market_feature_count": int(len(names)),
        "market_features": names,
        "same_report_candidates_excluded": int(same_report_candidates_excluded),
        "maximum_availability_date_used": None if maximum_availability_used is None else str(np.datetime64(maximum_availability_used, "D")),
        "rows_without_any_market_365d": int(features["market_backoff_count_365d"].eq(0).sum()),
        "rows_without_road_market_365d": int(features["market_road_count_365d"].eq(0).sum()),
        "leakage_guards": ["availability_date_strictly_before_target", "market_date_strictly_before_target", "same_report_excluded", "maximum_365_day_market_window"],
    }
    return features, manifest


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_features(path, dataframe):
    compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
    dataframe.to_json(path, orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)