 # Irrixa MK1 – Batch Runner
import subprocess
import os

base_dir = os.path.dirname(os.path.dirname(__file__))
src_dir = os.path.join(base_dir, "src")

print("🚀 Starting full Irrixa run...")

try:
    print("\n📡 STEP 1: Fetching NDVI and Vegetation Indexes...")
    subprocess.run(["python", os.path.join(src_dir, "ndvi_fetcher.py")], check=True)

    print("\n🌤️  STEP 2: Fetching Weather Data...")
    subprocess.run(["python", os.path.join(src_dir, "weather_fetcher.py")], check=True)

    print("\n💧 STEP 3: Calculating Irrigation Requirements...")
    subprocess.run(["python", os.path.join(src_dir, "irrigation_engine.py")], check=True)

    print("\n✅ Irrixa daily batch run complete.")

except subprocess.CalledProcessError as e:
    print("❌ Batch step failed:", e)
    exit(1)
