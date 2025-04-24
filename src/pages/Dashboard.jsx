import React from "react";

const mockData = [
  {
    block: "D2_Bay_1",
    irrigation_mm: 1.3,
    irrigation_minutes: 5.9,
    kc: 0.715,
    ndvi: 0.571,
    eto: 1.82,
  },
  {
    block: "D2_Bay_10",
    irrigation_mm: 1.81,
    irrigation_minutes: 9.2,
    kc: 0.993,
    ndvi: 0.794,
    eto: 1.82,
  },
];

const Dashboard = () => {
  return (
    <div className="p-4 bg-gray-100 min-h-screen">
      <h1 className="text-2xl font-bold mb-4">Irrixa Irrigation Dashboard</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {mockData.map((block, index) => (
          <div key={index} className="bg-white p-4 rounded-xl shadow-md">
            <h2 className="font-semibold text-lg mb-2">{block.block}</h2>
            <p>💧 Irrigation: {block.irrigation_mm} mm ({block.irrigation_minutes} min)</p>
            <p>🌿 NDVI: {block.ndvi}</p>
            <p>📈 Kc: {block.kc}</p>
            <p>☀️ ETo: {block.eto} mm</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
