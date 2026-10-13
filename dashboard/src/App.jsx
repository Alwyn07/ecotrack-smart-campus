// ============================================================
// ECOTRACK - SMART CAMPUS RESOURCE MONITORING SYSTEM
// Day 6: Analytics Dashboard + Recommendation Engine
// ============================================================

import { useCallback, useEffect, useState } from "react";

import {
  Activity,
  AlertTriangle,
  Building2,
  CalendarClock,
  Download,
  Gauge,
  Leaf,
  RefreshCw,
  Zap,
} from "lucide-react";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { generateRecommendations } from "./recommendations.js";

import "./App.css";

// ------------------------------------------------------------
// CONFIGURATION
// ------------------------------------------------------------

const DATA_FILES = {
  campus: "/data/campus_power_report.csv",
  building: "/data/building_report.csv",
  room: "/data/room_report.csv",
  alerts: "/data/energy_waste_alerts.csv",
  peak: "/data/peak_usage_report.csv",
  forecast: "/data/next_day_forecast.csv",
};

// ------------------------------------------------------------
// CSV PARSER
// Handles quoted fields and commas inside quoted values.
// ------------------------------------------------------------

function parseCSVLine(line) {
  const fields = [];
  let current = "";
  let insideQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];

    if (char === '"') {
      if (insideQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        insideQuotes = !insideQuotes;
      }
    } else if (char === "," && !insideQuotes) {
      fields.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }

  fields.push(current.trim());

  return fields;
}

function parseCSV(text) {
  const lines = text
    .replace(/^\uFEFF/, "")
    .split(/\r?\n/)
    .filter((line) => line.trim() !== "");

  if (lines.length < 2) {
    return [];
  }

  const headers = parseCSVLine(lines[0]);

  return lines.slice(1).map((line) => {
    const values = parseCSVLine(line);
    const row = {};

    headers.forEach((header, index) => {
      row[header] = values[index] ?? "";
    });

    return row;
  });
}

// ------------------------------------------------------------
// DATA UTILITIES
// ------------------------------------------------------------

function numberValue(value, fallback = 0) {
  const result = Number(value);

  return Number.isFinite(result) ? result : fallback;
}

