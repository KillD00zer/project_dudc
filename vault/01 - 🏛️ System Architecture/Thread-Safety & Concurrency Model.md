---
title: Thread-Safety & Concurrency Model
tags: [architecture, thread-safety, concurrency, matplotlib, edge]
related_files:
  - DUDC V3/server/session_manager.py
  - DUDC V3/core_gis/croquis.py
  - DUDC V3/server/pdf_service.py
---

# 🧵 Thread-Safety & Concurrency Model

In multi-user or high-frequency automated environments (e.g., automated test suites, background cron tasks, or simultaneous client requests), shared state corruption and matplotlib state leakage are common failure points. DUDC V4.0 enforces strict concurrency safety at three levels:

---

## 1. In-Memory Session Synchronization (`SessionManager`)
The backend application server uses Python's `ThreadingHTTPServer`, spawning a separate worker thread for each incoming HTTP request.

- In [`DUDC V3/server/session_manager.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/server/session_manager.py), all read and write operations on `current_parcels`, `output_dir`, and `active_session` are gated by a re-entrant thread lock:
  ```python
  class SessionManager:
      def __init__(self):
          self._lock = threading.Lock()
          ...
      def update_active_session(self, session_data):
          with self._lock:
              # Safe in-memory update & disk snapshot
  ```
- This guarantees that rapid autosave requests (`/api/sync-session` or `/api/save-draft`) never collide with file export operations (`/api/export-package`).

---

## 2. Object-Oriented Matplotlib Rendering (Zero Global State)
Matplotlib's default `pyplot` interface (`plt.*`) relies on global state and is notorious for memory leaks and cross-thread race conditions.

- In [`DUDC V3/core_gis/croquis.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/core_gis/croquis.py), pyplot is completely avoided. Rendering uses the pure Object-Oriented Agg backend:
  ```python
  import matplotlib
  matplotlib.use('Agg')
  from matplotlib.figure import Figure
  from matplotlib.backends.backend_agg import FigureCanvasAgg

  fig = Figure(figsize=(6.5, 4.8), dpi=300)
  FigureCanvasAgg(fig)
  ax = fig.add_subplot(111)
  # All plots, patches, and text rendered directly onto fig / ax instances
  fig.savefig(output_path, dpi=300, bbox_inches='tight')
  ```
- Each croquis request instantiates its own isolated `Figure` and canvas. No thread can overwrite or alter the active axes of another request.

---

## 3. Microsoft Edge Headless Subprocess Isolation
When rendering HTML certificates to vector A4 PDFs, the server uses Microsoft Edge in headless mode.

- In [`DUDC V3/server/pdf_service.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/server/pdf_service.py), each PDF request writes a uniquely timestamped temporary HTML file:
  `temp_assets/temp_print_<timestamp>.html`
- A dedicated, isolated OS subprocess is spawned:
  ```powershell
  msedge.exe --headless --disable-gpu --no-sandbox --no-pdf-header-footer --run-all-compositor-stages-before-draw --print-to-pdf=<pdf_path> <html_path>
  ```
- Subprocesses are strictly isolated by PID and automatically cleaned up in a `finally` block, ensuring no leaked temp files or process contention.

