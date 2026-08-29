import math

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

from property_price_forecasting_tsss.market_features import clean_market_source


PAIR_CATEGORICAL_FEATURES = [
    "target_district", "target_ward", "target_road", "target_price_position", "target_land_use", "target_plot_shape", "target_business_advantage",
    "candidate_district", "candidate_ward", "candidate_road", "candidate_price_position", "candidate_land_use", "candidate_plot_shape", "candidate_business_advantage",
]

PAIR_NUMERIC_FEATURES = [
    "candidate_age_days", "candidate_raw_log", "candidate_estimated_log", "candidate_is_transaction", "base_distance",
    "same_district", "same_ward", "same_road", "same_price_position", "same_land_use", "same_plot_shape", "same_business_advantage",
    "log_area_ratio", "log_frontage_ratio", "log_length_ratio", "log_distance_ratio", "log_alley_ratio", "target_month_index",
]

PAIR_FEATURES = PAIR_CATEGORICAL_FEATURES + PAIR_NUMERIC_FEATURES


def signed_log_ratio(target_value, candidate_value):
    target_number = float(target_value)
    candidate_number = float(candidate_value)
    if not np.isfinite(target_number) or not np.isfinite(candidate_number) or target_number <= 0 or candidate_number <= 0:
        return 0.0
    return float(math.log(target_number / candidate_number))


