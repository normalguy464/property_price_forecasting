import math

import numpy as np
from catboost import CatBoostRegressor, Pool


def regression_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.maximum(np.asarray(y_pred, dtype=float), 1.0)
    error = y_pred - y_true
    absolute = np.abs(error)
    percentage = absolute / np.maximum(np.abs(y_true), 1.0)
    return {
        "rows": int(len(y_true)),
        "mae_vnd_m2": float(absolute.mean()),
        "rmse_vnd_m2": float(np.sqrt(np.mean(error ** 2))),
        "wape": float(absolute.sum() / np.maximum(np.abs(y_true).sum(), 1.0)),
        "mape": float(percentage.mean()),
        "mdape": float(np.median(percentage)),
        "within_10pct": float((percentage <= 0.10).mean()),
        "within_20pct": float((percentage <= 0.20).mean()),
    }


def price_band(value):
    if value < 60_000_000:
        return "below_60m"
    if value < 100_000_000:
        return "60m_to_100m"
    if value < 200_000_000:
        return "100m_to_200m"
    return "at_least_200m"


def band_weights(target, max_weight):
    values = np.asarray(target, dtype=float)
    bands = np.asarray([price_band(value) for value in values], dtype=object)
    labels, counts = np.unique(bands, return_counts=True)
    count_map = dict(zip(labels.tolist(), counts.tolist()))
    largest = max(count_map.values())
    raw = {band: min(math.sqrt(largest / count), max_weight) for band, count in count_map.items()}
    weights = np.asarray([raw[band] for band in bands], dtype=float)
    return weights / weights.mean(), count_map, raw


def oversample_indices(target, max_multiplier, seed):
    values = np.asarray(target, dtype=float)
    bands = np.asarray([price_band(value) for value in values], dtype=object)
    labels, counts = np.unique(bands, return_counts=True)
    count_map = dict(zip(labels.tolist(), counts.tolist()))
    largest = max(count_map.values())
    generator = np.random.default_rng(seed)
    indices = [np.arange(len(values), dtype=int)]
    for band, count in count_map.items():
        multiplier = min(math.sqrt(largest / count), max_multiplier)
        extra = int(round((multiplier - 1.0) * count))
        band_indices = np.flatnonzero(bands == band)
        if extra > 0:
            indices.append(generator.choice(band_indices, size=extra, replace=True))
    return np.concatenate(indices), count_map


def frame_for_catboost(dataframe, features, categorical):
    frame = dataframe[features].copy()
    for name in categorical:
        frame[name] = frame[name].astype(str)
    return frame


def parameters(config, seed):
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
        "loss_function": "RMSE",
        "eval_metric": "MAE",
        "random_seed": seed,
        "thread_count": config["thread_count"],
        "allow_writing_files": False,
        "verbose": False
    }


def fit_predict_catboost(train, validation, target, features, categorical, config, seed, variant, rare_config):
    train_frame = frame_for_catboost(train, features, categorical)
    validation_frame = frame_for_catboost(validation, features, categorical)
    train_target = train[target].to_numpy(dtype=float)
    validation_target = validation[target].to_numpy(dtype=float)
    transform = variant != "catboost_raw"
    weights = None
    details = {"variant": variant, "oversampling": False, "sample_weight": False}
    if variant == "catboost_weighted":
        weights, counts, raw = band_weights(train_target, rare_config["max_weight"])
        details.update({"sample_weight": True, "band_counts": counts, "raw_weight_by_band": raw})
    if variant == "catboost_oversampled":
        sampled, counts = oversample_indices(train_target, rare_config["oversample_max_multiplier"], seed)
        train_frame = train_frame.iloc[sampled].reset_index(drop=True)
        train_target = train_target[sampled]
        details.update({"oversampling": True, "original_train_rows": int(len(train)), "sampled_train_rows": int(len(sampled)), "band_counts": counts})
    if transform:
        train_target = np.log1p(train_target)
        validation_target = np.log1p(validation_target)
    train_pool = Pool(train_frame, label=train_target, cat_features=categorical, weight=weights)
    validation_pool = Pool(validation_frame, label=validation_target, cat_features=categorical)
    model = CatBoostRegressor(**parameters(config, seed))
    model.fit(train_pool, eval_set=validation_pool, early_stopping_rounds=config["early_stopping_rounds"], use_best_model=True)
    prediction = model.predict(validation_pool)
    if transform:
        prediction = np.expm1(prediction)
    return model, np.maximum(prediction, 1.0), int(model.get_best_iteration() + 1), details


def fit_full_catboost(dataframe, target, features, categorical, config, seed, variant, rare_config, iterations):
    frame = frame_for_catboost(dataframe, features, categorical)
    values = dataframe[target].to_numpy(dtype=float)
    transform = variant != "catboost_raw"
    weights = None
    if variant == "catboost_weighted":
        weights, _, _ = band_weights(values, rare_config["max_weight"])
    if variant == "catboost_oversampled":
        sampled, _ = oversample_indices(values, rare_config["oversample_max_multiplier"], seed)
        frame = frame.iloc[sampled].reset_index(drop=True)
        values = values[sampled]
    if transform:
        values = np.log1p(values)
    final = {**config, "iterations": int(iterations)}
    model = CatBoostRegressor(**parameters(final, seed))
    model.fit(Pool(frame, label=values, cat_features=categorical, weight=weights))
    return model
