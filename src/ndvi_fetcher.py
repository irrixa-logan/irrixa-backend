# Irrixa MK1 – NDVI Fetcher (Phase 4 Enhanced + Full Feature Merge)
import os
import json
import glob
import datetime
import requests
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping
from matplotlib import pyplot as plt
from matplotlib import colormaps

# === Configuration ===
ENABLE_NDRE = True
ENABLE_EVI = True
ENABLE_GNDVI = True
SAVE_PNG = True

import os

CLIENT_ID = os.getenv("SENTINELHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("SENTINELHUB_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise Exception("❌ SentinelHub credentials missing in environment variables")

print("🔒 Using environment variables:")
print("CLIENT_ID =", CLIENT_ID[:8] + "...")
print("CLIENT_SECRET =", "SET" if CLIENT_SECRET else "MISSING")

# Set base_dir using __file__ safely for rest of script
from pathlib import Path
base_dir = Path(__file__).resolve().parents[2]

# === Output directories ===
today = datetime.date.today()
today_str = str(today)
ndvi_output_dir = os.path.join(base_dir, "NDVI")
os.makedirs(ndvi_output_dir, exist_ok=True)
archive_dir = os.path.join(ndvi_output_dir, today_str)
os.makedirs(archive_dir, exist_ok=True)
planetscope_dir = os.path.join(base_dir, "Planetscope_Inputs", today_str)
ndvi_history_path = os.path.join(base_dir, "NDVI_HISTORY", "ndvi_history.json")
os.makedirs(os.path.dirname(ndvi_history_path), exist_ok=True)

block_summaries = {}

def get_access_token():
    print(f"\n\U0001f510 Requesting token with client_id: {CLIENT_ID}")
    response = requests.post("https://services.sentinel-hub.com/oauth/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    })
    if response.status_code != 200:
        raise Exception("Authentication failed.")
    return response.json()["access_token"]

def generate_evalscript(index_type):
    return {
        "NDVI": """//VERSION=3
function setup() { return {input: [\"B04\", \"B08\"], output: {bands: 1, sampleType: \"FLOAT32\"}}; }
function evaluatePixel(s) { return [(s.B08 - s.B04) / (s.B08 + s.B04)]; }
""",
        "NDRE": """//VERSION=3
function setup() { return {input: [\"B05\", \"B08\"], output: {bands: 1, sampleType: \"FLOAT32\"}}; }
function evaluatePixel(s) { return [(s.B08 - s.B05) / (s.B08 + s.B05)]; }
""",
        "EVI": """//VERSION=3
function setup() { return {input: [\"B02\", \"B04\", \"B08\"], output: {bands: 1, sampleType: \"FLOAT32\"}}; }
function evaluatePixel(s) {
  return [2.5 * (s.B08 - s.B04) / (s.B08 + 6 * s.B04 - 7.5 * s.B02 + 1)];
}
""",
        "GNDVI": """//VERSION=3
function setup() { return {input: [\"B03\", \"B08\"], output: {bands: 1, sampleType: \"FLOAT32\"}}; }
function evaluatePixel(s) { return [(s.B08 - s.B03) / (s.B08 + s.B03)]; }
"""
    }[index_type]

def calculate_dimensions_from_bounds(geometry, max_dim=1500):
    coords = geometry["coordinates"][0]
    xs = [pt[0] for pt in coords]
    ys = [pt[1] for pt in coords]
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)

    if width == 0 or height == 0:
        return 500, 500

    aspect_ratio = width / height
    if aspect_ratio > 1:
        w = max_dim
        h = int(max_dim / aspect_ratio)
    else:
        h = max_dim
        w = int(max_dim * aspect_ratio)

    return w, h

def load_last_valid_json(block_name, index_type):
    json_path = os.path.join(ndvi_output_dir, f"{block_name.lower()}_{index_type.lower()}.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
                if "mean" in data and data["mean"] is not None:
                    print(f"⚠️ Using fallback {index_type} data from previous run for {block_name}")
                    data["fallback_used"] = True
                    data["fallback_date"] = data["date"]
                    data["date"] = str(datetime.date.today())
                    return data
        except: pass
    return None

def fetch_index(geojson_path, index_type):
    block_name = os.path.basename(geojson_path).replace(".geojson", "")
    gdf = gpd.read_file(geojson_path).to_crs(epsg=4326)
    geometry = mapping(gdf.geometry.union_all())
    width, height = calculate_dimensions_from_bounds(geometry)
    print(f"🖼️  Auto-sizing image: {width} x {height}")

    ps_path = os.path.join(planetscope_dir, f"{block_name.lower()}_{index_type.lower()}.tif")
    if os.path.exists(ps_path):
        tif_path = ps_path
        source = "planetscope"
    else:
        payload = {
            "input": {
                "bounds": {"geometry": geometry, "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}},
                "data": [{"type": "sentinel-2-l2a", "dataFilter": {"mosaickingOrder": "mostRecent", "timeRange": {
                    "from": f"{datetime.date.today() - datetime.timedelta(days=10)}T00:00:00Z",
                    "to": f"{datetime.date.today()}T23:59:59Z"}}}]
            },
            "evalscript": generate_evalscript(index_type),
            "output": {"width": width, "height": height, "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]}
        }
        headers = {"Authorization": f"Bearer {get_access_token()}", "Content-Type": "application/json"}
        response = requests.post("https://services.sentinel-hub.com/api/v1/process", headers=headers, json=payload)
        response.raise_for_status()
        tif_path = os.path.join(archive_dir, f"{block_name.lower()}_{index_type.lower()}.tif")
        with open(tif_path, "wb") as f:
            f.write(response.content)
        source = "sentinel"

    with rasterio.open(tif_path) as src:
        index_data, _ = mask(src, gdf.geometry, crop=True)
        data = index_data[0]
        data = np.where((data < -1) | (data > 1), np.nan, data)
        nan_coverage = np.count_nonzero(np.isnan(data)) / data.size * 100
    # Force fallback values if entire image is blank or unusable
if np.isnan(np.nanmean(data)) or nan_coverage >= 99:
    print(f"⚠️ {block_name} {index_type} image is unusable — forcing fallback values")
    mean = 0.0
    p80 = 0.0
    score = 0
    fallback_used = True
    fallback_date = None
else:
    mean = float(np.nanmean(data))
    p80 = float(np.nanpercentile(data, 80))
    score = 100 if nan_coverage <= 10 else 75 if nan_coverage <= 30 else 50 if nan_coverage <= 50 else 0
    fallback_used = False
    fallback_date = None

        fallback_data = load_last_valid_json(block_name, index_type) if (np.isnan(np.nanmean(data)) or nan_coverage > 50) else None

        if fallback_data:
            mean = fallback_data["mean"]
            p80 = fallback_data["p80"]
            score = fallback_data["confidence_score"]
            fallback_used = True
            fallback_date = fallback_data.get("fallback_date")
        else:
            mean = float(np.nanmean(data))
            p80 = float(np.nanpercentile(data, 80))
            score = 100 if nan_coverage <= 10 else 75 if nan_coverage <= 30 else 50 if nan_coverage <= 50 else 0
            fallback_used = False
            fallback_date = None

        if SAVE_PNG:
            cmap = colormaps.get_cmap("RdYlGn")
            plt.imshow(data, cmap=cmap, vmin=0, vmax=1)
            plt.colorbar()
            plt.title(f"{block_name} {index_type}\nMean: {mean:.3f} | P80: {p80:.3f}")
            plt.axis("off")
            plt.savefig(os.path.join(archive_dir, f"{block_name.lower()}_{index_type.lower()}.png"), bbox_inches="tight")
            plt.close()

        json_output = {
            "block": block_name,
            "date": today_str,
            "index": index_type,
            "mean": mean,
            "p80": p80,
            "confidence_score": score,
            "nan_coverage": round(nan_coverage, 2),
            "fallback_used": fallback_used,
            "fallback_date": fallback_date,
            "cloud_affected": nan_coverage > 50,
            "source": source
        }
        with open(os.path.join(archive_dir, f"{block_name.lower()}_{index_type.lower()}.json"), "w") as f:
            json.dump(json_output, f, indent=2)

        if index_type == "NDVI":
            try:
                with open(ndvi_history_path, "r") as f:
                    history = json.load(f)
            except: history = {}
            history[block_name] = mean
            with open(ndvi_history_path, "w") as f:
                json.dump(history, f, indent=2)

        if block_name not in block_summaries:
            block_summaries[block_name] = {"block": block_name, "date": today_str}
        block_summaries[block_name][index_type.lower()] = mean
        block_summaries[block_name]["confidence_score"] = score
        block_summaries[block_name]["fallback_used"] = fallback_used
        block_summaries[block_name]["source"] = source
        block_summaries[block_name]["nan_coverage"] = round(nan_coverage, 2)
        block_summaries[block_name]["image_date"] = fallback_date or today_str

    return block_name, mean, p80

if __name__ == "__main__":
    block_dir = os.path.join(base_dir, "Blocks")
    block_files = glob.glob(os.path.join(block_dir, "*.geojson"))
    print(f"\U0001f50d Found {len(block_files)} block files")
    for geojson_path in block_files:
        for index in ["NDVI", "NDRE", "EVI", "GNDVI"]:
            if ((index == "NDRE" and ENABLE_NDRE) or
                (index == "EVI" and ENABLE_EVI) or
                (index == "GNDVI" and ENABLE_GNDVI) or
                (index == "NDVI")):
                try:
                    block_name, mean, p80 = fetch_index(geojson_path, index)
                    print(f"✅ {block_name} {index} mean: {mean:.3f} | P80: {p80:.3f}")
                except Exception as e:
                    print(f"❌ Error fetching {index} for {os.path.basename(geojson_path)}: {e}")

    for block, summary in block_summaries.items():
        with open(os.path.join(archive_dir, f"{block.lower()}_summary.json"), "w") as f:
            json.dump(summary, f, indent=2)
