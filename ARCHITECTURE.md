┌────────────────────┐
│  Client / Frontend │
│  (Dashboard, Maps) │
└─────────┬──────────┘
          │ HTTP (JSON)
          ▼
┌────────────────────┐
│   FastAPI Service  │
│  geo-analytics-api │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  Analytics Layer   │
│  (Pandas logic)    │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│   Data Source      │
│   CSV (local)      │
└────────────────────┘