function formatNumber(value, decimals = 2) {
  return numberValue(value).toLocaleString("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function formatPower(value) {
  return `${formatNumber(value, 0)} W`;
}

function formatEnergy(value) {
  return `${formatNumber(value, 2)} kWh`;
}

function getTimestamp(row) {
  return row.timestamp || row.time || row.hour || "Unknown";
}

// ------------------------------------------------------------
// DATA TRANSFORMATION
// ------------------------------------------------------------

function transformCampusData(rows) {
  return rows.map((row) => ({
    time: getTimestamp(row),
    power: numberValue(
      row.campus_power_w ??
        row.campus_power ??
        row.power
    ),
  }));
}

function transformBuildingData(rows) {
  return rows.map((row) => ({
    building: row.building || "Unknown",
    averagePower: numberValue(row.average_room_power),
    peakPower: numberValue(row.peak_room_power),
    energy: numberValue(row.total_recorded_energy),
    readings: numberValue(row.readings),
  }));
}

function transformRoomData(rows) {
  return rows.map((row) => ({
    building: row.building || "Unknown",
    room: row.room || "Unknown",
    averagePower: numberValue(row.average_power),
    maximumPower: numberValue(row.maximum_power),
    energy: numberValue(row.total_recorded_energy),
    occupancy: numberValue(row.average_occupancy),
  }));
}

function transformAlerts(rows) {
  return rows.map((row) => ({
    timestamp: getTimestamp(row),
    building: row.building || "Unknown",
    room: row.room || "Unknown",
    occupancy: numberValue(row.occupancy),
    power: numberValue(
      row.power ??
        row.current_power ??
        row.power_w
    ),
  }));
}

function transformPeakData(rows) {
  return rows.map((row) => ({
    time: getTimestamp(row),
    power: numberValue(
      row.campus_power ??
        row.campus_power_w ??
        row.power
    ),
    powerKW: numberValue(
      row.campus_power_kw,
      numberValue(
        row.campus_power ??
          row.campus_power_w ??
          row.power
      ) / 1000
    ),
  }));
}

function transformForecastData(rows) {
  const hourlyData = {};

  rows.forEach((row) => {
    const time = getTimestamp(row);

    const power = numberValue(
      row.predicted_power_w ??
        row.predicted_power ??
        row.power
    );

    const energy = numberValue(
      row.predicted_energy_kwh ??
        row.predicted_energy ??
        row.energy
    );

    if (!hourlyData[time]) {
      hourlyData[time] = {
        time,
        power: 0,
        energy: 0,
        rooms: 0,
      };
    }

    // Each row normally represents one room at one hour.
    hourlyData[time].power += power;
    hourlyData[time].energy += energy;
    hourlyData[time].rooms += 1;
  });

  return Object.values(hourlyData).sort((a, b) =>
    String(a.time).localeCompare(String(b.time))
  );
}

// ------------------------------------------------------------
// REUSABLE COMPONENTS
// ------------------------------------------------------------

function SectionHeading({ eyebrow, title, count }) {
  return (
    <div className="section-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h2>{title}</h2>
      </div>

      {count !== undefined && (
        <span className="record-count">{count}</span>
      )}
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  unit,
  description,
  className = "",
}) {
  return (
    <article className={`metric-card ${className}`}>
      <div className="metric-top">
        <span className="metric-label">{label}</span>

        <span className="metric-icon">
          <Icon size={19} />
        </span>
      </div>

      <div className="metric-value">
        {value}
        {unit && <span className="metric-unit">{unit}</span>}
      </div>

      <p className="metric-description">{description}</p>
    </article>
  );
}

function EmptyState({ message }) {
  return <div className="empty-state">{message}</div>;
}

// ------------------------------------------------------------
// MAIN DASHBOARD
// ------------------------------------------------------------

export default function App() {
  const [data, setData] = useState({
    campus: [],
    building: [],
    room: [],
    alerts: [],
    peak: [],
    forecast: [],
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  // ----------------------------------------------------------
  // LOAD CSV FILES
  // ----------------------------------------------------------

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const entries = Object.entries(DATA_FILES);

      const results = await Promise.all(
        entries.map(async ([key, path]) => {
          const response = await fetch(
            `${path}?_=${Date.now()}`
          );

          if (!response.ok) {
            throw new Error(
              `Unable to load ${path}. HTTP ${response.status}.`
            );
          }

          const text = await response.text();

          return [key, parseCSV(text)];
        })
      );

      const raw = Object.fromEntries(results);

      setData({
        campus: transformCampusData(raw.campus),
        building: transformBuildingData(raw.building),
        room: transformRoomData(raw.room),
        alerts: transformAlerts(raw.alerts),
        peak: transformPeakData(raw.peak),
        forecast: transformForecastData(raw.forecast),
      });

      setLastUpdated(new Date());
    } catch (loadError) {
      console.error("EcoTrack data loading error:", loadError);

      setError(
        `${loadError.message} Check that all six CSV files exist in dashboard/public/data and restart the Vite server if necessary.`
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ----------------------------------------------------------
  // SUMMARY CALCULATIONS
  // ----------------------------------------------------------

  const totalRecordedEnergy = data.building.reduce(
    (sum, building) => sum + building.energy,
    0
  );

  const averageCampusPower =
    data.campus.length > 0
      ? data.campus.reduce(
          (sum, row) => sum + row.power,
          0
        ) / data.campus.length
      : 0;

  const peakRecorded = data.campus.reduce(
    (best, row) =>
      row.power > best.power ? row : best,
    { time: "--", power: 0 }
  );

  const peakForecast = data.forecast.reduce(
    (best, row) =>
      row.power > best.power ? row : best,
    { time: "--", power: 0 }
  );

  const totalPredictedEnergy = data.forecast.reduce(
    (sum, row) => sum + row.energy,
    0
  );

  // ----------------------------------------------------------
  // RECOMMENDATION ENGINE
  // ----------------------------------------------------------

  const recommendations = generateRecommendations({
    rooms: data.room,
    alerts: data.alerts,
    forecast: data.forecast,
  });

  // ----------------------------------------------------------
  // FORECAST EXPORT
  // ----------------------------------------------------------

  function exportForecast() {
    if (data.forecast.length === 0) {
      return;
    }

    const header =
      "timestamp,predicted_campus_power_w,predicted_energy_kwh";

    const rows = data.forecast.map((row) =>
      [
        row.time,
        row.power.toFixed(2),
        row.energy.toFixed(4),
      ].join(",")
    );

    const csv = [header, ...rows].join("\n");

    const blob = new Blob([csv], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "ecotrack_campus_forecast.csv";

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
  }

  // ----------------------------------------------------------
  // LOADING STATE
  // ----------------------------------------------------------

  if (loading && !lastUpdated) {
    return (
      <main className="loading-screen">
        <div className="loading-logo">
          <Leaf size={30} />
        </div>

        <h1>EcoTrack</h1>

        <p>Loading campus energy analytics...</p>

        <div className="loading-track">
          <div className="loading-progress" />
        </div>
      </main>
    );
  }

  // ----------------------------------------------------------
  // DASHBOARD UI
  // ----------------------------------------------------------

  return (
    <main className="app-shell">
      {/* HEADER */}

      <header className="topbar">
        <div className="brand">
          <div className="brand-logo">
            <Leaf size={25} />
          </div>

          <div>
            <h1>EcoTrack</h1>
            <p>SMART CAMPUS RESOURCE MONITORING</p>
          </div>
        </div>

        <div className="topbar-actions">
          <div className="system-status">
            <span className="status-dot" />
            <span>Analytics Dashboard</span>
          </div>

          <button
            className="button button-secondary"
            onClick={loadData}
            disabled={loading}
          >
            <RefreshCw
              size={16}
              className={loading ? "spin" : ""}
            />

            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </header>

      {/* MAIN CONTENT */}

      <div className="dashboard-content">
        {/* INTRODUCTION */}

        <section className="page-intro">
          <div>
            <div className="eyebrow">CAMPUS INTELLIGENCE PLATFORM</div>

            <h2>
              Energy Overview<span className="title-period">.</span>
            </h2>

            <p>
              Monitor recorded consumption, identify potential
              energy waste, and review predicted campus demand.
            </p>
          </div>

          <div className="updated-badge">
            <Activity size={16} />

            <span>
              {lastUpdated
                ? `Updated ${lastUpdated.toLocaleTimeString(
                    "en-IN",
                    {
                      hour: "2-digit",
                      minute: "2-digit",
                    }
                  )}`
                : "Awaiting data"}
            </span>
          </div>
        </section>

        {/* ERROR MESSAGE */}

        {error && (
          <section className="error-banner">
            <AlertTriangle size={20} />

            <div>
              <strong>Data loading error</strong>
              <p>{error}</p>
            </div>
          </section>
        )}

        {/* KPI CARDS */}

        <section className="metrics-grid">
          <MetricCard
            icon={Zap}
            label="Recorded Energy"
            value={formatNumber(totalRecordedEnergy, 2)}
            unit="kWh"
            description="Total energy recorded across the available building reports"
            className="metric-primary"
          />

          <MetricCard
            icon={Gauge}
            label="Average Recorded Demand"
            value={formatNumber(
              averageCampusPower / 1000,
              2
            )}
            unit="kW"
            description="Mean campus power across recorded time slots"
          />

          <MetricCard
            icon={Activity}
            label="Peak Forecast Demand"
            value={formatNumber(
              peakForecast.power / 1000,
              2
            )}
            unit="kW"
            description={`Predicted maximum at ${peakForecast.time}`}
          />

          <MetricCard
            icon={AlertTriangle}
            label="Waste Alerts"
            value={data.alerts.length}
            description="Potential energy waste events in the loaded report"
            className={
              data.alerts.length > 0
                ? "metric-alert"
                : ""
            }
          />
        </section>

        {/* RECORDED SYSTEM SUMMARY */}

        <section className="summary-strip">
          <div className="summary-item">
            <Building2 size={19} />

            <div>
              <span className="summary-label">
                Buildings monitored
              </span>

              <strong>{data.building.length}</strong>
            </div>
          </div>

          <div className="summary-item">
            <Activity size={19} />

            <div>
              <span className="summary-label">
                Rooms monitored
              </span>

              <strong>{data.room.length}</strong>
            </div>
          </div>

          <div className="summary-item">
            <CalendarClock size={19} />

            <div>
              <span className="summary-label">
                Recorded time slots
              </span>

              <strong>{data.campus.length}</strong>
            </div>
          </div>

          <div className="summary-item">
            <Zap size={19} />

            <div>
              <span className="summary-label">
                Recorded peak
              </span>

              <strong>
                {formatNumber(
                  peakRecorded.power / 1000,
                  2
                )}{" "}
                kW
              </strong>
            </div>
          </div>
        </section>

        {/* CHART ROW 1 */}

        <section className="chart-grid">
          {/* FORECAST CHART */}

          <article className="panel chart-panel forecast-panel">
            <SectionHeading
              eyebrow="MACHINE LEARNING"
              title="Next-Day Demand Forecast"
              count={`${data.forecast.length} time slots`}
            />

            <div className="chart-summary">
              <div>
                <span>Predicted energy</span>

                <strong>
                  {formatEnergy(totalPredictedEnergy)}
                </strong>
              </div>

              <div>
                <span>Peak predicted demand</span>

                <strong>
                  {formatNumber(
                    peakForecast.power / 1000,
                    2
                  )}{" "}
                  kW
                </strong>
              </div>
            </div>

            <div className="chart-container chart-large">
              {data.forecast.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.forecast}>
                    <defs>
                      <linearGradient
                        id="forecastGradient"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="0%"
                          stopColor="#52e0a2"
                          stopOpacity={0.3}
                        />

                        <stop
                          offset="95%"
                          stopColor="#52e0a2"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>

                    <CartesianGrid
                      stroke="#26313f"
                      strokeDasharray="4 4"
                      vertical={false}
                    />

                    <XAxis
                      dataKey="time"
                      stroke="#8491a3"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 11 }}
                    />

                    <YAxis
                      stroke="#8491a3"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 11 }}
                      tickFormatter={(value) =>
                        `${(value / 1000).toFixed(0)}k`
                      }
                    />

                    <Tooltip
                      contentStyle={{
                        background: "#121b27",
                        border: "1px solid #303d4e",
                        borderRadius: "10px",
                        color: "#ffffff",
                      }}
                      formatter={(value, name) => [
                        name === "power"
                          ? `${formatNumber(
                              value,
                              2
                            )} W`
                          : `${formatNumber(
                              value,
                              2
                            )} kWh`,
                        name === "power"
                          ? "Predicted demand"
                          : "Predicted energy",
                      ]}
                    />

                    <Legend />

                    <Area
                      type="monotone"
                      dataKey="power"
                      name="Predicted demand"
                      stroke="#52e0a2"
                      strokeWidth={2.5}
                      fill="url(#forecastGradient)"
                      activeDot={{ r: 5 }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No forecast data available." />
              )}
            </div>

            <div className="chart-footer">
              <span className="chart-footer-dot" />

              <span>
                Forecast generated from the project's trained
                model and synthetic historical dataset.
              </span>
            </div>

            <button
              className="button button-primary export-button"
              onClick={exportForecast}
              disabled={data.forecast.length === 0}
            >
              <Download size={16} />
              Export Forecast CSV
            </button>
          </article>

          {/* RECORDED DEMAND CHART */}

          <article className="panel chart-panel">
            <SectionHeading
              eyebrow="RECORDED DATA"
              title="Campus Power Demand"
              count={`${data.campus.length} readings`}
            />

            <div className="chart-container">
              {data.campus.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.campus}>
                    <CartesianGrid
                      stroke="#26313f"
                      strokeDasharray="4 4"
                      vertical={false}
                    />

                    <XAxis
                      dataKey="time"
                      stroke="#8491a3"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 11 }}
                    />

                    <YAxis
                      stroke="#8491a3"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 11 }}
                      tickFormatter={(value) =>
                        `${(value / 1000).toFixed(0)}k`
                      }
                    />

                    <Tooltip
                      contentStyle={{
                        background: "#121b27",
                        border: "1px solid #303d4e",
                        borderRadius: "10px",
                      }}
                      formatter={(value) => [
                        formatPower(value),
                        "Campus demand",
                      ]}
                    />

                    <Bar
                      dataKey="power"
                      name="Campus demand"
                      fill="#7296ff"
                      radius={[5, 5, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No recorded demand data available." />
              )}
            </div>

            <div className="chart-note">
              Recorded peak:{" "}
              <strong>
                {formatNumber(
                  peakRecorded.power / 1000,
                  2
                )}{" "}
                kW
              </strong>{" "}
              at {peakRecorded.time}.
            </div>
          </article>
        </section>

        {/* CHART ROW 2 */}

        <section className="chart-grid">
          {/* BUILDING ENERGY */}

          <article className="panel chart-panel">
            <SectionHeading
              eyebrow="BUILDING ANALYTICS"
              title="Recorded Energy by Building"
              count={`${data.building.length} buildings`}
            />

            <div className="chart-container">
              {data.building.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.building}>
                    <CartesianGrid
                      stroke="#26313f"
                      strokeDasharray="4 4"
                      vertical={false}
                    />

                    <XAxis
                      dataKey="building"
                      stroke="#8491a3"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 11 }}
                    />

                    <YAxis
                      stroke="#8491a3"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 11 }}
                    />

                    <Tooltip
                      contentStyle={{
                        background: "#121b27",
                        border: "1px solid #303d4e",
                        borderRadius: "10px",
                      }}
                      formatter={(value) => [
                        formatEnergy(value),
                        "Recorded energy",
                      ]}
                    />

                    <Bar
                      dataKey="energy"
                      name="Recorded energy"
                      radius={[5, 5, 0, 0]}
                    >
                      {data.building.map((building, index) => (
                        <Cell
                          key={building.building}
                          fill={
                            index % 2 === 0
                              ? "#52e0a2"
                              : "#7296ff"
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No building data available." />
              )}
            </div>

            <div className="chart-note">
              Total recorded energy:{" "}
              <strong>
                {formatEnergy(totalRecordedEnergy)}
              </strong>
            </div>
          </article>

          {/* ROOM POWER */}

          <article className="panel chart-panel">
            <SectionHeading
              eyebrow="ROOM ANALYTICS"
              title="Average Room Power"
              count={`${data.room.length} rooms`}
            />

            <div className="chart-container">
              {data.room.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data.room}
                    layout="vertical"
                    margin={{
                      left: 12,
                      right: 12,
                    }}
                  >
                    <CartesianGrid
                      stroke="#26313f"
                      strokeDasharray="4 4"
                      horizontal={false}
                    />

                    <XAxis
                      type="number"
                      stroke="#8491a3"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 11 }}
                    />

                    <YAxis
                      type="category"
                      dataKey="room"
                      width={105}
                      stroke="#8491a3"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 10 }}
                    />

                    <Tooltip
                      contentStyle={{
                        background: "#121b27",
                        border: "1px solid #303d4e",
                        borderRadius: "10px",
                      }}
                      formatter={(value) => [
                        formatPower(value),
                        "Average power",
                      ]}
                      labelFormatter={(label) => {
                        const room = data.room.find(
                          (item) => item.room === label
                        );

                        return room
                          ? `${room.building} — ${label}`
                          : label;
                      }}
                    />

                    <Bar
                      dataKey="averagePower"
                      name="Average power"
                      fill="#7296ff"
                      radius={[0, 5, 5, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No room data available." />
              )}
            </div>

            <div className="chart-note">
              Room values represent average recorded power,
              not total energy consumption.
            </div>
          </article>
        </section>

        {/* ROOM DETAILS TABLE */}

        <section className="panel table-panel">
          <SectionHeading
            eyebrow="DETAILED ANALYTICS"
            title="Room Performance"
            count={`${data.room.length} rooms`}
          />

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Room</th>
                  <th>Building</th>
                  <th>Average Power</th>
                  <th>Maximum Power</th>
                  <th>Recorded Energy</th>
                  <th>Average Occupancy</th>
                </tr>
              </thead>

              <tbody>
                {[...data.room]
                  .sort(
                    (a, b) =>
                      b.averagePower - a.averagePower
                  )
                  .map((room) => (
                    <tr
                      key={`${room.building}-${room.room}`}
                    >
                      <td className="room-name">
                        {room.room}
                      </td>

                      <td>{room.building}</td>

                      <td>
                        {formatPower(room.averagePower)}
                      </td>

                      <td>
                        {formatPower(room.maximumPower)}
                      </td>

                      <td>{formatEnergy(room.energy)}</td>

                      <td>
                        {formatNumber(room.occupancy, 1)}
                      </td>
                    </tr>
                  ))}

                {data.room.length === 0 && (
                  <tr>
                    <td colSpan="6">
                      No room records available.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* ENERGY WASTE ALERTS */}

        <section className="panel alerts-panel">
          <SectionHeading
            eyebrow="ANOMALY DETECTION"
            title="Energy Waste Alerts"
            count={`${data.alerts.length} alerts`}
          />

          {data.alerts.length > 0 ? (
            <div className="alerts-list">
              {data.alerts.map((alert, index) => (
                <article
                  className="alert-card"
                  key={`${alert.building}-${alert.room}-${alert.timestamp}-${index}`}
                >
                  <div className="alert-icon">
                    <AlertTriangle size={21} />
                  </div>

                  <div className="alert-main">
                    <h3>
                      High power consumption while
                      unoccupied
                    </h3>

                    <p className="alert-location">
                      {alert.building} — {alert.room}
                    </p>

                    <p className="alert-detail">
                      Recorded at {alert.timestamp}. Room
                      occupancy: {alert.occupancy}.
                    </p>
                  </div>

                  <div className="alert-reading">
                    <strong>
                      {formatPower(alert.power)}
                    </strong>

                    <span>Recorded power</span>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState message="No energy-waste alerts were found in the loaded report." />
          )}
        </section>

        {/* DAY 6: RECOMMENDATIONS */}

        <section className="panel recommendations-panel">
          <SectionHeading
            eyebrow="SMART CAMPUS OPTIMIZATION"
            title="Recommendations"
            count={`${recommendations.length} insights`}
          />

          <p className="recommendations-intro">
            Actionable suggestions generated from recorded
            consumption, energy-waste alerts, and forecast
            results.
          </p>

          <div className="recommendation-list">
            {recommendations.map((item) => (
              <article
                className={`recommendation-card recommendation-${item.type}`}
                key={item.id}
              >
                <div className="recommendation-marker">
                  {item.type === "critical"
                    ? "!"
                    : item.type === "warning"
                      ? "↗"
                      : item.type === "success"
                        ? "✓"
                        : "i"}
                </div>

                <div className="recommendation-content">
                  <div className="recommendation-header">
                    <h3>{item.title}</h3>

                    <span
                      className={`recommendation-tag tag-${item.type}`}
                    >
                      {item.type}
                    </span>
                  </div>

                  <div className="recommendation-location">
                    {item.location}
                  </div>

                  <p>{item.detail}</p>

                  {item.action && (
                    <div className="recommendation-action">
                      <strong>Suggested action:</strong>{" "}
                      {item.action}
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* FORECAST INFORMATION */}

        <section className="forecast-disclaimer">
          <div className="disclaimer-icon">
            <Activity size={18} />
          </div>

          <div>
            <strong>About these analytics</strong>

            <p>
              EcoTrack currently uses simulated campus readings
              and a model trained on synthetic historical data.
              Recommendations are rule-based suggestions.
              Forecasts and alerts should be verified against
              actual campus conditions before operational
              decisions are made.
            </p>
          </div>
        </section>

        {/* FOOTER */}

        <footer className="dashboard-footer">
          <div className="footer-brand">
            <Leaf size={17} />

            <span>ECOTRACK</span>
          </div>

          <span>
            Smart Campus Resource Monitoring &amp; Optimization
          </span>

          <span>Day 6 · Recommendation Engine</span>
        </footer>
      </div>
    </main>
  );
}