def candidate_pool_features(base, source, config):
    market = clean_market_source(source, config)
    report_by_excel_row = pd.Series(source["Số báo cáo định giá"].astype(str).to_numpy(), index=source.index.to_numpy() + 2)
    arrays = {name: market[name].to_numpy() for name in market.columns}
    availability_days = market["availability_date"].to_numpy(dtype="datetime64[D]").astype("int64")
    market_days = market["market_date"].to_numpy(dtype="datetime64[D]").astype("int64")
    rows = []
    rows_without_district_candidate = 0
    same_report_candidates_excluded = 0
    top_pool = int(config["learned_comparable"]["candidate_pool_size"])
    max_days = int(config["learned_comparable"]["maximum_market_window_days"])
    for row_index, target in base.iterrows():
        target_day = np.datetime64(target["as_of_date"], "D").astype("int64")
        age = target_day - market_days
        target_report = report_by_excel_row.loc[int(target["source_excel_row"])]
        eligible = (availability_days < target_day) & (market_days < target_day) & (age <= max_days) & (arrays["report"] != target_report)
        same_report_candidates_excluded += int(np.sum((availability_days < target_day) & (market_days < target_day) & (age <= max_days) & (arrays["report"] == target_report)))
        eligible_indices = np.flatnonzero(eligible)
        district_indices = eligible_indices[arrays["district"][eligible_indices] == target["district"]]
        if len(district_indices) == 0:
            rows_without_district_candidate += 1
            candidate_indices = eligible_indices
        else:
            candidate_indices = district_indices
        if len(candidate_indices) == 0:
            continue
        distance = age[candidate_indices] / 365.0 * 0.25
        same_road = arrays["road"][candidate_indices] == target["road"]
        same_ward = arrays["ward"][candidate_indices] == target["ward_new"]
        distance += np.where(same_road, 0.0, np.where(same_ward, 2.0, 4.0))
        distance += (arrays["price_position"][candidate_indices] != target["price_position"]) * 1.0
        distance += (arrays["business_advantage"][candidate_indices] != target["business_advantage"]) * 0.5
        distance += (arrays["land_use"][candidate_indices] != target["land_use"]) * 0.25
        distance += (arrays["plot_shape"][candidate_indices] != target["plot_shape"]) * 0.25
        ratio_specs = [("area", "area_m2", 1.0), ("frontage", "frontage_m", 0.5), ("length", "length_m", 0.25), ("distance", "distance_to_main_road_m", 0.25), ("alley", "alley_width_m", 0.25)]
        ratios = {}
        for name, target_name, weight in ratio_specs:
            values = np.asarray([signed_log_ratio(target[target_name], value) for value in arrays[name][candidate_indices]])
            ratios[name] = values
            distance += np.abs(values) * weight
        order = np.argsort(distance)[:top_pool]
        selected = candidate_indices[order]
        for local_position, candidate_index in enumerate(selected):
            candidate = market.iloc[int(candidate_index)]
            raw_unit = float(candidate["raw_unit"])
            target_unit = float(target["target_price_vnd_m2"])
            rows.append({
                "row_index": int(row_index),
                "candidate_rank_by_rule": int(local_position + 1),
                "target": target_unit,
                "candidate_raw_unit": raw_unit,
                "candidate_age_days": float(age[candidate_index]),
                "candidate_raw_log": float(math.log1p(raw_unit)),
                "candidate_estimated_log": float(math.log1p(float(candidate["estimated_unit"]))),
                "candidate_is_transaction": float(candidate["is_transaction"]),
                "base_distance": float(distance[order[local_position]]),
                "same_district": float(candidate["district"] == target["district"]),
                "same_ward": float(candidate["ward"] == target["ward_new"]),
                "same_road": float(candidate["road"] == target["road"]),
                "same_price_position": float(candidate["price_position"] == target["price_position"]),
                "same_land_use": float(candidate["land_use"] == target["land_use"]),
                "same_plot_shape": float(candidate["plot_shape"] == target["plot_shape"]),
                "same_business_advantage": float(candidate["business_advantage"] == target["business_advantage"]),
                "log_area_ratio": float(ratios["area"][order[local_position]]),
                "log_frontage_ratio": float(ratios["frontage"][order[local_position]]),
                "log_length_ratio": float(ratios["length"][order[local_position]]),
                "log_distance_ratio": float(ratios["distance"][order[local_position]]),
                "log_alley_ratio": float(ratios["alley"][order[local_position]]),
                "target_month_index": float(pd.Timestamp(target["as_of_date"]).year * 12 + pd.Timestamp(target["as_of_date"]).month),
                "target_district": target["district"],
                "target_ward": target["ward_new"],
                "target_road": target["road"],
                "target_price_position": target["price_position"],
                "target_land_use": target["land_use"],
                "target_plot_shape": target["plot_shape"],
                "target_business_advantage": target["business_advantage"],
                "candidate_district": candidate["district"],
                "candidate_ward": candidate["ward"],
                "candidate_road": candidate["road"],
                "candidate_price_position": candidate["price_position"],
                "candidate_land_use": candidate["land_use"],
                "candidate_plot_shape": candidate["plot_shape"],
                "candidate_business_advantage": candidate["business_advantage"],
                "adjustment_log": float(math.log(target_unit / raw_unit)),
            })
    pairs = pd.DataFrame(rows)
    if len(pairs) == 0:
        raise RuntimeError("No eligible TSSS comparable pairs")
    pairs["absolute_adjustment_log"] = pairs["adjustment_log"].abs()
    manifest = {
        "target_rows": int(len(base)),
        "pair_rows": int(len(pairs)),
        "target_rows_with_pairs": int(pairs["row_index"].nunique()),
        "target_rows_without_pairs": int(len(base) - pairs["row_index"].nunique()),
        "rows_without_district_candidate": int(rows_without_district_candidate),
        "same_report_candidates_excluded": int(same_report_candidates_excluded),
        "candidate_pool_size": top_pool,
        "maximum_market_window_days": max_days,
        "leakage_guards": ["availability_date_strictly_before_target", "market_date_strictly_before_target", "same_report_excluded", "target_labels_fit_on_train_rows_only"],
    }
    return pairs, manifest


def pair_frame(dataframe):
    frame = dataframe[PAIR_FEATURES].copy()
    for name in PAIR_CATEGORICAL_FEATURES:
        frame[name] = frame[name].astype(str)
    return frame


def model_parameters(config, seed, loss_function):
    settings = config["learned_comparable"]
    return {
        "iterations": int(settings["iterations"]),
        "depth": int(settings["depth"]),
        "learning_rate": float(settings["learning_rate"]),
        "l2_leaf_reg": float(settings["l2_leaf_reg"]),
        "random_strength": float(settings["random_strength"]),
        "bagging_temperature": float(settings["bagging_temperature"]),
        "border_count": int(settings["border_count"]),
        "max_ctr_complexity": 1,
        "bootstrap_type": "Bayesian",
        "loss_function": loss_function,
        "eval_metric": "MAE",
        "random_seed": int(seed),
        "thread_count": int(settings["thread_count"]),
        "allow_writing_files": False,
        "verbose": False,
    }


