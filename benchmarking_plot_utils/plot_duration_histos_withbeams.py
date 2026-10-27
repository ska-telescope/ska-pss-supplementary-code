#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plot histograms for ...durations.csv file (produced by dighest_cheetahlog_fBM.py)
need coulmns "calc_start",  "dur_ns", "name"
Plots are put in .png files and annranged in one combined .pdf

If there is only one process (e.g, one FDAS SIFT), produce a "plot" 
which states the one number

@author: B. Posselt
"""

import math
from pathlib import Path
import matplotlib.pyplot as plt

import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import argparse
import os, sys

#------ example usage:
# python3 plot_duration_histos_withbeams.py --indir /home/posselt/benchmark_tikbalang/d151026R4stream/ \
#                                           --infile_root sps_1b_LOWstream_DMr4_d151026_NoAff_extract \
#                                           --outfilestamm sps_1b_LOWstream_DMr4_d151026_NoAff_TIK \
#                                           --pipeline SPS \
#                                           --samplingtime 69.12 \
#                                           --bindiv 4 \
#                                           --titlestring1 "tikbalang, 1b LOW stream" \
#                                           --dmtitlestring "4 x 1999 DMs" \
#                                           --titlestringend "NO affinities"     


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot duration histograms."
    )
    parser.add_argument("--indir", required=True,
                        help="Directory containing the input CSV files")
    parser.add_argument("--infile_root", required=True,
                        help="Root name for the input CSV files")
    parser.add_argument("--outfilestamm", required=True,
                        help="Root name for output files")

    # Optional values: None lets us detect whether each option was supplied.
    parser.add_argument("--pipeline", type=str, default=None)
    parser.add_argument("--samplingtime", type=float, default=None)
    parser.add_argument("--bindiv", type=int, default=None)
    parser.add_argument("--titlestring1", type=str, default=None)
    parser.add_argument("--dmtitlestring", type=str, default=None)
    parser.add_argument("--titlestringend", type=str, default=None)

    return parser.parse_args()


args = parse_args()

indir = args.indir
infile_root = args.infile_root
outfilestamm = args.outfilestamm

# make sure we use default value if nothing is supplied for optional arguments, 
# and print a note about it
def use_default(option_name, value, default):
    if value is None:
        print(f"Note: --{option_name} not supplied; using default: {default!r}")
        return default
    return value

pipeline = use_default("pipeline", args.pipeline, "SPS")
samplingtime = use_default("samplingtime", args.samplingtime, 69.12)
bindiv = use_default("bindiv", args.bindiv, 3)
titlestring1 = use_default("titlestring1", args.titlestring1, " ")
dmtitlestring = use_default("dmtitlestring", args.dmtitlestring, " ")
titlestringend = use_default("titlestringend", args.titlestringend, " ")

#--- reminder: 
#time_res = 69.12 * 1000 # microsec -> ns / LOW TV
#time_res = 64 * 1000 # microsec -> ns / testvector: tsamp=6.4e-05,
time_res_ns = samplingtime * 1000 # microsec -> ns / default sampling time = 69.12us for LOW TV, 64us for MID TV

outdir=indir
infile= infile_root + "_durations.csv"
parfile= infile_root + "_pars.csv"

# get extra parameters for klotski p/r calculation 
dfpar=pd.read_csv(indir+parfile)

downsample_factor = dfpar["downsample_factor"].iloc[0]
dedispersion_samples = dfpar["agg_buffer"].iloc[0]
overlap = dfpar["overlap"].iloc[0]
#overlap = 3072 #CNIC+TOPIC

FLDO_totalcand = dfpar["FLDO_totalcand"].iloc[0]
FLDO_threads = dfpar["FLDO_threads"].iloc[0]

buffer_time_ns = ( dedispersion_samples - overlap ) * time_res_ns * downsample_factor

# create figure title text with all relevant parameters
title_text = titlestring1 + ', ' + pipeline + ', DownSamp '+ str(downsample_factor) + ', ' + dmtitlestring + '\n dedispersion samples: ' +  str(dedispersion_samples) + ', ' +titlestringend

if "fdas" in pipeline.lower():
    title_text += f" (FLDO threads: {FLDO_threads}, N cand: {FLDO_totalcand})"

#------------------------------------------------------------------------


# Normalize possible stray values and convert to Int64 nullable dtype.
# Accept integer-like values or strings like "1","2","3".
def _clean_beam(x):
    if pd.isna(x):
        return pd.NA
    try:
        # accept strings like "1" or ints
        bi = int(x)
        return bi if bi in (1, 2, 3) else pd.NA
    except Exception:
        return pd.NA   
 
def combine_pngs_grid(png_paths, 
                      out_path="combined.png", 
                      n_per_row=3,
                      padding=10, 
                      bg_color=(255,255,255), 
                      uniform_size=None,
                      title=None,  
                      title_font=None,  
                      title_size=24,    
                      title_color='black', 
                      save_pdf=False
                      ):
    """
    Combine PNG images into a grid and save to out_path (PNG).
    png_paths: list of Path or str to PNG files
    n_per_row: images per row
    padding: pixels between images
    uniform_size: (w, h) to resize each image to; if None, uses max of images
    save_pdf: if True, also save a PDF named like out_path with .pdf extension
    """
    imgs = [Image.open(p) for p in png_paths]
    # Ensure RGB
    imgs = [img.convert("RGB") for img in imgs]

    if uniform_size is None:
        widths, heights = zip(*(im.size for im in imgs))
        max_w, max_h = max(widths), max(heights)
    else:
        max_w, max_h = uniform_size

    # Resize images to uniform size (preserve aspect by letterboxing)
    resized = []
    for im in imgs:
        w, h = im.size
        # scale to fit within max_w,max_h while preserving aspect
        scale = min(max_w / w, max_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        # Image.LANCZOS (formerly called ANTIALIAS) 
        # is a high-quality downsampling filter.
        im_resized = im.resize((new_w, new_h), Image.LANCZOS)
        
        # create background and paste centered
        bg = Image.new("RGB", (max_w, max_h), color=bg_color)
        x = (max_w - new_w) // 2
        y = (max_h - new_h) // 2
        
        bg.paste(im_resized, (x, y))
        # will copy image centered on the background
        resized.append(bg)

    n = len(resized)
    rows = math.ceil(n / n_per_row)
    grid_w = n_per_row * max_w + (n_per_row + 1) * padding
    grid_h = rows * max_h + (rows + 1) * padding

    title_space = 0  # 
    if title:
        title_space = int(title_size * 2.5)  # reserve some space for title text
    
    grid_img = Image.new("RGB", (grid_w, grid_h + title_space), color=bg_color)
    draw = ImageDraw.Draw(grid_img)
 
    # optional title  
    if title:
        # use default font if no font provided
        try:
        # Try to load a scalable TTF font
            if title_font:
                font = ImageFont.truetype(title_font, title_size)
            else:
                # Use DejaVuSans as default (comes with Pillow)
                font = ImageFont.truetype("DejaVuSans.ttf", title_size)
        except Exception:
        # Fallback: built-in bitmap font (very small, but guaranteed available)
            font = ImageFont.load_default()

        try:
            # Pillow ≥10
            bbox = draw.textbbox((0, 0), title, font=font)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            # Pillow <10 fallback
            text_w, text_h = draw.textsize(title, font=font)

        # put title centered at top 
        draw.text(
            ((grid_w - text_w) / 2, (title_space - text_h) / 2),
            title,
            fill=title_color,
            font=font
            )
        
        
    # paste all images below title_space
    for idx, im in enumerate(resized):
        row = idx // n_per_row
        col = idx % n_per_row
        x = padding + col * (max_w + padding)
        y = padding + row * (max_h + padding) + title_space
        grid_img.paste(im, (x, y))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    grid_img.save(out_path)

    if save_pdf:
        pdf_path = out_path.with_suffix(".pdf")
        grid_img.save(pdf_path, "PDF", resolution=100.0)
        print('--- wrote combined pdf: ',pdf_path)
    return out_path
    
 
    
 


df=pd.read_csv(indir+infile)

# Ensure beam column exists and has nullable integer dtype
if "beam" not in df.columns:
    # If no beam column present, create it as all missing
    df["beam"] = pd.NA
    
df["beam"] = df["beam"].apply(_clean_beam).astype("Int64")

# find unique names for which to plot histograms
#print(df.name.unique())
drop_names = ["cheetah_start", "cheetah_end"]
#the ~ inverts that mask
df_f = df[~df["name"].isin(drop_names)].copy()
print(df_f)

# Determine present beams in sorted order (1,2,3)
present_beams = sorted([int(b) for b in df_f["beam"].dropna().unique()])

produce_unknown_beam_group = True
if produce_unknown_beam_group and df_f["beam"].isna().any():
    # we will treat unknown beam group separately after numbered beams
    has_unknown = True
else:
    has_unknown = False

all_combined_paths = []  # store combined output paths per beam



# produce individual histograms per name in png files
# for each beam (1,2,3) in order produce plots for only that beam
for beam in present_beams:
    print(f"\n--- Producing plots for beam {beam} ---")
    beam_subset = df_f[df_f["beam"] == beam]
    saved_paths = []
    # loop all unique names for this beam
    for name in beam_subset["name"].unique():
        subset = beam_subset[beam_subset["name"] == name]
        sizesubset = len(subset)
        fig, ax1 = plt.subplots(figsize=(6, 4))

        if sizesubset > 1:
            binsize = max(1, int(sizesubset / bindiv))
            print('Chosen bin size: ', binsize, ' for name: ', name)

            ax1.hist(subset["dur_ns"], bins=binsize, edgecolor="black")
            ax1.set_title(f"{name} (beam {beam}, n= {sizesubset}) with {binsize} bins")
            ax1.set_xlabel("Duration (ns)")
            ax1.set_ylabel("Counts")
            ax1.grid(True, linestyle="--", alpha=0.6)

        else:
            # single value
            value = subset["dur_ns"].iloc[0] / 1e9
            if value > 0.01:
                ax1.text(
                    0.5, 0.5,
                    f"Only one value\n for {name}\n(beam unknown):\n{value:.2f} s",
                    fontsize=14, ha="center", va="center", transform=ax1.transAxes
                    )
            if value < 0.01:
                value2 = value * 1e9
                ax1.text(
                    0.5, 0.5,
                    f"Only one value\n for {name}\n(beam unknown):\n{(value2):.2f} ns",
                    fontsize=14, ha="center", va="center", transform=ax1.transAxes
                    )
            ax1.set_axis_off()
            ax1.set_title(f"Single value for {name} (beam {beam})")

        # Save to file; sanitize name for filenames
        safe_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name)
        path = outdir + f"hist_beam{beam}_{safe_name}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        saved_paths.append(path)

    # do extra processing time/ real time for kltoski
    for name in beam_subset["name"].unique():
        subset = beam_subset[beam_subset["name"] == name]
        sizesubset = len(subset)

        if (sizesubset > 1) & (name =="klotski"):
            fig, ax1 = plt.subplots(figsize=(6, 4))

            binsize = max(1, int(sizesubset / bindiv))
            print('Chosen bin size: ', binsize, ' for name: ', name)
            
            proc_time_vs_buffer_time = subset["dur_ns"] / buffer_time_ns
            med_proc_time_vs_buffer_time = np.median(proc_time_vs_buffer_time)
            ax1.hist(proc_time_vs_buffer_time, bins=binsize, color="blue", edgecolor="black")

            ax1.set_title(f"P/R Histo for {name} (beam {beam}), median = {med_proc_time_vs_buffer_time:.2f}")
            ax1.set_xlabel("proc time / real time")
            ax1.set_ylabel("Counts")
            ax1.grid(True, linestyle="--", alpha=0.6)
   
            # Save to file
            path = outdir+f"pr_hist_{name}.png"
            fig.savefig(path, dpi=150, bbox_inches="tight")

            # Close figure to free memory
            plt.close(fig)
            saved_paths.append(path)



        
        
    # combine the PNGs for this beam into a single PNG + PDF
    combined_out = outdir + f"{outfilestamm}_beam{beam}.png"
    combined = combine_pngs_grid(
        saved_paths,
        out_path=combined_out,
        n_per_row=3,
        padding=8,
        bg_color=(255, 255, 255),
        uniform_size=None,
        title=f"Beam {beam}: {title_text}",
        title_size=40,
        title_color="red",
        save_pdf=True
    )
    all_combined_paths.append(combined)



# Handle unknown-beam entries (those with beam == <NA>)
if has_unknown:
    print("\n--- Producing plots for unknown beam entries ---")
    beam_subset = df_f[df_f["beam"].isna()]
    saved_paths = []
    for name in beam_subset["name"].unique():
        subset = beam_subset[beam_subset["name"] == name]
        sizesubset = len(subset)
        fig, ax1 = plt.subplots(figsize=(6, 4))

        if sizesubset > 1:
            binsize = max(1, int(sizesubset / bindiv))
            ax1.hist(subset["dur_ns"], bins=binsize, edgecolor="black")
            ax1.set_title(f"Histogram for {name} (beam unknown) with {binsize} bins")
            ax1.set_xlabel("Duration (ns)")
            ax1.set_ylabel("Counts")
            ax1.grid(True, linestyle="--", alpha=0.6)
        else:
            value = subset["dur_ns"].iloc[0] / 1e9
            ax1.text(
                0.5, 0.5,
                f"Only one value\n for {name}\n(beam unknown):\n{value:.2f} s",
                fontsize=14, ha="center", va="center", transform=ax1.transAxes
            )
            ax1.set_axis_off()
            ax1.set_title(f"Single value for {name} (beam unknown)")

        safe_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name)
        path = outdir + f"hist_beam_unknown_{safe_name}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        saved_paths.append(path)

    # do extra processing time/ real time for kltoski
    for name in beam_subset["name"].unique():
        subset = beam_subset[beam_subset["name"] == name]
        sizesubset = len(subset)

        if (sizesubset > 1) & (name =="klotski"):
            fig, ax1 = plt.subplots(figsize=(6, 4))

            binsize = max(1, int(sizesubset / bindiv))
            print('Chosen bin size: ', binsize, ' for name: ', name)
            
            proc_time_vs_buffer_time = subset["dur_ns"] / buffer_time_ns
            med_proc_time_vs_buffer_time = np.median(proc_time_vs_buffer_time)
            ax1.hist(proc_time_vs_buffer_time, bins=binsize, color="blue", edgecolor="black")

            ax1.set_title(f"P/R Histo for {name} (beam {beam}), median = {med_proc_time_vs_buffer_time:.2f}")
            ax1.set_xlabel("proc time / real time")
            ax1.set_ylabel("Counts")
            ax1.grid(True, linestyle="--", alpha=0.6)
   
            # Save to file
            path = outdir+f"pr_hist_{name}.png"
            fig.savefig(path, dpi=150, bbox_inches="tight")

            # Close figure to free memory
            plt.close(fig)
            saved_paths.append(path)



    combined_out = outdir + f"{outfilestamm}_beam_unknown.png"
    combined = combine_pngs_grid(
        saved_paths,
        out_path=combined_out,
        n_per_row=3,
        padding=8,
        bg_color=(255, 255, 255),
        uniform_size=None,
        title=f"Beam unknown: {title_text}",
        title_size=40,
        title_color="red",
        save_pdf=True
    )
    all_combined_paths.append(combined)




# print all the paths of the png images    
print('----- Images saved -----')
# final report of produced combined files
print("\n--- Per-beam combined outputs ---")
for p in all_combined_paths:
    print(p)
print()




# Produce beam-comparison horizontal plots (one file per 'name'),
# with up to 3 subplots in one ROW: beam1 | beam2 | beam3.

#present_beams = sorted([int(b) for b in (df_f["beam"].dropna().unique() <4)])

def _safe_name(name):
    return "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in str(name))

beamcomp_png_paths = []

for name in df_f["name"].unique():
    safe_name = _safe_name(name)
    # Collect dur_ns arrays per beam to compute common x-limits
    per_beam_vals = {}
    for b in present_beams:
        vals = df_f.loc[(df_f["name"] == name) & (df_f["beam"] == b), "dur_ns"].dropna().values
        per_beam_vals[b] = vals

    # compute xlim across all beams that have values
    all_vals = np.concatenate([v for v in per_beam_vals.values() if len(v) > 0]) if any(len(v) > 0 for v in per_beam_vals.values()) else np.array([])
    use_xlim = None
    if all_vals.size > 0:
        xmin, xmax = float(all_vals.min()), float(all_vals.max())
        # add small margin
        span = xmax - xmin if xmax > xmin else max(1.0, xmax * 0.01)
        use_xlim = (max(0.0, xmin - 0.05 * span), xmax + 0.05 * span)

    # Create horizontal layout with up to 3 axes
    ncols = len(present_beams)
    fig, axes = plt.subplots(nrows=1, ncols=ncols, figsize=(6 * ncols, 4), sharey=False)    
    if ncols == 1:
        axes = [axes]
    
    #fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(18, 4), sharey=False)
    if not isinstance(axes, (list, np.ndarray)):
        axes = [axes]

    fig.suptitle(f"{name} — beam comparison", fontsize=16, y=0.98)

    for idx, beam in enumerate(present_beams):
        ax = axes[idx]
        vals = per_beam_vals.get(beam, np.array([]))
        nvals = len(vals)

        if nvals == 0:
            ax.text(0.5, 0.5, f"No data for beam {beam}", ha="center", va="center", transform=ax.transAxes, fontsize=12)
            ax.set_xticks([])
            ax.set_yticks([])
        elif nvals == 1:
            v_s = vals[0] / 1e9
            ax.text(0.5, 0.5, f"Only one value\n{v_s:.3f} s", ha="center", va="center", transform=ax.transAxes, fontsize=12)
            ax.set_xticks([])
        else:
            binsize = max(1, int(nvals / bindiv))
            ax.hist(vals, bins=binsize, edgecolor="black")
            ax.set_xlabel("Duration (ns)")
            ax.grid(True, linestyle="--", alpha=0.4)
            ax.set_title(f"beam {beam} (n={nvals})")

        # enforce the common x-limits if available
        if use_xlim is not None:
            ax.set_xlim(use_xlim)

    # Label y-axis of middle plot or leave as default
    axes[0].set_ylabel("Counts")

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    out_png = outdir + f"hist_beamcomp_{safe_name}.png"
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)
    beamcomp_png_paths.append(out_png)









# combine all per-name horizontal beam comparison PNGs into one PNG + PDF
if beamcomp_png_paths:
    combined_out = outdir + f"{outfilestamm}_beamcomp.png"
    combine_pngs_grid(
        beamcomp_png_paths,
        out_path=combined_out,
        n_per_row=1,            # stack one per-name horizontal row vertically in combined image
        padding=8,
        bg_color=(255, 255, 255),
        uniform_size=None,
        title=f"Beam comparison — {title_text}",
        title_size=40,
        title_color="red",
        save_pdf=True
    )
    print(f"--- wrote beam comparison combined file: {combined_out} (+ .pdf)")
else:
    print("--- No beam comparison images created (no names present).")



