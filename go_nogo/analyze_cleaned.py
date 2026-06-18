#!/usr/bin/env python3
"""
Part 2 + 3: Calculates Variables of Interest & Consolidating
Owner:    Hinton, Ph.D Laboratory
Version:  1.0

Usage:
    python analyze_cleaned.py 
    --input-dir cleaned_data/ 
    --exclude-file excluded_cleaning.txt 
    --output-file aggregate_metrics.xlsx
"""

import os
import glob
import argparse
import pandas as pd

# List of all metrics, per total (t), P-only (p), and R-only (r)
METRIC_COLS = [
    'go_nogo_accuracy_t','go_nogo_hits_t','go_nogo_omission_t','go_nogo_comission_t',
    'go_nogo_trueneg_t','go_nogo_120ms_t','go_nogo_RTmean_t','go_nogo_RTmed_t','go_nogo_RTstdev_t',
    'go_nogo_accuracy_p','go_nogo_hits_p','go_nogo_omission_p','go_nogo_comission_p',
    'go_nogo_trueneg_p','go_nogo_120ms_p','go_nogo_RTmean_p','go_nogo_RTmed_p','go_nogo_RTstdev_p',
    'go_nogo_accuracy_r','go_nogo_hits_r','go_nogo_omission_r','go_nogo_comission_r',
    'go_nogo_trueneg_r','go_nogo_120ms_r','go_nogo_RTmean_r','go_nogo_RTmed_r','go_nogo_RTstdev_r'
]

def compute_metrics(df):
    """
    Given cleaned df (incl. P/R trials, Correct recoded),
    returns a dict of all required metrics.
    """
    out = {}
    def tally(sub, sfx):
        out[f'go_nogo_accuracy_{sfx}'] = int(sub['Correct'].sum())
        out[f'go_nogo_hits_{sfx}']     = int(sub[(sub['Answer']=='Go')   & (sub['Attempt']==1) & (sub['Correct']==1)].shape[0])
        out[f'go_nogo_omission_{sfx}'] = int(sub[(sub['Answer']=='Go')   & (sub['Attempt'].isna()) & (sub['Correct']==0)].shape[0])
        out[f'go_nogo_comission_{sfx}']= int(sub[(sub['Answer']=='No Go')& (sub['Attempt']==1) & (sub['Correct']==0)].shape[0])
        out[f'go_nogo_trueneg_{sfx}']  = int(sub[(sub['Answer']=='No Go')& (sub['Attempt'].isna()) & (sub['Correct']==1)].shape[0])
        out[f'go_nogo_120ms_{sfx}']    = int((sub['Reaction Time'] < 120).sum())
        go_rt = sub[(sub['Answer']=='Go') & (sub['Correct']==1)]['Reaction Time'].dropna()
        out[f'go_nogo_RTmean_{sfx}']   = go_rt.mean()
        out[f'go_nogo_RTmed_{sfx}']    = go_rt.median()
        out[f'go_nogo_RTstdev_{sfx}']  = go_rt.std()

    if len(df) != 320:
        print(f"⚠️ Warning: expected 320 trials but got {len(df)}")

    # Total task
    tally(df, 't')
    # P-only trials
    tally(df[df['display']=='P Trials'], 'p')
    # R-only trials
    tally(df[df['display']=='R Trials'], 'r')

    return out    
        
def main():
    parser = argparse.ArgumentParser(
        description="Process cleaned Go/No-Go CSVs into aggregated Excel metrics"
    )
    parser.add_argument('-i','--input-dir',   required=True, help='Folder of cleaned per-subject CSVs')
    parser.add_argument('-e','--exclude-file',required=True, help='List of excluded subject IDs')
    parser.add_argument('-o','--output-file', required=True, help='Path to save aggregated Excel')
    args = parser.parse_args()

    # Load exclusions
    excluded = set()
    if os.path.exists(args.exclude_file):
        with open(args.exclude_file) as f:
            excluded = {line.strip() for line in f if line.strip()}
    print(f"[analyze] Excluding subjects: {sorted(excluded)}")

    # Collect metrics
    rows = []
    for fp in sorted(glob.glob(os.path.join(args.input_dir, '*.csv'))):
        subj = os.path.basename(fp).split('.')[0]
        if subj in excluded:
            print(f"[analyze] Skipping excluded {subj}")
            continue
        df = pd.read_csv(fp)
        metrics = compute_metrics(df)
        metrics['study_id'] = subj
        rows.append(metrics)

    # Write aggregated results
    agg_df = pd.DataFrame(rows, columns=METRIC_COLS + ['study_id'])
    agg_df.to_excel(args.output_file, index=False)
    print(f"✅ Saved aggregated metrics to {args.output_file}")

if __name__ == "__main__":
    main()