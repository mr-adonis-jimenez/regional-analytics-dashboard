// stateLookup.js

const STATE_META = {
  FL: {
    region_name: "Florida",
    lat: 27.7663,
    lng: -81.6868,
  },
  TX: {
    region_name: "Texas",
    lat: 31.0545,
    lng: -97.5635,
  },
  NY: {
    region_name: "New York",
    lat: 42.1657,
    lng: -74.9481,
  },
  CA: {
    region_name: "California",
    lat: 36.7783,
    lng: -119.4179,
  },
  // TODO: add all states you care about
};

function getRegionMeta(regionName) {
  // GA4 region string is usually full name: "Florida", "Texas", etc.
  const reverse = Object.entries(STATE_META).reduce((acc, [code, meta]) => {
    acc[meta.region_name] = code;
    return acc;
  }, {});

  const code = reverse[regionName];

  if (!code) {
    // Fallback: crude code + generic centroid
    return {
      region_code: regionName.slice(0, 3).toUpperCase(),
      region_name: regionName || "Unknown",
      lat: 37.0,
      lng: -95.0,
    };
  }

  const meta = STATE_META[code];
  return {
    region_code: code,
    region_name: meta.region_name,
    lat: meta.lat,
    lng: meta.lng,
  };
}

module.exports = {
  getRegionMeta,
  STATE_META,
};
