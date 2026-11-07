---
title: Modal Security Client (security.py)
tags: [core-gis, security, modal, token]
related_files:
  - DUDC V3/core_gis/security.py
---

# 📐 Modal Security Client (`security.py`)

File: [`DUDC V3/core_gis/security.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/core_gis/security.py)

Acts as the client bridge between the local cadastral studio and the cloud-isolated Modal.com security service.

---

## 🌐 Cloud Endpoints & Constants

```python
CLOUD_ENDPOINT = "https://killd00zer--dudc-security-service-generate-token-endpoint.modal.run"
CONFIRM_ENDPOINT = "https://killd00zer--dudc-security-service-confirm-issuance-endpoint.modal.run"
OFFICE_API_KEY = "DUDC_DAKAHLIA_OFFICE_SECRET_2026_KEY"
TRIAL_TOKEN = "DUDC-TRIAL-SAMPLE-PREVIEW-000000-000000"
```

---

## 🛠️ Key Functions

### 1. `generate_dudc_token(...)`
Requests a 210-bit encrypted token from Modal.
- **Parameters:**
  - `name: str` - Applicant citizen name
  - `lon: float, lat: float` - Coordinate of Vertex 1
  - `lon_2: float, lat_2: float` - Coordinate of Vertex 2
  - `receipt_1: int, receipt_2: int` - Receipt numerical identifiers
  - `center: Union[int, str]` - Administrative center ID / name
  - `date_val: datetime` - Issuance date
  - `system_officer: str` - Approving officer name
  - `survey_technician: str` - Cadastral technician name
- **Behavior:**
  - Sends an HTTPS POST request with a 12.0s timeout.
  - Returns the generated encrypted token string on success.
  - Raises `RuntimeError` if internet connectivity is missing or the server reports an error. Local fallback is strictly prohibited to protect document integrity.

### 2. `confirm_cloud_issuance(token: str)`
Verifies and records the certificate issuance in the central database ledger.
- **Parameters:** `token: str`
- **Behavior:**
  - Sends token and `OFFICE_API_KEY` to `CONFIRM_ENDPOINT`.
  - Ensures the certificate is marked officially issued in central records before the user is permitted to print or export.

