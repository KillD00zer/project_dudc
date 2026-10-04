/**
 * DUDC V3.5 - Application Bootstrap & Event Wiring (app.js)
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

      // مراقبة تعديل مسؤولي الخطوة 1 للتزامن مع المسودة
      const selTechEl = document.getElementById('selSurveyTech');
      if (selTechEl) {
        selTechEl.addEventListener('change', () => {
          syncDomToActiveParcel();
          scheduleDraftAutoSave();
        });
      }
      const selOffEl = document.getElementById('selSysOfficer');
      if (selOffEl) {
        selOffEl.addEventListener('change', () => {
          syncDomToActiveParcel();
          scheduleDraftAutoSave();
        });
      }

      // مراقبة تعديل جدول الأضلاع والحدود في المرحلة 1
      const s1SegsTable = document.getElementById('stage1SegmentsTbody');
      if (s1SegsTable) {
        s1SegsTable.addEventListener('input', () => {
          scheduleDraftAutoSave();
        });
        s1SegsTable.addEventListener('change', () => {
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
});
