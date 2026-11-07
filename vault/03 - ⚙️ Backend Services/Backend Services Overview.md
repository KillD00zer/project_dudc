---
title: Backend Services Overview
tags: [backend, server, architecture, services]
related_files:
  - DUDC V3/server/__init__.py
---

# ⚙️ Backend Services Overview (`server`)

The `server` package provides modular backend services running on Python's built-in HTTP server infrastructure. Each service is encapsulated into its own dedicated module to maintain clean separation of concerns.

---

## 🗂️ Module Map

```text
DUDC V3/
├── app_server.py              # Server entry point, port management, browser launch
└── server/
    ├── __init__.py            # Service package re-exports
    ├── config.py              # Path configuration, system drives, directory explorer backend
    ├── session_manager.py     # Thread-safe in-memory parcel state & recovery snapshotting
    ├── handlers.py            # Central HTTP REST router for GET and POST requests
    ├── pdf_service.py         # Microsoft Edge headless vector PDF rendering
    ├── drafts_service.py      # Self-contained JSON drafts with embedded base64 graphics
    └── git_service.py         # Git remote fetch/pull and conflict resolution
```

---

## 🔌 Decoupling & Import Boundaries
- `server/` modules import from `core_gis/`.
- `core_gis/` NEVER imports from `server/`.
- `app_server.py` acts as a thin bootstrap orchestrator (~170 lines) that starts the socket listener and delegates all HTTP routing to `handlers.py`.

