import math

import numpy as np
import pandas as pd

from property_price_forecasting_tsss.inference import build_base_features
from property_price_forecasting_tsss.market_features import clean_market_source, safe_log_ratio


def clean_retrieval_source(source, config):
    source_with_reference = source.copy()
    source_with_reference["source_excel_row"] = source_with_reference.index.to_numpy() + 2
    market = clean_market_source(source_with_reference, config)
    valid_rows = source_with_reference.loc[source_with_reference["Phân loại kho"].eq("TSSS")].copy()
    valid_rows["market_date"] = pd.to_datetime(valid_rows["Thời điểm giao dịch/rao bán (đ)"], format=config["market_date_format"], errors="coerce")
    valid_rows["availability_date"] = pd.to_datetime(valid_rows["Thời điểm hiệu lực"], format=config["market_date_format"], errors="coerce")
    valid_rows["age_at_collection"] = (valid_rows["availability_date"] - valid_rows["market_date"]).dt.days
    valid_rows["area"] = pd.to_numeric(valid_rows["Diện tích (m2)"], errors="coerce")
    valid_rows["raw_unit"] = pd.to_numeric(valid_rows["Giá giao dịch/rao bán (đ)"], errors="coerce") / valid_rows["area"]
    valid_rows["estimated_unit"] = pd.to_numeric(valid_rows["Giá ước tính (đ)"], errors="coerce") / valid_rows["area"]
    valid = valid_rows["market_date"].notna() & valid_rows["availability_date"].notna()
    valid &= valid_rows["age_at_collection"].between(0, config["maximum_market_age_at_collection_days"])
    valid &= valid_rows["area"].gt(0)
    valid &= valid_rows["raw_unit"].between(config["market_unit_price_min"], config["market_unit_price_max"])
    valid &= valid_rows["estimated_unit"].between(config["market_unit_price_min"], config["market_unit_price_max"])
    references = valid_rows.loc[valid, "source_excel_row"].astype(int).to_numpy()
    market["comparable_reference"] = [f"TSSS-{value:06d}" for value in references]
    return market


def candidate_distances(target, market, candidate_indices, age):
    distance = age[candidate_indices] / 365.0 * 0.25
    same_road = market["road"].to_numpy()[candidate_indices] == target["road"]
    same_ward = market["ward"].to_numpy()[candidate_indices] == target["ward_new"]
    distance += np.where(same_road, 0.0, np.where(same_ward, 2.0, 4.0))
    distance += (market["price_position"].to_numpy()[candidate_indices] != target["price_position"]) * 1.0
    distance += (market["business_advantage"].to_numpy()[candidate_indices] != target["business_advantage"]) * 0.5
    distance += (market["land_use"].to_numpy()[candidate_indices] != target["land_use"]) * 0.25
    distance += (market["plot_shape"].to_numpy()[candidate_indices] != target["plot_shape"]) * 0.25
    for candidate_name, target_name, weight in [
        ("area", "area_m2", 1.0),
        ("frontage", "frontage_m", 0.5),
        ("length", "length_m", 0.25),
        ("distance", "distance_to_main_road_m", 0.25),
        ("alley", "alley_width_m", 0.25),
    ]:
        values = market[candidate_name].to_numpy()[candidate_indices]
        distance += np.asarray([safe_log_ratio(value, float(target[target_name])) for value in values]) * weight
    return distance


def numeric_difference_percent(candidate_value, target_value):
    if not np.isfinite(candidate_value) or not np.isfinite(target_value) or target_value <= 0:
        return None
    return float((candidate_value / target_value - 1.0) * 100.0)


def geographic_level(candidate, target):
    if candidate["road"] == target["road"] and candidate["ward"] == target["ward_new"] and candidate["district"] == target["district"]:
        return "same_road"
    if candidate["ward"] == target["ward_new"] and candidate["district"] == target["district"]:
        return "same_ward"
    if candidate["district"] == target["district"]:
        return "same_district"
    return "cross_district"


