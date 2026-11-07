---
title: Application Server (app_server.py)
tags: [backend, server, http, port-handling]
related_files:
  - DUDC V3/app_server.py
---

# ⚙️ Application Server (`app_server.py`)

File: [`DUDC V3/app_server.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/app_server.py)

The lightweight entry point that binds the socket listener, manages Windows port conflicts, handles DNS delays, and launches the client browser.

---

## ⚡ Performance & Windows Resilience Features

### 1. Reverse DNS Delay Elimination
Windows `BaseHTTPRequestHandler` defaults to performing a reverse DNS lookup (`getfqdn()`) on every request client IP address. On local machines with certain firewall configurations, this causes a 2.0-second delay per request!
`app_server.py` overrides `address_string()` to return the IP immediately:
```python
class DUDCV3RequestHandler(BaseHTTPRequestHandler):
    def address_string(self):
        # Prevents 2.0s reverse DNS lookup penalty on Windows
        return self.client_address[0]
```

### 2. Automatic Port Conflict Resolution
Port 8765 is the standard listening port.
1. `kill_existing_on_port(port)` uses `netstat -ano` and `taskkill` to automatically terminate stale zombie processes listening on 8765 from previous crashed sessions.
2. If port 8765 remains occupied, `start_server()` dynamically probes ports sequentially from $8765 \dots 8785$ until an available socket is acquired.

### 3. Localhost to 127.0.0.1 Normalization
On Windows 10/11, navigating to `http://localhost:8765` often results in IPv6 resolution delays (`::1`). The request handler automatically redirects any `localhost` Host header to `http://127.0.0.1:<port>`.

### 4. Headless-Ready & Threaded
Uses `ThreadingHTTPServer` to process requests concurrently across separate threads without blocking.

