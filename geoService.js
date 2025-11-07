// geoService.js

const { getRegionMeta } = require("./stateLookup");

function aggregateByRegion(rows) {
  const agg = {};

  for (const r of rows) {
    // Filter to US only for now; drop this if you want global
    if (r.country !== "United States") continue;

    const regionName = r.region || "Unknown";
    if (!agg[regionName]) {
      agg[regionName] = {
        sessions: 0,
        conversions: 0,
        revenue: 0,
        dates: {}, // date -> { sessions, conversions, revenue }
      };
    }

    const entry = agg[regionName];
    entry.sessions += r.sessions;
    entry.conversions += r.conversions;
    entry.revenue += r.revenue;

    if (!entry.dates[r.date]) {
      entry.dates[r.date] = { sessions: 0, conversions: 0, revenue: 0 };
    }
    entry.dates[r.date].sessions += r.sessions;
    entry.dates[r.date].conversions += r.conversions;
    entry.dates[r.date].revenue += r.revenue;
  }

  return agg;
}

function calcConversionRate(conversions, sessions) {
  if (!sessions || sessions <= 0) return 0;
  return conversions / sessions;
}

function calcDeltas(currAgg, prevAgg) {
  for (const [regionName, curr] of Object.entries(currAgg)) {
    const prev = prevAgg[regionName];
    if (prev && prev.sessions > 0) {
      curr.delta_vs_prev = (curr.sessions - prev.sessions) / prev.sessions;
    } else {
      curr.delta_vs_prev = curr.sessions > 0 ? 1.0 : 0.0;
    }
  }
}

function buildTimeseries(currAgg) {
  const timeseries = [];

  for (const [regionName, stats] of Object.entries(currAgg)) {
    const meta = getRegionMeta(regionName);
    const regionCode = meta.region_code;

    const dates = Object.entries(stats.dates).sort(([d1], [d2]) =>
      d1.localeCompare(d2)
    );

    for (const [date, vals] of dates) {
      const convRate = calcConversionRate(vals.conversions, vals.sessions);
      timeseries.push({
        date,
        region_code: regionCode,
        sessions: Math.round(vals.sessions),
        conversion_rate: convRate,
      });
    }
  }

  return timeseries;
}

function makeInsights(currAgg) {
  const entries = Object.entries(currAgg);
  if (!entries.length) return ["No traffic data found in this period."];

  const rows = [];
  let totalSessions = 0;
  let totalRevenue = 0;

  for (const [regionName, s] of entries) {
    const sessions = s.sessions;
    const conversions = s.conversions;
    const revenue = s.revenue;
    const convRate = calcConversionRate(conversions, sessions);
    const delta = s.delta_vs_prev || 0;
    const rps = sessions > 0 ? revenue / sessions : 0;

    rows.push({
      region_name: regionName,
      sessions,
      conversions,
      revenue,
      conv_rate: convRate,
      delta_vs_prev: delta,
      rps,
    });

    totalSessions += sessions;
    totalRevenue += revenue;
  }

  const avgRps = totalSessions > 0 ? totalRevenue / totalSessions : 0;
  const insights = [];

  // 1) Top by sessions
  const topSessions = rows.reduce((a, b) =>
    a.sessions > b.sessions ? a : b
  );
  insights.push(
    `${topSessions.region_name} is driving the most traffic with ${Math.round(
      topSessions.sessions
    ).toLocaleString()} sessions this period.`
  );

  // 2) Biggest positive delta
  const topDelta = rows.reduce((a, b) =>
    (a.delta_vs_prev || 0) > (b.delta_vs_prev || 0) ? a : b
  );
  if (topDelta.delta_vs_prev > 0) {
    insights.push(
      `Traffic in ${
        topDelta.region_name
      } is up ${(topDelta.delta_vs_prev * 100).toFixed(
        1
      )}% vs the previous period.`
    );
  }

  // 3) Highest conversion rate (with minimal traffic filter)
  const meaningful = rows.filter((r) => r.sessions >= 100);
  const convPool = meaningful.length ? meaningful : rows;
  const topConv = convPool.reduce((a, b) =>
    a.conv_rate > b.conv_rate ? a : b
  );
  insights.push(
    `${topConv.region_name} has the strongest conversion rate at ${(topConv.conv_rate *
      100).toFixed(2)}% among meaningful-traffic regions.`
  );

  // 4) >20% swings, max 3 regions
  const movers = rows
    .filter(
      (r) => Math.abs(r.delta_vs_prev) >= 0.2 && r.sessions >= 200
    )
    .sort(
      (a, b) =>
        Math.abs(b.delta_vs_prev || 0) - Math.abs(a.delta_vs_prev || 0)
    )
    .slice(0, 3);

  for (const r of movers) {
    const direction = r.delta_vs_prev > 0 ? "up" : "down";
    insights.push(
      `Traffic in ${r.region_name} is ${direction} ${Math.abs(
        r.delta_vs_prev * 100
      ).toFixed(1)}% vs the prior period (${Math.round(
        r.sessions
      ).toLocaleString()} sessions, ${(r.conv_rate * 100).toFixed(
        2
      )}% conversion).`
    );
  }

  // 5) High-value users (≥ 1.5x avg revenue per session)
  if (avgRps > 0) {
    const premium = rows
      .filter((r) => r.rps >= avgRps * 1.5 && r.sessions >= 100)
      .sort((a, b) => b.rps - a.rps)
      .slice(0, 3);

    for (const r of premium) {
      const multiplier = r.rps / avgRps;
      insights.push(
        `Users from ${r.region_name} generate about ${multiplier.toFixed(
          1
        )}× the average revenue per session ($${r.rps.toFixed(
          2
        )} vs $${avgRps.toFixed(2)}).`
      );
    }
  }

  return insights;
}

function buildDashboardPayload(gaResult) {
  const currRows = gaResult.current.rows || [];
  const prevRows = gaResult.previous.rows || [];

  const currAgg = aggregateByRegion(currRows);
  const prevAgg = aggregateByRegion(prevRows);

  calcDeltas(currAgg, prevAgg);

  const regionsPayload = Object.entries(currAgg).map(
    ([regionName, stats]) => {
      const meta = getRegionMeta(regionName);

      const sessions = Math.round(stats.sessions);
      const conversions = Math.round(stats.conversions);
      const revenue = Math.round(stats.revenue * 100) / 100;
      const convRate = calcConversionRate(
        stats.conversions,
        stats.sessions
      );
      const deltaVsPrev = stats.delta_vs_prev || 0;

      return {
        region_code: meta.region_code,
        region_name: meta.region_name,
        country: "United States",
        sessions,
        conversions,
        conversion_rate: convRate,
        revenue,
        lat: meta.lat,
        lng: meta.lng,
        delta_vs_prev: deltaVsPrev,
      };
    }
  );

  const timeseriesPayload = buildTimeseries(currAgg);
  const insightsPayload = makeInsights(currAgg);

  return {
    metric: "conversion_rate",
    date_range: `${gaResult.current.start} to ${gaResult.current.end}`,
    regions: regionsPayload,
    timeseries: timeseriesPayload,
    insights: insightsPayload,
  };
}

module.exports = {
  buildDashboardPayload,
};
