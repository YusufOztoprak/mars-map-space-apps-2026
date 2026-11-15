"""Prepare a historical observation-based dust scenario display."""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.io import netcdf_file

project = Path(__file__).resolve().parents[1]
root = project / "data/processed/explorer"
root.mkdir(parents=True, exist_ok=True)
with netcdf_file(project / "data/raw/dust.nc", "r", mmap=False) as dataset:
    v = dataset.variables
    # MY34 planet-encircling dust event, this product uses interpolated daily means.
    row = np.flatnonzero(v["SOY"].data == 400)[0]
    source_lon = v["longitude"].data
    source_lat = v["latitude"].data
    values = v["cdod610"].data[row].astype(float)
    values[(values < 0) | ~np.isfinite(values)] = np.nan
    # 3-degree samples are centered at -180, -177, ... with wrapped longitude.
    # Shift the texture's bounds by half a cell and use opposite halves at 180°.
    longitude = -180 + (np.arange(720)+.5)/2
    latitude = 90 - (np.arange(360)+.5)/2
    j = np.floor((longitude - source_lon[0] + 1.5)/3).astype(int) % source_lon.size
    i = np.clip(np.floor((source_lat[0]+1.5-latitude)/3).astype(int), 0, source_lat.size-1)
    expanded = values[np.ix_(i,j)]
    scale = [0, .25, .5, 1, 2, 4]
    channels = [(28,37,82), (47,92,151), (65,167,172), (246,187,94), (245,106,54), (153,39,64)]
    rgb = [np.interp(np.nan_to_num(expanded), scale, channel) for channel in zip(*channels)]
    image = np.dstack((*rgb,np.isfinite(expanded)*255)).astype(np.uint8)
    Image.fromarray(image).save(root / "dust-my34-sol400.png")
    payload = {"year":34, "sol":400, "ls":round(float(v["Ls"].data[row]),2),
               "legend":{"values":scale,"colors":["#%02x%02x%02x" % tuple(c) for c in channels]},
               "values": [[round(float(x),4) if np.isfinite(x) else None for x in line] for line in values],
               "url":"https://www-mars.lmd.jussieu.fr/mars/dust_climatology/",
               "paper":"https://doi.org/10.1029/2019JE006111"}
    (root/"dust-my34-sol400.json").write_text(json.dumps(payload,separators=(",",":")),encoding="utf-8")
