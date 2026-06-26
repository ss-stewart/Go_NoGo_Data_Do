#!/usr/bin/env python3
"""
Run the full ANT/SNC processing pipeline.

This script runs the ANT/SNC cleaner and analyzer in one step.

Usage:
    python3 ant_snc/run_ant_snc_pipeline.py -i path/to/raw_data -o ant_snc_output

Outputs:
    ant_snc_output/
    ├── cleaned/
    ├── ant_snc_error_rates.xlsx
    └── ant_snc_analysis.xlsx
"""

import argparse
import os
import pandas as pd

from ant_snc_analyze import compute_subject_metrics, read_cleaned_file
from ant_snc_cleaner import clean_subject, find_subject_files


def run_cleaning(input_dir: str, cleaned_dir: str, error_rate_file: str) -> None:
    """Clean raw ANT/SNC files and export participant error rates."""
    os.makedirs(cleaned_dir, exist_ok=True)
    os.makedirs(os.path.dirname(error_rate_file), exist_ok=True)

    groups = find_subject_files(input_dir)

    if not groups:
        raise FileNotFoundError("No ANT/SNC spreadsheet files were found.")

    error_rate_rows = []
    processed = 0
    skipped = 0

    for subject_id in sorted(groups):
        file_paths = groups[subject_id]

        try:
            cleaned_df, summary = clean_subject(file_paths)
        except Exception as exc:
            skipped += 1
            print(f"[pipeline] Skipping cleaner step for {subject_id}: {exc}")
            continue

        cleaned_path = os.path.join(cleaned_dir, f"{subject_id}_ant_snc_cleaned.csv")
        cleaned_df.to_csv(cleaned_path, index=False)

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
            }
        )
        processed += 1
        print(f"[pipeline] Cleaned {subject_id} -> {cleaned_path}")

    if not error_rate_rows:
        raise RuntimeError("No participant files were cleaned.")

    error_rate_df = pd.DataFrame(error_rate_rows)
    error_rate_df.to_excel(error_rate_file, index=False)

    print(
        "[pipeline] Cleaning complete. "
        f"Processed={processed}, Skipped={skipped}, "
        f"Error-rate file={error_rate_file}"
    )


def run_analysis(cleaned_dir: str, analysis_file: str) -> None:
    """Analyze cleaned ANT/SNC files and export participant metrics."""
    os.makedirs(os.path.dirname(analysis_file), exist_ok=True)

    cleaned_files = [
        os.path.join(cleaned_dir, filename)
        for filename in os.listdir(cleaned_dir)
        if filename.endswith(("_ant_snc_cleaned.csv", "_ant_snc_cleaned.xlsx"))
    ]
    cleaned_files = sorted(cleaned_files)

    if not cleaned_files:
        raise FileNotFoundError("No cleaned ANT/SNC files were found.")

    rows = []
    skipped = 0

    for filepath in cleaned_files:
        filename = os.path.basename(filepath)
        study_id = filename.replace("_ant_snc_cleaned.csv", "")
        study_id = study_id.replace("_ant_snc_cleaned.xlsx", "")
        try:
            df = read_cleaned_file(filepath)
            metrics = compute_subject_metrics(df, study_id)
        except Exception as exc:
            skipped += 1
            print(f"[pipeline] Skipping analysis step for {study_id}: {exc}")
            continue
        rows.append(metrics)
        print(f"[pipeline] Analyzed {study_id}")
    if not rows:
        raise RuntimeError("No participant metrics were created.")

    output_df = pd.DataFrame(rows)
    output_df.to_excel(analysis_file, index=False)
    print(
        "[pipeline] Analysis complete. "
        f"Analyzed={len(rows)}, Skipped={skipped}, Output={analysis_file}"
    )


def run_pipeline(input_dir: str, output_dir: str) -> None:
    """Run ANT/SNC cleaning and analysis."""
    input_dir = os.path.abspath(input_dir)
    output_dir = os.path.abspath(output_dir)

    cleaned_dir = os.path.join(output_dir, "cleaned")
    error_rate_file = os.path.join(output_dir, "ant_snc_error_rates.xlsx")
    analysis_file = os.path.join(output_dir, "ant_snc_analysis.xlsx")

    os.makedirs(output_dir, exist_ok=True)

    print(f"[pipeline] Input folder: {input_dir}")
    print(f"[pipeline] Output folder: {output_dir}")

    run_cleaning(input_dir, cleaned_dir, error_rate_file)
    run_analysis(cleaned_dir, analysis_file)

    print("[pipeline] ANT/SNC pipeline complete.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full ANT/SNC cleaner and analyzer pipeline."
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        required=True,
        help="Folder containing raw ANT/SNC files.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        required=True,
        help="Folder where all ANT/SNC pipeline output will be saved.",
    )
    args = parser.parse_args()

    run_pipeline(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
