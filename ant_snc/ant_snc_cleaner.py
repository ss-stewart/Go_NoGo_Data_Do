#!/usr/bin/env python3
""" 
Part 1/3: Preparing the dataset (Data Cleaning)
Owner: Hinton, Ph.D Laboratory
Version 1.0

Usage:
    TBD
"""

import os
import glob
import argparse
import pandas as pd

REQUIRED_COLS = [
    "Task name",
    "Reaction Time",
    "Attempt outcome",
    "Cue type",
    "Location",
    "Congruency",
]

def subject_id_from_path(filepath: str) -> str:
    """
    STUB: derive subject ID from the participant folder name.

    Example:
        data/322 ANT SNC/file.xlsx -> 322
    """
    raise NotImplementedError("subject_id_from_path not yet implemented.")

def find_subject_files(input_dir: str) -> dict:
    """
    STUB: recursively discover ANT/SNC files and group them by subject.

    Returns:
        {
            "322": ["path/to/block1.xlsx", "path/to/block2.xlsx"],
            ...
        }
    """
    raise NotImplementedError("find_subject_files not yet implemented.")

def clean_subject(file_paths: list[str]) -> tuple[pd.DataFrame, dict]:
    """
    STUB: merge ANT/SNC block files, clean rows, and calculate error rate.

    Returns:
        cleaned_df:
            cleaned participant-level dataframe
        error_summary:
            dictionary containing subject-level error-rate information
    """
    raise NotImplementedError("clean_subject not yet implemented.")

def main():
    parser = argparse.ArgumentParser(
        description="Clean manually downloaded ANT/SNC task files and export error rates."
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

    print("[ant_snc_cleaner] Scaffold only")
    print(f"[ant_snc_cleaner] input-dir = {os.path.abspath(args.input_dir)}")
    print(f"[ant_snc_cleaner] output-dir = {os.path.abspath(args.output_dir)}")
    print(f"[ant_snc_cleaner] error-rate-file = {os.path.abspath(args.error_rate_file)}")

if __name__ == "__main__":
    main()
