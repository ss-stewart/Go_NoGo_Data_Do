#!/usr/bin/env python3
"""
Part 2/3: Analyze cleaned ANT/SNC data.
Owner:    Hinton, Ph.D Laboratory
Version:  1.0

This script reads cleaned ANT/SNC participant files and exports
participant-level RT summaries and ANT network scores.

Expected input:
    Cleaned CSV files created by ant_snc_cleaner.py.

Outputs:
    One aggregated Excel file with participant-level metrics.

Usage:
    python3 ant_snc/ant_snc_analyze.py -i ant_snc_cleaned -o ant_snc_analysis.xlsx
"""

import re
import os
import glob
import argparse
import pandas as pd

from pathlib import Path

REQUIRED_COLS = [
    "Task name",
    "Reaction Time",
    "Attempt outcome",
    "Cue type",
    "Location",
    "Congruency",
]


def normalize_text(value: object) -> str:
    """Normalize text values for safer matching."""
    if pd.isna(value):
        return ""

    return str(value).strip()


def normalize_condition(value: object) -> str:
    """Normalize condition labels for consistent comparisons."""
    cleaned = normalize_text(value).lower()
    cleaned = cleaned.replace("_", " ")
    cleaned = cleaned.replace("-", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def subject_id_from_filename(filepath: str) -> str:
    """
    Derive participant ID from a cleaned ANT/SNC filename.

    Example:
        322_ant_snc_cleaned.csv -> 322
    """
    stem = Path(filepath).stem
    return stem.replace("_ant_snc_cleaned", "")


def read_cleaned_file(filepath: str) -> pd.DataFrame:
    """Read a cleaned CSV or Excel file."""
    suffix = Path(filepath).suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(filepath)

    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(filepath)

    raise ValueError(f"Unsupported file type: {filepath}")


def safe_mean(series: pd.Series) -> float | None:
    """Return mean if possible, otherwise None."""
    values = pd.to_numeric(series, errors="coerce").dropna()

    if values.empty:
        return None

    return float(values.mean())


def safe_median(series: pd.Series) -> float | None:
    """Return median if possible, otherwise None."""
    values = pd.to_numeric(series, errors="coerce").dropna()

    if values.empty:
        return None

    return float(values.median())


def safe_sd(series: pd.Series) -> float | None:
    """Return sample standard deviation if possible, otherwise None."""
    values = pd.to_numeric(series, errors="coerce").dropna()

    if len(values) < 2:
        return None

    return float(values.std(ddof=1))


def safe_se(series: pd.Series) -> float | None:
    """Return standard error if possible, otherwise None."""
    values = pd.to_numeric(series, errors="coerce").dropna()
    sd = safe_sd(values)

    if sd is None or len(values) == 0:
        return None

    return float(sd / (len(values) ** 0.5))


def safe_cv(series: pd.Series) -> float | None:
    """
    Return coefficient of variation using the study team's convention.

    Note:
        This project uses Mean / SD, matching the team workflow notes.
        Standard statistical CV is usually SD / Mean.
    """
    mean = safe_mean(series)
    sd = safe_sd(series)

    if mean is None or sd in {None, 0}:
        return None

    return float(mean / sd)


def add_rt_summary(metrics: dict, prefix: str, series: pd.Series) -> None:
    """Add mean, median, SD, CV, N, and SE metrics for one RT series."""
    values = pd.to_numeric(series, errors="coerce").dropna()

    metrics[f"{prefix}_mean"] = safe_mean(values)
    metrics[f"{prefix}_median"] = safe_median(values)
    metrics[f"{prefix}_sd"] = safe_sd(values)
    metrics[f"{prefix}_cv"] = safe_cv(values)
    metrics[f"{prefix}_n"] = int(len(values))
    metrics[f"{prefix}_se"] = safe_se(values)


def condition_mask(
    df: pd.DataFrame, column: str, accepted_values: set[str]
) -> pd.Series:
    """Return mask for rows whose normalized column value matches accepted values."""
    return df[column].apply(normalize_condition).isin(accepted_values)


def get_condition_rt(
    df: pd.DataFrame,
    column: str,
    accepted_values: set[str],
    rt_column: str = "Reaction Time",
) -> pd.Series:
    """Return RT values for one condition."""
    return df.loc[condition_mask(df, column, accepted_values), rt_column]


def difference(left: float | None, right: float | None) -> float | None:
    """Return left - right when both values exist."""
    if left is None or right is None:
        return None
    return float(left - right)


def add_network_scores(
    metrics: dict, df: pd.DataFrame, rt_column: str, prefix: str
) -> None:
    """
    Add ANT network scores using mean and median RT values.

    Executive control:
        Incongruent RT - Congruent RT
    Alerting:
        No cue RT - Double cue RT
    Orienting:
        Center cue RT - Spatial cue RT

    Spatial cue includes both up and down cue labels.
    """
    congruent_rt = get_condition_rt(df, "Congruency", {"congruent"}, rt_column)
    incongruent_rt = get_condition_rt(df, "Congruency", {"incongruent"}, rt_column)

    no_cue_rt = get_condition_rt(
        df,
        "Cue type",
        {"no cue", "nocue", "none"},
        rt_column,
    )
    double_cue_rt = get_condition_rt(
        df,
        "Cue type",
        {"double cue", "double"},
        rt_column,
    )
    center_cue_rt = get_condition_rt(
        df,
        "Cue type",
        {"center cue", "centre cue", "center", "centre"},
        rt_column,
    )
    spatial_cue_rt = get_condition_rt(
        df,
        "Cue type",
        {
            "spatial cue",
            "spatial",
            "up cue",
            "down cue",
            "up",
            "down",
        },
        rt_column,
    )

    congruent_mean = safe_mean(congruent_rt)
    incongruent_mean = safe_mean(incongruent_rt)
    no_cue_mean = safe_mean(no_cue_rt)
    double_cue_mean = safe_mean(double_cue_rt)
    center_cue_mean = safe_mean(center_cue_rt)
    spatial_cue_mean = safe_mean(spatial_cue_rt)
    congruent_median = safe_median(congruent_rt)
    incongruent_median = safe_median(incongruent_rt)
    no_cue_median = safe_median(no_cue_rt)
    double_cue_median = safe_median(double_cue_rt)
    center_cue_median = safe_median(center_cue_rt)
    spatial_cue_median = safe_median(spatial_cue_rt)

    metrics[f"{prefix}_executive_control_mean"] = difference(
        incongruent_mean,
        congruent_mean,
    )
    metrics[f"{prefix}_alerting_mean"] = difference(
        no_cue_mean,
        double_cue_mean,
    )
    metrics[f"{prefix}_orienting_mean"] = difference(
        center_cue_mean,
        spatial_cue_mean,
    )
    metrics[f"{prefix}_executive_control_median"] = difference(
        incongruent_median,
        congruent_median,
    )
    metrics[f"{prefix}_alerting_median"] = difference(
        no_cue_median,
        double_cue_median,
    )
    metrics[f"{prefix}_orienting_median"] = difference(
        center_cue_median,
        spatial_cue_median,
    )


def compute_subject_metrics(df: pd.DataFrame, study_id: str) -> dict:
    """Compute participant-level ANT/SNC RT and network metrics."""
    missing_cols = [column for column in REQUIRED_COLS if column not in df.columns]

    if missing_cols:
        missing = ", ".join(missing_cols)
        raise ValueError(f"Missing required columns: {missing}")

    df = df.copy()
    df["Reaction Time"] = pd.to_numeric(df["Reaction Time"], errors="coerce")
    df = df.dropna(subset=["Reaction Time"])

    metrics = {"study_id": study_id}

    add_rt_summary(metrics, "overall_rt", df["Reaction Time"])
    add_rt_summary(
        metrics,
        "congruent_rt",
        get_condition_rt(df, "Congruency", {"congruent"}),
    )
    add_rt_summary(
        metrics,
        "incongruent_rt",
        get_condition_rt(df, "Congruency", {"incongruent"}),
    )
    add_rt_summary(
        metrics,
        "no_cue_rt",
        get_condition_rt(df, "Cue type", {"no cue", "nocue", "none"}),
    )
    add_rt_summary(
        metrics,
        "double_cue_rt",
        get_condition_rt(df, "Cue type", {"double cue", "double"}),
    )
    add_rt_summary(
        metrics,
        "center_cue_rt",
        get_condition_rt(
            df,
            "Cue type",
            {"center cue", "centre cue", "center", "centre"},
        ),
    )
    add_rt_summary(
        metrics,
        "spatial_cue_rt",
        get_condition_rt(
            df,
            "Cue type",
            {"spatial cue", "spatial", "up cue", "down cue", "up", "down"},
        ),
    )
    add_network_scores(metrics, df, "Reaction Time", "raw")

    overall_mean = safe_mean(df["Reaction Time"])
    overall_sd = safe_sd(df["Reaction Time"])

    if overall_mean is not None and overall_sd not in {None, 0}:
        df["Reaction Time Z"] = (df["Reaction Time"] - overall_mean) / overall_sd
        add_network_scores(metrics, df, "Reaction Time Z", "z")
    else:
        metrics["z_executive_control_mean"] = None
        metrics["z_alerting_mean"] = None
        metrics["z_orienting_mean"] = None
        metrics["z_executive_control_median"] = None
        metrics["z_alerting_median"] = None
        metrics["z_orienting_median"] = None

    return metrics


def find_cleaned_files(input_dir: str) -> list[str]:
    """Find cleaned ANT/SNC participant files."""
    patterns = [
        os.path.join(input_dir, "*_ant_snc_cleaned.csv"),
        os.path.join(input_dir, "*_ant_snc_cleaned.xlsx"),
        os.path.join(input_dir, "*_ant_snc_cleaned.xls"),
    ]

    files = []

    for pattern in patterns:
        files.extend(glob.glob(pattern))
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze cleaned ANT/SNC CSVs and export aggregated metrics."
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        required=True,
        help="Folder containing cleaned per-subject ANT/SNC CSVs.",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        required=True,
        help="Path to save aggregated ANT/SNC analysis spreadsheet.",
    )
    args = parser.parse_args()
    input_dir = os.path.abspath(args.input_dir)
    output_file = os.path.abspath(args.output_file)

    output_parent = os.path.dirname(output_file)

    if output_parent:
        os.makedirs(output_parent, exist_ok=True)

    print(f"[ant_snc_analyze] Input folder: {input_dir}")
    print(f"[ant_snc_analyze] Output file: {output_file}")

    cleaned_files = find_cleaned_files(input_dir)

    if not cleaned_files:
        print("[ant_snc_analyze] No cleaned ANT/SNC files were found.")
        return

    rows = []
    skipped = 0

    for filepath in cleaned_files:
        study_id = subject_id_from_filename(filepath)
        try:
            df = read_cleaned_file(filepath)
            metrics = compute_subject_metrics(df, study_id)
        except Exception as exc:
            skipped += 1
            print(f"[ant_snc_analyze] Skipping {study_id}: {exc}")
            continue

        rows.append(metrics)
        print(f"[ant_snc_analyze] Analyzed {study_id}")

    if not rows:
        print("[ant_snc_analyze] No participant metrics were created.")
        return

    output_df = pd.DataFrame(rows)
    output_df.to_excel(output_file, index=False)

    print(
        "[ant_snc_analyze] Complete. "
        f"Analyzed={len(rows)}, Skipped={skipped}, Output={output_file}"
    )


if __name__ == "__main__":
    main()
