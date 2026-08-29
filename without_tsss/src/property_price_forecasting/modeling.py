from hashlib import sha256
from pathlib import Path
import math

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.compose import ColumnTransformer
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


def frame_for_model(dataframe, feature_columns, categorical_features):
    frame = dataframe[feature_columns].copy()
    for name in categorical_features:
        frame[name] = frame[name].astype(str)
    return frame


def fold_masks(dataframe, fold):
    dates = pd.to_datetime(dataframe["as_of_date"], format="%Y-%m-%d")
    train = dates.between(fold["train_start"], fold["train_end"])
    validation = dates.between(fold["validation_start"], fold["validation_end"])
    return train, validation


class HierarchicalMedianRegressor:
    def __init__(self, lookback_months=6, road_min_count=5, ward_min_count=10, district_min_count=20):
        self.lookback_months = lookback_months
        self.levels = [
            (["district", "ward_new", "road"], road_min_count),
            (["district", "ward_new"], ward_min_count),
            (["district"], district_min_count),
        ]
        self.tables = []
        self.global_median = None

    def fit(self, dataframe, target, validation_start):
        dates = pd.to_datetime(dataframe["as_of_date"], format="%Y-%m-%d")
        cutoff = pd.Timestamp(validation_start) - pd.DateOffset(months=self.lookback_months)
        recent = dates.ge(cutoff)
        frame = dataframe.loc[recent].copy()
        frame["_target"] = np.asarray(target.loc[recent], dtype=float)
        self.global_median = float(frame["_target"].median())
        self.tables = []
        for keys, minimum in self.levels:
            grouped = frame.groupby(keys, dropna=False)["_target"].agg(["median", "count"])
            grouped = grouped[grouped["count"] >= minimum]
            self.tables.append((keys, grouped["median"].to_dict()))
        return self

    def predict(self, dataframe):
        predictions = []
        for _, row in dataframe.iterrows():
            value = None
            for keys, table in self.tables:
                key = tuple(row[name] for name in keys)
                if len(keys) == 1:
                    key = key[0]
                if key in table:
                    value = table[key]
                    break
            predictions.append(self.global_median if value is None else value)
        return np.asarray(predictions, dtype=float)


def build_ridge_pipeline(categorical_features, numeric_features, alpha, min_frequency):
    categorical = OneHotEncoder(handle_unknown="ignore", min_frequency=min_frequency, dtype=np.float64)
    numeric = StandardScaler()
    preprocessor = ColumnTransformer(
        [
            ("categorical", categorical, categorical_features),
            ("numeric", numeric, numeric_features),
        ],
        sparse_threshold=0.3,
    )
    model = Ridge(alpha=alpha, solver="lsqr", max_iter=5000, tol=1e-4)
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def fit_predict_ridge(train, validation, target_name, categorical_features, numeric_features, alpha, min_frequency):
    features = categorical_features + numeric_features
    pipeline = build_ridge_pipeline(categorical_features, numeric_features, alpha, min_frequency)
    pipeline.fit(train[features], np.log1p(train[target_name].to_numpy(dtype=float)))
    prediction = np.expm1(pipeline.predict(validation[features]))
    return pipeline, np.maximum(prediction, 1.0)


def catboost_parameters(parameters, common, seed, iterations=None):
    result = dict(parameters)
    result.update(
        {
            "loss_function": common["loss_function"],
            "eval_metric": common["eval_metric"],
            "bootstrap_type": common["bootstrap_type"],
            "one_hot_max_size": common["one_hot_max_size"],
            "max_ctr_complexity": common["max_ctr_complexity"],
            "rsm": common["rsm"],
            "random_seed": seed,
            "thread_count": common["thread_count"],
            "allow_writing_files": False,
            "verbose": False,
        }
    )
    if iterations is not None:
        result["iterations"] = int(iterations)
    return result


def fit_predict_catboost(train, validation, target_name, feature_columns, categorical_features, parameters, common, seed):
    train_frame = frame_for_model(train, feature_columns, categorical_features)
    validation_frame = frame_for_model(validation, feature_columns, categorical_features)
    train_target = train[target_name].to_numpy(dtype=float)
    validation_target = validation[target_name].to_numpy(dtype=float)
    if common["target_transform"] == "log1p":
        train_target = np.log1p(train_target)
        validation_target = np.log1p(validation_target)
    train_pool = Pool(train_frame, label=train_target, cat_features=categorical_features)
    validation_pool = Pool(validation_frame, label=validation_target, cat_features=categorical_features)
    model = CatBoostRegressor(**catboost_parameters(parameters, common, seed))
    model.fit(train_pool, eval_set=validation_pool, early_stopping_rounds=common["early_stopping_rounds"], use_best_model=True)
    prediction = model.predict(validation_pool)
    if common["target_transform"] == "log1p":
        prediction = np.expm1(prediction)
    prediction = np.maximum(prediction, 1.0)
    return model, prediction, int(model.get_best_iteration() + 1)


def fit_full_catboost(dataframe, target_name, feature_columns, categorical_features, parameters, common, seed, iterations):
    frame = frame_for_model(dataframe, feature_columns, categorical_features)
    target = dataframe[target_name].to_numpy(dtype=float)
    if common["target_transform"] == "log1p":
        target = np.log1p(target)
    pool = Pool(frame, label=target, cat_features=categorical_features)
    model = CatBoostRegressor(**catboost_parameters(parameters, common, seed, iterations))
    model.fit(pool)
    return model


def pooled_metrics(records):
    frame = pd.DataFrame(records)
    return regression_metrics(frame["target"], frame["prediction"])


def file_sha256(path):
    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def price_band(value):
    if value < 60_000_000:
        return "below_60m"
    if value < 100_000_000:
        return "60m_to_100m"
    if value < 200_000_000:
        return "100m_to_200m"
    return "at_least_200m"


def segmented_metrics(dataframe, segment_columns):
    output = {}
    for name in segment_columns:
        groups = []
        for value, frame in dataframe.groupby(name, dropna=False):
            groups.append({"segment": str(value), **regression_metrics(frame["target"], frame["prediction"])})
        output[name] = groups
    return output
