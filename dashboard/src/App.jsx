 // ✅ Irrixa Dashboard – Full Version w/ Toggleable NDVI Maps + Fixes Restored
import React, { useEffect, useState } from 'react';
import './index.css';

const CROP_OPTIONS = ["broccoli", "beans", "citrus", "grapes", "almonds"];
const STAGE_OPTIONS = ["emergent", "vegetative", "flowering", "harvest", "unspecified"];
const TYPE_OPTIONS = ["overhead_spray", "drip", "microjet"];
const SOIL_OPTIONS = ["clay", "loam", "sandy loam", "sand"];
const SOIL_RAW_DEFAULTS = { clay: 70, loam: 55, "sandy loam": 45, sand: 30 };

function Toast({ message }) {
  return (
    <div className="fixed top-4 right-4 bg-green-500 text-white py-2 px-4 rounded-lg shadow-lg z-50">
      {message}
    </div>
  );
}

function ConfidenceBar({ score }) {
  const width = Math.min(score, 100);
  let color = 'bg-green-500';
  if (score < 60) color = 'bg-red-500';
  else if (score < 80) color = 'bg-yellow-400';
  return (
    <div className="mb-2">
      <p className="text-sm">🧠 Confidence Score: {score}%</p>
      <div className="w-full h-2 rounded bg-gray-200">
        <div className={`h-full rounded ${color}`} style={{ width: `${width}%` }}></div>
      </div>
    </div>
  );
}

function WeatherTile({ data }) {
  if (!data) return null;
  const today = new Date().toISOString().split("T")[0];
  const todayData = data.find(d => d.date === today);
  if (!todayData) return null;

  const safe = (val, unit = '') => val != null ? `${Number(val).toFixed(1)}${unit}` : '–';

  return (
    <div className="p-4 rounded-2xl border border-blue-300 bg-white shadow-md mb-4">
      <h2 className="text-xl font-semibold mb-2">🌤️ Weather – {today}</h2>
      <p>• ETo: {safe(todayData.eto_estimated, ' mm')}</p>
      <p>• Temp: {safe(todayData.temperature, '°C')}</p>
      <p>• Humidity: {safe(todayData.humidity, '%')}</p>
      <p>• Wind: {safe(todayData.wind_speed, ' km/h')}</p>
      <p>• Rain: {safe(todayData.precip_mm, ' mm')}</p>
      <p>• Solar: {todayData.solar_ghi != null ? `${Number(todayData.solar_ghi).toFixed(1)} W/m²` : 'Not available'}</p>
    </div>
  );
}

function getTodayDateStr() {
  return new Date().toISOString().split('T')[0];
}

