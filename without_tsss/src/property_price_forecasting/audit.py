from hashlib import sha256
from pathlib import Path
import json

import numpy as np
import pandas as pd


SENSITIVE_COLUMNS = {
    "Mã kho",
    "Mã tài sản",
    "Số báo cáo định giá",
    "Chi tiết",
    "Thông tin liên hệ",
}


def to_builtin(value):
    if isinstance(value, dict):
        return {str(key): to_builtin(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_builtin(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if np.isnan(value) else float(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if pd.isna(value):
        return None
    return value


def file_sha256(path):
    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def numeric_summary(series):
    values = pd.to_numeric(series, errors="coerce")
    quantiles = values.quantile([0, 0.001, 0.01, 0.05, 0.5, 0.95, 0.99, 0.999, 1])
    return {
        "zero_count": int((values == 0).sum()),
        "negative_count": int((values < 0).sum()),
        "quantiles": {str(key): to_builtin(value) for key, value in quantiles.items()},
    }


def column_profile(dataframe, name):
    series = dataframe[name]
    result = {
        "name": name,
        "dtype": str(series.dtype),
        "rows": int(len(series)),
        "missing_count": int(series.isna().sum()),
        "missing_rate": float(series.isna().mean()),
        "unique_non_null": int(series.nunique(dropna=True)),
        "is_constant": bool(series.nunique(dropna=False) <= 1),
        "is_sensitive": name in SENSITIVE_COLUMNS,
    }
    if pd.api.types.is_numeric_dtype(series):
        result.update(numeric_summary(series))
    elif name not in SENSITIVE_COLUMNS:
        counts = series.value_counts(dropna=False).head(10)
        result["top_values"] = {str(key): int(value) for key, value in counts.items()}
    return result


def relative_error(left, right):
    left = pd.to_numeric(left, errors="coerce")
    right = pd.to_numeric(right, errors="coerce")
    valid = left.notna() & right.notna()
    denominator = np.maximum(np.maximum(left[valid].abs(), right[valid].abs()), 1)
    values = (left[valid] - right[valid]).abs() / denominator
    return values


def grouped_target_summary(dataframe, group, target):
    output = []
    for key, frame in dataframe.groupby(group, dropna=False):
        output.append(
            {
                group: to_builtin(key),
                "rows": int(len(frame)),
                "target_mean": float(frame[target].mean()),
                "target_median": float(frame[target].median()),
                "target_p05": float(frame[target].quantile(0.05)),
                "target_p95": float(frame[target].quantile(0.95)),
            }
        )
    return output


def build_audit(source_path):
    source_path = Path(source_path).resolve()
    workbook = pd.ExcelFile(source_path)
    dataframe = pd.read_excel(source_path, sheet_name=workbook.sheet_names[0])
    columns = dataframe.columns.tolist()
    target_primary = columns[34]
    target_duplicate = columns[33]
    effective_date = pd.to_datetime(dataframe[columns[55]], format="%d/%m/%Y", errors="coerce")
    transaction_date = pd.to_datetime(dataframe[columns[49]], format="%d/%m/%Y", errors="coerce")
    transaction_age = (effective_date - transaction_date).dt.days
    target_pair_error = relative_error(dataframe[target_duplicate], dataframe[target_primary])
    land_formula_error = relative_error(dataframe[columns[39]] / dataframe[columns[20]], dataframe[target_primary])
    report_size = dataframe.groupby(columns[4]).size()
    report_months = dataframe.groupby(columns[4])[columns[67]].nunique()
    class_report = pd.crosstab(dataframe[columns[4]], dataframe[columns[2]])
    all_null_columns = [name for name in columns if dataframe[name].isna().all()]
    constant_columns = [name for name in columns if dataframe[name].nunique(dropna=False) <= 1]
    macro_checks = {}
    for index in [68, 69, 70, 71, 72, 73, 75]:
        name = columns[index]
        unique_per_month = dataframe.groupby(columns[67])[name].nunique(dropna=False)
        macro_checks[name] = {
            "unique_total": int(dataframe[name].nunique(dropna=True)),
            "months_with_multiple_values": int((unique_per_month > 1).sum()),
            "missing_count": int(dataframe[name].isna().sum()),
        }
    rare_categories = {}
    for index in [9, 10, 11, 12, 14]:
        name = columns[index]
        counts = dataframe[name].value_counts(dropna=True)
        rare_categories[name] = {
            "unique_non_null": int(len(counts)),
            "singleton_categories": int((counts == 1).sum()),
            "rows_in_categories_below_5": int(counts[counts < 5].sum()),
            "missing_count": int(dataframe[name].isna().sum()),
        }
    class_summary = []
    for key, frame in dataframe.groupby(columns[2], dropna=False):
        class_summary.append(
            {
                "class": to_builtin(key),
                "rows": int(len(frame)),
                "reports": int(frame[columns[4]].nunique()),
                "target_median": float(frame[target_primary].median()),
                "missing_transaction_date": int(frame[columns[49]].isna().sum()),
                "missing_asset_id": int(frame[columns[3]].isna().sum()),
                "construction_count_above_100": int((frame[columns[41]] > 100).sum()),
                "land_total_zero": int((frame[columns[39]] == 0).sum()),
            }
        )
    official_max = 687_200_000
    extreme = dataframe[dataframe[target_primary] > official_max]
    result = {
        "source": {
            "path": str(source_path),
            "file_name": source_path.name,
            "size_bytes": source_path.stat().st_size,
            "sha256": file_sha256(source_path),
            "sheet_names": workbook.sheet_names,
            "selected_sheet": workbook.sheet_names[0],
            "rows": int(dataframe.shape[0]),
            "columns": int(dataframe.shape[1]),
        },
        "schema": {
            "column_names": columns,
            "column_profiles": [column_profile(dataframe, name) for name in columns],
            "all_null_columns": all_null_columns,
            "constant_columns": constant_columns,
        },
        "target": {
            "selected_provisional_target": target_primary,
            "duplicate_target": target_duplicate,
            "selected_target_summary": numeric_summary(dataframe[target_primary]),
            "pearson_correlation": float(dataframe[[target_duplicate, target_primary]].corr().iloc[0, 1]),
            "relative_error_below_1e_6": int((target_pair_error < 1e-6).sum()),
            "relative_error_above_1_percent": int((target_pair_error > 0.01).sum()),
            "absolute_difference_median": float((dataframe[target_duplicate] - dataframe[target_primary]).abs().median()),
            "absolute_difference_max": float((dataframe[target_duplicate] - dataframe[target_primary]).abs().max()),
            "declared_unit_counts": to_builtin(dataframe[columns[35]].value_counts(dropna=False).to_dict()),
            "land_total_divided_by_area_relative_error_below_1e_6": int((land_formula_error < 1e-6).sum()),
            "land_total_divided_by_area_relative_error_above_1_percent": int((land_formula_error > 0.01).sum()),
        },
        "time": {
            "effective_date_min": effective_date.min(),
            "effective_date_max": effective_date.max(),
            "effective_date_parse_failures": int(effective_date.isna().sum()),
            "transaction_date_min": transaction_date.min(),
            "transaction_date_max": transaction_date.max(),
            "transaction_date_parse_failures_non_null": int((dataframe[columns[49]].notna() & transaction_date.isna()).sum()),
            "transaction_after_effective_count": int((transaction_age < 0).sum()),
            "transaction_same_day_count": int((transaction_age == 0).sum()),
            "transaction_more_than_10_years_before_count": int((transaction_age > 3650).sum()),
            "effective_month_year_mismatch_count": int((((effective_date.dt.month != dataframe[columns[62]]) | (effective_date.dt.year != dataframe[columns[64]]))).sum()),
            "month_count": int(dataframe[columns[67]].nunique()),
            "monthly_target_summary": grouped_target_summary(dataframe.sort_values(columns[67]), columns[67], target_primary),
            "macro_consistency": macro_checks,
        },
        "business_structure": {
            "warehouse_class_summary": class_summary,
            "reports": int(len(report_size)),
            "report_size_quantiles": to_builtin(report_size.quantile([0, 0.5, 0.9, 0.99, 1]).to_dict()),
            "reports_spanning_multiple_months": int((report_months > 1).sum()),
            "class_rows": to_builtin(dataframe[columns[2]].value_counts().to_dict()),
            "class_rows_by_report": {str(name): to_builtin(class_report[name].value_counts().to_dict()) for name in class_report.columns},
        },
        "quality": {
            "full_row_duplicates": int(dataframe.duplicated().sum()),
            "warehouse_id_duplicates": int(dataframe[columns[1]].duplicated().sum()),
            "sequence_id_duplicates": int(dataframe[columns[0]].duplicated().sum()),
            "construction_count_above_100": int((dataframe[columns[41]] > 100).sum()),
            "target_above_official_2024_table_max_count": int(len(extreme)),
            "target_above_1_billion_count": int((dataframe[target_primary] > 1_000_000_000).sum()),
            "target_above_official_max_by_district": to_builtin(extreme[columns[8]].value_counts().to_dict()),
            "rare_categories": rare_categories,
            "shape_label_unique_count": int(dataframe[columns[25]].nunique(dropna=True)),
            "shape_label_top_values": to_builtin(dataframe[columns[25]].value_counts().head(15).to_dict()),
        },
        "geography": {
            "district_target_summary": grouped_target_summary(dataframe, columns[8], target_primary),
            "district_count": int(dataframe[columns[8]].nunique()),
            "old_ward_count": int(dataframe[columns[9]].nunique(dropna=True)),
            "new_ward_count": int(dataframe[columns[10]].nunique(dropna=True)),
            "road_primary_count": int(dataframe[columns[11]].nunique(dropna=True)),
            "road_secondary_count": int(dataframe[columns[12]].nunique(dropna=True)),
        },
        "privacy": {
            "sensitive_columns": sorted(SENSITIVE_COLUMNS),
            "sensitive_values_exported": False,
        },
        "market_reference": {
            "official_hcm_2024_land_table_max_vnd_per_m2": official_max,
            "official_table_is_not_market_price": True,
            "comparison_is_provisional_due_to_unit_conflict": True,
            "source_url": "https://xaydungchinhsach.chinhphu.vn/chi-tiet-bang-gia-dat-dieu-chinh-tai-tp-hcm-ap-dung-tu-31-10-119241022105804049.htm",
        },
    }
    return to_builtin(result)


def write_audit(source_path, output_path):
    result = build_audit(source_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
