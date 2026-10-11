/**
 * DUDC V4.0 - Application Bootstrap & Event Wiring (app.js)
 */

      // =========================================================================
      // نافذة ما بعد حفظ المشروع: السؤال عن الرغبة في الطباعة الفورية
      // =========================================================================
      var lastExportedData = null;
      var lastExportedFileBase = '';

      function openPostSavePrintModal(data, fileBase) {
        lastExportedData = data;
        lastExportedFileBase = fileBase;

        const modal = document.getElementById('postSavePrintModalBackdrop');
        if (!modal) return;

        const infoEl = document.getElementById('postSaveCitizenInfo');
        if (infoEl) {
          infoEl.textContent = `المواطن: ${fileBase || 'العميل'}`;
        }

        const pathEl = document.getElementById('postSaveFolderPath');
        if (pathEl) {
          pathEl.textContent = data.folder_path || '--';
        }

        modal.style.display = 'flex';
      }

      function closePostSavePrintModal() {
        const modal = document.getElementById('postSavePrintModalBackdrop');
        if (modal) modal.style.display = 'none';
      }

      // زر الطباعة الفورية من داخل المودال
      document.getElementById('btnModalConfirmPrint')?.addEventListener('click', () => {
        closePostSavePrintModal();
        triggerPdfPrint();
      });

      // زر فتح مجلد المشروع فقط من داخل المودال
      document.getElementById('btnModalOpenFolder')?.addEventListener('click', () => {
        if (lastExportedData && lastExportedData.folder_path) {
          fetch('/api/open-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_path: lastExportedData.folder_path })
          });
        }
        closePostSavePrintModal();
      });

      // زر إغلاق المودال
      document.getElementById('btnModalDismiss')?.addEventListener('click', closePostSavePrintModal);
      document.getElementById('btnClosePostSaveModal')?.addEventListener('click', closePostSavePrintModal);

      // إغلاق عند النقر على الخلفية المعتمة
      document.getElementById('postSavePrintModalBackdrop')?.addEventListener('click', (e) => {
        if (e.target.id === 'postSavePrintModalBackdrop') {
          closePostSavePrintModal();
        }
      });

      document.getElementById('btnOpenOutputDir').addEventListener('click', () => {
        fetch('/api/open-folder', { method: 'POST' });
      });

      document.getElementById('btnStartNewWorkflow').addEventListener('click', () => {
        if (confirm('هل تود بدء معاملة جديدة لمواطن آخر؟')) {
          location.reload();
        }
      });

      // زووم صفحة العرض
      let currentZoom = 1.0;
      const zoomLevelDisplay = document.getElementById('zoomLevel');
      function setZoom(factor) {
        currentZoom = Math.min(Math.max(0.4, factor), 1.8);
        pageContainer.style.transform = `scale(${currentZoom})`;
        zoomLevelDisplay.textContent = `${Math.round(currentZoom * 100)}%`;
      }
      document.getElementById('btnZoomIn').addEventListener('click', () => setZoom(currentZoom + 0.1));
      document.getElementById('btnZoomOut').addEventListener('click', () => setZoom(currentZoom - 0.1));
      document.getElementById('btnZoomReset').addEventListener('click', () => setZoom(1.0));
      document.getElementById('btnZoomFit').addEventListener('click', () => {
        setZoom((viewport.clientWidth - 70) / 794);
      });

      // مراقبة تعديل بيانات الشهادة بالاستوديو وإلغاء الاعتماد القديم مع المزامنة والحفظ التلقائي في المسودة
      const certPageElem = document.getElementById('certPage');
      if (certPageElem) {
        certPageElem.addEventListener('input', () => {
          if (isCertificateConfirmed) {
            resetConfirmationState();
          }
          syncDomToActiveParcel();
          scheduleDraftAutoSave();
        });

        certPageElem.addEventListener('focusout', () => {
          syncDomToActiveParcel();
          if (currentActiveDraftId) {
            if (draftAutoSaveTimer) {
              clearTimeout(draftAutoSaveTimer);
              draftAutoSaveTimer = null;
            }
            saveCurrentDraft(false);
          }
        });
      }

      // مراقبة تعديل مسؤولي الخطوة 1 للتزامن مع المسودة والاستوديو
      const selTechEl = document.getElementById('selSurveyTech');
      if (selTechEl) {
        selTechEl.addEventListener('change', () => {
          stage1IsModified = true;
          syncDomToActiveParcel();
          scheduleDraftAutoSave();
        });
      }
      const selOffEl = document.getElementById('selSysOfficer');
      if (selOffEl) {
        selOffEl.addEventListener('change', () => {
          stage1IsModified = true;
          syncDomToActiveParcel();
          scheduleDraftAutoSave();
        });
      }

      // مراقبة تعديل جدول الأضلاع والحدود في المرحلة 1 للتزامن اللحظي مع الاستوديو
      const s1SegsTable = document.getElementById('stage1SegmentsTbody');
      if (s1SegsTable) {
        s1SegsTable.addEventListener('input', () => {
          stage1IsModified = true;
          if (typeof syncStage1SegmentsToParcel === 'function') syncStage1SegmentsToParcel();
          scheduleDraftAutoSave();
        });
        s1SegsTable.addEventListener('change', () => {
          stage1IsModified = true;
          if (typeof syncStage1SegmentsToParcel === 'function') syncStage1SegmentsToParcel();
          scheduleDraftAutoSave();
        });
      }

      // التهيئة الابتدائية
      loadDefaultSettings();
      updateSpacing();
      renderWatermark();
      updateStep1State();
      initImageDragAndDrop();
      refreshDraftsBadge();


