import math
import re
import unicodedata

import numpy as np
import pandas as pd


REQUIRED_INPUTS = [
    "as_of_date", "district", "ward_new", "road", "price_position", "land_use", "plot_shape", "business_advantage", "area_m2", "frontage_m", "length_m",
    "distance_to_main_road_m", "alley_width_m",
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
    return {"kem": "kem", "trung binh": "trung_binh", "kha": "kha", "tot": "tot"}.get(text, "khac")


def finite_positive(record, name):
    value = float(record[name])
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


def build_targets(records):
    rows = []
    for request_index, record in enumerate(records):
        missing = [name for name in REQUIRED_INPUTS if name not in record or record[name] is None]
        if missing:
            raise ValueError(f"Missing required inputs: {missing}")
        timestamp = pd.to_datetime(record["as_of_date"], format="%Y-%m-%d", errors="raise")
        rows.append({
            "as_of_date": timestamp.strftime("%Y-%m-%d"),
            "report_reference": str(record.get("report_reference", f"__request_{request_index}")),
            "district": normalize_text(record["district"]),
            "ward": normalize_text(record["ward_new"]),
            "road": normalize_text(record["road"]),
            "price_position": normalize_text(record["price_position"]),
            "land_use": canonical_land_use(record["land_use"]),
            "plot_shape": canonical_shape(record["plot_shape"]),
            "business_advantage": canonical_business_advantage(record["business_advantage"]),
            "area": finite_positive(record, "area_m2"),
            "frontage": finite_positive(record, "frontage_m"),
            "length": finite_positive(record, "length_m"),
            "distance": finite_positive(record, "distance_to_main_road_m") if float(record["distance_to_main_road_m"]) > 0 else 0.0,
            "alley": finite_positive(record, "alley_width_m") if float(record["alley_width_m"]) > 0 else 0.0,
        })
    return pd.DataFrame(rows)


def clean_market_source(source, settings):
    frame = source.loc[source["Phân loại kho"].eq("TSSS")].copy()
    frame["source_excel_row"] = frame.index.to_numpy() + 2
    frame["market_date"] = pd.to_datetime(frame["Thời điểm giao dịch/rao bán (đ)"], format=settings["market_date_format"], errors="coerce")
    frame["availability_date"] = pd.to_datetime(frame["Thời điểm hiệu lực"], format=settings["market_date_format"], errors="coerce")
    frame["age_at_collection"] = (frame["availability_date"] - frame["market_date"]).dt.days
    frame["area"] = pd.to_numeric(frame["Diện tích (m2)"], errors="coerce")
    frame["raw_unit"] = pd.to_numeric(frame["Giá giao dịch/rao bán (đ)"], errors="coerce") / frame["area"]
    frame["estimated_unit"] = pd.to_numeric(frame["Giá ước tính (đ)"], errors="coerce") / frame["area"]
    valid = frame["market_date"].notna() & frame["availability_date"].notna()
    valid &= frame["age_at_collection"].between(0, settings["maximum_market_age_at_collection_days"])
    valid &= frame["area"].gt(0)
    valid &= frame["raw_unit"].between(settings["market_unit_price_min"], settings["market_unit_price_max"])
    valid &= frame["estimated_unit"].between(settings["market_unit_price_min"], settings["market_unit_price_max"])
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
        "source_excel_row", "market_date", "availability_date", "report", "district", "ward", "road", "price_position", "land_use", "plot_shape", "business_advantage",
        "area", "frontage", "length", "distance", "alley", "raw_unit", "estimated_unit", "is_transaction",
    ]
    return frame[columns].reset_index(drop=True)


def log_ratio(left, right):
    if not np.isfinite(left) or not np.isfinite(right) or left <= 0 or right <= 0:
        return 1.0
    return abs(math.log(left / right))


def candidate_distance(target, market, indices, age, arrays=None):
    if arrays is None:
        arrays = {name: market[name].to_numpy() for name in market.columns}
    distance = age[indices] / 365.0 * 0.25
    same_road = arrays["road"][indices] == target["road"]
    same_ward = arrays["ward"][indices] == target["ward"]
    distance += np.where(same_road, 0.0, np.where(same_ward, 2.0, 4.0))
    distance += (arrays["price_position"][indices] != target["price_position"]) * 1.0
    distance += (arrays["business_advantage"][indices] != target["business_advantage"]) * 0.5
    distance += (arrays["land_use"][indices] != target["land_use"]) * 0.25
    distance += (arrays["plot_shape"][indices] != target["plot_shape"]) * 0.25
    for name, weight in [("area", 1.0), ("frontage", 0.5), ("length", 0.25), ("distance", 0.25), ("alley", 0.25)]:
        distance += np.asarray([log_ratio(value, float(target[name])) for value in arrays[name][indices]]) * weight
    return distance


