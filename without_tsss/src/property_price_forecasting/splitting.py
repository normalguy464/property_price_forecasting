import pandas as pd


ROLLING_FOLDS = [
    {
        "name": "fold_1",
        "train_start": "2024-03-01",
        "train_end": "2024-08-31",
        "validation_start": "2024-09-01",
        "validation_end": "2024-10-31",
    },
    {
        "name": "fold_2",
        "train_start": "2024-03-01",
        "train_end": "2024-10-31",
        "validation_start": "2024-11-01",
        "validation_end": "2024-12-31",
    },
    {
        "name": "fold_3",
        "train_start": "2024-03-01",
        "train_end": "2024-12-31",
        "validation_start": "2025-01-01",
        "validation_end": "2025-02-28",
    },
    {
        "name": "fold_4",
        "train_start": "2024-03-01",
        "train_end": "2025-02-28",
        "validation_start": "2025-03-01",
        "validation_end": "2025-04-30",
    },
]


def build_split_manifest(cleaned, config):
    dates = pd.to_datetime(cleaned["as_of_date"], format="%Y-%m-%d")
    folds = []
    for definition in ROLLING_FOLDS:
        train = dates.between(definition["train_start"], definition["train_end"])
        validation = dates.between(definition["validation_start"], definition["validation_end"])
        folds.append(
            {
                **definition,
                "train_rows": int(train.sum()),
                "validation_rows": int(validation.sum()),
                "train_target_median": float(cleaned.loc[train, "target_price_vnd_m2"].median()),
                "validation_target_median": float(cleaned.loc[validation, "target_price_vnd_m2"].median()),
                "report_group_overlap": int(len(set(cleaned.loc[train, "report_group_id"]) & set(cleaned.loc[validation, "report_group_id"]))),
                "asset_group_overlap": int(len(set(cleaned.loc[train, "asset_group_id"]) & set(cleaned.loc[validation, "asset_group_id"]))),
            }
        )
    development = cleaned["split"].eq("development")
    test = cleaned["split"].eq("test")
    return {
        "strategy": "expanding_window",
        "population": "TSTĐ only",
        "tsss_used": False,
        "test_start": config["test_start"],
        "test_end": config["test_end"],
        "development_rows": int(development.sum()),
        "test_rows": int(test.sum()),
        "development_date_min": cleaned.loc[development, "as_of_date"].min(),
        "development_date_max": cleaned.loc[development, "as_of_date"].max(),
        "test_date_min": cleaned.loc[test, "as_of_date"].min(),
        "test_date_max": cleaned.loc[test, "as_of_date"].max(),
        "test_rows_with_asset_seen_in_development": int(cleaned.loc[test, "asset_seen_in_development"].sum()),
        "test_rows_with_new_asset": int(test.sum() - cleaned.loc[test, "asset_seen_in_development"].sum()),
        "report_group_overlap_development_test": int(len(set(cleaned.loc[development, "report_group_id"]) & set(cleaned.loc[test, "report_group_id"]))),
        "asset_group_overlap_development_test": int(len(set(cleaned.loc[development, "asset_group_id"]) & set(cleaned.loc[test, "asset_group_id"]))),
        "folds": folds,
    }
