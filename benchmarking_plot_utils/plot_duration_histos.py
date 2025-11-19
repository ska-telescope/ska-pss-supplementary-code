#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plot histograms for ...durations.csv file (produced by dighest_cheetahlog_fBM.py)
need coulmns "calc_start",  "dur_ns", "name"
Plots are put in .png files and annranged in one combined .pdf

If there is only one process (e.g, one FDAS SIFT), produce a "plot" 
which states the one number

@author: bposselt
"""

import math
from pathlib import Path
import matplotlib.pyplot as plt

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


#----- Input + output names and directories
indir = "/home/bposselt/benchmark_worker1b/Nov1025/cheetah/"
infile="cheetah_fdas_101125_ThresholdON_FoFon_extract_durations.csv"

outdir=indir
outfilestamm="cheetah_fdas_101125_ThresholdON_FoFon_extract_combi"

# list, e.g., the test vector for later reference
title_text='FLDO-MID_336a2a6_54.0_0.1_100_0.0_Gaussian_50.0_0000_123123.fil, 1000 DMs, 1 FLDO thread'

#------------------------------------------------------------------------


df=pd.read_csv(indir+infile)
# find unique names for which to plot histograms
#print(df.name.unique())
drop_names = ["cheetah_start", "cheetah_end"]
#the ~ inverts that mask
df_f = df[~df["name"].isin(drop_names)].copy()
print(df_f)


# produce individual histograms per name in png files
# save paths of these files
saved_paths = []
for name in df_f["name"].unique():
    subset = df_f[df_f["name"] == name]
    sizesubset=len(subset)
    fig, ax1 = plt.subplots(figsize=(6, 4))
    
    if sizesubset > 1:
        binsize=int(sizesubset/3)
        print('Chosen bin size: ',binsize,' for name: ',name)
        

        ax1.hist(subset["dur_ns"], bins=binsize, color="blue", edgecolor="black")
    
        ax1.set_title(f"Histogram for {name} with {binsize} bins")
        ax1.set_xlabel("Duration (ns)")
        ax1.set_ylabel("Counts")

        # Optional: grid or log scale
        ax1.grid(True, linestyle="--", alpha=0.6)

    else:
        # if no histogram possible (only one entry)
        value = subset["dur_ns"].iloc[0]/1e9
        ax1.text(
            0.5, 0.5, 
            f"Only one value\n for {name}:\n{value:.2f} s",
            fontsize=14, ha="center", va="center", transform=ax1.transAxes
        )
        ax1.set_axis_off()
        ax1.set_title(f"Single value for {name}")
    
    # Save to file
    path = outdir+f"hist_{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")

    # Close figure to free memory
    plt.close(fig)
    saved_paths.append(path)



# print all the paths of the png images    
print('----- Individual images saved -----')
print(saved_paths)    
print()



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



# actual call that puts the histograms plots together in one pdf
combined = combine_pngs_grid(saved_paths, 
                             out_path=outdir+outfilestamm+".png", 
                             n_per_row=3,
                             padding=8, 
                             bg_color=(255,255,255), # white in RGB
                             uniform_size=None,
                             title=title_text,
                             title_size=40,
                             title_color="red",
                             save_pdf=True)



