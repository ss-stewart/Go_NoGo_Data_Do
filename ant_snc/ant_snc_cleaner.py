#!/usr/bin/env python3
""" 
Part 1/3: Prepares Dataset
Owner: Hinton, Ph.D Laboratory
Version 1.0

This script cleans ANT/SNC task files and exports:
1. A cleaned, error-removed CSV per participant.
2. A separate spreadsheet of participant-level error rates.

Usage:
    TBD
"""

import os
import glob
import argparse
import re
import pathlib
import pandas as pd

REQUIRED_COLS = [
    "Task name",
    "Reaction Time",
    "Attempt outcome",
    "Cue type",
    "Location",
    "Congruency",
]

COLUMN_ALIASES = {
    "task name": "Task name",
    "task": "Task name",
    "task_name": "Task name",
    "reaction time": "Reaction Time",
    "reaction time rt": "Reaction Time",
    "reaction time (rt)": "Reaction Time",
    "rt": "Reaction Time",
    "response time": "Reaction Time",
    "attempt outcome": "Attempt outcome",
    "attempt": "Attempt outcome",
    "outcome": "Attempt outcome",
    "correct": "Attempt outcome",
    "accuracy": "Attempt outcome",
    "cue type": "Cue type",
    "cue": "Cue type",
    "location": "Location",
    "target location": "Location",
    "congruency": "Congruency",
    "congruent": "Congruency",
}

def normalize_text(value: object) -> str:
    """Normalize text values for safer matching."""
    if pd.isna(value):
        return ""
    return str(value).strip()