def geographic_match(target, candidate):
    if candidate["road"] == target["road"] and candidate["ward"] == target["ward"] and candidate["district"] == target["district"]:
        return "same_road"
    if candidate["ward"] == target["ward"] and candidate["district"] == target["district"]:
        return "same_ward"
    if candidate["district"] == target["district"]:
        return "same_district"
    return "cross_district"


def difference_percent(candidate_value, target_value):
    if not np.isfinite(candidate_value) or not np.isfinite(target_value) or target_value <= 0:
        return None
    return float((candidate_value / target_value - 1.0) * 100.0)


def serialise_candidate(target, candidate, age_days, distance):
    location = geographic_match(target, candidate)
    score = float(100.0 * math.exp(-min(float(distance), 20.0) / 4.0))
    flags = []
    if location == "cross_district":
        flags.append("cross_district_fallback")
    if age_days > 180:
        flags.append("older_than_180_days")
    if score < 50.0:
        flags.append("low_rule_similarity")
    return {
        "comparable_reference": f"TSSS-{int(candidate['source_excel_row']):06d}",
        "market_date": pd.Timestamp(candidate["market_date"]).strftime("%Y-%m-%d"),
        "age_days": int(age_days),
        "market_type": "transaction" if int(candidate["is_transaction"]) else "listing",
        "raw_unit_price_vnd_m2": float(candidate["raw_unit"]),
        "estimated_unit_price_vnd_m2": float(candidate["estimated_unit"]),
        "rule_distance": float(distance),
        "rule_similarity_score_0_100": score,
        "geographic_match": location,
        "matches": {
            "price_position": bool(candidate["price_position"] == target["price_position"]),
            "business_advantage": bool(candidate["business_advantage"] == target["business_advantage"]),
            "land_use": bool(candidate["land_use"] == target["land_use"]),
            "plot_shape": bool(candidate["plot_shape"] == target["plot_shape"]),
        },
        "numeric_difference_vs_target_pct": {name: difference_percent(float(candidate[name]), float(target[name])) for name in ["area", "frontage", "length", "distance", "alley"]},
        "flags": flags,
    }


def retrieve_comparables(records, market_source, config, count=3):
    settings = config["comparable_retrieval"]
    if not int(settings["minimum_count"]) <= int(count) <= int(settings["maximum_count"]):
        raise ValueError(f"count must be between {settings['minimum_count']} and {settings['maximum_count']}")
    targets = build_targets(records)
    start = pd.Timestamp(settings["supported_as_of_start"])
    end = pd.Timestamp(settings["supported_as_of_end"])
    if all(pd.Timestamp(value) < start or pd.Timestamp(value) > end for value in targets["as_of_date"]):
        return [{"status": "reject", "flags": ["unsupported_as_of_date"], "requested_comparable_count": int(count), "comparables": []} for _ in range(len(targets))]
    market = clean_market_source(market_source, settings)
    market_days = market["market_date"].to_numpy(dtype="datetime64[D]").astype("int64")
    availability_days = market["availability_date"].to_numpy(dtype="datetime64[D]").astype("int64")
    reports = market["report"].to_numpy()
    districts = market["district"].to_numpy()
    outputs = []
    for _, target in targets.iterrows():
        date = pd.Timestamp(target["as_of_date"])
        if date < start or date > end:
            outputs.append({"status": "reject", "flags": ["unsupported_as_of_date"], "requested_comparable_count": int(count), "comparables": []})
            continue
        target_day = np.datetime64(date, "D").astype("int64")
        age = target_day - market_days
        eligible = (market_days < target_day) & (availability_days < target_day) & (age <= int(settings["maximum_market_window_days"])) & (reports != target["report_reference"])
        eligible_indices = np.flatnonzero(eligible)
        district_indices = eligible_indices[districts[eligible_indices] == target["district"]]
        fallback = len(district_indices) == 0
        candidates = eligible_indices if fallback else district_indices
        if len(candidates) == 0:
            outputs.append({"status": "manual_review", "flags": ["no_eligible_tsss_within_365d"], "requested_comparable_count": int(count), "comparables": []})
            continue
        distances = candidate_distance(target, market, candidates, age)
        order = np.argsort(distances)[:int(count)]
        chosen = candidates[order]
        comparables = [serialise_candidate(target, market.iloc[int(candidate_index)], age[candidate_index], distances[position]) for position, candidate_index in zip(order, chosen)]
        flags = []
        if fallback:
            flags.append("district_candidate_unavailable")
        if len(comparables) < int(count):
            flags.append("fewer_than_requested_comparables")
        if any("low_rule_similarity" in item["flags"] for item in comparables):
            flags.append("manual_similarity_review")
        if any("cross_district_fallback" in item["flags"] for item in comparables):
            flags.append("cross_district_comparable_present")
        outputs.append({
            "status": "manual_review" if flags else "automatic",
            "flags": flags,
            "requested_comparable_count": int(count),
            "returned_comparable_count": len(comparables),
            "as_of_date": target["as_of_date"],
            "maximum_market_window_days": int(settings["maximum_market_window_days"]),
            "comparables": comparables,
        })
    return outputs
