from pathlib import Path
import json

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool


def metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.maximum(np.asarray(y_pred, dtype=float), 1.0)
    error = y_pred - y_true
    absolute = np.abs(error)
    percentage = absolute / np.maximum(y_true, 1.0)
    return {
        "rows": int(len(y_true)),
        "mae_vnd_m2": float(absolute.mean()),
        "rmse_vnd_m2": float(np.sqrt(np.mean(error ** 2))),
        "rmsle": float(np.sqrt(np.mean((np.log1p(y_pred) - np.log1p(y_true)) ** 2))),
        "wape": float(absolute.sum() / y_true.sum()),
        "mdape": float(np.median(percentage)),
        "within_10pct": float((percentage <= 0.10).mean()),
        "within_20pct": float((percentage <= 0.20).mean()),
        "within_30pct": float((percentage <= 0.30).mean()),
        "mean_error_vnd_m2": float(error.mean()),
    }


def first_valid(frame, names):
    result = pd.Series(np.nan, index=frame.index, dtype=float)
    for name in names:
        candidate = pd.to_numeric(frame[name], errors="coerce")
        valid = result.isna() & candidate.gt(0)
        result.loc[valid] = candidate.loc[valid]
    return result


def add_anchor_features(dataframe):
    frame = dataframe.copy()
    frame["market_anchor"] = first_valid(frame, [
        "comparable_weighted_estimated_price_365d",
        "market_backoff_estimated_median_365d",
        "market_backoff_estimated_median_180d",
        "market_backoff_estimated_median_90d",
        "market_district_estimated_median_365d",
    ])
    frame["history_anchor"] = first_valid(frame, [
        "history_asset_last_price",
        "history_backoff_median_180d",
        "history_backoff_median_365d",
        "history_district_median_365d",
    ])
    market_weight = np.log1p(frame["market_backoff_count_365d"].fillna(0).clip(lower=0, upper=100))
    history_weight = np.log1p(frame["history_backoff_count_365d"].fillna(0).clip(lower=0, upper=100))
    market_log = np.log1p(frame["market_anchor"])
    history_log = np.log1p(frame["history_anchor"])
    numerator = market_log.fillna(0) * market_weight + history_log.fillna(0) * history_weight
    denominator = market_weight.where(market_log.notna(), 0) + history_weight.where(history_log.notna(), 0)
    frame["hybrid_anchor"] = np.expm1(numerator / denominator.replace(0, np.nan))
    frame["hybrid_anchor"] = frame["hybrid_anchor"].fillna(frame["market_anchor"]).fillna(frame["history_anchor"])
    frame["log_market_anchor"] = np.log1p(frame["market_anchor"])
    frame["log_history_anchor"] = np.log1p(frame["history_anchor"])
    frame["log_hybrid_anchor"] = np.log1p(frame["hybrid_anchor"])
    frame["market_history_log_gap"] = frame["log_market_anchor"] - frame["log_history_anchor"]
    frame["market_anchor_missing"] = frame["market_anchor"].isna().astype("int8")
    frame["history_anchor_missing"] = frame["history_anchor"].isna().astype("int8")
    return frame


ANCHOR_FEATURES = ["market_anchor", "history_anchor", "hybrid_anchor", "log_market_anchor", "log_history_anchor", "log_hybrid_anchor", "market_history_log_gap", "market_anchor_missing", "history_anchor_missing"]


def parameters(config, seed, iterations=None):
    result = {
        "iterations": int(config["iterations"] if iterations is None else iterations),
        "depth": config["depth"],
        "learning_rate": config["learning_rate"],
        "l2_leaf_reg": config["l2_leaf_reg"],
        "random_strength": config["random_strength"],
        "bagging_temperature": config["bagging_temperature"],
        "border_count": config["border_count"],
        "max_ctr_complexity": config["max_ctr_complexity"],
        "rsm": config["rsm"],
        "bootstrap_type": "Bayesian",
        "loss_function": "RMSE",
        "eval_metric": "MAE",
        "random_seed": seed,
        "thread_count": config["thread_count"],
        "allow_writing_files": False,
        "verbose": False,
    }
    return result


def model_frame(dataframe, features, categorical):
    frame = dataframe[features].copy()
    for name in categorical:
        frame[name] = frame[name].astype(str)
    return frame


def anchors_for_split(train, validation, anchor_name, target_name):
    fallback = float(train[target_name].median())
    train_anchor = train[anchor_name].fillna(fallback).clip(lower=1.0).to_numpy(dtype=float)
    validation_anchor = validation[anchor_name].fillna(fallback).clip(lower=1.0).to_numpy(dtype=float)
    return train_anchor, validation_anchor


def fit_variant(train, validation, target_name, features, categorical, config, seed, variant):
    train_frame = model_frame(train, features, categorical)
    validation_frame = model_frame(validation, features, categorical)
    train_target = train[target_name].to_numpy(dtype=float)
    validation_target = validation[target_name].to_numpy(dtype=float)
    if variant == "direct_history":
        train_label = np.log1p(train_target)
        validation_label = np.log1p(validation_target)
        train_anchor = None
        validation_anchor = None
    else:
        anchor_name = "market_anchor" if variant == "residual_market" else "hybrid_anchor"
        train_anchor, validation_anchor = anchors_for_split(train, validation, anchor_name, target_name)
        train_label = np.log1p(train_target) - np.log1p(train_anchor)
        validation_label = np.log1p(validation_target) - np.log1p(validation_anchor)
    train_pool = Pool(train_frame, label=train_label, cat_features=categorical)
    validation_pool = Pool(validation_frame, label=validation_label, cat_features=categorical)
    model = CatBoostRegressor(**parameters(config, seed))
    model.fit(train_pool, eval_set=validation_pool, early_stopping_rounds=config["early_stopping_rounds"], use_best_model=True)
    raw = model.predict(validation_pool)
    prediction = np.expm1(raw) if variant == "direct_history" else np.expm1(np.log1p(validation_anchor) + raw)
    return model, np.maximum(prediction, 1.0), int(model.get_best_iteration() + 1)


def fit_full(dataframe, target_name, features, categorical, config, seed, variant, iterations):
    frame = model_frame(dataframe, features, categorical)
    target = dataframe[target_name].to_numpy(dtype=float)
    if variant == "direct_history":
        label = np.log1p(target)
        anchor = None
    else:
        anchor_name = "market_anchor" if variant == "residual_market" else "hybrid_anchor"
        anchor = dataframe[anchor_name].fillna(float(dataframe[target_name].median())).clip(lower=1.0).to_numpy(dtype=float)
        label = np.log1p(target) - np.log1p(anchor)
    model = CatBoostRegressor(**parameters(config, seed, iterations))
    model.fit(Pool(frame, label=label, cat_features=categorical))
    return model


def predict_full(model, dataframe, features, categorical, variant, fallback):
    raw = model.predict(Pool(model_frame(dataframe, features, categorical), cat_features=categorical))
    if variant == "direct_history":
        prediction = np.expm1(raw)
    else:
        anchor_name = "market_anchor" if variant == "residual_market" else "hybrid_anchor"
        anchor = dataframe[anchor_name].fillna(fallback).clip(lower=1.0).to_numpy(dtype=float)
        prediction = np.expm1(np.log1p(anchor) + raw)
    return np.maximum(prediction, 1.0)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
