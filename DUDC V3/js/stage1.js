/**
 * DUDC V3.5 - Stage 1: Survey Ingestion & Coordinate Validation (stage1.js)
 */

      // ==========================================================================
      // محرك شاشة التحميل الذكية ومراقبة حالة الاتصال بالسيرفر
      // ==========================================================================
      const appLoadingOverlay = document.getElementById('appLoadingOverlay');
      const loadingActiveState = document.getElementById('loadingActiveState');
      const loadingErrorState = document.getElementById('loadingErrorState');
      const loadingMainTitle = document.getElementById('loadingMainTitle');
      const loadingSubDetail = document.getElementById('loadingSubDetail');
      const loadingProgressFill = document.getElementById('loadingProgressFill');
      const btnCloseLoading = document.getElementById('btnCloseLoading');
      const btnDismissLoading = document.getElementById('btnDismissLoading');
      const btnRetryLoading = document.getElementById('btnRetryLoading');
      const loadingServerBadge = document.getElementById('loadingServerBadge');
      const loadingServerBadgeText = document.getElementById('loadingServerBadgeText');
      const serverStatusPill = document.getElementById('serverStatusPill');
      const serverStatusText = document.getElementById('serverStatusText');

      let currentRetryAction = null;
      let loadingTimeout = null;

      function setServerStatus(online, latency = null) {
        if (online) {
          if (serverStatusPill) {
            serverStatusPill.className = 'connection-status-pill online';
            serverStatusText.textContent = latency ? `السيرفر متصل (${latency}ms)` : 'السيرفر متصل';
          }
          if (loadingServerBadge) {
            loadingServerBadge.className = 'server-badge';
            loadingServerBadgeText.textContent = 'متصل بالسيرفر المحلي (127.0.0.1:8765)';
          }
        } else {
          if (serverStatusPill) {
            serverStatusPill.className = 'connection-status-pill offline';
            serverStatusText.textContent = 'السيرفر غير متصل';
          }
          if (loadingServerBadge) {
            loadingServerBadge.className = 'server-badge offline';
            loadingServerBadgeText.textContent = '⚠️ السيرفر غير متصل (127.0.0.1:8765)';
          }
        }
      }

      function checkServerHealth() {
        const start = Date.now();
        fetch('/api/health')
          .then(res => res.json())
          .then(data => {
            const lat = Date.now() - start;
            setServerStatus(data.status === 'online', lat);
          })
          .catch(() => {
            setServerStatus(false);
          });
      }

      // فحص دوري لحالة الاتصال بالسيرفر كل 12 ثانية
      checkServerHealth();
      setInterval(checkServerHealth, 12000);
      if (serverStatusPill) {
        serverStatusPill.addEventListener('click', checkServerHealth);
      }

      function showLoading(title, detail, onRetry = null) {
        currentRetryAction = onRetry;
        loadingActiveState.style.display = 'block';
        loadingErrorState.style.display = 'none';
        btnCloseLoading.style.display = 'none';
        
        loadingMainTitle.textContent = title || 'جاري المعالجة...';
        loadingSubDetail.textContent = detail || 'يرجى الانتظار، يتم التواصل مع سيرفر المنظومة';
        
        setLoadingStep(1, 'active');
        setLoadingStep(2, 'pending');
        setLoadingStep(3, 'pending');
        setLoadingStep(4, 'pending');
        loadingProgressFill.style.width = '20%';

        appLoadingOverlay.style.display = 'flex';

        if (loadingTimeout) clearTimeout(loadingTimeout);
        loadingTimeout = setTimeout(() => {
          if (btnCloseLoading) btnCloseLoading.style.display = 'block';
        }, 6000);
      }

      function setLoadingStep(stepNum, status) {
        const el = document.getElementById(`lStep${stepNum}`);
        if (!el) return;
        el.className = `loading-step-item ${status}`;
        const icon = el.querySelector('.step-icon');
        if (status === 'done') {
          if (icon) icon.textContent = '✔';
          loadingProgressFill.style.width = `${stepNum * 25}%`;
        } else if (status === 'active') {
          if (icon) icon.textContent = '⏳';
        } else {
          if (icon) icon.textContent = '⚪';
        }
      }

      function hideLoading() {
        if (loadingTimeout) clearTimeout(loadingTimeout);
        loadingProgressFill.style.width = '100%';
        setTimeout(() => {
          appLoadingOverlay.style.display = 'none';
        }, 280);
      }

      function showLoadingError(errorTitle, errorMsg, onRetry = null) {
        if (loadingTimeout) clearTimeout(loadingTimeout);
        currentRetryAction = onRetry || currentRetryAction;
        loadingActiveState.style.display = 'none';
        loadingErrorState.style.display = 'block';
        btnCloseLoading.style.display = 'block';
        
        document.getElementById('loadingErrorTitle').textContent = errorTitle || 'حدث خطأ في الاتصال بالسيرفر';
        document.getElementById('loadingErrorMessage').textContent = errorMsg || 'تعذر التواصل مع السيرفر المحلي. يرجى التأكد من تشغيل Run_DUDC_V3.bat على المنفذ 8765';
        setServerStatus(false);
      }

      if (btnCloseLoading) btnCloseLoading.addEventListener('click', () => appLoadingOverlay.style.display = 'none');
      if (btnDismissLoading) btnDismissLoading.addEventListener('click', () => appLoadingOverlay.style.display = 'none');
      if (btnRetryLoading) {
        btnRetryLoading.addEventListener('click', () => {
          if (typeof currentRetryAction === 'function') {
            currentRetryAction();
          } else {
            appLoadingOverlay.style.display = 'none';
          }
        });
      }

      // تحميل عينة ف.xls مع شاشة التحميل الذكية
      function triggerLoadSample() {
        if (!isStep1Complete()) {
          highlightStep1Requirement();
          return;
        }
        const techVal = document.getElementById('selSurveyTech').value;
        const officerVal = document.getElementById('selSysOfficer').value;

        showLoading(
          'تحميل العينة التجريبية (ف.xls)',
          `فني المساحة: ${techVal} • مسؤول النظم: ${officerVal}`,
          triggerLoadSample
        );

        setLoadingStep(1, 'active');

        fetch('/api/load-sample', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ survey_technician: techVal, system_officer: officerVal })
        })
          .then(res => {
            if (!res.ok) throw new Error(`كود الاستجابة من السيرفر: ${res.status}`);
            return res.json();
          })
          .then(data => {
            if (data.success && data.parcels && data.parcels.length > 0) {
              setLoadingStep(1, 'done');
              setLoadingStep(2, 'active');
              if (data.official_centers) officialCentersList = data.official_centers;
              loadParcelData(data.parcels[0], () => {
                setLoadingStep(4, 'done');
                hideLoading();
              });
            } else {
              showLoadingError('فشل معالجة ملف العينة', data.error || 'تعذر استخراج بيانات المضلع من ف.xls', triggerLoadSample);
            }
          })
          .catch(err => {
            showLoadingError(
              'تعذر الاتصال بسيرفر المنظومة (127.0.0.1:8765)',
              `تفاصيل الخطأ: ${err.message}. تأكد من تشغيل ملف Run_DUDC_V3.bat لتشغيل السيرفر`,
              triggerLoadSample
            );
          });
      }

      document.getElementById('btnLoadSample').addEventListener('click', (e) => {
        e.stopPropagation();
        triggerLoadSample();
      });

      // السحب والإفلات المطور لملفات المساحة
      const dropzone = document.getElementById('dropzone');
      const surveyFileInput = document.getElementById('surveyFileInput');

      // حماية النافذة بالكامل من محاولة فتح الملف إذا أُفلت خارج الصندوق
      window.addEventListener('dragover', (e) => e.preventDefault(), false);
      window.addEventListener('drop', (e) => e.preventDefault(), false);

      let dropzoneDragCounter = 0;

      dropzone.addEventListener('click', (e) => {
        if (!isStep1Complete()) {
          highlightStep1Requirement();
          return;
        }
        if (e.target !== document.getElementById('btnLoadSample')) {
          surveyFileInput.click();
        }
      });

      dropzone.addEventListener('dragenter', (e) => {
        e.preventDefault();
        dropzoneDragCounter++;
        if (isStep1Complete()) {
          dropzone.classList.add('dragover');
        }
      });

      dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (isStep1Complete()) {
          dropzone.classList.add('dragover');
        }
      });

      dropzone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropzoneDragCounter--;
        if (dropzoneDragCounter <= 0) {
          dropzoneDragCounter = 0;
          dropzone.classList.remove('dragover');
        }
      });

      dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzoneDragCounter = 0;
        dropzone.classList.remove('dragover');
        if (!isStep1Complete()) {
          highlightStep1Requirement();
          alert('⚠️ يرجى أولاً اختيار فني المساحة ومسؤول النظم في الخطوة 1 لتفعيل الرفع والمعالجة.');
          return;
        }
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          uploadFile(e.dataTransfer.files[0]);
        }
      });

      surveyFileInput.addEventListener('change', (e) => {
        if (!isStep1Complete()) {
          highlightStep1Requirement();
          return;
        }
        if (e.target.files.length > 0) uploadFile(e.target.files[0]);
      });

      function uploadFile(file) {
        if (!isStep1Complete()) {
          highlightStep1Requirement();
          return;
        }
        const techVal = document.getElementById('selSurveyTech').value;
        const officerVal = document.getElementById('selSysOfficer').value;

        showLoading(
          `رفع ومعالجة شيت الإحداثيات (${file.name})`,
          `الحجم: ${(file.size / 1024).toFixed(1)} KB • المسؤول: ${officerVal}`,
          () => uploadFile(file)
        );

        setLoadingStep(1, 'active');
        const formData = new FormData();
        formData.append('file', file);
        formData.append('survey_technician', techVal);
        formData.append('system_officer', officerVal);

        fetch('/api/upload', { method: 'POST', body: formData })
          .then(res => {
            if (!res.ok) throw new Error(`كود الاستجابة من السيرفر: ${res.status}`);
            return res.json();
          })
          .then(data => {
            if (data.success && data.parcels && data.parcels.length > 0) {
              setLoadingStep(1, 'done');
              setLoadingStep(2, 'active');
              if (data.official_centers) officialCentersList = data.official_centers;
              loadParcelData(data.parcels[0], () => {
                setLoadingStep(4, 'done');
                hideLoading();
              });
            } else {
              showLoadingError('خطأ في معالجة ملف الإحداثيات', data.error || 'تأكد من صحة الملف وأعمدة الإحداثيات', () => uploadFile(file));
            }
          })
          .catch(err => {
            showLoadingError(
              'تعذر الاتصال بالسيرفر أثناء رفع الملف',
              `تفاصيل الخطأ: ${err.message}. يرجى التحقق من تشغيل السيرفر على 8765`,
              () => uploadFile(file)
            );
          });
      }

      // التحديث اللحظي لحالة الخطوة 1 عند تغيير الفني أو المسؤول
      ['selSurveyTech', 'selSysOfficer'].forEach(id => {
        document.getElementById(id).addEventListener('change', () => {
          updateStep1State();
          if (typeof isCertificateConfirmed !== 'undefined' && isCertificateConfirmed) {
            resetConfirmationState();
          }
        });
      });

      function renderDistrictSelector(parcel) {
        const sel = document.getElementById('selDistrict');
        const badge = document.getElementById('districtStatusBadge');
        const tokDisplay = document.getElementById('resSecurityToken');
        if (!sel) return;

        sel.innerHTML = '';
        const centers = (officialCentersList && officialCentersList.length > 0) ? officialCentersList : OFFICIAL_CENTERS_FALLBACK;

        if (parcel.district_matched && parcel.district_id !== null && parcel.district_id !== undefined) {
          // حالة التطابق التلقائي الناجح
          centers.forEach(([cid, name]) => {
            const opt = document.createElement('option');
            opt.value = cid;
            opt.textContent = name;
            if (cid === parcel.district_id) opt.selected = true;
            sel.appendChild(opt);
          });

          sel.className = 'district-select matched';
          if (badge) badge.innerHTML = '<span style="color: #34d399; font-weight: bold; font-size: 10px;">✔ تم تحديد المركز</span>';

          if (tokDisplay) {
            if (parcel.security_token) {
              tokDisplay.className = 'token-active';
              tokDisplay.textContent = parcel.security_token;
            } else {
              tokDisplay.className = 'token-trial';
              tokDisplay.innerHTML = '<span style="font-size: 10px; color: #94a3b8;">🏷️ كود تجريبي (معاينة):</span> <span style="font-family: monospace;">' + TRIAL_TOKEN + '</span>';
            }
          }
        } else {
          // حالة عدم التطابق - تنبيه أحمر وقائمة منسدلة
          const placeholder = document.createElement('option');
          placeholder.value = "";
          placeholder.disabled = true;
          placeholder.selected = true;
          const rawVal = parcel.district ? `"${parcel.district}"` : 'غير محدد';
          placeholder.textContent = `⚠️ غير مطابق (${rawVal}) - اختر المركز...`;
          sel.appendChild(placeholder);

          centers.forEach(([cid, name]) => {
            const opt = document.createElement('option');
            opt.value = cid;
            opt.textContent = name;
            sel.appendChild(opt);
          });

          sel.className = 'district-select unmatched';
          if (badge) badge.innerHTML = '<span style="color: #ef4444; font-weight: bold; font-size: 10px;">⚠️ يرجى الاختيار</span>';

          if (tokDisplay) {
            tokDisplay.className = 'token-locked';
            tokDisplay.innerHTML = '<span>⏳ بانتظار تحديد المركز</span>';
          }
        }
      }

      function handleDistrictChange(newCid) {
        if (!activeParcel || newCid === "" || newCid === null || newCid === undefined) return;

        const sel = document.getElementById('selDistrict');
        const badge = document.getElementById('districtStatusBadge');
        const tokDisplay = document.getElementById('resSecurityToken');

        if (badge) badge.innerHTML = '<span style="color: var(--accent-cyan); font-size: 10px;">⏳ حفظ المركز...</span>';

        const techVal = document.getElementById('selSurveyTech') ? document.getElementById('selSurveyTech').value : '';
        const officerVal = document.getElementById('selSysOfficer') ? document.getElementById('selSysOfficer').value : '';

        fetch('/api/update-center', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            parcel_index: 0,
            center_id: parseInt(newCid),
            survey_technician: techVal,
            system_officer: officerVal
          })
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            activeParcel.district = data.district;
            activeParcel.district_id = data.district_id;
            activeParcel.district_matched = true;
            activeParcel.security_token = null; // Stays null until Stage 3 confirmation

            if (sel) sel.className = 'district-select matched';
            if (badge) badge.innerHTML = '<span style="color: #34d399; font-weight: bold; font-size: 10px;">✔ تم تحديد المركز</span>';

            if (tokDisplay) {
              tokDisplay.className = 'token-trial';
              tokDisplay.innerHTML = '<span style="font-size: 10px; color: #94a3b8;">🏷️ كود تجريبي (معاينة):</span> <span style="font-family: monospace;">' + TRIAL_TOKEN + '</span>';
            }

            resetConfirmationState();
            renderWatermark();

            // مزامنة الاستوديو في المرحلة 2
            const valCenterElem = document.getElementById('valCenter');
            if (valCenterElem) valCenterElem.textContent = data.district;

            // تحديث كروكي المرحلة 1
            if (data.croquis_url) {
              const croqImg = document.getElementById('stage1CroquisImg');
              const imgCroqStage2 = document.getElementById('imgCroquis');
              if (croqImg) croqImg.src = data.croquis_url;
              if (imgCroqStage2) imgCroqStage2.src = data.croquis_url;
            }

            if (typeof scheduleDraftAutoSave === 'function') {
              scheduleDraftAutoSave();
            }
          } else {
            alert('خطأ في حفظ المركز: ' + (data.error || 'غير معروف'));
          }
        })
        .catch(err => {
          alert('خطأ في الاتصال بالسيرفر: ' + err.message);
        });
      }

      function loadParcelData(parcel, onComplete = null) {
        activeParcel = parcel;
        if (typeof resetConfirmationState === 'function') resetConfirmationState();
        // إظهار باقي عناصر الصفحة (الخطوة 3) بسلاسة بعد نجاح المعالجة
        const resultsSec = document.getElementById('surveyResultsSection');
        if (resultsSec) {
          resultsSec.style.display = 'flex';
          resultsSec.style.flexDirection = 'column';
          setTimeout(() => {
            resultsSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }, 120);
        }

        // بيانات المواطن والتحقق
        document.getElementById('resApplicantName').textContent = parcel.applicant_name || 'لا يوجد بيانات متاحة';
        const st1Nid = (parcel.national_id && String(parcel.national_id).trim() !== '0') ? String(parcel.national_id).trim() : '';
        document.getElementById('resNationalId').textContent = st1Nid || 'لا يوجد بيانات متاحة';
        const st1Rcp = (parcel.receipt_no && String(parcel.receipt_no).trim() !== '0') ? String(parcel.receipt_no).trim() : '';
        document.getElementById('resReceiptNo').textContent = st1Rcp || 'لا يوجد بيانات متاحة';

        // تهيئة قائمة المراكز وتأمين الرمز الأمني
        renderDistrictSelector(parcel);
        renderWatermark();

        const statedArea = parseFloat(parcel.stated_area_m2) || 0;
        const calcArea = parseFloat(parcel.calculated_area_m2) || 0;
        const delta = Math.abs(calcArea - statedArea);

        document.getElementById('resStatedArea').textContent = `${statedArea.toFixed(2)} م²`;
        document.getElementById('resCalcArea').textContent = `${calcArea.toFixed(2)} م²`;
        document.getElementById('resDeltaArea').textContent = `${delta.toFixed(2)} م²`;

        const badge = document.getElementById('badgeTolerance');
        if (delta <= 2.0) {
          badge.className = 'badge-pass';
          badge.textContent = `✔ متطابق قانونياً (فرق المساحة ${delta.toFixed(2)} م² ضمن المسموح ±2.0 م²)`;
        } else {
          badge.className = 'badge-fail';
          badge.textContent = `⚠️ تنبيه: فرق المساحة ${delta.toFixed(2)} م² يتجاوز التفاوت القانوني (±2.0 م²)`;
        }

        // تهيئة مقاسات خطوط الكروكي
        croqFontSizes.pts = parcel.font_size_pts ? Number(parcel.font_size_pts) : 16;
        croqFontSizes.dim = parcel.font_size_dims ? Number(parcel.font_size_dims) : 16;
        croqFontSizes.text = parcel.font_size_text ? Number(parcel.font_size_text) : 16;
        const elPts = document.getElementById('croqFontPtsVal');
        const elText = document.getElementById('croqFontTextVal');
        const elDim = document.getElementById('croqFontDimVal');
        if (elPts) elPts.textContent = croqFontSizes.pts;
        if (elText) elText.textContent = croqFontSizes.text;
        if (elDim) elDim.textContent = croqFontSizes.dim;

        // بناء جدول الأضلاع
        buildSegmentsTable(parcel.segments || []);

        setLoadingStep(2, 'done');
        setLoadingStep(3, 'active');
        setLoadingStep(4, 'active');

        // تحميل الصورتين بالتوازي ومتابعة حالة التحميل اللحظية لكل صورة فور اكتمالها
        const pCroq = loadCroquisPreview()
          .then(res => {
            setLoadingStep(3, 'done');
            return res;
          })
          .catch(e => console.warn('Croquis preview warning:', e));

        const pSat = loadSatellitePreview()
          .then(res => {
            setLoadingStep(4, 'done');
            return res;
          })
          .catch(e => console.warn('Satellite preview warning:', e));

        Promise.all([pCroq, pSat]).then(() => {
          if (typeof onComplete === 'function') {
            onComplete();
          } else {
            hideLoading();
          }
        }).catch(() => {
          hideLoading();
        });
      }

      function loadCroquisPreview() {
        return fetch('/api/preview-croquis', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            parcel_index: 0,
            font_size_pts: croqFontSizes.pts,
            font_size_dims: croqFontSizes.dim,
            font_size_text: croqFontSizes.text
          })
        }).then(res => res.json()).then(data => {
          if (data.croquis_url) {
            const bustUrl = data.croquis_url + (data.croquis_url.includes('?') ? '&_t=' : '?_t=') + Date.now();
            document.getElementById('stage1CroquisImg').src = bustUrl;
            document.getElementById('imgCroquis').src = bustUrl;
          }
          return data;
        });
      }

      function loadSatellitePreview() {
        return fetch('/api/preview-satellite', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ parcel_index: 0 })
        }).then(res => res.json()).then(data => {
          if (data.image_url) {
            document.getElementById('stage1SatImg').src = data.image_url;
            document.getElementById('imgSatellite').src = data.image_url;
          }
          return data;
        });
      }

      function buildSegmentsTable(segments) {
        currentSegments = JSON.parse(JSON.stringify(segments));
        const tbody = document.getElementById('stage1SegmentsTbody');
        tbody.innerHTML = '';

        segments.forEach((seg, i) => {
          const tr = document.createElement('tr');
          const pFrom = seg.from_point !== undefined ? seg.from_point : (seg.from_pt !== undefined ? seg.from_pt : (i + 1));
          const pTo = seg.to_point !== undefined ? seg.to_point : (seg.to_pt !== undefined ? seg.to_pt : ((i + 1) % segments.length + 1));
          tr.innerHTML = `
            <td><strong style="color: var(--accent-green-light); font-size: 13px;">P${pFrom} - P${pTo}</strong></td>
            <td>
              <select class="stage1-select seg-dir-select" data-index="${i}">
                <option value="north" ${seg.direction === 'north' ? 'selected' : ''}>🌊 الحد البحري</option>
                <option value="east" ${seg.direction === 'east' ? 'selected' : ''}>🌅 الحد الشرقي</option>
                <option value="south" ${seg.direction === 'south' ? 'selected' : ''}>☀️ الحد القبلي</option>
                <option value="west" ${seg.direction === 'west' ? 'selected' : ''}>🌇 الحد الغربي</option>
              </select>
            </td>
            <td>
              <input type="text" class="stage1-input seg-neighbor-input" data-index="${i}" placeholder="اسم الجار أو الشارع..." value="${seg.neighbor || ''}">
            </td>
            <td><strong>${(parseFloat(seg.length_m) || 0).toFixed(2)} م</strong></td>
            <td>
              <input type="number" step="0.01" class="stage1-input seg-length-input" data-index="${i}" value="${(parseFloat(seg.length_m) || 0).toFixed(2)}">
            </td>
          `;
          tbody.appendChild(tr);
        });

        // ربط أحداث التغيير لإعادة حساب المجموع وتنبيه الحاجة للتحديث
        tbody.querySelectorAll('.seg-dir-select, .seg-length-input, .seg-neighbor-input').forEach(el => {
          el.addEventListener('input', () => {
            updateRunningSums();
            markCroquisNeedsUpdate();
          });
        });

        updateRunningSums();
      }

      // ضبط أحجام خطوط الكروكي (يدوي بالكامل - لا يتم التحديث إلا بضغط زر التحديث)
      let croqFontSizes = { pts: 16, text: 16, dim: 16 };

      function adjustCroqFont(type, delta) {
        if (!croqFontSizes.hasOwnProperty(type)) return;
        const limits = {
          pts: { min: 7, max: 26, id: 'croqFontPtsVal' },
          text: { min: 8, max: 28, id: 'croqFontTextVal' },
          dim: { min: 8, max: 26, id: 'croqFontDimVal' }
        };
        const cfg = limits[type];
        if (!cfg) return;
        croqFontSizes[type] = Math.max(cfg.min, Math.min(cfg.max, croqFontSizes[type] + delta));
        const valElem = document.getElementById(cfg.id);
        if (valElem) valElem.textContent = croqFontSizes[type];
        
        // تنبيه بصري بأن هناك تعديلات تنتظر ضغط زر التحديث
        markCroquisNeedsUpdate();
      }

      function markCroquisNeedsUpdate() {
        const btn = document.getElementById('btnUpdateCroquis');
        if (btn && !btn.disabled) {
          btn.style.boxShadow = '0 0 14px rgba(16, 185, 129, 0.75)';
          btn.style.borderColor = 'var(--accent-green-light)';
        }
      }

      // نسخ كود التأمين للحافظة
      function copySecurityToken() {
        if (!activeParcel || !activeParcel.security_token) {
          alert('⚠️ يرجى تأمين واختيار المركز لتوليد الكود قبل نسخه.');
          return;
        }
        const token = activeParcel.security_token;
        const btn = document.getElementById('btnCopyToken');

        function showSuccess() {
          if (btn) {
            const orig = btn.innerHTML;
            btn.className = 'btn-copy-token copied';
            btn.innerHTML = '✔ تم النسخ!';
            setTimeout(() => {
              btn.className = 'btn-copy-token';
              btn.innerHTML = orig;
            }, 1800);
          }
        }

        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(token).then(showSuccess).catch(() => {
            fallbackCopy(token);
            showSuccess();
          });
        } else {
          fallbackCopy(token);
          showSuccess();
        }
      }

      function fallbackCopy(text) {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); } catch(e){}
        document.body.removeChild(ta);
      }

      // تحديث رسم الكروكي الهندسي بالكامل (يتم فقط عند الضغط على زر التحديث)
      function updateCroquisDiagram() {
        if (!activeParcel) {
          alert('يرجى تحميل ملف الرفع المساحي أولاً لمعاينة وتحديث الكروكي.');
          return;
        }

        const btn = document.getElementById('btnUpdateCroquis');
        const quickBtn = document.getElementById('btnQuickRefreshCroquis');
        const defaultBtnHtml = '<span>🔄 تحديث رسم الكروكي</span>';
        
        if (btn) {
          btn.style.boxShadow = '';
          btn.style.borderColor = '';
          btn.innerHTML = '<span>⏳ جاري الرسم...</span>';
          btn.disabled = true;
        }
        if (quickBtn) {
          quickBtn.textContent = '⏳ جاري...';
          quickBtn.disabled = true;
        }

        // قراءة وتجميع بيانات الأضلاع المعدلة
        const editedSegs = [];
        const boundaries = { north: '', east: '', south: '', west: '' };

        document.querySelectorAll('#stage1SegmentsTbody tr').forEach((tr, i) => {
          const dirSel = tr.querySelector('.seg-dir-select');
          const lenInp = tr.querySelector('.seg-length-input');
          const neighInp = tr.querySelector('.seg-neighbor-input');

          const dir = dirSel ? dirSel.value : 'north';
          const len = lenInp ? (parseFloat(lenInp.value) || 0) : 0;
          const neigh = neighInp ? neighInp.value.trim() : '';

          editedSegs.push({
            direction: dir,
            length_m: len,
            neighbor: neigh
          });

          // ربط اسم الجار بالحد العام
          if (neigh && (!boundaries[dir] || boundaries[dir] === '')) {
            boundaries[dir] = neigh;
          }
        });

        // تحديث كائن الـ activeParcel
        if (activeParcel.segments) {
          editedSegs.forEach((es, i) => {
            if (activeParcel.segments[i]) {
              activeParcel.segments[i].direction = es.direction;
              activeParcel.segments[i].length_m = es.length_m;
              activeParcel.segments[i].neighbor = es.neighbor;
            }
          });
        }
        activeParcel.boundaries = boundaries;
        activeParcel.font_size_pts = croqFontSizes.pts;
        activeParcel.font_size_dims = croqFontSizes.dim;
        activeParcel.font_size_text = croqFontSizes.text;

        fetch('/api/preview-croquis', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            parcel_index: 0,
            boundaries: boundaries,
            edited_segments: editedSegs,
            font_size_pts: croqFontSizes.pts,
            font_size_dims: croqFontSizes.dim,
            font_size_text: croqFontSizes.text
          })
        })
        .then(res => res.json())
        .then(data => {
          if (data.croquis_url) {
            const croq1 = document.getElementById('stage1CroquisImg');
            const croq2 = document.getElementById('imgCroquis');
            const bustUrl = data.croquis_url + (data.croquis_url.includes('?') ? '&_t=' : '?_t=') + Date.now();
            if (croq1) croq1.src = bustUrl;
            if (croq2) croq2.src = bustUrl;
          }
          if (btn) {
            btn.innerHTML = '<span>✔ تم تحديث الكروكي</span>';
            setTimeout(() => {
              btn.innerHTML = defaultBtnHtml;
              btn.disabled = false;
            }, 1200);
          }
          if (quickBtn) {
            quickBtn.textContent = '✔ تم';
            setTimeout(() => {
              quickBtn.textContent = '🔄 تحديث';
              quickBtn.disabled = false;
            }, 1200);
          }
          updateRunningSums();
        })
        .catch(err => {
          alert('خطأ في تحديث الكروكي: ' + err.message);
          if (btn) {
            btn.innerHTML = defaultBtnHtml;
            btn.disabled = false;
          }
          if (quickBtn) {
            quickBtn.textContent = '🔄 تحديث';
            quickBtn.disabled = false;
          }
        });
      }

      const customUploadedImages = { croquis: null, satellite: null };

      function triggerImageUpload(targetType) {
        if (targetType === 'croquis') {
          const inp = document.getElementById('inputUploadCroquis');
          if (inp) inp.click();
        } else if (targetType === 'satellite') {
          const inp = document.getElementById('inputUploadSatellite');
          if (inp) inp.click();
        }
      }

      function applyUploadedImageData(targetType, dataUrl) {
        customUploadedImages[targetType] = dataUrl;
        if (targetType === 'croquis') {
          const img1 = document.getElementById('stage1CroquisImg');
          const img2 = document.getElementById('imgCroquis');
          if (img1) img1.src = dataUrl;
          if (img2) img2.src = dataUrl;
          if (activeParcel) {
            activeParcel.croquis_base64 = dataUrl;
            activeParcel.has_custom_croquis = true;
          }
        } else if (targetType === 'satellite') {
          const img1 = document.getElementById('stage1SatImg');
          const img2 = document.getElementById('imgSatellite');
          if (img1) img1.src = dataUrl;
          if (img2) img2.src = dataUrl;
          if (activeParcel) {
            activeParcel.satellite_base64 = dataUrl;
            activeParcel.has_custom_sat = true;
          }
        }

        // مزامنة الصورة المرفوعة مع السيرفر في الخلفية
        fetch('/api/upload-parcel-image', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: targetType,
            image_base64: dataUrl,
            parcel_index: 0
          })
        }).catch(() => {});

        const label = targetType === 'croquis' ? 'الكروكي (CAD Croquis)' : 'الصورة الفضائية (Satellite)';
        showSaveToast(`✔ تم رفع وتعيين صورة ${label} بنجاح من جهازك`);
      }

      function handleImageFileSelected(input, targetType) {
        const file = input.files && input.files[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
          alert('يرجى اختيار ملف صورة صالح (PNG, JPG, JPEG, WebP)');
          input.value = '';
          return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
          applyUploadedImageData(targetType, e.target.result);
        };
        reader.readAsDataURL(file);
        input.value = '';
      }

      function initImageDragAndDrop() {
        const setupDrop = (elemId, targetType) => {
          const el = document.getElementById(elemId);
          if (!el) return;

          ['dragenter', 'dragover'].forEach(evt => {
            el.addEventListener(evt, e => {
              e.preventDefault();
              e.stopPropagation();
              el.classList.add('drag-over');
            });
          });

          ['dragleave', 'drop'].forEach(evt => {
            el.addEventListener(evt, e => {
              e.preventDefault();
              e.stopPropagation();
              el.classList.remove('drag-over');
            });
          });

          el.addEventListener('drop', e => {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files[0]) {
              const file = dt.files[0];
              if (!file.type.startsWith('image/')) {
                alert('يرجى سحب وإفلات ملف صورة صالح (PNG, JPG, WebP)');
                return;
              }
              const reader = new FileReader();
              reader.onload = ev => applyUploadedImageData(targetType, ev.target.result);
              reader.readAsDataURL(file);
            }
          });
        };

        setupDrop('dropZoneCroquis', 'croquis');
        setupDrop('dropZoneSat', 'satellite');
      }

      function showSaveToast(text) {
        const saveToast = document.getElementById('saveToast');
        const msgSpan = document.getElementById('saveToastMsg');
        if (msgSpan) msgSpan.textContent = text;
        if (saveToast) {
          saveToast.classList.add('show');
          setTimeout(() => saveToast.classList.remove('show'), 3200);
        }
      }

      // إتاحة الدوال على كائن window للتفاعل الفوري مع أحداث HTML المباشرة (onclick, onchange)
      window.adjustCroqFont = adjustCroqFont;
      window.updateCroquisDiagram = updateCroquisDiagram;
      window.copySecurityToken = copySecurityToken;
      window.handleDistrictChange = handleDistrictChange;
      window.triggerImageUpload = triggerImageUpload;
      window.handleImageFileSelected = handleImageFileSelected;

      function updateRunningSums() {
        let sums = { north: 0, east: 0, south: 0, west: 0 };
        let perimeter = 0;

        document.querySelectorAll('#stage1SegmentsTbody tr').forEach(tr => {
          const dir = tr.querySelector('.seg-dir-select').value;
          const len = parseFloat(tr.querySelector('.seg-length-input').value) || 0;
          if (sums[dir] !== undefined) sums[dir] += len;
          perimeter += len;
        });

        document.getElementById('sumNorth').textContent = `${sums.north.toFixed(2)} م`;
        document.getElementById('sumEast').textContent = `${sums.east.toFixed(2)} م`;
        document.getElementById('sumSouth').textContent = `${sums.south.toFixed(2)} م`;
        document.getElementById('sumWest').textContent = `${sums.west.toFixed(2)} م`;
        document.getElementById('sumPerimeter').textContent = `${perimeter.toFixed(2)} م`;
      }

