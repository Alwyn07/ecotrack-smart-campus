// ============================================================
// ECOTRACK - SMART CAMPUS RECOMMENDATION ENGINE
// Day 6
//
// Generates rule-based recommendations using:
// 1. Energy waste alerts
// 2. Room-level power consumption
// 3. Predicted campus energy demand
//
// This is a rule-based recommendation engine, not an AI model.
// ============================================================

function toNumber(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function formatPower(value) {
  return `${toNumber(value).toLocaleString("en-IN", {
    maximumFractionDigits: 1,
  })} W`;
}

export function generateRecommendations({
  rooms = [],
  alerts = [],
  forecast = [],
} = {}) {
  const recommendations = [];

  // ----------------------------------------------------------
  // RULE 1: Detect energy waste in unoccupied rooms
  // ----------------------------------------------------------

  alerts.forEach((alert) => {
    const power = toNumber(
      alert.power ?? alert.current_power ?? alert.power_w
    );

    const occupancy = toNumber(alert.occupancy);

    if (occupancy === 0 && power > 500) {
      recommendations.push({
        id: `waste-${alert.building}-${alert.room}-${alert.timestamp}`,
        type: "critical",
        title: "Investigate Energy Waste",
        location: `${alert.building || "Unknown Building"} — ${
          alert.room || "Unknown Room"
        }`,
        detail:
          `The room is unoccupied but consumes ${formatPower(
            power
          )}. Check whether lights, air conditioning, computers, or other appliances can be switched off.`,
        action:
          "Inspect the room and verify which appliances are operating.",
      });
    }
  });

  // ----------------------------------------------------------
  // RULE 2: Identify rooms with high average power consumption
  // ----------------------------------------------------------

  const rankedRooms = [...rooms].sort(
    (a, b) =>
      toNumber(b.averagePower) - toNumber(a.averagePower)
  );

  const highestPowerRoom = rankedRooms[0];

  if (
    highestPowerRoom &&
    toNumber(highestPowerRoom.averagePower) > 1000
  ) {
    recommendations.push({
      id: "highest-power-room",
      type: "warning",
      title: "Review High-Consumption Room",
      location: `${highestPowerRoom.building || "Unknown Building"} — ${
        highestPowerRoom.room || "Unknown Room"
      }`,
      detail:
        `This room has an average recorded power consumption of ${formatPower(
          highestPowerRoom.averagePower
        )}. Review appliance usage and operating schedules.`,
      action:
        "Compare appliance ratings, occupancy, and operating hours.",
    });
  }

  // ----------------------------------------------------------
  // RULE 3: Prepare for the predicted peak-demand period
  // ----------------------------------------------------------

  if (forecast.length > 0) {
    const peak = forecast.reduce((highest, current) =>
      toNumber(current.power) > toNumber(highest.power)
        ? current
        : highest
    );

    if (peak && toNumber(peak.power) > 0) {
      recommendations.push({
        id: "forecast-peak",
        type: "info",
        title: "Prepare for Peak Campus Demand",
        location: `Predicted peak: ${peak.time || "Unknown time"}`,
        detail:
          `The model predicts campus demand of ${(
            toNumber(peak.power) / 1000
          ).toFixed(2)} kW during this period.`,
        action:
          "Where practical, schedule flexible activities outside the predicted peak period and review major equipment usage.",
      });
    }
  }

  // ----------------------------------------------------------
  // RULE 4: Identify multiple high-consumption rooms
  // ----------------------------------------------------------

  const highLoadRooms = rooms.filter(
    (room) => toNumber(room.averagePower) > 1000
  );

  if (highLoadRooms.length >= 2) {
    recommendations.push({
      id: "multiple-high-load-rooms",
      type: "info",
      title: "Conduct an Appliance Efficiency Review",
      location: `${highLoadRooms.length} high-consumption rooms`,
      detail:
        "Several rooms have average recorded power consumption above 1,000 W. This may reflect legitimate equipment use rather than energy waste.",
      action:
        "Review appliance efficiency, room occupancy, and operating schedules before making changes.",
    });
  }

  // ----------------------------------------------------------
  // RULE 5: No recommendations triggered
  // ----------------------------------------------------------

  if (recommendations.length === 0) {
    recommendations.push({
      id: "no-recommendations",
      type: "success",
      title: "No Recommendations Triggered",
      location: "Current Reports",
      detail:
        "None of the configured recommendation rules were triggered by the loaded data.",
      action:
        "Continue monitoring campus energy usage and review new reports when available.",
    });
  }

  return recommendations;
}