def normalize_column_key(column_name: str) -> str:
    """Normalize a raw column name before checking aliases."""
    cleaned = str(column_name).strip().lower()
    cleaned = cleaned.replace("_", " ")
    cleaned = cleaned.replace("-", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned

def subject_id_from_path(filepath: str, input_dir: str) -> str:
    """
    Derive subject ID from the first folder inside the input directory.
    Eg. data/322 ANT_SNC/file.xlsx -> 322
    """
    relative_path = os.path.relpath(filepath, input_dir)
    parts = pathlib.Path(relative_path).parts

    if len(parts) > 1:
        folder_name = parts[0]
    else:
        folder_name = pathlib.Path(filepath).stem
           
    digit_match = re.search(r"\d+", folder_name)
    if digit_match:
        return digit_match.group(0)
    return folder_name.strip().replace(" ", "_")

def read_spreadsheet(filepath: str) -> pd.DataFrame:
    """Read a CSV or Excel file into a DataFrame."""
    suffix = pathlib.Path(filepath).suffix.lower()
    
    if suffix == ".csv":
        return pd.read_csv(filepath)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(filepath)
    raise ValueError(f"Unsupported file type: {filepath}")

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename known raw columns to the standard ANT/SNC column names."""
    rename_map = {}

    for column in df.columns:
        normalized = normalize_column_key(column)
        if normalized in COLUMN_ALIASES:
            rename_map[column] = COLUMN_ALIASES[normalized]
    return df.rename(columns=rename_map)

def has_required_columns(df: pd.DataFrame) -> bool:
    """Check whether a file contains the columns needed for ANT/SNC cleaning."""
    return all(column in df.columns for column in REQUIRED_COLS)

def find_subject_files(input_dir: str) -> dict[str, list[str]]:
    """
    Recursively discover ANT/SNC spreadsheets and group by subject.
    """
    patterns = [
        os.path.join(input_dir, "**", "*.csv"),
        os.path.join(input_dir, "**", "*.xlsx"),
        os.path.join(input_dir, "**", "*.xls"),
    ]

    groups: dict[str, list[str]] = {}

    for pattern in patterns:
        for filepath in glob.glob(pattern, recursive=True):
            filename = os.path.basename(filepath)
            if filename.startswith("~$"):
                continue
            subject_id = subject_id_from_path(filepath, input_dir)
            groups.setdefault(subject_id, []).append(filepath)
    return groups

def is_error_trial(value: object) -> bool:
    """
    Identify error trials from Attempt Outcome column.
    Supports common labels such as incorrect/error/wrong/false/0.
    """
    normalized = normalize_text(value).lower()

    if normalized in {"incorrect", "error", "wrong", "false", "0", "no"}:
        return True
    return False

def clean_subject(file_paths: list[str]) -> tuple[pd.DataFrame, dict]:
    """
    Clean individual participant's files.

    Error rate is calculated after removing blank rows, missing RT rows,
    and RT = 1500 timeout rows.

    The exported cleaned CSV removes error trials so RT analysis uses
    correct, non-timeout trials only.
    """
    readable_frames = []
    source_files_used = []

    for filepath in file_paths:
        try:
            raw_df = read_spreadsheet(filepath)
        except Exception as exc:
            print(f"[ant_snc_cleaner] Skipping unreadable file: {filepath}")
            print(f"  Reason: {exc}")
            continue

        raw_df = standardize_columns(raw_df)

        if not has_required_columns(raw_df):
            continue

        readable_frames.append(raw_df[REQUIRED_COLS].copy())
        source_files_used.append(filepath)

    if not readable_frames:
        raise ValueError("No readable ANT/SNC files with the required columns were found.")

    combined = pd.concat(readable_frames, ignore_index=True)

    starting_rows = len(combined)

    combined = combined.dropna(how="all")
    blank_rows_removed = starting_rows - len(combined)

    combined["Reaction Time"] = pd.to_numeric(
        combined["Reaction Time"],
        errors="coerce",
    )

    before_rt_filter = len(combined)
    combined = combined.dropna(subset=["Reaction Time"])
    rt_missing_removed = before_rt_filter - len(combined)

    before_timeout_filter = len(combined)
    combined = combined[combined["Reaction Time"] != 1500].copy()
    timeout_1500_removed = before_timeout_filter - len(combined)

    combined["is_error_trial"] = combined["Attempt outcome"].apply(is_error_trial)

    n_total_trials = len(combined)
    n_error_trials = int(combined["is_error_trial"].sum())

    if n_total_trials == 0:
        error_rate = None
    else:
        error_rate = n_error_trials / n_total_trials

    cleaned = combined[~combined["is_error_trial"]].copy()
    cleaned = cleaned.drop(columns=["is_error_trial"])

    cleaning_summary = {
        "source_file_count": len(source_files_used),
        "source_files": "; ".join(source_files_used),
        "starting_rows": starting_rows,
        "blank_rows_removed": blank_rows_removed,
        "rt_missing_removed": rt_missing_removed,
        "timeout_1500_removed": timeout_1500_removed,
        "n_total_trials": n_total_trials,
        "n_error_trials": n_error_trials,
        "error_rate": error_rate,
        "n_rows_exported": len(cleaned),
    }
    
    return cleaned, cleaning_summary

def main():
    parser = argparse.ArgumentParser(
        description="Clean extracted ANT/SNC task files."
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        required=True,
        help="Folder containing per-subject ANT/SNC folders/files.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        required=True,
        help="Folder to save cleaned per-subject CSVs.",
    )
    parser.add_argument(
        "--error-rate-file",
        required=True,
        help="Path to save participant error-rate spreadsheet.",
    )
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)
    error_rate_file = os.path.abspath(args.error_rate_file)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(error_rate_file), exist_ok=True)
    
    print(f"[ant_snc_cleaner] Input folder: {input_dir}")
    print(f"[ant_snc_cleaner] Output folder: {output_dir}")
    print(f"[ant_snc_cleaner] Error rate file: {error_rate_file}")

    groups = find_subject_files(input_dir)

    if not groups:
        print("[ant_snc_cleaner] No spreadsheet files were found.")
        return

    error_rate_rows = []
    processed = 0
    skipped = 0

    for subject_id in sorted(groups):
        file_paths = groups[subject_id]
        try:
            cleaned_df, summary = clean_subject(file_paths)
        except Exception as exc:
            skipped += 1
            print(f"[ant_snc_cleaner] Skipping participant {subject_id}: {exc}")
            continue

        output_path = os.path.join(output_dir, f"{subject_id}_ant_snc_cleaned.csv")
        cleaned_df.to_csv(output_path, index=False)

        error_rate_rows.append(
            {
                "study_id": subject_id,
                "source_file_count": summary["source_file_count"],
                "starting_rows": summary["starting_rows"],
                "blank_rows_removed": summary["blank_rows_removed"],
                "rt_missing_removed": summary["rt_missing_removed"],
                "timeout_1500_removed": summary["timeout_1500_removed"],
                "n_total_trials": summary["n_total_trials"],
                "n_error_trials": summary["n_error_trials"],
                "error_rate": summary["error_rate"],
                "n_rows_exported": summary["n_rows_exported"],
                "source_files": summary["source_files"],
            })

        processed += 1
        print(f"[ant_snc_cleaner] Wrote {subject_id} -> {output_path}")

    error_rate_df = pd.DataFrame(error_rate_rows)
    error_rate_df.to_excel(error_rate_file, index=False)

    print(
        "[ant_snc_cleaner] Complete. "
        f"Processed={processed}, Skipped={skipped}, "
        f"Error-rate rows={len(error_rate_rows)}"
    )

if __name__ == "__main__":
    main()