def fit_pair_models(train_pairs, validation_pairs, config, seed):
    selection = CatBoostRegressor(**model_parameters(config, seed, "MAE"))
    adjustment = CatBoostRegressor(**model_parameters(config, seed + 1, "RMSE"))
    selection_train_pool = Pool(pair_frame(train_pairs), label=train_pairs["absolute_adjustment_log"], cat_features=PAIR_CATEGORICAL_FEATURES)
    selection_validation_pool = Pool(pair_frame(validation_pairs), label=validation_pairs["absolute_adjustment_log"], cat_features=PAIR_CATEGORICAL_FEATURES)
    adjustment_train_pool = Pool(pair_frame(train_pairs), label=train_pairs["adjustment_log"], cat_features=PAIR_CATEGORICAL_FEATURES)
    adjustment_validation_pool = Pool(pair_frame(validation_pairs), label=validation_pairs["adjustment_log"], cat_features=PAIR_CATEGORICAL_FEATURES)
    selection.fit(selection_train_pool, eval_set=selection_validation_pool, early_stopping_rounds=int(config["learned_comparable"]["early_stopping_rounds"]), use_best_model=True)
    adjustment.fit(adjustment_train_pool, eval_set=adjustment_validation_pool, early_stopping_rounds=int(config["learned_comparable"]["early_stopping_rounds"]), use_best_model=True)
    return selection, adjustment, int(selection.get_best_iteration() + 1), int(adjustment.get_best_iteration() + 1)


def fit_pair_models_full(train_pairs, config, seed, selection_iterations, adjustment_iterations):
    selection_settings = model_parameters(config, seed, "MAE")
    adjustment_settings = model_parameters(config, seed + 1, "RMSE")
    selection_settings["iterations"] = int(selection_iterations)
    adjustment_settings["iterations"] = int(adjustment_iterations)
    selection = CatBoostRegressor(**selection_settings)
    adjustment = CatBoostRegressor(**adjustment_settings)
    selection_train_pool = Pool(pair_frame(train_pairs), label=train_pairs["absolute_adjustment_log"], cat_features=PAIR_CATEGORICAL_FEATURES)
    adjustment_train_pool = Pool(pair_frame(train_pairs), label=train_pairs["adjustment_log"], cat_features=PAIR_CATEGORICAL_FEATURES)
    selection.fit(selection_train_pool)
    adjustment.fit(adjustment_train_pool)
    return selection, adjustment


def predict_adjusted_three(pair_data, selection_model, adjustment_model, config):
    frame = pair_data.copy()
    pool = Pool(pair_frame(frame), cat_features=PAIR_CATEGORICAL_FEATURES)
    frame["selection_score"] = selection_model.predict(pool)
    adjustment = adjustment_model.predict(pool)
    cap = math.log1p(float(config["learned_comparable"]["adjustment_cap_ratio"]))
    frame["predicted_adjustment_log"] = np.clip(adjustment, -cap, cap)
    frame["adjusted_unit"] = frame["candidate_raw_unit"] * np.exp(frame["predicted_adjustment_log"])
    selected = frame.sort_values(["row_index", "selection_score", "candidate_rank_by_rule"]).groupby("row_index", sort=False).head(int(config["learned_comparable"]["selected_comparable_count"])).copy()
    output = selected.groupby("row_index", sort=False).agg(
        retrieval_prediction=("adjusted_unit", "mean"),
        comparable_count_selected=("adjusted_unit", "size"),
        mean_selection_score=("selection_score", "mean"),
        mean_adjustment_abs_pct=("predicted_adjustment_log", lambda values: float(np.mean(np.abs(np.expm1(values))))),
        same_road_share_selected=("same_road", "mean"),
        mean_candidate_age_days=("candidate_age_days", "mean"),
    ).reset_index()
    return output
