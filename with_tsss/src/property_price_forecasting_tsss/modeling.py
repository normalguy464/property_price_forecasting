from hashlib import sha256
from pathlib import Path
import math

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def regression_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.maximum(np.asarray(y_pred, dtype=float), 1.0)
    error = y_pred - y_true
    absolute = np.abs(error)
    percentage = absolute / np.maximum(np.abs(y_true), 1.0)
    log_error = np.log1p(y_pred) - np.log1p(y_true)
    return {
        "rows": int(len(y_true)),
        "mae_vnd_m2": float(absolute.mean()),
        "rmse_vnd_m2": float(np.sqrt(np.mean(error ** 2))),
        "rmsle": float(np.sqrt(np.mean(log_error ** 2))),
        "wape": float(absolute.sum() / np.maximum(np.abs(y_true).sum(), 1.0)),
        "mdape": float(np.median(percentage)),
        "within_10pct": float((percentage <= 0.10).mean()),
        "within_20pct": float((percentage <= 0.20).mean()),
        "within_30pct": float((percentage <= 0.30).mean()),
        "mean_error_vnd_m2": float(error.mean()),
    }


def build_ridge(categorical_features, numeric_features, alpha, min_frequency):
    categorical = OneHotEncoder(handle_unknown="ignore", min_frequency=min_frequency, dtype=np.float64)
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median", add_indicator=True)), ("scaler", StandardScaler())])
    preprocessor = ColumnTransformer([("categorical", categorical, categorical_features), ("numeric", numeric, numeric_features)], sparse_threshold=0.3)
    model = Ridge(alpha=alpha, solver="lsqr", max_iter=5000, tol=1e-4)
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def fit_predict_ridge(train, validation, target, categorical_features, numeric_features, alpha, min_frequency):
    features = categorical_features + numeric_features
    model = build_ridge(categorical_features, numeric_features, alpha, min_frequency)
    model.fit(train[features], np.log1p(train[target].to_numpy(dtype=float)))
    prediction = np.maximum(np.expm1(model.predict(validation[features])), 1.0)
    return model, prediction


def catboost_parameters(config, seed):
    return {
        "iterations": config["iterations"],
        "depth": config["depth"],
        "learning_rate": config["learning_rate"],
        "l2_leaf_reg": config["l2_leaf_reg"],
        "random_strength": config["random_strength"],
        "bagging_temperature": config["bagging_temperature"],
        "border_count": config["border_count"],
        "max_ctr_complexity": config["max_ctr_complexity"],
        "rsm": config["rsm"],
        "bootstrap_type": "Bayesian",
        "loss_function": config.get("loss_function", "RMSE"),
        "eval_metric": config.get("eval_metric", "MAE"),
        "random_seed": seed,
        "thread_count": config["thread_count"],
        "allow_writing_files": False,
        "verbose": False,
    }


def frame_for_catboost(dataframe, features, categorical_features):
    frame = dataframe[features].copy()
    for name in categorical_features:
        frame[name] = frame[name].astype(str)
    return frame


def fit_predict_catboost(train, validation, target, features, categorical_features, config, seed, sample_weight=None):
    train_frame = frame_for_catboost(train, features, categorical_features)
    validation_frame = frame_for_catboost(validation, features, categorical_features)
    if sample_weight is not None and len(sample_weight) != len(train):
        raise ValueError("sample_weight phải có cùng số dòng với train")
    train_pool = Pool(train_frame, label=np.log1p(train[target].to_numpy(dtype=float)), cat_features=categorical_features, weight=sample_weight)
    validation_pool = Pool(validation_frame, label=np.log1p(validation[target].to_numpy(dtype=float)), cat_features=categorical_features)
    model = CatBoostRegressor(**catboost_parameters(config, seed))
    model.fit(train_pool, eval_set=validation_pool, early_stopping_rounds=config["early_stopping_rounds"], use_best_model=True)
    prediction = np.maximum(np.expm1(model.predict(validation_pool)), 1.0)
    return model, prediction, int(model.get_best_iteration() + 1)


def price_band(value):
    if value < 60_000_000:
        return "below_60m"
    if value < 100_000_000:
        return "60m_to_100m"
    if value < 200_000_000:
        return "100m_to_200m"
    return "at_least_200m"


def price_band_sample_weights(target, max_weight):
    values = np.asarray(target, dtype=float)
    bands = np.asarray([price_band(value) for value in values], dtype=object)
    labels, counts = np.unique(bands, return_counts=True)
    count_by_band = dict(zip(labels.tolist(), counts.tolist()))
    largest_count = max(count_by_band.values())
    raw_weight_by_band = {
        band: min(math.sqrt(largest_count / count), float(max_weight))
        for band, count in count_by_band.items()
    }
    weights = np.asarray([raw_weight_by_band[band] for band in bands], dtype=float)
    weights = weights / weights.mean()
    manifest = {
        "bands": {band: int(count_by_band[band]) for band in sorted(count_by_band)},
        "raw_weight_by_band": {band: float(raw_weight_by_band[band]) for band in sorted(raw_weight_by_band)},
        "mean_normalized": True,
        "mean_weight": float(weights.mean()),
        "min_weight": float(weights.min()),
        "max_weight": float(weights.max()),
    }
    return weights, manifest


def segment_metrics(dataframe, columns):
    output = {}
    for name in columns:
        groups = []
        for value, frame in dataframe.groupby(name, dropna=False):
            groups.append({"segment": str(value), **regression_metrics(frame["target"], frame["prediction"])})
        output[name] = groups
    return output


def file_sha256(path):
    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
