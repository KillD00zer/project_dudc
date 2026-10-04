/**
 * DUDC V3.5 - Global State & Workflow Navigation (state.js)
 */

if (window.location.hostname === 'localhost') {
  window.location.replace(window.location.href.replace('localhost', '127.0.0.1'));
}

      // كود الأمان التجريبي للمعاينة وضبط الإخراج الطباعي في الاستوديو
      var TRIAL_TOKEN = 'DUDC-TRIAL-SAMPLE-PREVIEW-000000-000000';

      // متغيرات الحالة العالمية (Global Workflow State)
      var currentStage = 1;
      var activeParcel = null;
      var currentSegments = [];
      var outputDir = '';
      var isBrowsingFolder = false;
      var savedTextDefaults = null;
      var hasSavedCurrentPackage = false; // يمنع الطباعة تماماً قبل إتمام حفظ وتصدير حزمة المشروع رسمياً

      // قائمة المراكز الرسمية الـ 18 لمحافظة الدقهلية
      const OFFICIAL_CENTERS_FALLBACK = [
        [0, "المنصورة"], [1, "طلخا"], [2, "ميت غمر"], [3, "دكرنس"],
        [4, "السنبلاوين"], [5, "بلقاس"], [6, "شربين"], [7, "المنزلة"],
        [8, "منية النصر"], [9, "أجا"], [10, "نبروه"], [11, "تمي الأمديد"],
        [12, "الجمالية"], [13, "الكردي"], [14, "المطرية"], [15, "ميت سلسيل"],
        [16, "بني عبيد"], [17, "جمصة"]
      ];
      var officialCentersList = OFFICIAL_CENTERS_FALLBACK;

      // عناصر مسار العمل
      const stepTab1 = document.getElementById('stepTab1');
      const stepTab2 = document.getElementById('stepTab2');
      const stepTab3 = document.getElementById('stepTab3');
      const stage1View = document.getElementById('stage1View');
      const stage2View = document.getElementById('stage2View');
      const stage3View = document.getElementById('stage3View');

      function switchStage(stageNum) {
        currentStage = stageNum;
        [stage1View, stage2View, stage3View].forEach((el, i) => {
          el.classList.toggle('active', i + 1 === stageNum);
        });
        [stepTab1, stepTab2, stepTab3].forEach((el, i) => {
          el.classList.toggle('active', i + 1 === stageNum);
          el.classList.toggle('completed', i + 1 < stageNum);
        });

        if (stageNum === 2) {
          syncStage1ToStage2();
          updateSpacing();
          renderWatermark();
        } else if (stageNum === 3) {
          syncDomToActiveParcel();
          syncStage2ToStage3();
        }
      }

      stepTab1.addEventListener('click', () => switchStage(1));
      stepTab2.addEventListener('click', () => {
        if (!activeParcel) return;
        if (!activeParcel.district_matched) {
          alert('⚠️ تنبيه: يرجى اختيار وتحديد المركز أولاً من القائمة قبل الانتقال للاستوديو.');
          const sel = document.getElementById('selDistrict');
          if (sel) { sel.scrollIntoView({ behavior: 'smooth', block: 'center' }); sel.focus(); }
          return;
        }
        switchStage(2);
      });
      stepTab3.addEventListener('click', () => {
        if (!activeParcel) return;
        if (!activeParcel.district_matched) {
          alert('⚠️ تنبيه: يرجى تحديد المركز أولاً من القائمة.');
          return;
        }
        switchStage(3);
      });

      document.getElementById('btnGoToStage2').addEventListener('click', () => {
        if (!activeParcel) return;
        if (!activeParcel.district_matched) {
          alert('⚠️ تنبيه: لا يمكن الانتقال للاستوديو حتى يتم اختيار وتحديد خانة المركز من القائمة!');
          const sel = document.getElementById('selDistrict');
          if (sel) { sel.scrollIntoView({ behavior: 'smooth', block: 'center' }); sel.focus(); }
          return;
        }
        switchStage(2);
      });
      document.getElementById('btnBackToStage1').addEventListener('click', () => switchStage(1));
      document.getElementById('btnGoToStage3').addEventListener('click', () => switchStage(3));
      document.getElementById('btnBackToStage2').addEventListener('click', () => switchStage(2));

      /* ==========================================================================
         المرحلة 1: استدعاء الـ APIs وإدارة مجلد الحفظ (المطابق للمشروع القديم تماماً)
         ========================================================================== */
      window.browseOutputDir = async function() {
        if (isBrowsingFolder) return;
        isBrowsingFolder = true;
        const btn = document.querySelector('button[onclick="browseOutputDir()"]');
        if (btn) btn.disabled = true;
        const statusEl = document.getElementById('outputDirStatus');
        const dirInput = document.getElementById('outputDirInput');
        const curDir = dirInput ? dirInput.value.trim() : '';
        if (statusEl) statusEl.textContent = '⏳ جاري فتح نافذة اختيار المجلد...';

        try {
          const res = await fetch('/api/browse-output-dir', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ initial_dir: curDir })
          });
          const data = await res.json();
          if (data.folder_path) {
            if (dirInput) dirInput.value = data.folder_path;
            outputDir = data.folder_path;
            if (statusEl) {
              statusEl.textContent = '✔ تم تحديد وتحديث مجلد الحفظ بنجاح';
              setTimeout(() => { if (statusEl) statusEl.textContent = ''; }, 4000);
            }
          } else {
            if (statusEl) statusEl.textContent = '';
          }
        } catch (err) {
          alert('تعذر فتح نافذة اختيار المجلد: ' + err.message);
          if (statusEl) statusEl.textContent = '';
        } finally {
          isBrowsingFolder = false;
          if (btn) btn.disabled = false;
        }
      };

      window.saveOutputDir = async function(customDir) {
        const dirInput = document.getElementById('outputDirInput');
        const statusEl = document.getElementById('outputDirStatus');
        const newDir = customDir || (dirInput ? dirInput.value.trim() : '');
        if (!newDir) { alert('الرجاء إدخال مسار المجلد.'); return; }
        try {
          const res = await fetch('/api/set-output-dir', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ output_dir: newDir })
          });
          const data = await res.json();
          if (data.error) throw new Error(data.error);
          outputDir = newDir;
          if (dirInput) dirInput.value = newDir;
          if (statusEl) {
            statusEl.textContent = '✔ تم الحفظ بنجاح';
            setTimeout(() => { if (statusEl) statusEl.textContent = ''; }, 3000);
          }
        } catch (err) {
          alert('فشل حفظ المجلد: ' + err.message);
        }
      };

      window.openOutputFolder = async function() {
        try {
          await fetch('/api/open-folder', { method: 'POST' });
        } catch (err) {
          alert('تعذر فتح المجلد تلقائياً: ' + err.message);
        }
      };

      async function loadOutputDir() {
        try {
          const res = await fetch('/api/get-output-dir');
          const data = await res.json();
          outputDir = data.output_dir || '';
          const inp = document.getElementById('outputDirInput');
          if (inp) inp.value = outputDir;
        } catch (err) {
          console.error('Could not load output dir:', err);
        }
      }
      loadOutputDir();

      // ==========================================================================
