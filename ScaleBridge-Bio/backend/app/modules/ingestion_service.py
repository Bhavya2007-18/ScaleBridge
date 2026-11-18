"""Ingestion parsing, unit normalization, and data-quality (DQ-*) validation service (docs/09_DATA_INGESTION.md)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import io
import math
from typing import Any

import numpy as np
import pandas as pd

from scalebridge_science.units import (
    AmbiguousUnitError,
    PINT_VERSION,
    UnitDimensionError,
    VARIABLE_UNIT_SPECS,
    convert_value,
)


def read_dataframe_from_bytes(
    raw_bytes: bytes,
    filename: str,
    sheet_name: str | None = None,
    header_row: int = 1,
) -> tuple[pd.DataFrame, list[str]]:
    header_idx = max(0, header_row - 1)
    lower = filename.lower()
    if lower.endswith(".xlsx") or lower.endswith(".xls"):
        excel = pd.ExcelFile(io.BytesIO(raw_bytes))
        sheets = [str(s) for s in excel.sheet_names]
        target_sheet = sheet_name if sheet_name in sheets else sheets[0]
        df = pd.read_excel(excel, sheet_name=target_sheet, header=header_idx)
        return df, sheets
    if lower.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(raw_bytes), header=header_idx)
        return df, ["CSV"]
    raise ValueError(f"Unsupported file format for '{filename}'. Only CSV and XLSX are supported.")


def preview_file_bytes(
    raw_bytes: bytes,
    filename: str,
    sheet_name: str | None = None,
    max_rows: int = 25,
) -> dict[str, Any]:
    df, sheets = read_dataframe_from_bytes(raw_bytes, filename, sheet_name=sheet_name)
    cols_info: list[dict[str, Any]] = []
    for col in df.columns:
        col_str = str(col)
        series = df[col].dropna()
        sample_vals = [
            v.item() if hasattr(v, "item") else (str(v) if isinstance(v, datetime) else v)
            for v in series.head(5).tolist()
        ]
        inferred = "numeric" if pd.api.types.is_numeric_dtype(df[col]) else "string"
        cols_info.append(
            {
                "name": col_str,
                "inferred_type": inferred,
                "sample_values": sample_vals,
                "Suggested_variable": _suggest_canonical_variable(col_str),
                "Suggested_unit": _suggest_unit(col_str),
            }
        )

    preview_df = df.head(max_rows).where(pd.notnull(df.head(max_rows)), None)
    rows_out: list[dict[str, Any]] = []
    for _, row in preview_df.iterrows():
        rdict: dict[str, Any] = {}
        for k, v in row.items():
            if v is None or (isinstance(v, float) and math.isnan(v)):
                rdict[str(k)] = None
            elif hasattr(v, "item"):
                rdict[str(k)] = v.item()
            elif isinstance(v, (datetime, pd.Timestamp)):
                rdict[str(k)] = v.isoformat()
            else:
                rdict[str(k)] = v
        rows_out.append(rdict)

    return {
        "sheets": sheets,
        "total_rows": int(len(df)),
        "columns": cols_info,
        "rows": rows_out,
    }


def _suggest_canonical_variable(col_name: str) -> str | None:
    low = col_name.lower()
    if "ph" in low:
        return "ph"
    if "do" in low or "dissolved_oxygen" in low or "dissolved oxygen" in low:
        return "dissolved_oxygen"
    if "temp" in low:
        return "temperature"
    if "rpm" in low or "stir" in low or "agit" in low:
        return "agitation_speed"
    if "air" in low or "sparg" in low:
        return "airflow"
    if "our" in low:
        return "our"
    if "cer" in low:
        return "cer"
    if "vol" in low:
        return "working_volume"
    if "feed" in low and ("rate" in low or "/h" in low):
        return "feed_rate"
    if "od" in low:
        return "od600"
    if "dcw" in low or "biomass" in low:
        return "biomass_dcw"
    if "titr" in low or "product" in low or "enzyme" in low:
        return "product_titre"
    if "power" in low:
        return "power_draw"
    return None


def _suggest_unit(col_name: str) -> str | None:
    low = col_name.lower()
    if "rpm" in low:
        return "rpm"
    if "% air" in low or "do" in low:
        return "percent_air_saturation"
    if "degc" in low or "°c" in low or "[c]" in low or "(c)" in low or "temp" in low:
        return "degC"
    if "l/min" in low or "slpm" in low:
        return "L/min"
    if "mmol" in low and "h" in low:
        return "mmol/(L*h)"
    if "g/l" in low:
        return "g/L"
    if "ml/h" in low:
        return "mL/h"
    if "ph" in low:
        return "pH"
    return None


def _check_physical_impossibility(variable: str, val_si: float) -> bool:
    if variable == "ph":
        return val_si < 0.0 or val_si > 14.0
    if variable == "temperature":
        return val_si <= 0.0  # K <= 0
    if variable in (
        "dissolved_oxygen",
        "dissolved_oxygen_conc",
        "agitation_speed",
        "airflow",
        "oxygen_flow",
        "gas_flow_total",
        "working_volume",
        "our",
        "cer",
        "power_draw",
        "od600",
        "biomass_dcw",
        "substrate_glucose",
        "product_titre",
    ):
        return val_si < 0.0
    return False


def validate_and_normalize_dataframe(
    df: pd.DataFrame,
    mapping: dict[str, Any],
) -> dict[str, Any]:
    """Run full column mapping, timestamp normalization, Pint unit conversion, and DQ-* checks."""
    issues: list[dict[str, Any]] = []
    conversions: list[dict[str, Any]] = []
    blocking = False

    if df.empty:
        issues.append(
            {
                "check_code": "DQ-FILE-EMPTY",
                "severity": "critical",
                "variable": None,
                "row_start": 0,
                "row_end": 0,
                "count": 1,
                "message": "Uploaded file contains zero data rows.",
            }
        )
        return {
            "rows_total": 0,
            "rows_imported": 0,
            "variables": [],
            "issues": issues,
            "conversions": [],
            "blocking": True,
            "normalized_measurements": [],
        }

    ts_cfg = mapping.get("timestamp", {})
    ts_col = ts_cfg.get("column")
    ts_kind = ts_cfg.get("kind", "elapsed")  # "elapsed" | "absolute"
    elapsed_unit = ts_cfg.get("elapsed_unit", "h")
    batch_start_str = mapping.get("batch_start") or "2026-11-01T00:00:00Z"
    try:
        batch_start_dt = datetime.fromisoformat(batch_start_str.replace("Z", "+00:00"))
    except Exception:
        batch_start_dt = datetime(2026, 11, 1, 0, 0, tzinfo=timezone.utc)

    if not ts_col or ts_col not in df.columns:
        issues.append(
            {
                "check_code": "DQ-TS-PARSE",
                "severity": "critical",
                "variable": None,
                "row_start": 1,
                "row_end": len(df),
                "count": len(df),
                "message": f"Timestamp column '{ts_col}' not found in file columns.",
            }
        )
        return {
            "rows_total": int(len(df)),
            "rows_imported": 0,
            "variables": [],
            "issues": issues,
            "conversions": [],
            "blocking": True,
            "normalized_measurements": [],
        }

    # Parse timestamps into (row_idx, ts_utc, elapsed_s)
    parsed_ts: list[tuple[int, datetime, float]] = []
    ts_fail_count = 0
    elapsed_factor = {"s": 1.0, "min": 60.0, "h": 3600.0}.get(elapsed_unit, 3600.0)

    for idx, raw_ts in enumerate(df[ts_col].tolist()):
        if raw_ts is None or (isinstance(raw_ts, float) and math.isnan(raw_ts)) or pd.isna(raw_ts):
            ts_fail_count += 1
            continue
        try:
            if ts_kind == "elapsed":
                el_s = float(raw_ts) * elapsed_factor
                dt_utc = batch_start_dt + timedelta(seconds=el_s)
                parsed_ts.append((idx, dt_utc, el_s))
            else:
                dt_parsed = pd.to_datetime(raw_ts, utc=True).to_pydatetime()
                el_s = (dt_parsed - batch_start_dt).total_seconds()
                parsed_ts.append((idx, dt_parsed, el_s))
        except Exception:
            ts_fail_count += 1

    if ts_fail_count > 0:
        fail_pct = (ts_fail_count / len(df)) * 100.0
        is_block = fail_pct > 5.0
        if is_block:
            blocking = True
        issues.append(
            {
                "check_code": "DQ-TS-PARSE",
                "severity": "high",
                "variable": None,
                "row_start": 1,
                "row_end": len(df),
                "count": ts_fail_count,
                "message": f"{ts_fail_count} row(s) ({fail_pct:.1f}%) had unparseable timestamps.",
            }
        )

    if parsed_ts:
        # Check monotonic order
        el_series = [p[2] for p in parsed_ts]
        non_mono = sum(1 for i in range(1, len(el_series)) if el_series[i] < el_series[i - 1])
        if non_mono > 0:
            issues.append(
                {
                    "check_code": "DQ-TS-ORDER",
                    "severity": "high",
                    "variable": None,
                    "row_start": 1,
                    "row_end": len(df),
                    "count": non_mono,
                    "message": f"Timestamps were non-monotonic at {non_mono} step(s); rows were sorted chronologically.",
                }
            )
            parsed_ts.sort(key=lambda x: x[2])
            el_series = [p[2] for p in parsed_ts]

        # Check duplicate timestamps
        dup_indices: set[int] = set()
        for i in range(1, len(parsed_ts)):
            if math.isclose(parsed_ts[i][2], parsed_ts[i - 1][2], abs_tol=1e-6):
                dup_indices.add(parsed_ts[i][0])
        if dup_indices:
            issues.append(
                {
                    "check_code": "DQ-TS-DUP",
                    "severity": "medium",
                    "variable": None,
                    "row_start": min(dup_indices) + 1,
                    "row_end": max(dup_indices) + 1,
                    "count": len(dup_indices),
                    "message": f"{len(dup_indices)} duplicate timestamp row(s) detected and flagged as 'suspect'.",
                }
            )

        # Check timestamp gaps (> 10x median interval)
        if len(el_series) >= 3:
            diffs = [el_series[i] - el_series[i - 1] for i in range(1, len(el_series)) if el_series[i] > el_series[i - 1]]
            if diffs:
                med_dt = float(np.median(diffs))
                if med_dt > 0:
                    large_gaps = [d for d in diffs if d > 10.0 * med_dt]
                    if large_gaps:
                        issues.append(
                            {
                                "check_code": "DQ-TS-GAP",
                                "severity": "medium",
                                "variable": None,
                                "row_start": 1,
                                "row_end": len(df),
                                "count": len(large_gaps),
                                "message": f"{len(large_gaps)} timestamp gap(s) exceeded 10x median sampling interval ({med_dt:.1f} s); max gap = {max(large_gaps):.1f} s.",
                            }
                        )
    else:
        dup_indices = set()

    col_Configs: list[dict[str, Any]] = mapping.get("columns", [])
    mapped_sources = {c.get("source") for c in col_Configs if c.get("variable")}
    unmapped = [str(c) for c in df.columns if str(c) != ts_col and str(c) not in mapped_sources]
    if unmapped:
        issues.append(
            {
                "check_code": "DQ-COL-UNMAPPED",
                "severity": "info",
                "variable": None,
                "row_start": 1,
                "row_end": 1,
                "count": len(unmapped),
                "message": f"Unmapped columns ignored: {', '.join(unmapped)}.",
            }
        )

    variables_summary: list[dict[str, Any]] = []
    normalized_measurements: list[dict[str, Any]] = []

    for col_cfg in col_Configs:
        src_col = col_cfg.get("source")
        var_key = col_cfg.get("variable")
        unit_orig = str(col_cfg.get("unit") or "").strip()
        prov = str(col_cfg.get("provenance") or "sensor")
        sensor_name = col_cfg.get("sensor_or_assay")
        cal_status = str(col_cfg.get("calibration_status") or "unknown")

        if not var_key or not src_col or src_col not in df.columns:
            continue

        spec = VARIABLE_UNIT_SPECS.get(var_key)
        if spec is None:
            blocking = True
            issues.append(
                {
                    "check_code": "DQ-UNIT-UNKNOWN",
                    "severity": "critical",
                    "variable": var_key,
                    "row_start": 1,
                    "row_end": len(df),
                    "count": 1,
                    "message": f"Unknown canonical variable '{var_key}'.",
                }
            )
            continue

        unit_si = str(spec["si"])
        unit_disp = str(spec["display"])

        # Test unit conversion once up front
        try:
            _ = convert_value(1.0, unit_orig, unit_si)
        except AmbiguousUnitError as exc:
            blocking = True
            issues.append(
                {
                    "check_code": "DQ-UNIT-AMBIGUOUS",
                    "severity": "high",
                    "variable": var_key,
                    "row_start": 1,
                    "row_end": len(df),
                    "count": 1,
                    "message": str(exc),
                }
            )
            continue
        except UnitDimensionError as exc:
            blocking = True
            issues.append(
                {
                    "check_code": "DQ-UNIT-UNKNOWN",
                    "severity": "critical",
                    "variable": var_key,
                    "row_start": 1,
                    "row_end": len(df),
                    "count": 1,
                    "message": str(exc),
                }
            )
            continue

        conversions.append(
            {
                "variable": var_key,
                "from_unit": unit_orig,
                "to_unit": unit_si,
                "method": "pint",
                "pint_version": PINT_VERSION,
            }
        )

        if var_key in ("ph", "dissolved_oxygen") and cal_status in ("unknown", "not_calibrated"):
            issues.append(
                {
                    "check_code": "DQ-CAL-UNKNOWN",
                    "severity": "low",
                    "variable": var_key,
                    "row_start": 1,
                    "row_end": len(df),
                    "count": 1,
                    "message": f"Sensor calibration status for '{var_key}' is '{cal_status}'.",
                }
            )

        col_values = df[src_col].tolist()
        missing_count = 0
        impossible_count = 0
        valid_si_vals: list[float] = []

        for row_idx, dt_utc, el_s in parsed_ts:
            raw_v = col_values[row_idx]
            if (
                raw_v is None
                or (isinstance(raw_v, float) and math.isnan(raw_v))
                or pd.isna(raw_v)
                or str(raw_v).strip() in ("", "NA", "N/A", "-", "NaN", "#VALUE!")
            ):
                missing_count += 1
                normalized_measurements.append(
                    {
                        "ts": dt_utc,
                        "elapsed_s": el_s,
                        "variable": var_key,
                        "value_original": None,
                        "unit_original": unit_orig,
                        "value_si": None,
                        "unit_si": unit_si,
                        "provenance": prov,
                        "sensor_or_assay": sensor_name,
                        "calibration_status": cal_status,
                        "quality_flag": "missing",
                        "source_row": row_idx + 1,
                    }
                )
                continue

            try:
                f_orig = float(raw_v)
                f_si = convert_value(f_orig, unit_orig, unit_si)
            except Exception:
                missing_count += 1
                continue

            qflag = "ok"
            if _check_physical_impossibility(var_key, f_si):
                qflag = "invalid"
                impossible_count += 1
            elif row_idx in dup_indices:
                qflag = "suspect"
            else:
                valid_si_vals.append(f_si)

            normalized_measurements.append(
                {
                    "ts": dt_utc,
                    "elapsed_s": el_s,
                    "variable": var_key,
                    "value_original": f_orig,
                    "unit_original": unit_orig,
                    "value_si": f_si,
                    "unit_si": unit_si,
                    "provenance": prov,
                    "sensor_or_assay": sensor_name,
                    "calibration_status": cal_status,
                    "quality_flag": qflag,
                    "source_row": row_idx + 1,
                }
            )

        if missing_count > 0:
            issues.append(
                {
                    "check_code": "DQ-VAL-MISSING",
                    "severity": "medium" if missing_count / max(1, len(parsed_ts)) > 0.1 else "low",
                    "variable": var_key,
                    "row_start": 1,
                    "row_end": len(df),
                    "count": missing_count,
                    "message": f"{missing_count} missing value(s) detected in '{var_key}'.",
                }
            )

        if impossible_count > 0:
            issues.append(
                {
                    "check_code": "DQ-VAL-IMPOSSIBLE",
                    "severity": "high",
                    "variable": var_key,
                    "row_start": 1,
                    "row_end": len(df),
                    "count": impossible_count,
                    "message": f"{impossible_count} physically impossible reading(s) in '{var_key}' flagged as 'invalid' and excluded from calculations.",
                }
            )

        min_si = min(valid_si_vals) if valid_si_vals else None
        max_si = max(valid_si_vals) if valid_si_vals else None
        min_disp = convert_value(min_si, unit_si, unit_disp) if min_si is not None else None
        max_disp = convert_value(max_si, unit_si, unit_disp) if max_si is not None else None

        variables_summary.append(
            {
                "variable": var_key,
                "unit_original": unit_orig,
                "unit_si": unit_si,
                "unit_display": unit_disp,
                "count": len(parsed_ts),
                "valid_count": len(valid_si_vals),
                "missing_count": missing_count,
                "invalid_count": impossible_count,
                "min_si": min_si,
                "max_si": max_si,
                "min_display": min_disp,
                "max_display": max_disp,
            }
        )

    return {
        "rows_total": int(len(df)),
        "rows_imported": len(parsed_ts),
        "variables": variables_summary,
        "issues": issues,
        "conversions": conversions,
        "blocking": blocking,
        "normalized_measurements": normalized_measurements,
        "start_time": parsed_ts[0][1] if parsed_ts else None,
        "end_time": parsed_ts[-1][1] if parsed_ts else None,
    }