// Run initial bootstrap on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  loadOutputDir();
  checkServerHealth();

  // زر ريسيت وتفريغ مساحة العمل لبدء معاملة جديدة
  document.getElementById('btnNewSessionReset')?.addEventListener('click', () => {
    if (typeof window.resetFullWorkspace === 'function') {
      window.resetFullWorkspace(true);
    }
  });
});


// =========================================================================
// Dropdown & Popover UI Controllers
// =========================================================================
window.toggleDropdown = function(id, event) {
  if (event) {
    event.stopPropagation();
    event.preventDefault();
  }
  const target = document.getElementById(id);
  if (!target) return;
  const isAlreadyOpen = target.classList.contains('open');
  closeAllDropdowns();
  if (!isAlreadyOpen) {
    target.classList.add('open');
  }
};

window.closeAllDropdowns = function() {
  document.querySelectorAll('.hdr-dropdown.open, .croq-popover-container.open').forEach(function(el) {
    el.classList.remove('open');
  });
};

window.toggleCroqSettings = function(event) {
  if (event) {
    event.stopPropagation();
    event.preventDefault();
  }
  const container = document.getElementById('croqSettingsPopoverContainer');
  if (!container) return;
  const isAlreadyOpen = container.classList.contains('open');
  closeAllDropdowns();
  if (!isAlreadyOpen) {
    container.classList.add('open');
  }
};

// Global click outside listener
document.addEventListener('click', function(e) {
  // If clicked inside the croquis settings popover, do not close (user adjusting values)
  if (e.target.closest('#croqSettingsPopoverContainer')) {
    return;
  }
  // If clicked an item inside a dropdown menu, close menu smoothly after click
  if (e.target.closest('.hdr-dropdown-item')) {
    setTimeout(window.closeAllDropdowns, 80);
    return;
  }
  // If clicked outside any dropdown, close all
  if (!e.target.closest('.hdr-dropdown')) {
    window.closeAllDropdowns();
  }
});

// Close on Escape key
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    window.closeAllDropdowns();
  }
});


// =========================================================================
// Real-Time Active Session Synchronization to Backend Memory
// =========================================================================
var sessionSyncTimer = null;

window.syncSessionToBackend = function() {
  if (sessionSyncTimer) {
    clearTimeout(sessionSyncTimer);
    sessionSyncTimer = null;
  }
  if (!activeParcel || typeof window.collectFullSessionData !== 'function') return;

  if (typeof saveCurrentStudioTextState === 'function') {
    saveCurrentStudioTextState();
  }

  const sessionData = window.collectFullSessionData();
  fetch('/api/sync-session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_data: sessionData })
  }).catch(() => {});
};

window.scheduleSessionSync = function(delay = 500) {
  if (sessionSyncTimer) clearTimeout(sessionSyncTimer);
  sessionSyncTimer = setTimeout(window.syncSessionToBackend, delay);
};

// Monitor text edits in studio and sync in real time
document.addEventListener('DOMContentLoaded', () => {
  const cPage = document.getElementById('certPage');
  if (cPage) {
    cPage.addEventListener('input', () => {
      window.scheduleSessionSync(400);
    });
    cPage.addEventListener('focusout', () => {
      window.syncSessionToBackend();
    });
  }

  // Floating toolbar buttons
  ['fltFontInc', 'fltFontDec', 'fltBold', 'fltColorBlue', 'fltColorBlack', 'fltAlignRight', 'fltAlignCenter', 'fltAlignLeft', 'fltFontFamily'].forEach(btnId => {
    document.getElementById(btnId)?.addEventListener('click', () => {
      window.scheduleSessionSync(200);
    });
  });
});
