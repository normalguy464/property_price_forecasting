from pathlib import Path
import json
import math

import numpy as np
import pandas as pd

from property_price_forecasting_wape.comparable_retrieval import candidate_distance, clean_market_source


def price_metrics(target, prediction):
    target = np.asarray(target, dtype=float)
    prediction = np.maximum(np.asarray(prediction, dtype=float), 1.0)
    absolute = np.abs(prediction - target)
    percentage = absolute / np.maximum(target, 1.0)
    return {
        "rows": int(len(target)),
        "mae_vnd_m2": float(absolute.mean()),
        "wape": float(absolute.sum() / target.sum()),
        "mape": float(percentage.mean()),
        "mdape": float(np.median(percentage)),
        "within_10pct": float((percentage <= 0.10).mean()),
        "within_20pct": float((percentage <= 0.20).mean()),
        "within_30pct": float((percentage <= 0.30).mean()),
    }


def quantiles(values):
    array = np.asarray(values, dtype=float)
    if len(array) == 0:
        return {"min": None, "p25": None, "median": None, "p75": None, "p90": None, "max": None}
    return {
        "min": float(np.min(array)),
        "p25": float(np.quantile(array, 0.25)),
        "median": float(np.median(array)),
        "p75": float(np.quantile(array, 0.75)),
        "p90": float(np.quantile(array, 0.90)),
        "max": float(np.max(array)),
    }


def targets_from_base(base, source):
    report_by_excel_row = pd.Series(source["Số báo cáo định giá"].astype(str).to_numpy(), index=source.index.to_numpy() + 2)
    rows = []
    for _, row in base.iterrows():
        rows.append({
            "as_of_date": row["as_of_date"],
            "report_reference": report_by_excel_row.loc[int(row["source_excel_row"])],
            "district": row["district"],
            "ward": row["ward_new"],
            "road": row["road"],
            "price_position": row["price_position"],
            "land_use": row["land_use"],
            "plot_shape": row["plot_shape"],
            "business_advantage": row["business_advantage"],
            "area": row["area_m2"],
            "frontage": row["frontage_m"],
            "length": row["length_m"],
            "distance": row["distance_to_main_road_m"],
            "alley": row["alley_width_m"],
        })
    return pd.DataFrame(rows)


def duplicate_signature(frame):
    return list(zip(
        frame["market_date"].astype(str), frame["district"], frame["ward"], frame["road"], frame["price_position"], frame["land_use"], frame["plot_shape"],
        frame["business_advantage"], frame["area"].round(6), frame["frontage"].round(6), frame["length"].round(6), frame["distance"].round(6), frame["alley"].round(6),
        frame["raw_unit"].round(6), frame["estimated_unit"].round(6),
    ))


def safe_mean(values):
    return None if len(values) == 0 else float(np.mean(values))


