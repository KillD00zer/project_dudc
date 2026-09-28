
    document.addEventListener('DOMContentLoaded', () => {
      // متغيرات الحالة العالمية (Global Workflow State)
      let currentStage = 1;
      let activeParcel = null;
      let currentSegments = [];
      let outputDir = '';

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
          syncStage2ToStage3();
        }
      }

      stepTab1.addEventListener('click', () => switchStage(1));
      stepTab2.addEventListener('click', () => {
        if (!activeParcel) return;
        if (!activeParcel.district_matched || !activeParcel.security_token) {
          alert('⚠️ تنبيه أمني: يرجى تحديد وتأمين المركز أولاً من القائمة لتوليد كود التأمين الرقابي قبل الانتقال للاستوديو.');
          const sel = document.getElementById('selDistrict');
          if (sel) { sel.scrollIntoView({ behavior: 'smooth', block: 'center' }); sel.focus(); }
          return;
        }
        switchStage(2);
      });
      stepTab3.addEventListener('click', () => {
        if (!activeParcel) return;
        if (!activeParcel.district_matched || !activeParcel.security_token) {
          alert('⚠️ تنبيه أمني: يرجى تأمين المركز وكود الأمان أولاً.');
          return;
        }
        switchStage(3);
      });

      document.getElementById('btnGoToStage2').addEventListener('click', () => {
        if (!activeParcel) return;
        if (!activeParcel.district_matched || !activeParcel.security_token) {
          alert('⚠️ تنبيه أمني: لا يمكن الانتقال للاستوديو أو اعتماد الشهادة حتى يتم تأمين وتحديد خانة المركز من القائمة لتوليد كود التأمين الرقابي!');
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
         المرحلة 1: استدعاء الـ APIs ورفع الملفات
         ========================================================================== */
      function fetchOutputDir() {
        fetch('/api/get-output-dir')
          .then(res => res.json())
          .then(data => {
            outputDir = data.output_dir || '';
            document.getElementById('txtOutputDirDisplay').textContent = outputDir;
          }).catch(() => {});
      }
      fetchOutputDir();

      function openFolderInExplorer(targetPath) {
        fetch('/api/open-folder', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ folder_path: targetPath || outputDir })
        }).catch(err => alert('خطأ في فتح المجلد: ' + err.message));
      }

      const btnOpenDirDirect = document.getElementById('btnOpenOutputDirDirect');
      if (btnOpenDirDirect) {
        btnOpenDirDirect.addEventListener('click', () => openFolderInExplorer(outputDir));
      }

      const txtDirDisplay = document.getElementById('txtOutputDirDisplay');
      if (txtDirDisplay) {
        txtDirDisplay.addEventListener('click', () => openFolderInExplorer(outputDir));
      }

      const btnBrowseOutputDir = document.getElementById('btnBrowseOutputDir');
      if (btnBrowseOutputDir) {
        btnBrowseOutputDir.addEventListener('click', () => {
          const origHtml = btnBrowseOutputDir.innerHTML;
          btnBrowseOutputDir.innerHTML = '⏳ جاري فتح الاختيار...';
          btnBrowseOutputDir.disabled = true;

          fetch('/api/browse-output-dir', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ initial_dir: outputDir })
          })
            .then(res => res.json())
            .then(data => {
              btnBrowseOutputDir.innerHTML = origHtml;
              btnBrowseOutputDir.disabled = false;
              if (data.output_dir) {
                outputDir = data.output_dir;
                document.getElementById('txtOutputDirDisplay').textContent = outputDir;
              }
            })
            .catch(err => {
              btnBrowseOutputDir.innerHTML = origHtml;
              btnBrowseOutputDir.disabled = false;
              alert('خطأ في استعراض المجلد: ' + err.message);
            });
        });
      }

      // ==========================================================================
      // استيراد جلسة عمل سابقة (*_session.json)
      // ==========================================================================
      const btnImportJson = document.getElementById('btnImportJson');
      const fileJsonInput = document.getElementById('fileJsonInput');

      if (btnImportJson && fileJsonInput) {
        btnImportJson.addEventListener('click', () => {
          fileJsonInput.value = '';
          fileJsonInput.click();
        });

        fileJsonInput.addEventListener('change', (e) => {
          const file = e.target.files && e.target.files[0];
          if (!file) return;

          const reader = new FileReader();
          reader.onload = (ev) => {
            try {
              const session = JSON.parse(ev.target.result);
              applyImportedSession(session, file.name);
            } catch (err) {
              alert('⚠️ خطأ في قراءة ملف الجلسة: ' + err.message);
            }
          };
          reader.readAsText(file, 'utf-8');
        });
      }

      function applyImportedSession(rawSession, fileName) {
        if (!rawSession || typeof rawSession !== 'object') {
          alert('⚠️ ملف الجلسة غير صالح أو تالف.');
          return;
        }

        // دمج session_data إن كانت الجلسة مصدرة من حزمة التصدير
        const s = rawSession.session_data ? Object.assign({}, rawSession, rawSession.session_data) : rawSession;

        const applicantName = s.applicant_name || s.name || '';
        const receiptNo = s.receipt_no || '';
        const nationalId = s.national_id || '';
        const district = s.district || s.center || '';
        const village = s.village || '';
        const address = s.address || '';
        const area = s.area || s.stated_area_m2 || '';
        const dealType = s.deal_type || s.transaction_type || '';
        const siteDesc = s.site_desc || s.site_status || '';
        const orderNo = s.order_no || s.request_no || '';
        const secToken = s.security_token || s.token || '';

        // 1. ملء بيانات المواطن
        if (applicantName) {
          document.getElementById('valApplicantName').textContent = applicantName;
          const resApp = document.getElementById('resApplicantName');
          if (resApp) resApp.textContent = applicantName;
          const st3Name = document.getElementById('stage3CitizenName');
          if (st3Name) st3Name.textContent = applicantName;
        }
        if (receiptNo) {
          document.getElementById('valReceiptNo').textContent = toArabicNumerals(receiptNo);
          const resRec = document.getElementById('resReceiptNo');
          if (resRec) resRec.textContent = receiptNo;
        }
        if (nationalId) {
          document.getElementById('valNationalId').textContent = toArabicNumerals(nationalId);
          const resNat = document.getElementById('resNationalId');
          if (resNat) resNat.textContent = nationalId;
        }
        if (district) {
          document.getElementById('valCenter').textContent = district;
          const st3Center = document.getElementById('stage3Center');
          if (st3Center) st3Center.textContent = district;
        }
        if (village) document.getElementById('valVillage').textContent = village;
        if (address) document.getElementById('valAddress').textContent = address;
        if (area) {
          const areaStr = String(area);
          document.getElementById('valArea').textContent = areaStr.includes('م') ? areaStr : `${toArabicNumerals(areaStr)} م²`;
          const resArea = document.getElementById('resCalcArea');
          if (resArea) resArea.textContent = areaStr.includes('م') ? areaStr : `${areaStr} م²`;
          const st3Area = document.getElementById('stage3Area');
          if (st3Area) st3Area.textContent = areaStr.includes('م') ? areaStr : `${areaStr} م²`;
        }
        if (dealType) document.getElementById('valDealType').textContent = dealType;
        if (siteDesc) document.getElementById('valSiteDesc').textContent = siteDesc;
        if (orderNo) document.getElementById('valOrderNo').textContent = orderNo;

        // 2. مسؤولو المعاملة (الخطوة 1)
        if (s.survey_technician) {
          const selT = document.getElementById('selSurveyTech');
          if (selT) {
            let found = false;
            for (let opt of selT.options) {
              if (opt.value === s.survey_technician) { opt.selected = true; found = true; break; }
            }
            if (!found && s.survey_technician) {
              const opt = new Option(s.survey_technician, s.survey_technician, true, true);
              selT.add(opt);
            }
          }
          document.getElementById('sigTech').textContent = `أ / ${s.survey_technician}`;
        }
        if (s.system_officer) {
          const selO = document.getElementById('selSysOfficer');
          if (selO) {
            let found = false;
            for (let opt of selO.options) {
              if (opt.value === s.system_officer) { opt.selected = true; found = true; break; }
            }
            if (!found && s.system_officer) {
              const opt = new Option(s.system_officer, s.system_officer, true, true);
              selO.add(opt);
            }
          }
          document.getElementById('sigGis').textContent = `أ / ${s.system_officer}`;
        }

        // 3. استعادة السلايدرات والمسافات
        const sliders = s.sliders || s;
        if (sliders.margin !== undefined || sliders.margin_mm !== undefined) {
          rngMargin.value = sliders.margin ?? sliders.margin_mm ?? 7;
        }
        if (sliders.gapHeader !== undefined || sliders.gap_header !== undefined) {
          rngGapHeader.value = sliders.gapHeader ?? sliders.gap_header ?? 0;
        }
        if (sliders.gapApplicant !== undefined || sliders.gap_applicant !== undefined) {
          rngGapApplicant.value = sliders.gapApplicant ?? sliders.gap_applicant ?? 8;
        }
        if (sliders.gapCoords !== undefined || sliders.gap_coords !== undefined) {
          rngGapCoords.value = sliders.gapCoords ?? sliders.gap_coords ?? 8;
        }
        if (sliders.gapImages !== undefined || sliders.gap_images !== undefined) {
          rngGapImages.value = sliders.gapImages ?? sliders.gap_images ?? 5;
        }
        if (sliders.tablePad !== undefined || sliders.table_pad !== undefined) {
          rngTablePad.value = sliders.tablePad ?? sliders.table_pad ?? 3.6;
        }
        if (sliders.imageHeight !== undefined || sliders.image_height !== undefined) {
          rngImageHeight.value = Math.max(200, sliders.imageHeight ?? sliders.image_height ?? 230);
        }

        // 4. استعادة العلامة المائية
        const wm = s.watermark || s;
        if (wm.active !== undefined || wm.wm_active !== undefined) {
          chkWatermarkActive.checked = Boolean(wm.active ?? wm.wm_active);
        }
        if (wm.opacity !== undefined || wm.wm_opacity !== undefined) {
          rngWmOpacity.value = wm.opacity ?? wm.wm_opacity ?? 10;
        }
        if (wm.angle !== undefined || wm.wm_angle !== undefined) {
          rngWmAngle.value = wm.angle ?? wm.wm_angle ?? -30;
        }
        if (wm.size !== undefined || wm.wm_size !== undefined) {
          rngWmSize.value = wm.size ?? wm.wm_size ?? 13;
        }

        // 5. استعادة الصورتين إن وجدتا
        if (s.croquis_base64) {
          document.getElementById('imgCroquis').src = s.croquis_base64;
          const s1 = document.getElementById('stage1CroquisImg');
          if (s1) s1.src = s.croquis_base64;
        }
        if (s.satellite_base64) {
          document.getElementById('imgSatellite').src = s.satellite_base64;
          const s1 = document.getElementById('stage1SatImg');
          if (s1) s1.src = s.satellite_base64;
        }

        // 6. كود التأمين الرقابي
        if (secToken) {
          const resTok = document.getElementById('resSecurityToken');
          if (resTok) {
            resTok.textContent = secToken;
            resTok.className = 'token-active';
          }
          const prnTok = document.getElementById('certTokenPrintVal');
          if (prnTok) prnTok.textContent = secToken;
        }

        // 7. كائن activeParcel
        if (!activeParcel) activeParcel = {};
        activeParcel.applicant_name = applicantName;
        activeParcel.receipt_no = receiptNo;
        activeParcel.national_id = nationalId;
        activeParcel.district = district;
        activeParcel.district_matched = true;
        activeParcel.village = village;
        activeParcel.address = address;
        activeParcel.stated_area_m2 = area;
        activeParcel.calculated_area_m2 = area;
        activeParcel.security_token = secToken || activeParcel.security_token || 'DUDC SECURE';
        if (s.segments) activeParcel.segments = s.segments;
        if (s.vertices) activeParcel.vertices = s.vertices;

        // 8. استعادة التخصيصات النصية إن وجدت
        if (s.text_customs && typeof applySavedTextDefaults === 'function') {
          applySavedTextDefaults(s.text_customs);
        }

        // 9. تحديث العرض وتفعيل الأقسام
        updateStep1State();
        updateSpacing();
        renderWatermark();

        const resultsSec = document.getElementById('surveyResultsSection');
        if (resultsSec) resultsSec.style.display = 'flex';

        // 10. الانتقال التلقائي إلى استوديو المعاينة (Stage 2)
        switchStage(2);

        alert(`✔ تم استيراد الجلسة بنجاح من (${fileName})\nللمواطن: ${applicantName || 'بدون اسم'}`);
      }

      // قائمة المراكز الرسمية الـ 18 لمحافظة الدقهلية
      const OFFICIAL_CENTERS_FALLBACK = [
        [0, "المنصورة"], [1, "طلخا"], [2, "ميت غمر"], [3, "دكرنس"],
        [4, "السنبلاوين"], [5, "بلقاس"], [6, "شربين"], [7, "المنزلة"],
        [8, "منية النصر"], [9, "أجا"], [10, "نبروه"], [11, "تمي الأمديد"],
        [12, "الجمالية"], [13, "الكردي"], [14, "المطرية"], [15, "ميت سلسيل"],
        [16, "بني عبيد"], [17, "جمصة"]
      ];
      let officialCentersList = OFFICIAL_CENTERS_FALLBACK;

      // --------------------------------------------------------------------------
      // منطق التحقق من الخطوة 1 (اختيار الفني ومسؤول النظم المعتمد)
      // --------------------------------------------------------------------------
      function isStep1Complete() {
        const tech = document.getElementById('selSurveyTech').value.trim();
        const officer = document.getElementById('selSysOfficer').value.trim();
        return Boolean(tech && officer);
      }

      function updateStep1State() {
        const complete = isStep1Complete();
        const badge = document.getElementById('step1StatusBadge');
        const dropzone = document.getElementById('dropzone');
        const fileInput = document.getElementById('surveyFileInput');
        const btnSample = document.getElementById('btnLoadSample');
        const lockNotice = document.getElementById('dropzoneLockedNotice');
        const step1Card = document.getElementById('step1Card');

        if (complete) {
          if (badge) {
            badge.className = 'badge-pass';
            badge.innerHTML = '✔ تم تحديد المسؤولين بنجاح';
          }
          if (step1Card) {
            step1Card.style.borderColor = 'rgba(16, 185, 129, 0.45)';
          }
          if (dropzone) {
            dropzone.classList.remove('locked');
          }
          if (fileInput) fileInput.disabled = false;
          if (btnSample) {
            btnSample.disabled = false;
            btnSample.style.pointerEvents = 'auto';
          }
          if (lockNotice) {
            lockNotice.style.display = 'none';
          }
        } else {
          if (badge) {
            badge.className = 'badge-pending';
            badge.innerHTML = '⏳ بانتظار تحديد المسؤولين';
          }
          if (step1Card) {
            step1Card.style.borderColor = 'rgba(56, 189, 248, 0.35)';
          }
          if (dropzone) {
            dropzone.classList.add('locked');
          }
          if (fileInput) fileInput.disabled = true;
          if (btnSample) {
            btnSample.disabled = true;
            btnSample.style.pointerEvents = 'none';
          }
          if (lockNotice) {
            lockNotice.style.display = 'flex';
          }
        }
      }

      function highlightStep1Requirement() {
        const card = document.getElementById('step1Card');
        if (card) {
          card.style.transition = 'all 0.3s ease';
          card.style.boxShadow = '0 0 25px rgba(245, 158, 11, 0.7)';
          card.style.borderColor = '#f59e0b';
          setTimeout(() => {
            card.style.boxShadow = '';
            card.style.borderColor = isStep1Complete() ? 'rgba(16, 185, 129, 0.45)' : 'rgba(56, 189, 248, 0.35)';
          }, 1200);
        }
        const selTech = document.getElementById('selSurveyTech');
        const selOfficer = document.getElementById('selSysOfficer');
        if (!selTech.value) {
          selTech.scrollIntoView({ behavior: 'smooth', block: 'center' });
          selTech.focus();
        } else if (!selOfficer.value) {
          selOfficer.scrollIntoView({ behavior: 'smooth', block: 'center' });
          selOfficer.focus();
        }
      }

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

      // التحديث اللحظي للشفرة السحابية وحالة الخطوة 1 عند تغيير الفني أو المسؤول
      ['selSurveyTech', 'selSysOfficer'].forEach(id => {
        document.getElementById(id).addEventListener('change', () => {
          updateStep1State();

          if (activeParcel && activeParcel.district_id !== null && activeParcel.district_id !== undefined) {
            const newCid = activeParcel.district_id;
            const techVal = document.getElementById('selSurveyTech').value;
            const officerVal = document.getElementById('selSysOfficer').value;
            if (!techVal || !officerVal) return;

            const badge = document.getElementById('districtStatusBadge');
            const tokDisplay = document.getElementById('resSecurityToken');
            if (badge) badge.innerHTML = '<span style="color: var(--accent-cyan); font-size: 10px;">⏳ تحديث بالسحابة...</span>';

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
                activeParcel.security_token = data.security_token;
                if (badge) badge.innerHTML = '<span style="color: #34d399; font-weight: bold; font-size: 10px;">✔ موثق بالسحابة</span>';
                if (tokDisplay) {
                  tokDisplay.className = 'token-active';
                  tokDisplay.textContent = data.security_token;
                }
                renderWatermark();
              }
            }).catch(() => {});
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
          if (badge) badge.innerHTML = '<span style="color: #34d399; font-weight: bold; font-size: 10px;">✔ مطابق</span>';

          if (tokDisplay) {
            tokDisplay.className = 'token-active';
            tokDisplay.textContent = parcel.security_token || '--';
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

          // قاعدة صارمة: حجب كود التأمين حتى يتم تأمين المركز
          if (tokDisplay) {
            tokDisplay.className = 'token-locked';
            tokDisplay.innerHTML = '<span>⏳ بانتظار تأمين المركز</span>';
          }
        }
      }

      function handleDistrictChange(newCid) {
        if (!activeParcel || newCid === "" || newCid === null || newCid === undefined) return;

        const sel = document.getElementById('selDistrict');
        const badge = document.getElementById('districtStatusBadge');
        const tokDisplay = document.getElementById('resSecurityToken');

        if (badge) badge.innerHTML = '<span style="color: var(--accent-cyan); font-size: 10px;">⏳ جاري التشفير...</span>';

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
            activeParcel.security_token = data.security_token;

            if (sel) sel.className = 'district-select matched';
            if (badge) badge.innerHTML = '<span style="color: #34d399; font-weight: bold; font-size: 10px;">✔ تم التأمين</span>';

            if (tokDisplay) {
              tokDisplay.className = 'token-active';
              tokDisplay.textContent = data.security_token;
            }

            renderWatermark();

            // مزامنة الاستوديو في المرحلة 2
            const valCenterElem = document.getElementById('valCenter');
            if (valCenterElem) valCenterElem.textContent = data.district;

            // تحديث كروكي المرحلة 1 لإظهار البصمة المشفرة
            if (data.croquis_url) {
              const croqImg = document.getElementById('stage1CroquisImg');
              const imgCroqStage2 = document.getElementById('imgCroquis');
              if (croqImg) croqImg.src = data.croquis_url;
              if (imgCroqStage2) imgCroqStage2.src = data.croquis_url;
            }
          } else {
            alert('خطأ في تأمين المركز: ' + (data.error || 'غير معروف'));
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
        document.getElementById('resApplicantName').textContent = parcel.applicant_name || 'غير محدد';
        document.getElementById('resNationalId').textContent = parcel.national_id || 'غير محدد';
        document.getElementById('resReceiptNo').textContent = parcel.receipt_no || '0';

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

        // تحميل الصورتين بالتوازي ومتابعة حالة التحميل
        Promise.all([
          loadCroquisPreview().catch(e => console.warn('Croquis preview warning:', e)),
          loadSatellitePreview().catch(e => console.warn('Satellite preview warning:', e))
        ]).then(() => {
          setLoadingStep(3, 'done');
          setLoadingStep(4, 'done');
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

      // إتاحة الدوال على كائن window للتفاعل الفوري مع أحداث HTML المباشرة (onclick, onchange)
      window.adjustCroqFont = adjustCroqFont;
      window.updateCroquisDiagram = updateCroquisDiagram;
      window.copySecurityToken = copySecurityToken;
      window.handleDistrictChange = handleDistrictChange;

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

      /* ==========================================================================
         المرحلة 2: المزامنة من المرحلة 1 إلى استوديو التحرير
         ========================================================================== */
      function toArabicNumerals(val) {
        if (val === null || val === undefined) return '';
        const arabicDigits = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
        return String(val).replace(/[0-9]/g, d => arabicDigits[+d]);
      }

      function syncStage1ToStage2() {
        if (!activeParcel) return;

        // ملء بيانات المواطن بالشهادة بالأرقام العربية
        document.getElementById('valApplicantName').textContent = activeParcel.applicant_name || 'محمد إبراهيم محمد حسن';
        document.getElementById('valReceiptNo').textContent = toArabicNumerals(activeParcel.receipt_no || '104523');
        document.getElementById('valNationalId').textContent = toArabicNumerals(activeParcel.national_id || '29001011234567');
        document.getElementById('valCenter').textContent = activeParcel.district || 'نبروه';
        document.getElementById('valVillage').textContent = activeParcel.village || 'كفر الجنينة';
        document.getElementById('valAddress').textContent = activeParcel.address || 'شارع داير الناحية';
        
        // المساحة تتكتب أرقام عربية وبدون علامة _
        const areaVal = (parseFloat(activeParcel.calculated_area_m2) || 0).toFixed(2);
        document.getElementById('valArea').textContent = `${toArabicNumerals(areaVal)} م²`;
        if (savedTextDefaults && savedTextDefaults['valOrderNo'] && savedTextDefaults['valOrderNo'].html) {
          document.getElementById('valOrderNo').innerHTML = savedTextDefaults['valOrderNo'].html;
        } else {
          document.getElementById('valOrderNo').textContent = `${toArabicNumerals('2605')}s`;
        }

        // التوقيعات المحددة
        document.getElementById('sigTech').textContent = `أ / ${document.getElementById('selSurveyTech').value}`;
        document.getElementById('sigGis').textContent = `أ / ${document.getElementById('selSysOfficer').value}`;

        // إعادة تطبيق التنسيقات المحفوظة على الحقول الديناميكية
        reapplyDynamicTextStyles();

        // تاريخ اليوم بالأرقام العربية
        const now = new Date();
        const days = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'];
        const dayName = days[now.getDay()];
        const dateStr = toArabicNumerals(`${now.getFullYear()}/${String(now.getMonth()+1).padStart(2,'0')}/${String(now.getDate()).padStart(2,'0')}`);
        document.getElementById('certDateDisplay').textContent = `تم تحرير الشهادة في يوم ${dayName} الموافق ${dateStr}`;

        // كود التأمين الرقابي الرسمي تحت التاريخ مطبوع وغير قابل للتعديل
        const certTokElem = document.getElementById('certTokenPrintVal');
        if (certTokElem) {
          certTokElem.textContent = activeParcel.security_token || document.getElementById('resSecurityToken')?.textContent?.trim() || '--';
        }

        // بناء جدول الحدود والإحداثيات بالدمج الرأسي الدقيق
        buildCertCoordsTable();
      }

      function buildCertCoordsTable() {
        const tbody = document.getElementById('certCoordsTbody');
        tbody.innerHTML = '';

        const directions = [
          { key: 'north', title: 'الحد البحري' },
          { key: 'east', title: 'الحد الشرقي' },
          { key: 'south', title: 'الحد القبلي' },
          { key: 'west', title: 'الحد الغربي' }
        ];

        // تجميع الأضلاع حسب الاتجاه
        const segRows = document.querySelectorAll('#stage1SegmentsTbody tr');
        let dirGroups = { north: [], east: [], south: [], west: [] };

        segRows.forEach(tr => {
          const dir = tr.querySelector('.seg-dir-select').value;
          const neighbor = tr.querySelector('.seg-neighbor-input').value.trim();
          const len = parseFloat(tr.querySelector('.seg-length-input').value) || 0;
          dirGroups[dir].push({ neighbor, len });
        });

        // قراءة الإحداثيات من النقاط
        const verts = activeParcel.vertices || [];

        // التحقق من وجود تنسيقات افتراضية مخصصة لخلايا جدول الإحداثيات
        const titleStyle = (savedTextDefaults && savedTextDefaults['__coords_title_styles']) ? savedTextDefaults['__coords_title_styles'] : null;
        const coordStyle = (savedTextDefaults && savedTextDefaults['__coord_num_styles']) ? savedTextDefaults['__coord_num_styles'] : null;
        const betoolStyle = (savedTextDefaults && savedTextDefaults['__coords_betool_styles']) ? savedTextDefaults['__coords_betool_styles'] : null;
        const betoolText = (savedTextDefaults && savedTextDefaults['__coords_betool_text']) ? savedTextDefaults['__coords_betool_text'] : 'بطول';

        let titleStyleAttr = 'font-weight: bold;';
        if (titleStyle) {
          if (titleStyle.fontFamily) titleStyleAttr += ` font-family: ${titleStyle.fontFamily};`;
          if (titleStyle.fontSize) titleStyleAttr += ` font-size: ${titleStyle.fontSize};`;
          if (titleStyle.color) titleStyleAttr += ` color: ${titleStyle.color};`;
          if (titleStyle.textAlign) titleStyleAttr += ` text-align: ${titleStyle.textAlign};`;
        }

        let coordStyleAttr = '';
        if (coordStyle) {
          if (coordStyle.fontFamily) coordStyleAttr += ` font-family: ${coordStyle.fontFamily};`;
          if (coordStyle.fontSize) coordStyleAttr += ` font-size: ${coordStyle.fontSize};`;
          if (coordStyle.fontWeight) coordStyleAttr += ` font-weight: ${coordStyle.fontWeight};`;
          if (coordStyle.color) coordStyleAttr += ` color: ${coordStyle.color};`;
        }

        let betoolStyleAttr = '';
        if (betoolStyle) {
          if (betoolStyle.fontFamily) betoolStyleAttr += ` font-family: ${betoolStyle.fontFamily};`;
          if (betoolStyle.fontSize) betoolStyleAttr += ` font-size: ${betoolStyle.fontSize};`;
          if (betoolStyle.fontWeight) betoolStyleAttr += ` font-weight: ${betoolStyle.fontWeight};`;
          if (betoolStyle.color) betoolStyleAttr += ` color: ${betoolStyle.color};`;
        }

        directions.forEach((d, dIdx) => {
          const group = dirGroups[d.key];
          const totalLen = group.reduce((acc, curr) => acc + curr.len, 0);
          const neighborName = group.map(g => g.neighbor).filter(Boolean).join(' • ') || '';
          const rowCount = Math.max(1, group.length);

          const customTitle = (savedTextDefaults && savedTextDefaults[`__dir_${d.key}`]) ? savedTextDefaults[`__dir_${d.key}`] : d.title;

          for (let r = 0; r < rowCount; r++) {
            const tr = document.createElement('tr');
            let v = verts[(dIdx * 2 + r) % Math.max(1, verts.length)] || { lon: 31.27530894, lat: 30.80509232 };
            // الإحداثيات تبقى أرقام إنجليزية لعدم تغيير صيغة الـ GPS
            const lonStr = v.lon ? parseFloat(v.lon).toFixed(8) : '';
            const latStr = v.lat ? parseFloat(v.lat).toFixed(8) : '';

            if (r === 0) {
              tr.innerHTML = `
                <td rowspan="${rowCount}" class="cell-dir-title" data-dir-key="${d.key}" style="${titleStyleAttr}" contenteditable="true" spellcheck="false">${customTitle}</td>
                <td rowspan="${rowCount}" class="cell-dir-neighbor" contenteditable="true" spellcheck="false">${neighborName}</td>
                <td rowspan="${rowCount}" class="cell-dir-betool" style="${betoolStyleAttr}" contenteditable="true" spellcheck="false">${betoolText}</td>
                <td rowspan="${rowCount}" class="cell-dir-len" style="font-weight: bold;" contenteditable="true" spellcheck="false">${totalLen > 0 ? toArabicNumerals(totalLen.toFixed(2)) : ''}</td>
                <td><span class="coord-num" style="${coordStyleAttr}" contenteditable="true" spellcheck="false">${lonStr}</span></td>
                <td><span class="coord-num" style="${coordStyleAttr}" contenteditable="true" spellcheck="false">${latStr}</span></td>
              `;
            } else {
              tr.innerHTML = `
                <td><span class="coord-num" style="${coordStyleAttr}" contenteditable="true" spellcheck="false">${lonStr}</span></td>
                <td><span class="coord-num" style="${coordStyleAttr}" contenteditable="true" spellcheck="false">${latStr}</span></td>
              `;
            }
            tbody.appendChild(tr);
          }
        });
      }

      /* ==========================================================================
         أدوات استوديو التحرير (Spacing, Typography, Watermark, Zoom & Crop)
         ========================================================================== */
      const certPage = document.getElementById('certPage');
      const pageContainer = document.getElementById('pageContainer');
      const watermarkLayer = document.getElementById('watermarkLayer');
      const viewport = document.getElementById('viewport');

      const rngMargin = document.getElementById('rngMargin');
      const valMargin = document.getElementById('valMargin');
      const rngGapHeader = document.getElementById('rngGapHeader');
      const valGapHeader = document.getElementById('valGapHeader');
      const rngGapApplicant = document.getElementById('rngGapApplicant');
      const valGapApplicant = document.getElementById('valGapApplicant');
      const rngGapCoords = document.getElementById('rngGapCoords');
      const valGapCoords = document.getElementById('valGapCoords');
      const rngGapImages = document.getElementById('rngGapImages');
      const valGapImages = document.getElementById('valGapImages');
      const rngTablePad = document.getElementById('rngTablePad');
      const valTablePad = document.getElementById('valTablePad');
      const rngImageHeight = document.getElementById('rngImageHeight');
      const valImageHeight = document.getElementById('valImageHeight');

      const chkWatermarkActive = document.getElementById('chkWatermarkActive');
      const rngWmOpacity = document.getElementById('rngWmOpacity');
      const valWmOpacity = document.getElementById('valWmOpacity');
      const rngWmAngle = document.getElementById('rngWmAngle');
      const valWmAngle = document.getElementById('valWmAngle');
      const rngWmSize = document.getElementById('rngWmSize');
      const valWmSize = document.getElementById('valWmSize');

      function updateSpacing() {
        document.documentElement.style.setProperty('--cert-margin', `${rngMargin.value}mm`);
        valMargin.textContent = `${rngMargin.value} mm`;
        document.documentElement.style.setProperty('--sec-gap-header', `${rngGapHeader.value}px`);
        valGapHeader.textContent = `${rngGapHeader.value} px`;
        document.documentElement.style.setProperty('--sec-gap-applicant', `${rngGapApplicant.value}px`);
        valGapApplicant.textContent = `${rngGapApplicant.value} px`;
        document.documentElement.style.setProperty('--sec-gap-coords', `${rngGapCoords.value}px`);
        valGapCoords.textContent = `${rngGapCoords.value} px`;
        document.documentElement.style.setProperty('--sec-gap-images', `${rngGapImages.value}px`);
        valGapImages.textContent = `${rngGapImages.value} px`;
        document.documentElement.style.setProperty('--table-padding-y', `${rngTablePad.value}px`);
        valTablePad.textContent = `${rngTablePad.value} px`;
        document.documentElement.style.setProperty('--image-height', `${rngImageHeight.value}px`);
        valImageHeight.textContent = `${rngImageHeight.value} px`;
      }

      [rngMargin, rngGapHeader, rngGapApplicant, rngGapCoords, rngGapImages, rngTablePad, rngImageHeight].forEach(el => {
        el.addEventListener('input', updateSpacing);
      });

      // زر فتح وإغلاق خيارات المسافات والتباعد المتقدمة (Accordion)
      const btnToggleSpacing = document.getElementById('btnToggleSpacing');
      const spacingControlsBody = document.getElementById('spacingControlsBody');
      const spacingToggleIcon = document.getElementById('spacingToggleIcon');
      if (btnToggleSpacing && spacingControlsBody) {
        btnToggleSpacing.addEventListener('click', () => {
          const isHidden = spacingControlsBody.style.display === 'none' || !spacingControlsBody.style.display;
          spacingControlsBody.style.display = isHidden ? 'flex' : 'none';
          if (spacingToggleIcon) spacingToggleIcon.textContent = isHidden ? '▲ إخفاء' : '▼ إظهار التحكمات';
        });
      }

      document.getElementById('btnAutoFit').addEventListener('click', () => {
        const targetHeight = 1123;
        const currentHeight = certPage.scrollHeight;
        if (currentHeight > targetHeight) {
          rngMargin.value = Math.max(5, rngMargin.value - 1);
          rngGapHeader.value = 1;
          rngGapApplicant.value = 2;
          rngGapCoords.value = 3;
          rngGapImages.value = 2;
          rngTablePad.value = 1.8;
          rngImageHeight.value = Math.max(140, rngImageHeight.value - 15);
          updateSpacing();
        }
        alert('⚡ تم ضبط وتنسيق المسافات بنجاح لقفل الشهادة في صفحة A4 واحدة تماماً.');
      });

      function renderWatermark() {
        const isActive = chkWatermarkActive.checked;
        const opacity = isActive ? (rngWmOpacity.value / 100) : 0;
        const angle = `${rngWmAngle.value}deg`;
        const size = `${rngWmSize.value}pt`;

        document.documentElement.style.setProperty('--wm-opacity', opacity);
        document.documentElement.style.setProperty('--wm-angle', angle);
        document.documentElement.style.setProperty('--wm-size', size);

        valWmOpacity.textContent = `${rngWmOpacity.value} %`;
        valWmAngle.textContent = `${rngWmAngle.value}°`;
        valWmSize.textContent = `${rngWmSize.value} pt`;

        // استخدام الكود السري المولد كعلامة مائية مطابقة تماماً للمطلوب
        const rawToken = (activeParcel && activeParcel.security_token)
          ? activeParcel.security_token
          : (document.getElementById('resSecurityToken')?.textContent?.trim() || '');

        const validToken = (rawToken && rawToken !== '--' && !rawToken.includes('بانتظار'))
          ? rawToken
          : 'DUDC SECURE';

        watermarkLayer.innerHTML = '';
        if (isActive) {
          for (let i = 0; i < 9; i++) {
            const row = document.createElement('div');
            row.className = 'watermark-row';
            row.textContent = `${validToken}    •    ${validToken}    •    ${validToken}`;
            watermarkLayer.appendChild(row);
          }
        }
      }

      [chkWatermarkActive, rngWmOpacity, rngWmAngle, rngWmSize].forEach(el => {
        el.addEventListener('input', renderWatermark);
      });

      // الشريط العائم للنصوص
      const floatingToolbar = document.getElementById('floatingToolbar');
      const fltFontFamily = document.getElementById('fltFontFamily');
      const fltFontSizeVal = document.getElementById('fltFontSizeVal');
      const fltFontInc = document.getElementById('fltFontInc');
      const fltFontDec = document.getElementById('fltFontDec');
      const fltBold = document.getElementById('fltBold');
      const fltColorBlue = document.getElementById('fltColorBlue');
      const fltColorBlack = document.getElementById('fltColorBlack');
      const fltAlignRight = document.getElementById('fltAlignRight');
      const fltAlignCenter = document.getElementById('fltAlignCenter');
      const fltAlignLeft = document.getElementById('fltAlignLeft');
      let activeEditableElement = null;

      certPage.addEventListener('focusin', (e) => {
        if (e.target && e.target.isContentEditable) {
          activeEditableElement = e.target;
          const rect = e.target.getBoundingClientRect();
          const vRect = viewport.getBoundingClientRect();
          floatingToolbar.style.top = `${(rect.top - vRect.top) + viewport.scrollTop - 44}px`;
          floatingToolbar.style.left = `${(rect.left - vRect.left) + (rect.width / 2)}px`;
          floatingToolbar.style.display = 'flex';

          const comp = window.getComputedStyle(e.target);
          fltFontSizeVal.textContent = `${parseInt(comp.fontSize) || 12}px`;
          fltBold.classList.toggle('active', comp.fontWeight === 'bold' || parseInt(comp.fontWeight) >= 700);
        }
      });

      document.addEventListener('click', (e) => {
        if (!e.target.isContentEditable && !floatingToolbar.contains(e.target)) {
          floatingToolbar.style.display = 'none';
        }
      });

      fltFontFamily.addEventListener('change', () => { if (activeEditableElement) activeEditableElement.style.fontFamily = fltFontFamily.value; });
      fltFontInc.addEventListener('click', () => {
        if (activeEditableElement) {
          const s = (parseInt(window.getComputedStyle(activeEditableElement).fontSize) || 12) + 1;
          activeEditableElement.style.fontSize = `${s}px`;
          fltFontSizeVal.textContent = `${s}px`;
        }
      });
      fltFontDec.addEventListener('click', () => {
        if (activeEditableElement) {
          const s = Math.max(8, (parseInt(window.getComputedStyle(activeEditableElement).fontSize) || 12) - 1);
          activeEditableElement.style.fontSize = `${s}px`;
          fltFontSizeVal.textContent = `${s}px`;
        }
      });
      fltBold.addEventListener('click', () => {
        if (activeEditableElement) {
          const b = activeEditableElement.style.fontWeight === 'bold';
          activeEditableElement.style.fontWeight = b ? 'normal' : 'bold';
          fltBold.classList.toggle('active', !b);
        }
      });
      fltColorBlue.addEventListener('click', () => { if (activeEditableElement) activeEditableElement.style.color = '#365F91'; });
      fltColorBlack.addEventListener('click', () => { if (activeEditableElement) activeEditableElement.style.color = '#000000'; });

      if (fltAlignRight) {
        fltAlignRight.addEventListener('click', () => {
          if (activeEditableElement) activeEditableElement.style.textAlign = 'right';
        });
      }
      if (fltAlignCenter) {
        fltAlignCenter.addEventListener('click', () => {
          if (activeEditableElement) activeEditableElement.style.textAlign = 'center';
        });
      }
      if (fltAlignLeft) {
        fltAlignLeft.addEventListener('click', () => {
          if (activeEditableElement) activeEditableElement.style.textAlign = 'left';
        });
      }

      // استوديو قص وتكبير الصور بالأبعاد الحقيقية
      const imageModalBackdrop = document.getElementById('imageModalBackdrop');
      const modalTargetImg = document.getElementById('modalTargetImg');
      const cropFrameGuide = document.getElementById('cropFrameGuide');
      const cropCanvasWrapper = document.getElementById('cropCanvasWrapper');
      const rngModalZoom = document.getElementById('rngModalZoom');
      const txtModalZoom = document.getElementById('txtModalZoom');
      const btnModalRotate = document.getElementById('btnModalRotate');
      const btnModalReset = document.getElementById('btnModalReset');
      const btnApplyCrop = document.getElementById('btnApplyCrop');
      const btnCloseModal = document.getElementById('btnCloseModal');
      const btnCancelCrop = document.getElementById('btnCancelCrop');

      let currentEditingTarget = null;
      let imgState = { baseWidth: 0, baseHeight: 0, zoom: 1.0, posX: 0, posY: 0, rotate: 0 };
      let isDraggingImg = false;
      let startMouseX = 0, startMouseY = 0;
      let frameW = 500, frameH = 240;

      function openImageStudio(targetType) {
        currentEditingTarget = targetType;
        const sourceImg = (targetType === 'croquis') ? document.getElementById('imgCroquis') : document.getElementById('imgSatellite');
        const targetWrapper = (targetType === 'croquis') ? document.getElementById('croquisWrapper') : document.getElementById('satWrapper');

        const targetAspect = targetWrapper.clientWidth / targetWrapper.clientHeight;
        const wrapperW = cropCanvasWrapper.clientWidth || 700;
        const wrapperH = cropCanvasWrapper.clientHeight || 380;
        const maxW = wrapperW * 0.85;
        const maxH = wrapperH * 0.85;

        if (maxW / maxH > targetAspect) {
          frameH = maxH; frameW = frameH * targetAspect;
        } else {
          frameW = maxW; frameH = frameW / targetAspect;
        }

        cropFrameGuide.style.width = `${frameW}px`;
        cropFrameGuide.style.height = `${frameH}px`;

        modalTargetImg.onload = () => {
          const natW = modalTargetImg.naturalWidth;
          const natH = modalTargetImg.naturalHeight;
          const scaleToFit = Math.min(frameW / natW, frameH / natH) * 1.05;
          imgState.baseWidth = natW * scaleToFit;
          imgState.baseHeight = natH * scaleToFit;
          imgState.zoom = 1.0; imgState.posX = 0; imgState.posY = 0; imgState.rotate = 0;

          modalTargetImg.style.width = `${imgState.baseWidth}px`;
          modalTargetImg.style.height = `${imgState.baseHeight}px`;
          rngModalZoom.value = 1.0;
          txtModalZoom.textContent = '100%';
          applyImgTransform();
        };

        modalTargetImg.src = sourceImg.src;
        imageModalBackdrop.style.display = 'flex';
      }

      function applyImgTransform() {
        modalTargetImg.style.transform = `translate(${imgState.posX}px, ${imgState.posY}px) scale(${imgState.zoom}) rotate(${imgState.rotate}deg)`;
      }

      document.getElementById('btnOpenCropCroquis').addEventListener('click', () => openImageStudio('croquis'));
      document.getElementById('btnOpenCropSat').addEventListener('click', () => openImageStudio('sat'));
      document.getElementById('btnCropCroqQuick').addEventListener('click', () => openImageStudio('croquis'));
      document.getElementById('btnCropSatQuick').addEventListener('click', () => openImageStudio('sat'));

      function closeModal() { imageModalBackdrop.style.display = 'none'; }
      btnCloseModal.addEventListener('click', closeModal);
      btnCancelCrop.addEventListener('click', closeModal);

      rngModalZoom.addEventListener('input', () => {
        imgState.zoom = parseFloat(rngModalZoom.value);
        txtModalZoom.textContent = `${Math.round(imgState.zoom * 100)}%`;
        applyImgTransform();
      });
      btnModalRotate.addEventListener('click', () => { imgState.rotate = (imgState.rotate + 90) % 360; applyImgTransform(); });
      btnModalReset.addEventListener('click', () => {
        imgState.zoom = 1.0; imgState.posX = 0; imgState.posY = 0; imgState.rotate = 0;
        rngModalZoom.value = 1.0; txtModalZoom.textContent = '100%'; applyImgTransform();
      });

      cropCanvasWrapper.addEventListener('mousedown', (e) => {
        isDraggingImg = true;
        startMouseX = e.clientX - imgState.posX;
        startMouseY = e.clientY - imgState.posY;
      });
      window.addEventListener('mousemove', (e) => {
        if (!isDraggingImg) return;
        imgState.posX = e.clientX - startMouseX;
        imgState.posY = e.clientY - startMouseY;
        applyImgTransform();
      });
      window.addEventListener('mouseup', () => { isDraggingImg = false; });

      btnApplyCrop.addEventListener('click', () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = frameW * 2; canvas.height = frameH * 2;
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.src = modalTargetImg.src;
        img.onload = () => {
          ctx.save();
          ctx.translate(canvas.width / 2, canvas.height / 2);
          ctx.rotate((imgState.rotate * Math.PI) / 180);
          const ratio = canvas.width / frameW;
          const drawW = imgState.baseWidth * imgState.zoom * ratio;
          const drawH = imgState.baseHeight * imgState.zoom * ratio;
          ctx.drawImage(img, (imgState.posX * ratio) - (drawW / 2), (imgState.posY * ratio) - (drawH / 2), drawW, drawH);
          ctx.restore();

          const croppedUrl = canvas.toDataURL('image/jpeg', 0.95);
          if (currentEditingTarget === 'croquis') {
            document.getElementById('imgCroquis').src = croppedUrl;
          } else {
            document.getElementById('imgSatellite').src = croppedUrl;
          }
          closeModal();
        };
      });

      // ==========================================================================
      // محرك حفظ واستعادة الإعدادات الافتراضية الشاملة (Layout + النصوص والتنسيقات)
      // ==========================================================================
      let savedTextDefaults = null;

      function collectAllTextCustomizations() {
        const customs = {};

        // جمع كافة العناصر التي تحتوي على data-text-id أو id أو نصوص الملاحظات
        const elements = certPage.querySelectorAll('[data-text-id], [id^="val"], [id^="sig"], .cert-notes p');
        elements.forEach(el => {
          const key = el.getAttribute('data-text-id') || el.id;
          if (!key) return;

          const isDynamic = el.getAttribute('data-dynamic') === 'true';

          const styles = {};
          if (el.style.fontFamily) styles.fontFamily = el.style.fontFamily;
          if (el.style.fontSize) styles.fontSize = el.style.fontSize;
          if (el.style.fontWeight) styles.fontWeight = el.style.fontWeight;
          if (el.style.color) styles.color = el.style.color;
          if (el.style.textAlign) styles.textAlign = el.style.textAlign;

          const item = {
            isDynamic: isDynamic,
            styles: styles
          };

          // حفظ محتوى النص للعناصر الثابتة والرسمية (الملاحظات، العناوين، مدير المركز، إلخ)
          if (!isDynamic) {
            item.html = el.innerHTML;
          }

          customs[key] = item;
        });

        // تخصيصات جدول الإحداثيات
        const firstDirTitle = certPage.querySelector('.cell-dir-title');
        if (firstDirTitle) {
          customs['__coords_title_styles'] = {
            fontFamily: firstDirTitle.style.fontFamily || '',
            fontSize: firstDirTitle.style.fontSize || '',
            fontWeight: firstDirTitle.style.fontWeight || '',
            color: firstDirTitle.style.color || '',
            textAlign: firstDirTitle.style.textAlign || ''
          };
        }
        const firstCoordNum = certPage.querySelector('.coord-num');
        if (firstCoordNum) {
          customs['__coord_num_styles'] = {
            fontFamily: firstCoordNum.style.fontFamily || '',
            fontSize: firstCoordNum.style.fontSize || '',
            fontWeight: firstCoordNum.style.fontWeight || '',
            color: firstCoordNum.style.color || ''
          };
        }
        const firstBetool = certPage.querySelector('.cell-dir-betool');
        if (firstBetool) {
          customs['__coords_betool_text'] = firstBetool.textContent.trim();
          customs['__coords_betool_styles'] = {
            fontFamily: firstBetool.style.fontFamily || '',
            fontSize: firstBetool.style.fontSize || '',
            fontWeight: firstBetool.style.fontWeight || '',
            color: firstBetool.style.color || ''
          };
        }

        // حفظ مسميات الحدود الأربعة إن تم تعديلها
        certPage.querySelectorAll('.cell-dir-title[data-dir-key]').forEach(el => {
          const dirKey = el.getAttribute('data-dir-key');
          if (dirKey) {
            customs[`__dir_${dirKey}`] = el.textContent.trim();
          }
        });

        return customs;
      }

      function applySavedTextDefaults(textData) {
        if (!textData) return;

        for (const [key, item] of Object.entries(textData)) {
          if (key.startsWith('__')) continue;

          const el = certPage.querySelector(`[data-text-id="${key}"]`) || document.getElementById(key);
          if (!el) continue;

          // 1. استعادة النص أو الصياغة للعناصر غير الديناميكية
          if (!item.isDynamic && item.html !== undefined && item.html !== null) {
            el.innerHTML = item.html;
          }

          // 2. تطبيق التنسيقات (الخط، الحجم، اللون، البولد، المحاذاة) على كافة العناصر
          if (item.styles) {
            if (item.styles.fontFamily) el.style.fontFamily = item.styles.fontFamily;
            if (item.styles.fontSize) el.style.fontSize = item.styles.fontSize;
            if (item.styles.fontWeight) el.style.fontWeight = item.styles.fontWeight;
            if (item.styles.color) el.style.color = item.styles.color;
            if (item.styles.textAlign) el.style.textAlign = item.styles.textAlign;
          }
        }
      }

      function reapplyDynamicTextStyles() {
        if (!savedTextDefaults) return;
        for (const [key, item] of Object.entries(savedTextDefaults)) {
          if (!item.isDynamic || !item.styles) continue;
          const el = certPage.querySelector(`[data-text-id="${key}"]`) || document.getElementById(key);
          if (!el) continue;
          if (item.styles.fontFamily) el.style.fontFamily = item.styles.fontFamily;
          if (item.styles.fontSize) el.style.fontSize = item.styles.fontSize;
          if (item.styles.fontWeight) el.style.fontWeight = item.styles.fontWeight;
          if (item.styles.color) el.style.color = item.styles.color;
          if (item.styles.textAlign) el.style.textAlign = item.styles.textAlign;
        }
      }

      function applyLayoutDefaults(data) {
        if (data) {
          // ترقية القيم القديمة تلقائياً إلى القيم القياسية المحسنة
          if (data.image_height && Number(data.image_height) < 200) {
            data.margin_mm = 7;
            data.gap_header = 0;
            data.gap_applicant = 8;
            data.gap_coords = 8;
            data.gap_images = 5;
            data.table_pad = 3.6;
            data.image_height = 230;
            data.wm_active = true;
            data.wm_opacity = 10;
            data.wm_angle = -30;
            data.wm_size = 13;
          }
          rngMargin.value = data.margin_mm ?? 7;
          rngGapHeader.value = data.gap_header ?? 0;
          rngGapApplicant.value = data.gap_applicant ?? 8;
          rngGapCoords.value = data.gap_coords ?? 8;
          rngGapImages.value = data.gap_images ?? 5;
          rngTablePad.value = data.table_pad ?? 3.6;
          rngImageHeight.value = data.image_height ?? 230;
          chkWatermarkActive.checked = data.wm_active ?? true;
          rngWmOpacity.value = data.wm_opacity ?? 10;
          rngWmAngle.value = data.wm_angle ?? -30;
          rngWmSize.value = data.wm_size ?? 13;
        } else {
          rngMargin.value = 7;
          rngGapHeader.value = 0;
          rngGapApplicant.value = 8;
          rngGapCoords.value = 8;
          rngGapImages.value = 5;
          rngTablePad.value = 3.6;
          rngImageHeight.value = 230;
          chkWatermarkActive.checked = true;
          rngWmOpacity.value = 10;
          rngWmAngle.value = -30;
          rngWmSize.value = 13;
        }
        updateSpacing();
        renderWatermark();
      }

      // حفظ كإعدادات افتراضية (Layout + النصوص والتنسيقات)
      const saveToast = document.getElementById('saveToast');
      document.getElementById('btnSaveAsDefault').addEventListener('click', () => {
        const textCustoms = collectAllTextCustomizations();
        savedTextDefaults = textCustoms;

        const defs = {
          margin_mm: rngMargin.value,
          gap_header: rngGapHeader.value,
          gap_applicant: rngGapApplicant.value,
          gap_coords: rngGapCoords.value,
          gap_images: rngGapImages.value,
          table_pad: rngTablePad.value,
          image_height: rngImageHeight.value,
          wm_active: chkWatermarkActive.checked,
          wm_opacity: rngWmOpacity.value,
          wm_angle: rngWmAngle.value,
          wm_size: rngWmSize.value,
          text_customs: textCustoms
        };

        // 1. الحفظ الفوري في ذاكرة المتصفح
        localStorage.setItem('dudc_v3_default_settings', JSON.stringify(defs));

        // 2. الحفظ السحابي/المحلي الدائم في السيرفر (user_default_settings.json)
        fetch('/api/save-defaults', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(defs)
        }).catch(() => {});

        const msgSpan = document.getElementById('saveToastMsg');
        if (msgSpan) msgSpan.textContent = 'تم حفظ الإعدادات الافتراضية وتعديلات النصوص بنجاح!';
        saveToast.classList.add('show');
        setTimeout(() => saveToast.classList.remove('show'), 3200);
      });

      // زر استعادة الإعدادات الأصلية المصنعية
      const btnResetDefaultSettings = document.getElementById('btnResetDefaultSettings');
      if (btnResetDefaultSettings) {
        btnResetDefaultSettings.addEventListener('click', () => {
          if (confirm('هل تود استعادة جميع نصوص وتنسيقات وإعدادات الشهادة إلى الحالة الأصلية الافتراضية وحذف التخصيصات؟')) {
            localStorage.removeItem('dudc_v3_default_settings');
            fetch('/api/reset-defaults', { method: 'POST' }).finally(() => {
              location.reload();
            });
          }
        });
      }

      function loadDefaultSettings() {
        const saved = localStorage.getItem('dudc_v3_default_settings');
        if (saved) {
          try {
            const data = JSON.parse(saved);
            applyLayoutDefaults(data);
            if (data.text_customs) {
              savedTextDefaults = data.text_customs;
              applySavedTextDefaults(savedTextDefaults);
            }
          } catch (e) {
            applyLayoutDefaults(null);
          }
        } else {
          applyLayoutDefaults(null);
        }

        // المزامنة الهادئة مع السيرفر إن وجدت إعدادات مخزنة سابقة
        fetch('/api/get-defaults')
          .then(res => res.json())
          .then(resData => {
            if (resData.success && resData.defaults) {
              const data = resData.defaults;
              if (!saved) {
                applyLayoutDefaults(data);
              }
              if (data.text_customs) {
                savedTextDefaults = data.text_customs;
                applySavedTextDefaults(savedTextDefaults);
                localStorage.setItem('dudc_v3_default_settings', JSON.stringify(data));
              }
            }
          })
          .catch(() => {});
      }

      /* ==========================================================================
         المرحلة 3: الإخراج النهائي وتصدير الحزمة
         ========================================================================== */
      function syncStage2ToStage3() {
        const name = document.getElementById('valApplicantName').textContent.trim() || 'محمد إبراهيم محمد حسن';
        const center = document.getElementById('valCenter').textContent.trim() || 'نبروه';
        const area = document.getElementById('valArea').textContent.trim() || '-- م²';

        document.getElementById('stage3CitizenName').textContent = name;
        document.getElementById('stage3Center').textContent = center;
        document.getElementById('stage3Area').textContent = area;

        document.getElementById('lblFilePdf').textContent = `${name}.pdf (الشهادة الرسمية مقفولة A4)`;
        document.getElementById('lblFileDocx').textContent = `${name}.docx (الشهادة الرسمية Word)`;
        document.getElementById('lblFileJson').textContent = `${name}_session.json (ملف الجلسة الكامل)`;
      }

      // منطق الاعتماد السحابي الرسمي للطباعة والتصدير (Stage 3)
      let isCertificateConfirmed = false;

      function resetConfirmationState() {
        isCertificateConfirmed = false;
        const card = document.getElementById('cardOfficialConfirmation');
        const btn = document.getElementById('btnConfirmIssuance');
        const icon = document.getElementById('confirmBtnIcon');
        const text = document.getElementById('confirmBtnText');
        const msg = document.getElementById('confirmationStatusMsg');
        const grid = document.getElementById('deliveryActionsGrid');
        const topBadge = document.querySelector('.stage3-layout .badge-pass, .stage3-layout .badge-pending');

        if (card) {
          card.style.borderColor = '#0284c7';
          card.style.background = 'rgba(15, 23, 42, 0.75)';
        }
        if (btn) {
          btn.disabled = false;
          btn.style.background = 'linear-gradient(135deg, #0284c7, #0369a1)';
          btn.style.cursor = 'pointer';
        }
        if (icon) icon.textContent = '🔒';
        if (text) text.textContent = 'تأكيد واعتماد البيانات للطباعة والتصدير الرسمي';
        if (msg) { msg.style.display = 'none'; msg.textContent = ''; }
        if (grid) {
          grid.style.opacity = '0.45';
          grid.style.pointerEvents = 'none';
          grid.style.filter = 'grayscale(0.7)';
        }
        if (topBadge) {
          topBadge.textContent = '⏳ في انتظار الاعتماد';
          topBadge.className = 'badge-pending';
        }
      }

      document.getElementById('btnConfirmIssuance').addEventListener('click', () => {
        if (!activeParcel || !activeParcel.security_token) {
          alert('⚠️ تنبيه: لم يتم توليد كود الأمان للشهادة بعد!');
          return;
        }

        const btn = document.getElementById('btnConfirmIssuance');
        const icon = document.getElementById('confirmBtnIcon');
        const text = document.getElementById('confirmBtnText');
        const msg = document.getElementById('confirmationStatusMsg');
        const card = document.getElementById('cardOfficialConfirmation');
        const grid = document.getElementById('deliveryActionsGrid');
        const topBadge = document.querySelector('.stage3-layout .badge-pending, .stage3-layout .badge-pass');

        btn.disabled = true;
        icon.textContent = '⏳';
        text.textContent = 'جاري الاعتماد السحابي وتوثيق السجل...';

        fetch('/api/confirm-issuance', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: activeParcel.security_token })
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            isCertificateConfirmed = true;
            icon.textContent = '✔️';
            text.textContent = 'تم اعتماد الشهادة رسمياً في السجل السحابي للطباعة والتسليم';
            btn.style.background = 'linear-gradient(135deg, #059669, #047857)';
            btn.style.cursor = 'default';
            btn.style.boxShadow = 'none';

            if (card) {
              card.style.borderColor = '#10b981';
              card.style.background = 'rgba(6, 95, 70, 0.2)';
            }
            if (msg) {
              msg.style.display = 'block';
              msg.innerHTML = `✔ تم توثيق الإصدار الرسمي في السجل السحابي بتاريخ: <strong>${data.confirmed_at}</strong>`;
            }
            if (grid) {
              grid.style.opacity = '1';
              grid.style.pointerEvents = 'auto';
              grid.style.filter = 'none';
            }
            if (topBadge) {
              topBadge.textContent = '✔ معتمد رسمي للطباعة والتصدير';
              topBadge.className = 'badge-pass';
            }
          } else {
            btn.disabled = false;
            icon.textContent = '🔒';
            text.textContent = 'إعادة محاولة الاعتماد السحابي';
            alert('خطأ أثناء الاعتماد السحابي: ' + (data.error || 'تعذر الاتصال'));
          }
        })
        .catch(err => {
          btn.disabled = false;
          icon.textContent = '🔒';
          text.textContent = 'إعادة محاولة الاعتماد';
          alert('خطأ في الاتصال بالسيرفر: ' + err.message);
        });
      });

      // طباعة الـ PDF الفورية
      function triggerPdfPrint() {
        switchStage(2);
        setTimeout(() => window.print(), 150);
      }

      document.getElementById('btnActionPrintPdf').addEventListener('click', triggerPdfPrint);
      const btnPrintCertQuickEl = document.getElementById('btnPrintCertQuick');
      if (btnPrintCertQuickEl) {
        btnPrintCertQuickEl.addEventListener('click', triggerPdfPrint);
      }

      // تصدير حزمة المشروع الكاملة من الباك إند
      document.getElementById('btnActionExportPackage').addEventListener('click', () => {
        if (!activeParcel) {
          alert('يرجى تحميل ملف الرفع المساحي أولاً');
          return;
        }

        const citizenName = document.getElementById('valApplicantName').textContent.trim() || activeParcel.applicant_name;
        const payload = {
          parcel_index: 0,
          applicant_name: citizenName,
          survey_technician: document.getElementById('selSurveyTech').value,
          system_officer: document.getElementById('selSysOfficer').value,
          croquis_base64: document.getElementById('imgCroquis').src,
          satellite_base64: document.getElementById('imgSatellite').src,
          session_data: {
            applicant_name: citizenName,
            receipt_no: document.getElementById('valReceiptNo').textContent.trim(),
            national_id: document.getElementById('valNationalId').textContent.trim(),
            district: document.getElementById('valCenter').textContent.trim(),
            area: document.getElementById('valArea').textContent.trim(),
            sliders: {
              margin: rngMargin.value, gapHeader: rngGapHeader.value, gapApplicant: rngGapApplicant.value,
              gapCoords: rngGapCoords.value, gapImages: rngGapImages.value, tablePad: rngTablePad.value,
              imageHeight: rngImageHeight.value
            },
            watermark: {
              active: chkWatermarkActive.checked, opacity: rngWmOpacity.value, angle: rngWmAngle.value, size: rngWmSize.value
            }
          }
        };

        showLoading('تصدير حزمة المشروع الكاملة', `جاري إنشاء ملفات PDF و Word DOCX لمجلد المواطن: ${citizenName}`);
        fetch('/api/export-package', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        }).then(res => res.json()).then(data => {
          hideLoading();
          if (data.success) {
            alert(`✔ تم تصدير حزمة المشروع بنجاح داخل مجلد العميل:\n${data.folder_path}`);
            // فتح المجلد تلقائياً
            fetch('/api/open-folder', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ folder_path: data.folder_path })
            });
          } else {
            showLoadingError('خطأ في تصدير الحزمة', data.error || 'تعذر التصدير');
          }
        }).catch(err => {
          showLoadingError('خطأ في الاتصال أثناء التصدير', err.message);
        });
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

      // التهيئة الابتدائية
      loadDefaultSettings();
      updateSpacing();
      renderWatermark();
      updateStep1State();
    });
  