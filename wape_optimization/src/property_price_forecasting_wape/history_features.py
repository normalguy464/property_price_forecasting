from pathlib import Path
import json

import numpy as np
import pandas as pd


LEVELS = ["road", "ward", "district"]
METRICS = ["count", "median", "p25", "p75", "age_min"]


def feature_names(config):
    names = []
    for window in config["history_windows_days"]:
        for level in LEVELS:
            for metric in METRICS:
                names.append(f"history_{level}_{metric}_{window}d")
        names.extend([f"history_backoff_median_{window}d", f"history_backoff_count_{window}d", f"history_backoff_level_{window}d"])
    names.extend(["history_asset_count", "history_asset_last_price", "history_asset_age_days", "history_asset_previous_log_trend"])
    return names


def aggregate(indices, ages, target):
    if len(indices) == 0:
        return {"count": 0.0, "median": np.nan, "p25": np.nan, "p75": np.nan, "age_min": np.nan}
    values = target[indices]
    return {
        "count": float(len(indices)),
        "median": float(np.median(values)),
        "p25": float(np.quantile(values, 0.25)),
        "p75": float(np.quantile(values, 0.75)),
        "age_min": float(np.min(ages[indices])),
    }


def build_history_features(dataframe, config):
    dates = pd.to_datetime(dataframe["as_of_date"], format="%Y-%m-%d").to_numpy(dtype="datetime64[D]").astype("int64")
    target = dataframe["target_price_vnd_m2"].to_numpy(dtype=float)
    district = dataframe["district"].to_numpy()
    ward = dataframe["ward_new"].to_numpy()
    road = dataframe["road"].to_numpy()
    report = dataframe["report_group_id"].to_numpy()
    asset = dataframe["asset_group_id"].to_numpy()
    lag = int(config["label_availability_lag_days"])
    maximum_window = max(config["history_windows_days"])
    rows = []
    maximum_history_date = None
    for position in range(len(dataframe)):
        ages = dates[position] - dates
        eligible = ages > lag
        eligible &= ages <= maximum_window
        eligible &= report != report[position]
        eligible_indices = np.flatnonzero(eligible)
        if len(eligible_indices):
            current = int(dates[eligible_indices].max())
            maximum_history_date = current if maximum_history_date is None else max(maximum_history_date, current)
        row = {"source_excel_row": int(dataframe.iloc[position]["source_excel_row"])}
        for window in config["history_windows_days"]:
            window_indices = eligible_indices[ages[eligible_indices] <= window]
            levels = {
                "road": window_indices[(district[window_indices] == district[position]) & (ward[window_indices] == ward[position]) & (road[window_indices] == road[position])],
                "ward": window_indices[(district[window_indices] == district[position]) & (ward[window_indices] == ward[position])],
                "district": window_indices[district[window_indices] == district[position]],
                "global": window_indices,
            }
            values = {}
            for level in LEVELS:
                values[level] = aggregate(levels[level], ages, target)
                for metric, value in values[level].items():
                    row[f"history_{level}_{metric}_{window}d"] = value
            thresholds = {"road": config["history_road_min_count"], "ward": config["history_ward_min_count"], "district": config["history_district_min_count"], "global": 1}
            selected = "global"
            for level in ["road", "ward", "district", "global"]:
                if len(levels[level]) >= thresholds[level]:
                    selected = level
                    break
            selected_values = aggregate(levels[selected], ages, target)
            row[f"history_backoff_median_{window}d"] = selected_values["median"]
            row[f"history_backoff_count_{window}d"] = selected_values["count"]
            row[f"history_backoff_level_{window}d"] = float({"road": 0, "ward": 1, "district": 2, "global": 3}[selected])
        asset_indices = eligible_indices[asset[eligible_indices] == asset[position]]
        row["history_asset_count"] = float(len(asset_indices))
        if len(asset_indices):
            latest = asset_indices[np.argmin(ages[asset_indices])]
            row["history_asset_last_price"] = float(target[latest])
            row["history_asset_age_days"] = float(ages[latest])
            if len(asset_indices) >= 2:
                ordered = asset_indices[np.argsort(ages[asset_indices])]
                row["history_asset_previous_log_trend"] = float(np.log1p(target[ordered[0]]) - np.log1p(target[ordered[1]]))
            else:
                row["history_asset_previous_log_trend"] = np.nan
        else:
            row["history_asset_last_price"] = np.nan
            row["history_asset_age_days"] = np.nan
            row["history_asset_previous_log_trend"] = np.nan
        rows.append(row)
        if (position + 1) % 500 == 0:
            print(f"history_rows={position + 1}")
    output = pd.DataFrame(rows)[["source_excel_row"] + feature_names(config)]
    manifest = {
        "rows": int(len(output)),
        "feature_count": int(len(feature_names(config))),
        "features": feature_names(config),
        "label_availability_lag_days": lag,
        "maximum_history_date_used": None if maximum_history_date is None else str(np.datetime64(maximum_history_date, "D")),
        "rows_without_history_365d": int(output["history_backoff_count_365d"].eq(0).sum()),
        "rows_with_prior_asset": int(output["history_asset_count"].gt(0).sum()),
        "guards": ["history_label_date_plus_lag_strictly_before_target", "same_report_excluded", "maximum_365_day_window"],
    }
    return output, manifest


def write_artifacts(features, manifest, output_directory):
    output = Path(output_directory)
    compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
    features.to_json(output / "history_features.jsonl.gz", orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
    (output / "history_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
