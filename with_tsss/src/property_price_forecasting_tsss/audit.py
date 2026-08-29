from pathlib import Path
import json

import numpy as np
import pandas as pd


def quantiles(series):
    values = pd.Series(series).replace([np.inf, -np.inf], np.nan).dropna()
    return {str(value): float(values.quantile(value)) for value in [0, 0.001, 0.01, 0.05, 0.5, 0.95, 0.99, 0.999, 1]}


def audit_tsss(source, config):
    tsss = source.loc[source["Phân loại kho"].eq("TSSS")].copy()
    tstd = source.loc[source["Phân loại kho"].eq("TSTĐ")].copy()
    market_date = pd.to_datetime(tsss["Thời điểm giao dịch/rao bán (đ)"], format=config["market_date_format"], errors="coerce")
    effective_date = pd.to_datetime(tsss["Thời điểm hiệu lực"], format=config["market_date_format"], errors="coerce")
    age_at_collection = (effective_date - market_date).dt.days
    area = pd.to_numeric(tsss["Diện tích (m2)"], errors="coerce")
    raw_total = pd.to_numeric(tsss["Giá giao dịch/rao bán (đ)"], errors="coerce")
    estimated_total = pd.to_numeric(tsss["Giá ước tính (đ)"], errors="coerce")
    raw_unit = raw_total / area
    estimated_unit = estimated_total / area
    adjusted_unit = pd.to_numeric(tsss["Đơn giá quyền sử dụng đất (đ/m2)1"], errors="coerce")
    date_eligible = market_date.notna() & effective_date.notna() & age_at_collection.between(0, config["maximum_market_age_at_collection_days"])
    price_eligible = area.gt(0) & raw_unit.between(config["market_unit_price_min"], config["market_unit_price_max"]) & estimated_unit.between(config["market_unit_price_min"], config["market_unit_price_max"])
    eligible = date_eligible & price_eligible
    tstd_reports = set(tstd["Số báo cáo định giá"].astype(str))
    tsss_reports = tsss["Số báo cáo định giá"].astype(str)
    result = {
        "source_rows": int(len(source)),
        "tsss_rows": int(len(tsss)),
        "tstd_rows": int(len(tstd)),
        "eligible_tsss_rows": int(eligible.sum()),
        "excluded_tsss_rows": int((~eligible).sum()),
        "date_quality": {
            "market_date_valid": int(market_date.notna().sum()),
            "effective_date_valid": int(effective_date.notna().sum()),
            "market_before_effective": int(age_at_collection.gt(0).sum()),
            "market_same_day_effective": int(age_at_collection.eq(0).sum()),
            "market_after_effective": int(age_at_collection.lt(0).sum()),
            "market_older_than_maximum": int(age_at_collection.gt(config["maximum_market_age_at_collection_days"]).sum()),
            "market_date_min": market_date.min().strftime("%Y-%m-%d"),
            "market_date_max": market_date.max().strftime("%Y-%m-%d"),
            "age_at_collection_days_quantiles": quantiles(age_at_collection),
        },
        "price_quality": {
            "raw_unit_vnd_m2_quantiles": quantiles(raw_unit),
            "estimated_unit_vnd_m2_quantiles": quantiles(estimated_unit),
            "adjusted_unit_vnd_m2_quantiles": quantiles(adjusted_unit),
            "raw_to_estimated_ratio_quantiles": quantiles(raw_unit / estimated_unit),
            "raw_vs_adjusted_median_absolute_percentage_difference": float(((raw_unit - adjusted_unit).abs() / adjusted_unit.abs()).median()),
            "estimated_vs_adjusted_median_absolute_percentage_difference": float(((estimated_unit - adjusted_unit).abs() / adjusted_unit.abs()).median()),
        },
        "report_linkage": {
            "unique_tsss_reports": int(tsss_reports.nunique()),
            "unique_tstd_reports": int(tstd["Số báo cáo định giá"].nunique()),
            "tsss_rows_with_report_present_in_tstd": int(tsss_reports.isin(tstd_reports).sum()),
            "shared_report_count": int(len(set(tsss_reports) & tstd_reports)),
        },
        "transaction_status": {str(key): int(value) for key, value in tsss["Tình trạng giao dịch"].value_counts(dropna=False).items()},
        "information_source": {str(key): int(value) for key, value in tsss["Nguồn thông tin"].value_counts(dropna=False).items()},
        "field_policy": {
            "raw_unit_price": "use separately as transaction or listing signal",
            "estimated_unit_price": "use separately as historical analyst-adjusted signal",
            "adjusted_land_unit_price": "exclude from initial model because derivation is insufficiently documented",
            "Don_gia_TB_Min_Max_std_count": "exclude because they are precomputed aggregates with unknown temporal lineage",
            "availability_date": "TSSS report effective date",
            "market_recency_date": "transaction or listing date",
            "same_report": "always excluded for each TSTĐ",
        },
    }
    return result


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
