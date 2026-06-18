#!/usr/bin/env python3
import os
import glob
import tkinter as tk 
from tkinter import filedialog, messagebox
import pandas as pd
from data_cleaner import clean_subject, subject_id_from_path   
from analyze_cleaned import compute_metrics  

def main():
    root = tk.Tk(); root.withdraw() 
    
    # 1) Select the top-level data folder of per-subject folders
    root_dir = filedialog.askdirectory(title="Select folder containing Gorilla data exports (unzipped)")
    if not root_dir:
        messagebox.showinfo("Cancelled", "No folder selected.")
        return
    
    # 2) Discover spreadsheet files recursively and group by subject ID
    groups = {}
    pattern = os.path.join(root_dir, "**", "*.*")
    for fp in glob.glob(pattern, recursive=True):
        if not fp.lower().endswith((".csv", ".xlsx", ".xls")):
            continue
        sid = subject_id_from_path(fp)
        groups.setdefault(sid, []).append(fp)
        
    if not groups:
        messagebox.showwarning("No files", "No .csv/.xlsx found under that folder.")
        return
        
    # 3) Choose where to save clean CSVs
    clean_dir = filedialog.askdirectory(
        title="Select folder for cleaned CSVs"
    )
    if not clean_dir:
        messagebox.showinfo("Cancelled","No output folder chosen.")
        return
    os.makedirs(clean_dir, exist_ok=True)
    
    # 4) Clean each subject
    excluded = []
    cleaned = []
    for sid, fps in groups.items():
        if len(fps) < 2:
            messagebox.showwarning("Skipping", f"{sid}: found {len(fps)} file(s), need 2 task files.")
            continue
        # keep the two largest files to drop practice runs
        fps = sorted(fps, key=os.path.getsize, reverse=True)[:2]    
        try:             
            dfc, flag = clean_subject(fps)
        except Exception as ex:
            messagebox.showerror("Cleaning error", f"{sid}: {ex}")
            continue
        outp = os.path.join(clean_dir, f"{sid}.csv")
        try:
            dfc.to_csv(outp, index=False)
        except Exception as ex:
            messagebox.showerror("Write error", f"{sid}: {ex}")
            continue
        cleaned.append((sid, outp))
        if flag:
            excluded.append(sid)
            
    # 5) Choose destination filename for aggregated metrics (spreadsheet)
    agg_fp = filedialog.asksaveasfilename(
        title="Save aggregated",
        defaultextension=".xlsx",
        filetypes=[("Excel","*.xlsx")]
    )
    if not agg_fp:
        messagebox.showinfo("Cancelled","No save location.")
        return
    # 6) Analyze clean data
    rows = []
    for sid, path in cleaned:
        if sid in excluded: 
            continue
        try:
            df = pd.read_csv(path)
            m = compute_metrics(df)
        except Exception as ex:
            messagebox.showerror("Analysis error", f"{sid}: {ex}")
            continue
        m['study_id'] = sid
        rows.append(m)
    pd.DataFrame(rows).to_excel(agg_fp, index=False)
    
    # 7) Report status
    messagebox.showinfo("Done", f"Cleaned: {len(cleaned)}\nExcluded: {excluded}\nSaved: {agg_fp}")
    
if __name__ == "__main__":
    main()