def serialise_candidate(candidate, target, age_days, distance):
    level = geographic_level(candidate, target)
    flags = []
    if level == "cross_district":
        flags.append("cross_district_fallback")
    if float(age_days) > 180:
        flags.append("older_than_180_days")
    similarity = float(100.0 * math.exp(-min(float(distance), 20.0) / 4.0))
    if similarity < 50.0:
        flags.append("low_rule_similarity")
    return {
        "comparable_reference": str(candidate["comparable_reference"]),
        "market_date": pd.Timestamp(candidate["market_date"]).strftime("%Y-%m-%d"),
        "age_days": int(age_days),
        "market_type": "transaction" if int(candidate["is_transaction"]) == 1 else "listing",
        "raw_unit_price_vnd_m2": float(candidate["raw_unit"]),
        "estimated_unit_price_vnd_m2": float(candidate["estimated_unit"]),
        "rule_distance": float(distance),
        "rule_similarity_score_0_100": similarity,
        "geographic_match": level,
        "matches": {
            "price_position": bool(candidate["price_position"] == target["price_position"]),
            "business_advantage": bool(candidate["business_advantage"] == target["business_advantage"]),
            "land_use": bool(candidate["land_use"] == target["land_use"]),
            "plot_shape": bool(candidate["plot_shape"] == target["plot_shape"]),
        },
        "numeric_difference_vs_target_pct": {
            "area": numeric_difference_percent(float(candidate["area"]), float(target["area_m2"])),
            "frontage": numeric_difference_percent(float(candidate["frontage"]), float(target["frontage_m"])),
            "length": numeric_difference_percent(float(candidate["length"]), float(target["length_m"])),
            "distance_to_main_road": numeric_difference_percent(float(candidate["distance"]), float(target["distance_to_main_road_m"])),
            "alley_width": numeric_difference_percent(float(candidate["alley"]), float(target["alley_width_m"])),
        },
        "flags": flags,
    }


def retrieve_comparables(records, market_source, config, count=3):
    settings = config["comparable_retrieval"]
    if not int(settings["minimum_count"]) <= int(count) <= int(settings["maximum_count"]):
        raise ValueError(f"count must be between {settings['minimum_count']} and {settings['maximum_count']}")
    input_records = []
    report_references = []
    for record in records:
        copied = dict(record)
        report_references.append(str(copied.pop("report_reference", f"__request_{len(report_references)}")))
        input_records.append(copied)
    base = build_base_features(input_records)
    start = pd.Timestamp(settings["supported_as_of_start"])
    end = pd.Timestamp(settings["supported_as_of_end"])
    if all(pd.Timestamp(value) < start or pd.Timestamp(value) > end for value in base["as_of_date"]):
        return [{
            "status": "reject",
            "flags": ["unsupported_as_of_date"],
            "requested_comparable_count": int(count),
            "comparables": [],
        } for _ in range(len(base))]
    market = clean_retrieval_source(market_source, config)
    market_dates = market["market_date"].to_numpy(dtype="datetime64[D]").astype("int64")
    availability_dates = market["availability_date"].to_numpy(dtype="datetime64[D]").astype("int64")
    reports = market["report"].to_numpy()
    maximum_window = int(settings["maximum_market_window_days"])
    outputs = []
    for request_index, target in base.iterrows():
        as_of_date = pd.Timestamp(target["as_of_date"])
        if as_of_date < start or as_of_date > end:
            outputs.append({
                "status": "reject",
                "flags": ["unsupported_as_of_date"],
                "requested_comparable_count": int(count),
                "comparables": [],
            })
            continue
        target_day = np.datetime64(as_of_date, "D").astype("int64")
        age = target_day - market_dates
        eligible = (availability_dates < target_day) & (market_dates < target_day) & (age <= maximum_window) & (reports != report_references[request_index])
        eligible_indices = np.flatnonzero(eligible)
        district_indices = eligible_indices[market["district"].to_numpy()[eligible_indices] == target["district"]]
        fallback = len(district_indices) == 0
        candidate_indices = eligible_indices if fallback else district_indices
        if len(candidate_indices) == 0:
            outputs.append({
                "status": "manual_review",
                "flags": ["no_eligible_tsss_within_365d"],
                "requested_comparable_count": int(count),
                "comparables": [],
            })
            continue
        distances = candidate_distances(target, market, candidate_indices, age)
        order = np.argsort(distances)[:int(count)]
        selected = candidate_indices[order]
        comparables = [serialise_candidate(market.iloc[int(candidate_index)], target, age[candidate_index], distances[position]) for position, candidate_index in zip(order, selected)]
        flags = []
        if fallback:
            flags.append("district_candidate_unavailable")
        if len(comparables) < int(count):
            flags.append("fewer_than_requested_comparables")
        if any("low_rule_similarity" in comparable["flags"] for comparable in comparables):
            flags.append("manual_similarity_review")
        if any("cross_district_fallback" in comparable["flags"] for comparable in comparables):
            flags.append("cross_district_comparable_present")
        outputs.append({
            "status": "manual_review" if flags else "automatic",
            "flags": flags,
            "requested_comparable_count": int(count),
            "returned_comparable_count": len(comparables),
            "as_of_date": target["as_of_date"],
            "maximum_market_window_days": maximum_window,
            "comparables": comparables,
        })
    return outputs
