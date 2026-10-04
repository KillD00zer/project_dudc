/**
 * DUDC V3.5 - Drafts & Session Management (drafts.js)
 */

      // ==========================================================================
      // ==========================================================================
      // استيراد جلسة عمل سابقة بالكامل (.json) ونظام إدارة المسودات (Drafts Box)
      // ==========================================================================
      var currentActiveDraftId = null;

      function restoreSessionFromData(rawData, draftId = null) {
        try {
          const data = (rawData.session_data && typeof rawData.session_data === 'object')
            ? Object.assign({}, rawData, rawData.session_data)
            : rawData;
          const parcelData = data.parcel || {};
          const applicantName = data.applicant_name || parcelData.applicant_name || data.name || 'مواطن بدون اسم';

          // قراءة واستخراج المركز والتحقق من القاموس الرسمي
          let distName = data.district || parcelData.district || 'نبروه';
          let distId = (data.district_id !== undefined && data.district_id !== null)
            ? data.district_id
            : parcelData.district_id;

          if (distId === undefined || distId === null) {
            const cleanDist = String(distName).trim();
            const matched = OFFICIAL_CENTERS_FALLBACK.find(([cid, cname]) => cname === cleanDist || cleanDist.includes(cname));
            if (matched) {
              distId = matched[0];
              distName = matched[1];
            } else {
              distId = 10;
              distName = 'نبروه';
            }
          }

          // تنظيف وتحويل المساحات بأمان
          const statedArea = parseFloat(toEnglishNumerals(String(data.stated_area_m2 || parcelData.stated_area_m2 || data.area || 0))) || 0;
          const calcArea = parseFloat(toEnglishNumerals(String(data.calculated_area_m2 || parcelData.calculated_area_m2 || data.area || 0))) || statedArea;

          // بناء كائن activeParcel المتكامل
          activeParcel = {
            parcel_id: parcelData.parcel_id || data.parcel_id || '0',
            applicant_name: applicantName,
            national_id: toEnglishNumerals(String(data.national_id || parcelData.national_id || '')),
            receipt_no: toEnglishNumerals(String(data.receipt_no || parcelData.receipt_no || '')),
            district: distName,
            district_id: distId,
            district_matched: true,
            village: data.village || parcelData.village || '',
            address: data.address || parcelData.address || '',
            stated_area_m2: statedArea,
            calculated_area_m2: calcArea,
            order_no: data.order_no || parcelData.order_no || '2605s',
            deal_type: data.deal_type || parcelData.deal_type || 'انشاء',
            site_desc: data.site_desc || parcelData.site_desc || 'موقع عينة تجريبية',
            security_token: data.security_token || data.token || parcelData.security_token || null,
            survey_technician: data.survey_technician || parcelData.survey_technician || 'محمد ابراهيم بدير',
            system_officer: data.system_officer || parcelData.system_officer || 'شريف محمد',
            segments: data.segments || parcelData.segments || [],
            boundaries: data.boundaries || parcelData.boundaries || {},
            vertices: data.vertices || parcelData.vertices || []
          };

          // 1. استعادة مسؤولي الخطوة 1
          const selTech = document.getElementById('selSurveyTech');
          if (selTech && activeParcel.survey_technician) {
            let found = false;
            for (let opt of selTech.options) {
              if (opt.value === activeParcel.survey_technician) { opt.selected = true; found = true; break; }
            }
            if (!found) {
              selTech.add(new Option(activeParcel.survey_technician, activeParcel.survey_technician, true, true));
            }
            selTech.value = activeParcel.survey_technician;
          }

          const selOff = document.getElementById('selSysOfficer');
          if (selOff && activeParcel.system_officer) {
            let found = false;
            for (let opt of selOff.options) {
              if (opt.value === activeParcel.system_officer) { opt.selected = true; found = true; break; }
            }
            if (!found) {
              selOff.add(new Option(activeParcel.system_officer, activeParcel.system_officer, true, true));
            }
            selOff.value = activeParcel.system_officer;
          }

          updateStep1State();

          // 2. إظهار قسم نتائج الرفع
          const resultsSec = document.getElementById('surveyResultsSection');
          if (resultsSec) {
            resultsSec.style.display = 'flex';
            resultsSec.style.flexDirection = 'column';
          }

          // 3. ملء بيانات المرحلة 1
          document.getElementById('resApplicantName').textContent = activeParcel.applicant_name;
          document.getElementById('resNationalId').textContent = activeParcel.national_id || '--';
          document.getElementById('resReceiptNo').textContent = activeParcel.receipt_no || '--';
          document.getElementById('resStatedArea').textContent = `${activeParcel.stated_area_m2.toFixed(2)} م²`;
          document.getElementById('resCalcArea').textContent = `${activeParcel.calculated_area_m2.toFixed(2)} م²`;
          document.getElementById('resDeltaArea').textContent = '0.00 م²';

          const badge = document.getElementById('badgeTolerance');
          if (badge) {
            badge.className = 'badge-pass';
            badge.textContent = draftId ? '✔ مسودة مسترجعة' : '✔ متطابق قانونياً (جلسة مستوردة معتمدة)';
          }

          renderDistrictSelector(activeParcel);

          // 4. استعادة الصورتين إن وُجدتا
          const croqSrc = data.croquis_base64 || data.session_data?.croquis_base64 || data.parcel?.croquis_base64 || data.croquis_url || data.croquis || (parcelData.croquis_url ? parcelData.croquis_url : null);
          if (croqSrc) {
            const cImg1 = document.getElementById('stage1CroquisImg');
            const cImg2 = document.getElementById('imgCroquis');
            if (cImg1) cImg1.src = croqSrc;
            if (cImg2) cImg2.src = croqSrc;
            customUploadedImages.croquis = croqSrc;
            if (activeParcel) activeParcel.croquis_base64 = croqSrc;
          }

          const satSrc = data.satellite_base64 || data.session_data?.satellite_base64 || data.parcel?.satellite_base64 || data.satellite_url || data.satellite || (parcelData.satellite_url ? parcelData.satellite_url : null);
          if (satSrc) {
            const sImg1 = document.getElementById('stage1SatImg');
            const sImg2 = document.getElementById('imgSatellite');
            if (sImg1) sImg1.src = satSrc;
            if (sImg2) sImg2.src = satSrc;
            customUploadedImages.satellite = satSrc;
            if (activeParcel) activeParcel.satellite_base64 = satSrc;
          }

          // 5. استعادة جدول الأضلاع
          if (activeParcel.segments && activeParcel.segments.length > 0) {
            buildSegmentsTable(activeParcel.segments);
          } else if (data.boundaries && typeof data.boundaries === 'object') {
            activeParcel.segments = [
              { from_point: 1, to_point: 2, direction: 'north', neighbor: data.boundaries.north?.neighbor || '', length_m: data.boundaries.north?.length_m || 0 },
              { from_point: 2, to_point: 3, direction: 'east', neighbor: data.boundaries.east?.neighbor || '', length_m: data.boundaries.east?.length_m || 0 },
              { from_point: 3, to_point: 4, direction: 'south', neighbor: data.boundaries.south?.neighbor || '', length_m: data.boundaries.south?.length_m || 0 },
              { from_point: 4, to_point: 1, direction: 'west', neighbor: data.boundaries.west?.neighbor || '', length_m: data.boundaries.west?.length_m || 0 }
            ];
            buildSegmentsTable(activeParcel.segments);
          }

          // 6. استعادة إعدادات السلايدرات والمسافات والعلامة المائية
          const sliders = data.sliders || data;
          const elMargin = document.getElementById('rngMargin');
          const elGapHeader = document.getElementById('rngGapHeader');
          const elGapApplicant = document.getElementById('rngGapApplicant');
          const elGapCoords = document.getElementById('rngGapCoords');
          const elGapImages = document.getElementById('rngGapImages');
          const elTablePad = document.getElementById('rngTablePad');
          const elImageHeight = document.getElementById('rngImageHeight');

          if (sliders.margin !== undefined || sliders.margin_mm !== undefined) { if (elMargin) elMargin.value = sliders.margin ?? sliders.margin_mm; }
          if (sliders.gapHeader !== undefined || sliders.gap_header !== undefined) { if (elGapHeader) elGapHeader.value = sliders.gapHeader ?? sliders.gap_header; }
          if (sliders.gapApplicant !== undefined || sliders.gap_applicant !== undefined) { if (elGapApplicant) elGapApplicant.value = sliders.gapApplicant ?? sliders.gap_applicant; }
          if (sliders.gapCoords !== undefined || sliders.gap_coords !== undefined) { if (elGapCoords) elGapCoords.value = sliders.gapCoords ?? sliders.gap_coords; }
          if (sliders.gapImages !== undefined || sliders.gap_images !== undefined) { if (elGapImages) elGapImages.value = sliders.gapImages ?? sliders.gap_images; }
          if (sliders.tablePad !== undefined || sliders.table_pad !== undefined) { if (elTablePad) elTablePad.value = sliders.tablePad ?? sliders.table_pad; }
          if (sliders.imageHeight !== undefined || sliders.image_height !== undefined) { if (elImageHeight) elImageHeight.value = sliders.imageHeight ?? sliders.image_height; }

          const wm = data.watermark || data;
          const elWmActive = document.getElementById('chkWatermarkActive');
          const elWmOpacity = document.getElementById('rngWmOpacity');
          const elWmAngle = document.getElementById('rngWmAngle');
          const elWmSize = document.getElementById('rngWmSize');

          if (wm.active !== undefined || wm.wm_active !== undefined) { if (elWmActive) elWmActive.checked = Boolean(wm.active ?? wm.wm_active); }
          if (wm.opacity !== undefined || wm.wm_opacity !== undefined) { if (elWmOpacity) elWmOpacity.value = wm.opacity ?? wm.wm_opacity; }
          if (wm.angle !== undefined || wm.wm_angle !== undefined) { if (elWmAngle) elWmAngle.value = wm.angle ?? wm.wm_angle; }
          if (wm.size !== undefined || wm.wm_size !== undefined) { if (elWmSize) elWmSize.value = wm.size ?? wm.wm_size; }

          if (typeof updateSpacing === 'function') updateSpacing();
          if (typeof renderWatermark === 'function') renderWatermark();

          // 7. استعادة تخصيصات النصوص إن وجدت
          if (data.text_customs) {
            savedTextDefaults = data.text_customs;
            applySavedTextDefaults(data.text_customs);
          }

          // 8. المزامنة إلى استوديو التحرير (Stage 2)
          syncStage1ToStage2();

          if (data.deal_type) document.getElementById('valDealType').textContent = data.deal_type;
          if (data.site_desc) document.getElementById('valSiteDesc').textContent = data.site_desc;
          if (data.order_no) document.getElementById('valOrderNo').textContent = data.order_no;

          // 9. مزامنة الجلسة مع الباك إند
          fetch('/api/restore-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              parcel: activeParcel,
              croquis_base64: croqSrc || '',
              satellite_base64: satSrc || ''
            })
          }).then(res => res.json()).then(resData => {
            if (resData.croquis_url && (!croqSrc || croqSrc.length < 20)) {
              const c1 = document.getElementById('stage1CroquisImg');
              const c2 = document.getElementById('imgCroquis');
              if (c1) c1.src = resData.croquis_url;
              if (c2) c2.src = resData.croquis_url;
            }
            if (resData.satellite_url && (!satSrc || satSrc.length < 20)) {
              const s1 = document.getElementById('stage1SatImg');
              const s2 = document.getElementById('imgSatellite');
              if (s1) s1.src = resData.satellite_url;
              if (s2) s2.src = resData.satellite_url;
            }
          }).catch(() => {});

          currentActiveDraftId = draftId;

          // 10. الانتقال مباشرة إلى استوديو التحرير مع إشعار النجاح
          switchStage(2);
          hideLoading();

          const label = draftId ? `✔ تم استرجاع مسودة (${activeParcel.applicant_name}) بنجاح!` : `✔ تم استيراد جلسة (${activeParcel.applicant_name}) بنجاح!`;
          showSaveToast(label);

        } catch (err) {
          hideLoading();
          alert('⚠️ خطأ في قراءة ملف الجلسة أو المسودة: ' + err.message);
        }
      }

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

          showLoading('استيراد جلسة سابقة', `جاري قراءة واستعادة ملف الجلسة: ${file.name}`);

          const reader = new FileReader();
          reader.onload = (event) => {
            try {
              const rawData = JSON.parse(event.target.result);
              restoreSessionFromData(rawData, null);
            } catch (err) {
              hideLoading();
              alert('⚠️ خطأ في تحليل ملف الجلسة JSON: ' + err.message);
            }
          };

          reader.onerror = () => {
            hideLoading();
            alert('⚠️ فشل قراءة الملف من القرص.');
          };

          reader.readAsText(file, 'utf-8');
        });
      }

      // --------------------------------------------------------------------------
      // منطق حفظ واسترجاع وإدارة المسودات (Drafts Queue Management)
      // --------------------------------------------------------------------------
      function getDraftPayload() {
        if (!activeParcel) return null;
        const citizenName = document.getElementById('valApplicantName')?.textContent?.trim() || activeParcel.applicant_name || 'بدون اسم';
        const centerName = document.getElementById('valCenter')?.textContent?.trim() || activeParcel.district || '';
        const areaVal = document.getElementById('valArea')?.textContent?.trim() || (activeParcel.calculated_area_m2 ? `${activeParcel.calculated_area_m2} م²` : '--');

        function extractElementBase64(imgEl, fallbackVal) {
          if (fallbackVal && typeof fallbackVal === 'string' && fallbackVal.startsWith('data:image/')) {
            return fallbackVal;
          }
          if (imgEl) {
            if (imgEl.src && imgEl.src.startsWith('data:image/')) return imgEl.src;
            try {
              if (imgEl.complete && imgEl.naturalWidth > 0) {
                const canvas = document.createElement('canvas');
                canvas.width = imgEl.naturalWidth;
                canvas.height = imgEl.naturalHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(imgEl, 0, 0);
                const isPng = (imgEl.src || '').toLowerCase().includes('.png');
                return canvas.toDataURL(isPng ? 'image/png' : 'image/jpeg', 0.95);
              }
            } catch(e) {}
            if (imgEl.src && !imgEl.src.endsWith('/') && imgEl.src !== window.location.href) {
              return imgEl.src;
            }
          }
          return fallbackVal || '';
        }

        const croqEl = document.getElementById('imgCroquis') || document.getElementById('stage1CroquisImg');
        const croqSrc = extractElementBase64(croqEl, customUploadedImages.croquis || activeParcel.croquis_base64 || (document.getElementById('stage1CroquisImg')?.src || ''));

        const satEl = document.getElementById('imgSatellite') || document.getElementById('stage1SatImg');
        const satSrc = extractElementBase64(satEl, customUploadedImages.satellite || activeParcel.satellite_base64 || (document.getElementById('stage1SatImg')?.src || ''));

        return {
          draft_id: currentActiveDraftId,
          applicant_name: citizenName,
          district: centerName,
          area: areaVal,
          parcel: activeParcel,
          croquis_base64: croqSrc,
          satellite_base64: satSrc,
          session_data: {
            applicant_name: citizenName,
            receipt_no: document.getElementById('valReceiptNo')?.textContent?.trim() || activeParcel.receipt_no || '',
            national_id: document.getElementById('valNationalId')?.textContent?.trim() || activeParcel.national_id || '',
            district: centerName,
            village: document.getElementById('valVillage')?.textContent?.trim() || activeParcel.village || '',
            address: document.getElementById('valAddress')?.textContent?.trim() || activeParcel.address || '',
            area: areaVal,
            deal_type: document.getElementById('valDealType')?.textContent?.trim() || activeParcel.deal_type || 'إنشاء',
            site_desc: document.getElementById('valSiteDesc')?.textContent?.trim() || activeParcel.site_desc || 'أرض فضاء',
            order_no: document.getElementById('valOrderNo')?.textContent?.trim() || activeParcel.order_no || '',
            survey_technician: document.getElementById('selSurveyTech')?.value || activeParcel.survey_technician || '',
            system_officer: document.getElementById('selSysOfficer')?.value || activeParcel.system_officer || '',
            security_token: activeParcel.security_token || '',
            parcel: activeParcel,
            croquis_base64: croqSrc,
            satellite_base64: satSrc,
            text_customs: typeof collectAllTextCustomizations === 'function' ? collectAllTextCustomizations() : null,
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
      }

      function toArabicNumerals(val) {
        if (val === null || val === undefined) return '';
        return toEnglishNumerals(val);
      }

      function toEnglishNumerals(val) {
        if (val === null || val === undefined) return '';
        return String(val)
          .replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d))
          .replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d));
      }

      function syncDomToActiveParcel() {
        if (!activeParcel) return;
        
        const nameEl = document.getElementById('valApplicantName');
        if (nameEl) {
          const val = nameEl.textContent.trim();
          if (val && val !== 'لا يوجد بيانات متاحة' && val !== '--') {
            activeParcel.applicant_name = val;
            const r1 = document.getElementById('resApplicantName');
            if (r1) r1.textContent = val;
            const s3 = document.getElementById('stage3CitizenName');
            if (s3) s3.textContent = val;
          }
        }

        const rcpEl = document.getElementById('valReceiptNo');
        if (rcpEl) {
          const val = rcpEl.textContent.trim();
          if (val && val !== 'لا يوجد بيانات متاحة' && val !== '--') {
            activeParcel.receipt_no = toEnglishNumerals(val);
            const r1 = document.getElementById('resReceiptNo');
            if (r1) r1.textContent = val;
          }
        }

        const nidEl = document.getElementById('valNationalId');
        if (nidEl) {
          const val = nidEl.textContent.trim();
          if (val && val !== 'لا يوجد بيانات متاحة' && val !== '--') {
            activeParcel.national_id = toEnglishNumerals(val);
            const r1 = document.getElementById('resNationalId');
            if (r1) r1.textContent = val;
          }
        }

        const centerEl = document.getElementById('valCenter');
        if (centerEl) {
          const val = centerEl.textContent.trim();
          if (val && val !== 'لا يوجد بيانات متاحة' && val !== '--') {
            activeParcel.district = val;
            const s3 = document.getElementById('stage3Center');
            if (s3) s3.textContent = val;
          }
        }

        const vilEl = document.getElementById('valVillage');
        if (vilEl) {
          const val = vilEl.textContent.trim();
          if (val && val !== '--------' && val !== '--') {
            activeParcel.village = val;
          }
        }

        const addrEl = document.getElementById('valAddress');
        if (addrEl) {
          const val = addrEl.textContent.trim();
          if (val && val !== 'لا يوجد بيانات متاحة' && val !== '--') {
            activeParcel.address = val;
          }
        }

        const orderEl = document.getElementById('valOrderNo');
        if (orderEl) {
          const val = orderEl.textContent.trim();
          if (val && val !== 'لا يوجد بيانات متاحة' && val !== '--') {
            activeParcel.order_no = toEnglishNumerals(val.replace(/s$/i, '').trim());
            activeParcel.request_no = activeParcel.order_no;
          }
        }

        const dealEl = document.getElementById('valDealType');
        if (dealEl) {
          const val = dealEl.textContent.trim();
          if (val && val !== '--') {
            activeParcel.deal_type = val;
            activeParcel.transaction_type = val;
          }
        }

        const siteEl = document.getElementById('valSiteDesc');
        if (siteEl) {
          const val = siteEl.textContent.trim();
          if (val && val !== '--') {
            activeParcel.site_desc = val;
            activeParcel.site_status = val;
          }
        }

        const techEl = document.getElementById('selSurveyTech');
        if (techEl && techEl.value) {
          activeParcel.survey_technician = techEl.value;
          const s = document.getElementById('sigTech');
          if (s) s.textContent = `أ / ${techEl.value}`;
        }

        const offEl = document.getElementById('selSysOfficer');
        if (offEl && offEl.value) {
          activeParcel.system_officer = offEl.value;
          const s = document.getElementById('sigGis');
          if (s) s.textContent = `أ / ${offEl.value}`;
        }
      }

      function showAutoSaveIndicator(state) {
        const el = document.getElementById('draftAutoSaveStatus');
        if (!el) return;
        if (state === 'saving') {
          el.style.display = 'block';
          el.style.color = '#38bdf8';
          el.innerHTML = '<span>⏳ جاري حفظ التعديل بالمسودة...</span>';
        } else if (state === 'saved') {
          el.style.display = 'block';
          el.style.color = '#10b981';
          const timeStr = new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          el.innerHTML = `<span>✔ تم تحديث المسودة تلقائياً (${timeStr})</span>`;
        } else if (state === 'error') {
          el.style.display = 'block';
          el.style.color = '#ef4444';
          el.innerHTML = '<span>⚠️ تعذر حفظ التعديل تلقائياً</span>';
        }
      }

      var draftAutoSaveTimer = null;
      function scheduleDraftAutoSave() {
        if (!activeParcel) return;
        syncDomToActiveParcel();
        if (currentActiveDraftId) {
          showAutoSaveIndicator('saving');
          clearTimeout(draftAutoSaveTimer);
          draftAutoSaveTimer = setTimeout(() => {
            saveCurrentDraft(false);
          }, 350);
        }
      }

      function saveCurrentDraft(showFeedback = true) {
        if (!activeParcel) {
          if (showFeedback) alert('⚠️ يرجى تحميل ملف الرفع المساحي أو بيانات المعاملة أولاً قبل الحفظ كمسودة.');
          return;
        }

        syncDomToActiveParcel();
        const payload = getDraftPayload();
        if (!payload) return;

        if (!showFeedback) showAutoSaveIndicator('saving');

        fetch('/api/save-draft', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            currentActiveDraftId = data.draft_id;
            refreshDraftsBadge();
            showAutoSaveIndicator('saved');
            if (showFeedback) {
              showSaveToast(`✔ تم حفظ (${payload.applicant_name}) في صندوق مسودات اليوم`);
            }
          } else {
            showAutoSaveIndicator('error');
            if (showFeedback) {
              alert('خطأ في حفظ المسودة: ' + (data.error || 'تعذر الحفظ'));
            }
          }
        })
        .catch(err => {
          showAutoSaveIndicator('error');
          if (showFeedback) {
            alert('خطأ في الاتصال أثناء حفظ المسودة: ' + err.message);
          }
        });
      }

      function refreshDraftsBadge() {
        fetch('/api/list-drafts')
          .then(res => res.json())
          .then(data => {
            const badge = document.getElementById('draftsBadgeCount');
            const modalBadge = document.getElementById('draftsModalBadge');
            const count = data.count || 0;
            if (badge) {
              if (count > 0) {
                badge.textContent = count;
                badge.style.display = 'inline-block';
              } else {
                badge.style.display = 'none';
              }
            }
            if (modalBadge) {
              modalBadge.textContent = `${count} مسودات`;
            }
          })
          .catch(() => {});
      }

      function openDraftsModal() {
        const modal = document.getElementById('draftsModalBackdrop');
        const container = document.getElementById('draftsListContainer');
        if (!modal || !container) return;

        container.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--text-muted);">⏳ جاري تحميل قائمة المسودات...</div>';
        modal.style.display = 'flex';

        fetch('/api/list-drafts')
          .then(res => res.json())
          .then(data => {
            const drafts = data.drafts || [];
            refreshDraftsBadge();
            if (drafts.length === 0) {
              container.innerHTML = `
                <div style="text-align: center; padding: 36px 20px; color: var(--text-muted); background: rgba(0,0,0,0.2); border-radius: 8px;">
                  <span style="font-size: 38px; display: block; margin-bottom: 10px;">📭</span>
                  <strong style="color: #cbd5e1; font-size: 14px;">صندوق المسودات فارغ</strong>
                  <p style="font-size: 11px; margin-top: 6px;">لا توجد أي شهادات محفوظة كمسودات حالياً. يمكنك استخدام زر "حفظ كمسودة" في أي وقت لحفظ الشهادات غير المكتملة.</p>
                </div>
              `;
              return;
            }

            container.innerHTML = '';
            drafts.forEach(d => {
              const item = document.createElement('div');
              item.style.cssText = `
                display: flex; justify-content: space-between; align-items: center; gap: 12px;
                background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 8px; padding: 10px 14px; transition: all 0.2s ease;
              `;
              item.onmouseenter = () => item.style.borderColor = 'rgba(245, 158, 11, 0.6)';
              item.onmouseleave = () => item.style.borderColor = 'rgba(56, 189, 248, 0.2)';

              const isCurrent = currentActiveDraftId === d.draft_id;

              item.innerHTML = `
                <div style="display: flex; flex-direction: column; gap: 4px; flex: 1;">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <strong style="color: #ffffff; font-size: 13px;">${d.applicant_name}</strong>
                    <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-size: 10.5px; padding: 1px 7px; border-radius: 6px; font-weight: bold;">
                      🏛️ ${d.district}
                    </span>
                    ${isCurrent ? '<span style="background: rgba(16, 185, 129, 0.2); color: #34d399; font-size: 10px; padding: 1px 6px; border-radius: 6px; font-weight: bold;">نشطة الآن</span>' : ''}
                  </div>
                  <div style="font-size: 11px; color: var(--text-muted); display: flex; gap: 14px;">
                    <span>📐 المساحة: <strong style="color: #94a3b8;">${d.area}</strong></span>
                    <span>🕒 حُفظت في: <strong style="color: #94a3b8;">${d.saved_at}</strong></span>
                  </div>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                  <button class="btn btn-green btn-load-draft" data-id="${d.draft_id}" style="padding: 6px 12px; font-size: 11.5px; gap: 4px;">
                    <span>▶</span> استكمال
                  </button>
                  <button class="btn btn-glass btn-delete-draft" data-id="${d.draft_id}" data-name="${d.applicant_name}" style="padding: 6px 10px; font-size: 11.5px; color: #ef4444; border-color: rgba(239, 68, 68, 0.3);">
                    <span>🗑️</span>
                  </button>
                </div>
              `;
              container.appendChild(item);
            });

            // Bind buttons
            container.querySelectorAll('.btn-load-draft').forEach(b => {
              b.addEventListener('click', () => {
                loadDraftById(b.getAttribute('data-id'));
              });
            });
            container.querySelectorAll('.btn-delete-draft').forEach(b => {
              b.addEventListener('click', () => {
                deleteDraftById(b.getAttribute('data-id'), b.getAttribute('data-name'));
              });
            });
          })
          .catch(err => {
            container.innerHTML = `<div style="color: #ef4444; text-align: center; padding: 20px;">خطأ في قراءة المسودات: ${err.message}</div>`;
          });
      }

      function loadDraftById(draftId) {
        showLoading('استرجاع المسودة', 'جاري جلب بيانات الشهادة والصور وإعادة ضبط الاستوديو...');
        fetch('/api/load-draft', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ draft_id: draftId })
        })
        .then(res => res.json())
        .then(data => {
          if (data.success && data.draft) {
            document.getElementById('draftsModalBackdrop').style.display = 'none';
            if (data.croquis_url && !data.draft.croquis_base64) data.draft.croquis_base64 = data.croquis_url;
            if (data.satellite_url && !data.draft.satellite_base64) data.draft.satellite_base64 = data.satellite_url;
            restoreSessionFromData(data.draft, data.draft_id);
          } else {
            hideLoading();
            alert('تعذر استرجاع المسودة: ' + (data.error || 'غير موجودة'));
          }
        })
        .catch(err => {
          hideLoading();
          alert('خطأ في الاتصال أثناء استرجاع المسودة: ' + err.message);
        });
      }

      function deleteDraftById(draftId, name) {
        if (!confirm(`هل أنت متأكد من حذف مسودة المعاملة (${name}) نهائياً من صندوق المسودات؟`)) {
          return;
        }

        fetch('/api/delete-draft', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ draft_id: draftId })
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            if (currentActiveDraftId === draftId) {
              currentActiveDraftId = null;
            }
            openDraftsModal(); // Refresh modal
            refreshDraftsBadge();
            showSaveToast(`✔ تم حذف مسودة (${name}) بنجاح`);
          } else {
            alert('تعذر حذف المسودة: ' + (data.error || 'غير معروف'));
          }
        })
        .catch(err => {
          alert('خطأ في الاتصال أثناء الحذف: ' + err.message);
        });
      }

      // ربط أزرار المسودات
      const btnOpenDraftsBox = document.getElementById('btnOpenDraftsBox');
      if (btnOpenDraftsBox) btnOpenDraftsBox.addEventListener('click', openDraftsModal);

      const btnCloseDraftsModal = document.getElementById('btnCloseDraftsModal');
      if (btnCloseDraftsModal) btnCloseDraftsModal.addEventListener('click', () => {
        document.getElementById('draftsModalBackdrop').style.display = 'none';
      });

      const btnCloseDraftsModalBottom = document.getElementById('btnCloseDraftsModalBottom');
      if (btnCloseDraftsModalBottom) btnCloseDraftsModalBottom.addEventListener('click', () => {
        document.getElementById('draftsModalBackdrop').style.display = 'none';
      });

      const btnSaveToDrafts = document.getElementById('btnSaveToDrafts');
      if (btnSaveToDrafts) btnSaveToDrafts.addEventListener('click', () => saveCurrentDraft(true));

      const btnQuickSaveDraft = document.getElementById('btnQuickSaveDraft');
      if (btnQuickSaveDraft) btnQuickSaveDraft.addEventListener('click', () => saveCurrentDraft(true));

      // --------------------------------------------------------------------------
      // نظام فحص وتحديث المنظومة التلقائي من GitHub (System Updater Logic)
      // --------------------------------------------------------------------------
      function escapeHtml(str) {
        if (!str) return '';
        return String(str)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#039;');
      }

      window.openUpdateModal = function() {
        const modal = document.getElementById('updateModalBackdrop');
        if (modal) modal.style.display = 'flex';
        fetchUpdateInfo(false);
      };

      window.closeUpdateModal = function() {
        const modal = document.getElementById('updateModalBackdrop');
        if (modal) modal.style.display = 'none';
      };

      window.fetchUpdateInfo = function(forceRefresh = false) {
        const checkingState = document.getElementById('updateCheckingState');
        const upToDateState = document.getElementById('updateUpToDateState');
        const availableState = document.getElementById('updateAvailableState');
        const errorState = document.getElementById('updateErrorState');
        const applyingState = document.getElementById('updateApplyingState');
        const successState = document.getElementById('updateSuccessState');
        const statusBadge = document.getElementById('updateModalStatusBadge');
        const btnExecutePull = document.getElementById('btnExecutePull');
        const updateBadge = document.getElementById('updateAvailableBadge');

        // Reset state displays
        if (checkingState) checkingState.style.display = 'block';
        if (upToDateState) upToDateState.style.display = 'none';
        if (availableState) availableState.style.display = 'none';
        if (errorState) errorState.style.display = 'none';
        if (applyingState) applyingState.style.display = 'none';
        if (successState) successState.style.display = 'none';
        if (btnExecutePull) btnExecutePull.style.display = 'none';

        if (statusBadge) {
          statusBadge.textContent = 'جارٍ الفحص...';
          statusBadge.style.color = '#38bdf8';
          statusBadge.style.borderColor = '#38bdf8';
          statusBadge.style.background = 'rgba(56, 189, 248, 0.2)';
        }

        fetch('/api/check-update')
          .then(res => res.json())
          .then(data => {
            if (checkingState) checkingState.style.display = 'none';

            if (!data.success) {
              if (errorState) errorState.style.display = 'block';
              const errElem = document.getElementById('updateErrorMsg');
              if (errElem) errElem.textContent = data.error || 'فشل الاتصال بـ GitHub';
              if (statusBadge) {
                statusBadge.textContent = 'تعذر الفحص';
                statusBadge.style.color = '#f87171';
                statusBadge.style.borderColor = '#f87171';
                statusBadge.style.background = 'rgba(239, 68, 68, 0.2)';
              }
              return;
            }

            // Update current installed commit display
            if (data.current_commit) {
              const hashElem = document.getElementById('currentCommitHash');
              const dateElem = document.getElementById('currentCommitDate');
              if (hashElem) hashElem.textContent = data.current_commit.hash || '--';
              if (dateElem) dateElem.textContent = `(${data.current_commit.date || ''})`;
            }

            if (!data.update_available) {
              if (upToDateState) upToDateState.style.display = 'block';
              if (updateBadge) updateBadge.style.display = 'none';
              if (statusBadge) {
                statusBadge.textContent = 'محدث بالكامل ✔';
                statusBadge.style.color = '#34d399';
                statusBadge.style.borderColor = '#34d399';
                statusBadge.style.background = 'rgba(16, 185, 129, 0.2)';
              }
            } else {
              // Update available!
              if (availableState) availableState.style.display = 'flex';
              if (btnExecutePull) btnExecutePull.style.display = 'inline-flex';
              if (updateBadge) updateBadge.style.display = 'inline-block';

              if (statusBadge) {
                statusBadge.textContent = `يتوفر ${data.count || 1} تحديث جديد 🚀`;
                statusBadge.style.color = '#10b981';
                statusBadge.style.borderColor = '#10b981';
                statusBadge.style.background = 'rgba(16, 185, 129, 0.25)';
              }

              const countNotice = document.getElementById('updateIncomingCountNotice');
              if (countNotice) {
                countNotice.textContent = `يوجد ${data.count || 1} تعديل منشور على GitHub بانتظار السحب والتطبيق.`;
              }

              // Render incoming commits list with subjects and bodies
              const listContainer = document.getElementById('updateCommitsList');
              if (listContainer) {
                listContainer.innerHTML = '';
                const commits = data.commits || [];
                commits.forEach((c) => {
                  const item = document.createElement('div');
                  item.style.cssText = 'background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 6px; padding: 10px 12px; display: flex; flex-direction: column; gap: 4px;';
                  
                  const headerRow = document.createElement('div');
                  headerRow.style.cssText = 'display: flex; justify-content: space-between; align-items: center; font-size: 13px; font-weight: bold; color: #38bdf8;';
                  headerRow.innerHTML = `<span>⚡ ${escapeHtml(c.subject || 'تحديث بدون عنوان')}</span> <span style="font-family: monospace; font-size: 11px; background: rgba(56, 189, 248, 0.15); padding: 1px 6px; border-radius: 4px; color: #bae6fd;">${escapeHtml(c.hash)}</span>`;
                  
                  const metaRow = document.createElement('div');
                  metaRow.style.cssText = 'font-size: 11px; color: var(--text-muted); display: flex; gap: 12px;';
                  metaRow.innerHTML = `<span>👤 ${escapeHtml(c.author || 'المطور')}</span> <span>🕒 ${escapeHtml(c.date || '')}</span>`;

                  item.appendChild(headerRow);
                  item.appendChild(metaRow);

                  // Show comments/body if present
                  if (c.body && c.body.trim()) {
                    const bodyBox = document.createElement('div');
                    bodyBox.style.cssText = 'font-size: 11.5px; color: #cbd5e1; background: rgba(0, 0, 0, 0.3); border-right: 3px solid #38bdf8; padding: 6px 10px; margin-top: 4px; border-radius: 4px; white-space: pre-wrap; line-height: 1.5; direction: rtl;';
                    bodyBox.textContent = c.body.trim();
                    item.appendChild(bodyBox);
                  }

                  listContainer.appendChild(item);
                });
              }
            }
          })
          .catch(err => {
            if (checkingState) checkingState.style.display = 'none';
            if (errorState) errorState.style.display = 'block';
            const errElem = document.getElementById('updateErrorMsg');
            if (errElem) errElem.textContent = 'خطأ بالاتصال: ' + err.message;
          });
      };

      window.applyAppUpdate = function() {
        const availableState = document.getElementById('updateAvailableState');
        const applyingState = document.getElementById('updateApplyingState');
        const successState = document.getElementById('updateSuccessState');
        const errorState = document.getElementById('updateErrorState');
        const btnExecutePull = document.getElementById('btnExecutePull');
        const statusBadge = document.getElementById('updateModalStatusBadge');

        if (availableState) availableState.style.display = 'none';
        if (applyingState) applyingState.style.display = 'block';
        if (btnExecutePull) btnExecutePull.style.display = 'none';

        if (statusBadge) {
          statusBadge.textContent = 'جارٍ التحديث...';
          statusBadge.style.color = '#38bdf8';
        }

        fetch('/api/perform-update', { method: 'POST' })
          .then(res => res.json())
          .then(data => {
            if (applyingState) applyingState.style.display = 'none';
            if (data.success) {
              if (successState) successState.style.display = 'block';
              if (statusBadge) {
                statusBadge.textContent = 'اكتمل التحديث بنجاح ✔';
                statusBadge.style.color = '#34d399';
                statusBadge.style.borderColor = '#34d399';
              }
              const detail = document.getElementById('updateSuccessDetail');
              if (detail && data.commit) {
                detail.innerHTML = `تم سحب التحديث بنجاح: <strong>${escapeHtml(data.commit.subject || '')}</strong> (<span style="font-family: monospace;">${escapeHtml(data.commit.hash || '')}</span>).<br>يرجى النقر على الزر بالأسفل لإعادة تحميل الصفحة.`;
              }
              const updateBadge = document.getElementById('updateAvailableBadge');
              if (updateBadge) updateBadge.style.display = 'none';
            } else {
              if (errorState) errorState.style.display = 'block';
              const errElem = document.getElementById('updateErrorMsg');
              if (errElem) errElem.textContent = data.error || 'تعذر استكمال التحديث.';
              if (statusBadge) {
                statusBadge.textContent = 'فشل التحديث';
                statusBadge.style.color = '#f87171';
              }
            }
          })
          .catch(err => {
            if (applyingState) applyingState.style.display = 'none';
            if (errorState) errorState.style.display = 'block';
            const errElem = document.getElementById('updateErrorMsg');
            if (errElem) errElem.textContent = 'خطأ أثناء تطبيق التحديث: ' + err.message;
          });
      };

      // فحص صامت في الخلفية بعد تحميل الصفحة بـ 3 ثوانٍ
      setTimeout(() => {
        fetch('/api/check-update')
          .then(res => res.json())
          .then(data => {
            if (data.success && data.update_available) {
              const badge = document.getElementById('updateAvailableBadge');
              if (badge) {
                badge.style.display = 'inline-block';
                badge.title = `يتوفر تحديث: ${data.latest_subject || ''}`;
              }
            }
          })
          .catch(() => {});
      }, 3000);

      // (قائمة المراكز الرسمية تم تعريفها بالأعلى)

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

