---
title: Frontend Architecture & State
tags: [frontend, architecture, state, wizard]
related_files:
  - DUDC V3/index.html
  - DUDC V3/js/state.js
  - DUDC V3/js/app.js
---

# 💻 Frontend Architecture & State

The DUDC V4.0 user interface is designed as an interactive, single-page application (SPA) built without heavy JavaScript frameworks (React/Vue/Angular), ensuring zero build steps, ultra-fast initial render, and complete offline independence.

---

## 🗂️ Script Modularization Map

```text
DUDC V3/js/
├── state.js                   # Global variables, workflow navigation, stage tabs
├── stage1.js                  # Survey ingestion, parcel cards, tables, image uploaders
├── stage2.js                  # Live A4 certificate editor, typography, spacing, watermark
├── stage3.js                  # Official cloud issuance verification, printing & export
├── drafts.js                  # Draft drawer, auto-save timers, session restoration
├── folder_explorer.js         # In-app visual folder browser modal
└── app.js                     # System bootstrap, keyboard shortcuts, update checks
```

---

## 🧭 Three-Stage Wizard State Machine

```mermaid
stateDiagram-v2
    [*] --> Stage1: Load Survey File / Sample

    state "Stage 1: استيراد وتدقيق الرفع" as Stage1 {
        Upload: Drag & Drop (.xls, .xlsx, .csv)
        Validate: Geodesic Area ±2.0m² Check
        SelectDistrict: Assign Official Center
    }

    state "Stage 2: استوديو التحرير والمراجعة" as Stage2 {
        LiveEdit: Editable A4 Certificate Table
        Spacing: Adjust Layout & Gaps
        Typography: Font sizes & Colors
        Watermark: Official DUDC Canvas Stamp
    }

    state "Stage 3: الاعتماد السحابي والطباعة" as Stage3 {
        VerifyToken: Modal.com Cloud Audit
        ExportPackage: PDF + JSON + PNG + JPG
        OpenFolder: Windows Explorer Launch
    }

    Stage1 --> Stage2: Center Assigned & Validated
    Stage2 --> Stage1: Back to Data Verification (Bidirectional Sync)
    Stage2 --> Stage3: Proceed to Cloud Issuance
    Stage3 --> Stage2: Back to Layout Edits
    Stage3 --> [*]: Completed & Archived
```

---

## 🌐 Global Variables (`state.js`)
- `currentStage: int` - Active stage index ($1, 2, 3$).
- `activeParcel: Optional[Object]` - Primary parcel record currently displayed and edited.
- `currentSegments: Array` - Segment boundary array with directions, lengths, azimuths, and neighbors.
- `outputDir: string` - Currently selected Windows output directory path.
- `savedTextDefaults: Object` - User typography preferences loaded from `user_default_settings.json`.
- `hasSavedCurrentPackage: bool` - Safety flag: strictly blocks printing before official package export.
- `officialCentersList: Array` - Array of $[id, name]$ for the 18 Dakahlia centers.

### Stage Transition Handlers (`switchStage(stageNum)`)
- **Exiting Stage 2:** Calls `saveCurrentStudioTextState()` and `syncDomToActiveParcel()` to preserve custom font styles and inline text edits.
- **Entering Stage 2:** Calls `syncStage1SegmentsToParcel()`, `syncStage1ToStage2(true)`, `updateSpacing()`, and `renderWatermark()`.
- **Exiting to Stage 1:** Calls `syncStage2ToStage1()` so any manual changes made on the certificate table reflect back in the coordinate table.