function BlockCard({ block, refreshData }) {
  const [editMode, setEditMode] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [actualInput, setActualInput] = useState(block.actual_irrigation_mm || '');
  const [saving, setSaving] = useState(false);
  const [showMaps, setShowMaps] = useState(false);
  const [edited, setEdited] = useState({
    name: block.block,
    crop: block.crop,
    crop_stage: block.crop_stage,
    irrigation_type: block.irrigation_type,
    application_rate_mm_hr: block.application_rate_mm_hr,
    soil_type: block.soil_type || "loam",
    raw_mm_per_m: block.raw_mm_used || '',
    ndvi_display_mode: block.ndvi_display_mode || "average"
  });

  const round = val => val != null ? Number(val).toFixed(2) : "–";
  const blockName = block.block.toLowerCase();
  const todayStr = getTodayDateStr();
  const imgBasePath = `/NDVI/${todayStr}/${blockName}`;

  const saveConfig = async () => {
    const res = await fetch(`https://irrixa-backend.onrender.com/api/save_config/${block.block}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(edited)
    });
    if (res.ok) {
      setShowToast(true);
      setTimeout(() => {
        setShowToast(false);
        setEditMode(false);
        refreshData();
      }, 1500);
    }
  };

  const saveActualIrrigation = async () => {
    const parsed = parseFloat(actualInput);
    if (isNaN(parsed)) return alert("⚠️ Enter a valid number");
    const res = await fetch("https://irrixa-backend.onrender.com/api/save_actual_irrigation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ block: block.block, date: todayStr, mm: parsed })
    });
    if (res.ok) refreshData();
    else alert("❌ Failed to save actual irrigation");
  };

  return (
    <div className="p-4 rounded-2xl border-4 shadow-md bg-white relative border-gray-300">
      {showToast && <Toast message="✅ Saved & Recalculated" />}
      <h2 className="text-xl font-bold mb-2">{block.block}</h2>
      {block.stress_flag && <p className="text-red-600 font-bold mb-1">⚠️ NDVI drop – check canopy, pests, or irrigation</p>}
      <ConfidenceBar score={block.confidence_score || 100} />
      <p><strong>Crop:</strong> {block.crop} | <strong>Stage:</strong> {block.crop_stage}</p>
      <p><strong>💧 Rec:</strong> {round(block.irrigation_mm)} mm
        {block.irrigation_mm === 0 && block.rain_mm > 0 && (
          <span className="ml-2 text-blue-500">💧❌ Skipped due to rain</span>
        )}
      </p>
      <p><strong>🌤️ ETo:</strong> {round(block.eto)} mm | <strong>🌧️ Rain:</strong> {round(block.rain_mm)} mm</p>
      <div className="flex items-center gap-2 mt-2">
        <input type="number" className="border p-1 rounded w-24" placeholder="Actual (mm)" value={actualInput} onChange={e => setActualInput(e.target.value)} />
        <button onClick={saveActualIrrigation} disabled={saving} className="bg-indigo-600 text-white px-3 py-1 rounded hover:bg-indigo-700">Save</button>
        <button onClick={() => setShowMaps(!showMaps)} className="ml-auto text-sm text-blue-600 underline">ℹ️ Info</button>
      </div>

      {showMaps && (
        <div className="mt-3 text-sm">
          <p><strong>Soil:</strong> {block.soil_type} | RAW: {block.raw_mm_used} mm/m</p>
          <p><strong>Kc:</strong> {round(block.kc)}</p>
          <p><strong>NDVI:</strong> {round(block.ndvi)} ({block.ndvi_display_mode})</p>
          {["ndvi", "ndre", "gndvi", "evi"].map(index => (
            <div key={index} className="mt-2">
              <p className="font-semibold uppercase">{index}</p>
              <img
                src={`${imgBasePath}_${index}.png`}
                alt={`${index} map`}
                className="w-full rounded shadow border cursor-pointer"
                onClick={() => window.open(`${imgBasePath}_${index}.png`, '_blank')}
                onError={e => e.target.style.display = 'none'}
              />
            </div>
          ))}
          <button onClick={() => setEditMode(true)} className="mt-2 text-blue-600 underline">✏️ Edit</button>
        </div>
      )}

      {editMode && (
        <div className="mt-4 text-sm space-y-2">
          <label>Block Name <input type="text" value={edited.name} onChange={e => setEdited({ ...edited, name: e.target.value })} className="w-full p-1 border rounded" /></label>
          <label>Crop <select value={edited.crop} onChange={e => setEdited({ ...edited, crop: e.target.value })} className="w-full p-1 border rounded">{CROP_OPTIONS.map(opt => <option key={opt}>{opt}</option>)}</select></label>
          <label>Stage <select value={edited.crop_stage} onChange={e => setEdited({ ...edited, crop_stage: e.target.value })} className="w-full p-1 border rounded">{STAGE_OPTIONS.map(opt => <option key={opt}>{opt}</option>)}</select></label>
          <label>Irrigation Type <select value={edited.irrigation_type} onChange={e => setEdited({ ...edited, irrigation_type: e.target.value })} className="w-full p-1 border rounded">{TYPE_OPTIONS.map(opt => <option key={opt}>{opt}</option>)}</select></label>
          <label>Application Rate (mm/hr) <input type="number" value={edited.application_rate_mm_hr} onChange={e => setEdited({ ...edited, application_rate_mm_hr: parseFloat(e.target.value) })} className="w-full p-1 border rounded" /></label>
          <label>Soil Type <select value={edited.soil_type} onChange={e => {
            const newSoil = e.target.value;
            const defaultRAW = SOIL_RAW_DEFAULTS[newSoil];
            const oldDefault = SOIL_RAW_DEFAULTS[edited.soil_type];
            const shouldReset = edited.raw_mm_per_m === oldDefault;
            setEdited(prev => ({ ...prev, soil_type: newSoil, raw_mm_per_m: shouldReset ? defaultRAW : prev.raw_mm_per_m }));
          }} className="w-full p-1 border rounded">{SOIL_OPTIONS.map(opt => <option key={opt}>{opt}</option>)}</select></label>
          <label>RAW (mm/m) <input type="number" value={edited.raw_mm_per_m} onChange={e => setEdited({ ...edited, raw_mm_per_m: parseFloat(e.target.value) })} className="w-full p-1 border rounded" /></label>
          <label>NDVI Mode <select value={edited.ndvi_display_mode} onChange={e => setEdited({ ...edited, ndvi_display_mode: e.target.value })} className="w-full p-1 border rounded"><option value="average">Average</option><option value="p80">P80</option></select></label>
          <button onClick={saveConfig} className="bg-blue-600 text-white mt-2 px-4 py-1 rounded">💾 Save</button>
          <button onClick={() => setEditMode(false)} className="ml-4 underline text-gray-500">Cancel</button>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [blocks, setBlocks] = useState([]);
  const [weather, setWeather] = useState(null);

  const fetchData = () => {
    fetch('/data/block_irrigation.json')
      .then(res => res.json())
      .then(data => setBlocks(data))
      .catch(err => console.error("Failed to load irrigation data:", err));

    fetch(`/Weather/${getTodayDateStr()}/weather_data.json`)
      .then(res => res.json())
      .then(data => setWeather(data))
      .catch(err => console.error("Failed to load weather data"));
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <h1 className="text-3xl font-bold text-center mb-6">💦 Irrixa Smart Irrigation Dashboard</h1>
      <div className="flex justify-center gap-4 mb-6">
        <button onClick={async () => {
          const res = await fetch("https://irrixa-backend.onrender.com/api/refresh_weather", { method: "POST" });
          if (res.ok) window.location.reload();
          else alert("❌ Weather update failed");
        }} className="bg-blue-500 text-white px-4 py-2 rounded shadow hover:bg-blue-600">🌤️ Refresh Weather</button>

        <button onClick={async () => {
          const res = await fetch("https://irrixa-backend.onrender.com/api/run_engine", { method: "POST" });
          if (res.ok) window.location.reload();
          else alert("❌ Engine run failed");
        }} className="bg-green-600 text-white px-4 py-2 rounded shadow hover:bg-green-700">🔁 Run Irrigation Engine</button>
      </div>

      <WeatherTile data={weather} />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {blocks.map(block => (
          <BlockCard key={block.block} block={block} refreshData={fetchData} />
        ))}
      </div>
    </div>
  );
}