def build_retrieval_quality_report(base, source, config, progress=None):
    settings = config["comparable_retrieval"]
    report_settings = config["retrieval_quality_report"]
    top_k = int(report_settings["top_k"])
    older_than_days = int(report_settings["older_than_days"])
    targets = targets_from_base(base, source)
    market = clean_market_source(source, settings)
    market_days = market["market_date"].to_numpy(dtype="datetime64[D]").astype("int64")
    availability_days = market["availability_date"].to_numpy(dtype="datetime64[D]").astype("int64")
    reports = market["report"].to_numpy()
    districts = market["district"].to_numpy()
    arrays = {name: market[name].to_numpy() for name in market.columns}
    district_index = {district: np.flatnonzero(districts == district) for district in pd.unique(districts)}
    rows = []
    for position, target in targets.iterrows():
        target_day = np.datetime64(target["as_of_date"], "D").astype("int64")
        age = target_day - market_days
        district_candidates = district_index.get(target["district"], np.empty(0, dtype=int))
        district_eligible = district_candidates[(market_days[district_candidates] < target_day) & (availability_days[district_candidates] < target_day) & (age[district_candidates] <= int(settings["maximum_market_window_days"])) & (reports[district_candidates] != target["report_reference"])]
        fallback = len(district_eligible) == 0
        if fallback:
            candidates = np.flatnonzero((market_days < target_day) & (availability_days < target_day) & (age <= int(settings["maximum_market_window_days"])) & (reports != target["report_reference"]))
        else:
            candidates = district_eligible
        result = {"row_index": int(position), "as_of_date": target["as_of_date"], "target": float(base.iloc[position]["target_price_vnd_m2"]), "eligible_candidate_count": int(len(candidates)), "district_fallback": int(fallback)}
        if len(candidates) == 0:
            result.update({"selected_count": 0, "top1_score": np.nan, "mean_score": np.nan, "min_score": np.nan, "weighted_raw_prediction": np.nan, "weighted_estimated_prediction": np.nan})
            rows.append(result)
            continue
        distances = candidate_distance(target, market, candidates, age, arrays)
        order = np.argsort(distances)[:top_k]
        chosen = candidates[order]
        selected = market.iloc[chosen].copy()
        selected_age = age[chosen]
        selected_distance = distances[order]
        selected_score = 100.0 * np.exp(-np.minimum(selected_distance, 20.0) / 4.0)
        weights = np.exp(-np.minimum(selected_distance, 20.0))
        weights = weights / weights.sum()
        geography = np.select(
            [selected["road"].to_numpy() == target["road"], selected["ward"].to_numpy() == target["ward"]],
            ["same_road", "same_ward"],
            default="same_district" if not fallback else "cross_district",
        )
        signatures = duplicate_signature(selected)
        duplicate_share = 1.0 - len(set(signatures)) / len(signatures)
        result.update({
            "selected_count": int(len(selected)),
            "top1_score": float(selected_score[0]),
            "mean_score": float(selected_score.mean()),
            "min_score": float(selected_score.min()),
            "mean_age_days": float(selected_age.mean()),
            "older_than_threshold_share": float((selected_age > older_than_days).mean()),
            "same_road_share": float((geography == "same_road").mean()),
            "same_ward_share": float((geography == "same_ward").mean()),
            "same_district_share": float((geography == "same_district").mean()),
            "cross_district_share": float((geography == "cross_district").mean()),
            "price_position_match_share": float((selected["price_position"].to_numpy() == target["price_position"]).mean()),
            "business_advantage_match_share": float((selected["business_advantage"].to_numpy() == target["business_advantage"]).mean()),
            "land_use_match_share": float((selected["land_use"].to_numpy() == target["land_use"]).mean()),
            "plot_shape_match_share": float((selected["plot_shape"].to_numpy() == target["plot_shape"]).mean()),
            "duplicate_candidate_share": float(duplicate_share),
            "raw_price_relative_spread": float(np.std(selected["raw_unit"].to_numpy()) / np.mean(selected["raw_unit"].to_numpy())),
            "estimated_price_relative_spread": float(np.std(selected["estimated_unit"].to_numpy()) / np.mean(selected["estimated_unit"].to_numpy())),
            "weighted_raw_prediction": float(np.sum(selected["raw_unit"].to_numpy() * weights)),
            "weighted_estimated_prediction": float(np.sum(selected["estimated_unit"].to_numpy() * weights)),
        })
        rows.append(result)
        if progress is not None and (position + 1) % 500 == 0:
            progress(position + 1, len(targets))
    detail = pd.DataFrame(rows)
    covered = detail.loc[detail["selected_count"].gt(0)].copy()
    score_bands = report_settings["score_bands"]
    covered["score_band"] = pd.cut(covered["mean_score"], bins=[-np.inf, *score_bands, np.inf], labels=[f"below_{score_bands[0]}", f"{score_bands[0]}_to_{score_bands[1]}", f"at_least_{score_bands[1]}"], right=False)
    band_metrics = {}
    for band, frame in covered.groupby("score_band", observed=False):
        if len(frame) == 0:
            continue
        band_metrics[str(band)] = {
            "rows": int(len(frame)),
            "mean_score": float(frame["mean_score"].mean()),
            "weighted_raw": price_metrics(frame["target"], frame["weighted_raw_prediction"]),
            "weighted_estimated": price_metrics(frame["target"], frame["weighted_estimated_prediction"]),
        }
    report = {
        "scope": {"target_rows": int(len(base)), "market_source_rows_after_cleaning": int(len(market)), "top_k": top_k, "maximum_market_window_days": int(settings["maximum_market_window_days"]), "historical_evaluation": True},
        "leakage_guards": ["market_date_strictly_before_target", "availability_date_strictly_before_target", "same_report_excluded", "maximum_365_day_market_window"],
        "coverage": {
            "rows_with_at_least_one_tsss": int(len(covered)),
            "coverage_rate": float(len(covered) / len(detail)),
            "rows_with_full_top_k": int(covered["selected_count"].eq(top_k).sum()),
            "full_top_k_rate": float(covered["selected_count"].eq(top_k).mean()),
            "district_fallback_rows": int(detail["district_fallback"].sum()),
        },
        "score": {"top1": quantiles(covered["top1_score"]), "top_k_mean": quantiles(covered["mean_score"]), "top_k_min": quantiles(covered["min_score"]), "band_counts": {str(key): int(value) for key, value in covered["score_band"].value_counts(dropna=False).items()}},
        "candidate_quality": {
            "mean_age_days": safe_mean(covered["mean_age_days"]), "mean_share_older_than_threshold": safe_mean(covered["older_than_threshold_share"]),
            "mean_same_road_share": safe_mean(covered["same_road_share"]), "mean_same_ward_share": safe_mean(covered["same_ward_share"]), "mean_same_district_share": safe_mean(covered["same_district_share"]),
            "mean_cross_district_share": safe_mean(covered["cross_district_share"]), "mean_price_position_match_share": safe_mean(covered["price_position_match_share"]),
            "mean_business_advantage_match_share": safe_mean(covered["business_advantage_match_share"]), "mean_land_use_match_share": safe_mean(covered["land_use_match_share"]),
            "mean_plot_shape_match_share": safe_mean(covered["plot_shape_match_share"]), "mean_duplicate_candidate_share": safe_mean(covered["duplicate_candidate_share"]),
            "mean_raw_price_relative_spread": safe_mean(covered["raw_price_relative_spread"]), "mean_estimated_price_relative_spread": safe_mean(covered["estimated_price_relative_spread"]),
        },
        "historical_price_backtest": {"weighted_raw_top_k": price_metrics(covered["target"], covered["weighted_raw_prediction"]), "weighted_estimated_top_k": price_metrics(covered["target"], covered["weighted_estimated_prediction"]), "by_mean_score_band": band_metrics},
        "interpretation": ["Score measures rule similarity, not verified valuation accuracy.", "Historical price backtest uses target labels only for evaluation and never as retrieval input.", "Weighted comparable prices are diagnostic baselines, not the WAPE ensemble prediction or an approved adjusted valuation."],
    }
    return detail, report


def write_retrieval_report(detail, report, artifact_directory, suffix=""):
    artifact_directory = Path(artifact_directory)
    compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
    detail.to_json(artifact_directory / f"retrieval_quality_rows{suffix}.jsonl.gz", orient="records", lines=True, compression=compression, double_precision=15)
    (artifact_directory / f"retrieval_quality_report{suffix}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
