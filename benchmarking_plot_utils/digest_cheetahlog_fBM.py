#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Derives a pandas data frame/csv output from the Cheetah log file in [bench] modus

Cheetah log time is in sec, durations from benchmarking is in ns
The calc_start times are the CALCULATED start times as  time-duration from
[bench]...[time]... duration

for cheetah_start/end [control] log times are used

Currently covered modules:
    rfim (iqrm only)
    ddtr (klotski, corner turn,...)
    spdt
    spsclustering (FoF, HDBSCan)
    spsift (only total)
    psbc
    fdas_laby
    strongSift
    simpleSift
    fldo    

Two csv files are produced

(1) outroot+ _durations.csv 
(2) outroot+ _forBM.csv

Both have columns:
__orig_index", "calc_start",  "dur_ns", "name"

(1) includes outputs from multiple duration outputs (e.g., corner turn, spdt) 
for which the standard calculated starting times (calc_start) are NOT correct
because they simply use the cheetah log timestamp and do not account for the 
multiple-process (DDTR,SPDT) nature - These durations are marked with _NoST in their name
They can be still used, for instance, to plot benchmarked process durations in histograms

(2) removed the ..NoST entries. The remaining entries should be good to overplot withbenchmon 

Note 1 : The current calc_start accuracy is 1s (because of timestamp in cheetah logfile)
         Durations have ns accuracy
Note 2 : multiple beams can currently not be differentiate in the log level

@author: bposselt
"""
import pandas as pd
import numpy as np
import re
import warnings

#================== Input directoy, input log file, output name root
indir = "/home/bposselt/benchmark_worker1b/Nov1025/cheetah/"
infile="cheetah_fdas_101125_ThresholdON_FoFon.txt"
outfile_root="cheetah_fdas_101125_ThresholdON_FoFon_extract"

#========================================================================

with open(indir+infile) as f:
    lines = f.readlines()

records = []
for line in lines:
    # Extract parts inside [ ] and the trailing message
    # .*? is non-greedy — it stops as soon as it finds the first possible 
    # closing bracket ], then starts again after that.
    parts = re.findall(r'\[(.*?)\]', line)
    
    # \d+ means one or more digits in [], 
    # splitting and [-1] gives the last chunk, i.e. what comes after the final [number]
    message = re.split(r'\[\d+\]', line)[-1].strip()  # text after last [number]
    
    if len(parts) >= 4:
        entry_type = parts[0]             # e.g. control, log, bench
        thread_id = parts[1].split('=')[1]  # e.g. tid=... get just the number
        # parts[2] = file path + line number (to drop)
        numeric_value = int(parts[3])     # convert to integer
        records.append([entry_type, thread_id, numeric_value, message])

# Build DataFrame
df = pd.DataFrame(records, columns=["type", "thread_id", "time_in_s", "message"])

# intermediate output - cheetah log as a pandas dataframe
print('chaeetah Log as pandas dataframe:')
print(df)
print()

# get the unique (based on first 20 characters) log message beginnings
unique_prefixes = df["message"].str.slice(0, 20).unique()
print('Unique starting first 20 characters in line in Cheetah logfile')
print(unique_prefixes)
print()

# define all the names + numbers we want to extract from the cheetah config
# can be expanded to include new modules - if not in here it will not be extracted!
config = {
    "rfim_iqrm": {
        "pattern": r'(?i)^RFIM_iqrm_all duration',
        "processors": [
        # We'll extract dur_ns then compute calc_start
        # lambda wrapper to do calculation.
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                # capture group for the duration number
                regex=r'RFIM_iqrm_all duration\s+\(ns\):\s+(\d+)',
                out_col="dur_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="dur_ns", 
                                          out_col="calc_start")
        ]
    },
    "klotski": {
        "pattern": r'(?i)^Klotski Total duration',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                regex=r'Klotski Total duration\s+\(ns\):\s+(\d+)',
                out_col="dur_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="dur_ns", 
                                          out_col="calc_start")
        ]
    },
    # NoST = No Starting Time means that the calculated starting time 
    #        is NOT the actual starting time, just a stand-in
    # these entries should only be used to plot the histograms, not the benchmon+process plot
    # out col has to be different than the rest, but should have "_ns" at the end
    "klotski_ddtr_NoST": {
        "pattern": r'(?i)^Klotski Total duration',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                regex=r'ddtr duration:\s+(\d+)',
                #needed as it would otherwise overwrite  total duration above
                out_col="ddtr_ns",
                dtype=float
            ),
            # compute a calc_start using ddtr_ns (so the subframe has calc_start) == but it is NOT the correct DDTR start time
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s",
                                          dur_ns_col="ddtr_ns",
                                          out_col="calc_start")
            ]
    },
    "klotski_corner_NoST": {
        "pattern": r'(?i)^Klotski Total duration',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                regex=r'corner_turn duration:\s+(\d+)',
                #needed as it would otherwise overwrite  total duration above
                out_col="corner_ns",
                dtype=float
            ),
            # compute a calc_start using ddtr_ns (so the subframe has calc_start) == but it is NOT the correct DDTR start time
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s",
                                          dur_ns_col="corner_ns",
                                          out_col="calc_start")
            ]
    },
    "klotski_spdt_NoST": {
        "pattern": r'(?i)^Klotski Total duration',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                regex=r'spdt duration:\s+(\d+)',
                #needed as it would otherwise overwrite  total duration above
                out_col="spdt_ns",
                dtype=float
            ),
            # compute a calc_start using ddtr_ns (so the subframe has calc_start) == but it is NOT the correct DDTR start time
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s",
                                          dur_ns_col="spdt_ns",
                                          out_col="calc_start")
            ]
    },
    
    "spsift": {
        "pattern": r'(?i)^SPSIFT_end',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                regex=r'SPSIFT_end total duration\s+\(ns\):\s+(\d+)',
                out_col="dur_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="dur_ns", 
                                          out_col="calc_start")
        ]
    },
    "spsift_Thresh_NoST": {
        "pattern": r'(?i)^SPSIFT_Thresh_iter duration',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                regex=r'SPSIFT_Thresh_iter duration\s+\(ns\):\s+(\d+)',
                out_col="thresh_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="thresh_ns", 
                                          out_col="calc_start")
        ]
    },
    "spscluster": {
        "pattern": r'(?i)^SPS_CLUSTERING Total duration',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                regex=r'SPS_CLUSTERING Total duration\s+\(ns\):\s+(\d+)',
                out_col="dur_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="dur_ns", 
                                          out_col="calc_start")
        ]
    },
    "spscluster_FoF_rtree_NoST": {
        "pattern": r'(?i)^SPS_CLUSTERING_FoF durations',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                regex=r'- rTree:\s+(\d+)',
                out_col="fofrtree_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="fofrtree_ns", 
                                          out_col="calc_start")
        ]
    },
    "spscluster_FoF_MakeClstr_NoST": {
        "pattern": r'(?i)^SPS_CLUSTERING_FoF durations',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                regex=r'MakeClstr:\s+(\d+)',
                out_col="fofmakec_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="fofmakec_ns", 
                                          out_col="calc_start")
        ]
    },
    "spscluster_HDBSCAN_SpanTree_NoST": {
        "pattern": r'(?i)^SPS_CLUSTERING_HDBSCAN durations',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                regex=r'SpanTree:\s+(\d+)',
                out_col="hdbscan_stree_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="hdbscan_stree_ns", 
                                          out_col="calc_start")
        ]
    },
    "spscluster_HDBSCAN_MakeClstr_NoST": {
        "pattern": r'(?i)^SPS_CLUSTERING_HDBSCAN durations',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                # capture group for the duration number
                regex=r'MakeClstr:\s+(\d+)',
                out_col="hdbscan_makec_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="hdbscan_makec_ns", 
                                          out_col="calc_start")
        ]
    },
    "spscluster_HDBSCAN_WidthClstr_NoST": {
        "pattern": r'(?i)^SPS_CLUSTERING_HDBSCAN durations',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                # capture group for the duration number
                regex=r'WidthClstr:\s+(\d+)',
                out_col="hdbscan_widthc_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="hdbscan_widthc_ns", 
                                          out_col="calc_start")
        ]
    },
    "FDAS_laby": {
        "pattern": r'(?i)^FDAS_laby_end',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                # capture group for the duration number
                regex=r'FDAS_laby_end total duration\s+\(ns\):\s+(\d+)',
                out_col="dur_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="dur_ns", 
                                          out_col="calc_start")
        ]
    },
    "strongSIFT": {
        "pattern": r'(?i)^strongSIFT duration',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                # capture group for the duration number
                regex=r'strongSIFT duration\s+\(ns\):\s+(\d+)',
                out_col="dur_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="dur_ns", 
                                          out_col="calc_start")
        ]
    },
    "simpleSIFT": {
        "pattern": r'(?i)^simpleSIFT duration',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                # capture group for the duration number
                regex=r'simpleSIFT duration\s+\(ns\):\s+(\d+)',
                out_col="dur_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="dur_ns", 
                                          out_col="calc_start")
        ]
    },    
    "fldo": {
        "pattern": r'(?i)^FLDO_ended',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                regex=r'FLDO_ended FLDO Total duration\s+\(ns\):\s+(\d+)',
                out_col="dur_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col="time_in_s", 
                                          dur_ns_col="dur_ns", 
                                          out_col="calc_start")
        ]
    },
    "psbc": {
        "pattern": r'(?i)^PSBC duration',
        "processors": [
            lambda df: extract_to_numeric(
                df,
                source_col="message",
                # capture group for the duration number
                regex=r'PSBC duration\s+\(ns\):\s+(\d+)',
                out_col="dur_ns",
                dtype=float
            ),
            lambda df: compute_calc_start(df, 
                                          time_col=
                                          "time_in_s", 
                                          dur_ns_col="dur_ns", 
                                          out_col="calc_start")
            ]
    }    
   }



# ---------- helper routines

def extract_to_numeric(df, source_col, regex, out_col, dtype=float):
    """
    Extract one capture group (first) from 'source_col' using regex and
    store as numeric in 'out_col'.
    - regex must have one capturing group to extract.
    - returns the modified df (in-place).
    - check if empty, put in NaN values if it is
    """
    df = df.copy()
    if source_col not in df.columns:
        # nothing to extract, create empty column
        df[out_col] = pd.Series([pd.NA]*len(df), index=df.index).astype("float")
        return df
    
    df[out_col] = df[source_col].str.extract(regex, expand=False)
    # convert to numeric, coercing errors to NaN
    df[out_col] = pd.to_numeric(df[out_col], errors="coerce")
    
    # only cast to dtype if there actual not-NaN value 
    if df[out_col].notna().any():
        df[out_col] = df[out_col].astype(dtype)
   
    return df


def extract_named_groups(df, source_col, regex):
    """
    Extract named groups from regex into separate columns.
    Use a regex with named capture groups.
    Returns a new DataFrame (copy) with new columns added.
    """
    df = df.copy()
    extracted = df[source_col].str.extract(regex)
    # convert any digit-like columns to numeric where possible
    for c in extracted.columns:
        extracted[c] = pd.to_numeric(extracted[c], errors="coerce")
    return pd.concat([df.reset_index(drop=True), extracted.reset_index(drop=True)], axis=1)

def compute_calc_start(df, time_col="time_in_s", dur_ns_col="dur_ns", out_col="calc_start"):
    """
    Compute calc_start = time_in_s - dur_ns/1e9   (assumes dur_ns is numeric)
    """
    df = df.copy()
    if time_col not in df.columns or dur_ns_col not in df.columns:
        df[out_col] = pd.NA
        return df
    
    mask=  (df[dur_ns_col].notna() & (df[time_col] - (df[dur_ns_col] / 1.0e9) > 0 ))
    if (len(df) == len(df[mask])):
        df[out_col] = df[time_col] - (df[dur_ns_col] / 1.0e9)
    if (len(df) > len(df[mask])):
        df.loc[mask,out_col] = df.loc[mask,time_col] - (df.loc[mask,dur_ns_col] / 1.0e9)
        df.loc[~mask,out_col] = df.loc[~mask,time_col]
    return df



def make_filtered_dataframes(df, config, message_col="message"):
    """
    Return a dict: name -> processed DataFrame (copy, reset index).
    """
    results = {}
    for name, spec in config.items():
        pat = spec["pattern"]
        # filter (use .str.match for anchored/case-insensitive patterns)
        mask = df[message_col].str.match(pat, na=False)
        if not mask.any():
            results[name] = pd.DataFrame()   # empty
            continue
        sub = df[mask].copy()
        
        # keep original index for later joins
        sub["__orig_index"] = sub.index
        # apply processors in config (extract + calculate start time) in order
        for proc in spec.get("processors", []):
            sub = proc(sub)
        results[name] = sub
    return results





#---------- apply for all entries in config
#--- gets all the wanted entries out of Cheetah
processed = make_filtered_dataframes(df, config)
#print(processed["spsift"])


master = df.copy()
# save index for easier later merging
master["__orig_index"] = master.index

for name, sub in processed.items():
    print('Working on: ', name)

    if sub.empty:
#        warnings.warn(f"processor --- {name} --- produced empty DataFrame — skipping [This CAN be OK]")
        print(f"--- NOTE: processor --- {name} --- produced empty DataFrame — skipping \n [This can be OK if module was not used]")
        continue
    
    if "__orig_index" not in sub.columns:
        warnings.warn(f"processor {name} has no __orig_index column; adding from index()")
        sub = sub.copy()
        sub["__orig_index"] = sub.index

    # find duration columns (no real starting time) that were newly added by processors
    new_cols = [c for c in sub.columns if c not in master.columns and c != "__orig_index"]
    print(' --- The created new column(s) :', new_cols)
    
#    if not new_cols:
#        warnings.warn(f"processor {name} added no new columns: {new_cols}")
#        continue
    # prepare the right-hand frame for merging: keep orig_index + new cols
    right = sub[["__orig_index"] + new_cols].drop_duplicates("__orig_index")
    if right.empty:
        warnings.warn(f"processor {name} right frame empty after selecting columns; skipping.")
        continue
    
    # merge on left_index (original df) to right.__orig_index
    master = master.merge(right, how="left", on="__orig_index")
    
    # leave helper column in for later checks
    # master.drop(columns=["__orig_index"], inplace=True)



frames = []
for name, sub in processed.items():
    if sub.empty:
        continue
    s = sub.copy()
    # ensure orig_index exists
    if "__orig_index" not in s.columns:
        s["__orig_index"] = s.index
        
    # find all duration-like columns in this sub
    dur_cols = [c for c in s.columns if re.search(r'(?i)_ns$', c)]
    if not dur_cols:
        continue
    
    # Ensure there is a calc_start for each dur_col; compute if missing
    for dcol in dur_cols:
        calc_col = f"calc_start_{dcol}"
        if calc_col not in s.columns:
            # compute calc_start for this dur_col (will respect masks inside compute_calc_start)
            # compute_calc_start expects dur_ns_col name 'dur_ns' by default; we call it generically:
            s = compute_calc_start(s.rename(columns={dcol: "dur_ns"}), time_col="time_in_s", dur_ns_col="dur_ns", out_col=calc_col)
            # rename back so original duration column stays named dcol
            s = s.rename(columns={"dur_ns": dcol})

    # now melt the found dur_cols for this sub, first get temporary selection for each duration column in s (e.g., corner-turn, spdt,...)
    tmp = s[["__orig_index", "time_in_s", "message"] + dur_cols + [f"calc_start_{d}" for d in dur_cols if f"calc_start_{d}" in s.columns]].copy()
    # "Melt" durations
    # transform a DataFrame from wide to long format - with this we get one row per duration measurement
    m = tmp.melt(id_vars=["__orig_index", "time_in_s", "message"],
                 value_vars=dur_cols,
                 var_name="duration_string",
                 value_name="duration_ns")
    
    
    # attach calc_start for corresponding duration variable
    def lookup_calc(row):
        calc_col = f"calc_start_{row['duration_string']}"
        return tmp.loc[tmp["__orig_index"] == row["__orig_index"], calc_col].iloc[0] if calc_col in tmp.columns else pd.NA
    
    m["calc_start"] = m.apply(lookup_calc, axis=1)
    m["name"] = name
    frames.append(m)


# concat all and drop missing durations
if frames:
    df_combined_long = pd.concat(frames, ignore_index=True)
    df_combined_long = df_combined_long[df_combined_long["duration_ns"].notna()].reset_index(drop=True)
else:
    df_combined_long = pd.DataFrame(columns=["__orig_index", "time_in_s", "message", "duration_string", "duration_ns", "calc_start", "name"])

# normalize names and columns
df_combined_long["dur_sel_comp"] = df_combined_long["duration_string"].str.replace(r'(?i)_ns$', '', regex=True)
# rename duration_ns -> dur_ns to keep previous naming
df_combined_long = df_combined_long.rename(columns={"duration_ns": "dur_ns"})
# extract the actual interesting stuff for histograms and benchmon overplotting
df_combined = df_combined_long[["__orig_index", "calc_start",  "dur_ns", "name"]].copy()


# ----- add Cheetah start and end, e.g., for overplot in benchmon (no duration)
st_mask = df["message"].str.startswith("Cheetah pipeline configured", na=False)
if st_mask.any():
    starttime = df.loc[st_mask, "time_in_s"].iloc[0]
else:
    starttime = df["time_in_s"].min()  # or pd.NA or raise a warning

et_mask = df["message"].str.startswith("End of pipeline", na=False)
if et_mask.any():
    endtime = df.loc[et_mask, "time_in_s"].iloc[-1]
    endindex=df.index[df["message"].str.startswith("End of pipeline")][0]
else:
    endtime = df["time_in_s"].max()  # or pd.NA or raise a warning
    endindex=df.index.max()

df_combined.loc[len(df_combined)]=[0,starttime-0.1,0,'cheetah_start']
df_combined.loc[len(df_combined)]=[endindex,endtime,0,'cheetah_end']
df_combined.sort_values('__orig_index',inplace=True)
#df_combined.sort_values('calc_start',inplace=True)
df_combined.reset_index(inplace=True,drop=True)

print()

# for the plot-with-benchmon .csv remove the NoST entries (no actual start times known)
mask = df_combined["name"].str.endswith("_NoST", na=False)
aus_df_combined=df_combined[~mask].copy() # select those that do not fulfil the mask
# One could remove helper column if potential internal benchmon routine gets confused 
# aus_df_combined.drop(columns=["__orig_index"])
aus_df_combined.reset_index(inplace=True,drop=True)

outfile1=outfile_root+'_durations.csv' # to plot benchmark histograms
outfile2=outfile_root+'_forBM.csv' # to overplot with resources

df_combined.to_csv(indir+outfile1,index=False)
aus_df_combined.to_csv(indir+outfile2,index=False)

print('--- wrote ',indir+outfile1,indir+outfile2)

