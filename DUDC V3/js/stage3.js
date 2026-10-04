/**
 * DUDC V3.5 - Stage 3: Official Verification & PDF Export (stage3.js)
 */

      /* ==========================================================================
         المرحلة 3: الإخراج النهائي وتصدير الحزمة
         ========================================================================== */
      function syncStage2ToStage3() {
        const name = document.getElementById('valApplicantName').textContent.trim() || activeParcel?.applicant_name || 'مواطن';
        const center = document.getElementById('valCenter').textContent.trim() || activeParcel?.district || '';
        const area = document.getElementById('valArea').textContent.trim() || '-- م²';
        const fileBase = center ? `${name}-${center}` : name;

        document.getElementById('stage3CitizenName').textContent = name;
        document.getElementById('stage3Center').textContent = center;
        document.getElementById('stage3Area').textContent = area;

        document.getElementById('lblFilePdf').textContent = `${fileBase}.pdf (الشهادة الرسمية مقفولة A4)`;
        document.getElementById('lblFileJson').textContent = `${fileBase}_session.json (ملف الجلسة الكامل)`;
      }

      // بناء صفحة HTML مستقلة كاملة التنسيقات لشهادة الـ PDF
      function buildStandaloneCertificateHtml() {
        const certPage = document.getElementById('certPage');
        if (!certPage) return '';
        
        const clone = certPage.cloneNode(true);
        // إزالة أزرار وأدوات التحرير من كود الـ PDF المطبوع
        clone.querySelectorAll('.no-print, .btn-cert-img-upload, .img-action-overlay').forEach(el => el.remove());
        
        // ضمان عمل روابط الشعارات والصور بالمسار الكامل
        const isoImg = document.getElementById('logoIso');
        const dudcImg = document.getElementById('logoDudc');
        const cloneIso = clone.querySelector('#logoIso');
        const cloneDudc = clone.querySelector('#logoDudc');
        if (isoImg && cloneIso) cloneIso.src = isoImg.src;
        if (dudcImg && cloneDudc) cloneDudc.src = dudcImg.src;

        const croqImg = document.getElementById('imgCroquis');
        const satImg = document.getElementById('imgSatellite');
        const cloneCroq = clone.querySelector('#imgCroquis');
        const cloneSat = clone.querySelector('#imgSatellite');
        if (croqImg && cloneCroq) cloneCroq.src = croqImg.src;
        if (satImg && cloneSat) cloneSat.src = satImg.src;

        let styles = '';
        document.querySelectorAll('style').forEach(s => { styles += s.innerHTML + '\n'; });
        const cssLink = `<link rel="stylesheet" href="${window.location.origin}/css/main.css">`;

        return `<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<base href="${window.location.origin}/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400&family=Cairo:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
${cssLink}
<style>
${styles}
@page { size: A4 portrait; margin: 0; }
body { background: #ffffff !important; margin: 0 !important; padding: 0 !important; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
.certificate-page { width: 100% !important; min-height: 297mm !important; max-height: 297mm !important; box-shadow: none !important; margin: 0 auto !important; border-radius: 0 !important; page-break-inside: avoid !important; }
</style>
</head>
<body style="background: #ffffff; margin: 0; padding: 0;">
${clone.outerHTML}
</body>
</html>`;
      }

      // منطق الاعتماد السحابي الرسمي للطباعة والتصدير (Stage 3)
      var isCertificateConfirmed = false;

      function resetConfirmationState() {
        isCertificateConfirmed = false;
        if (activeParcel) {
          activeParcel.security_token = null;
        }

        const certTokElem = document.getElementById('certTokenPrintVal');
        const trialBadge = document.getElementById('certTrialBadge');
        if (certTokElem) {
          certTokElem.textContent = TRIAL_TOKEN;
          certTokElem.style.color = '#64748b';
        }
        if (trialBadge) trialBadge.style.display = 'inline-block';

        const tokDisplay = document.getElementById('resSecurityToken');
        if (tokDisplay) {
          if (activeParcel && activeParcel.district_matched) {
            tokDisplay.className = 'token-trial';
            tokDisplay.innerHTML = '<span style="font-size: 10px; color: #94a3b8;">🏷️ كود تجريبي (معاينة):</span> <span style="font-family: monospace;">' + TRIAL_TOKEN + '</span>';
          }
        }

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
        if (!activeParcel || !activeParcel.district_matched) {
          alert('⚠️ تنبيه: يرجى اختيار وتحديد المركز أولاً من القائمة قبل الاعتماد!');
          return;
        }

        // 1. Immediately flush auto-save timer and sync all DOM values into activeParcel
        if (draftAutoSaveTimer) {
          clearTimeout(draftAutoSaveTimer);
          draftAutoSaveTimer = null;
        }
        syncDomToActiveParcel();

        const domName = document.getElementById('valApplicantName')?.textContent?.trim();
        const applicantName = (domName && domName !== 'لا يوجد بيانات متاحة' && domName !== '--') ? domName : (activeParcel.applicant_name || '');

        const domNid = document.getElementById('valNationalId')?.textContent?.trim();
        const nationalId = (domNid && domNid !== 'لا يوجد بيانات متاحة' && domNid !== '--') ? toEnglishNumerals(domNid) : (activeParcel.national_id || '');

        const domRcp = document.getElementById('valReceiptNo')?.textContent?.trim();
        const receiptNo = (domRcp && domRcp !== 'لا يوجد بيانات متاحة' && domRcp !== '--') ? toEnglishNumerals(domRcp) : (activeParcel.receipt_no || '');

        const domCenter = document.getElementById('valCenter')?.textContent?.trim();
        const centerName = (domCenter && domCenter !== 'لا يوجد بيانات متاحة' && domCenter !== '--') ? domCenter : (activeParcel.district || '');

        const domVil = document.getElementById('valVillage')?.textContent?.trim();
        const village = (domVil && domVil !== '--------' && domVil !== '--') ? domVil : (activeParcel.village || '');

        const domAddr = document.getElementById('valAddress')?.textContent?.trim();
        const address = (domAddr && domAddr !== 'لا يوجد بيانات متاحة' && domAddr !== '--') ? domAddr : (activeParcel.address || '');

        const domOrder = document.getElementById('valOrderNo')?.textContent?.trim();
        const orderNo = (domOrder && domOrder !== 'لا يوجد بيانات متاحة' && domOrder !== '--') ? toEnglishNumerals(domOrder.replace(/s$/i, '').trim()) : (activeParcel.order_no || '');

        const domDeal = document.getElementById('valDealType')?.textContent?.trim();
        const dealType = (domDeal && domDeal !== '--') ? domDeal : (activeParcel.deal_type || 'إنشاء');

        const domSite = document.getElementById('valSiteDesc')?.textContent?.trim();
        const siteDesc = (domSite && domSite !== '--') ? domSite : (activeParcel.site_desc || 'أرض فضاء');

        const techVal = document.getElementById('selSurveyTech')?.value || activeParcel.survey_technician || '';
        const officerVal = document.getElementById('selSysOfficer')?.value || activeParcel.system_officer || '';

        // Update activeParcel directly with the latest confirmed values
        activeParcel.applicant_name = applicantName;
        activeParcel.national_id = nationalId;
        activeParcel.receipt_no = receiptNo;
        activeParcel.district = centerName;
        activeParcel.village = village;
        activeParcel.address = address;
        activeParcel.order_no = orderNo;
        activeParcel.deal_type = dealType;
        activeParcel.site_desc = siteDesc;
        activeParcel.survey_technician = techVal;
        activeParcel.system_officer = officerVal;

        const btn = document.getElementById('btnConfirmIssuance');
        const icon = document.getElementById('confirmBtnIcon');
        const text = document.getElementById('confirmBtnText');
        const msg = document.getElementById('confirmationStatusMsg');
        const card = document.getElementById('cardOfficialConfirmation');
        const grid = document.getElementById('deliveryActionsGrid');
        const topBadge = document.querySelector('.stage3-layout .badge-pending, .stage3-layout .badge-pass');

        btn.disabled = true;
        icon.textContent = '⏳';
        text.textContent = 'جاري توليد كود الأمان الرسمي النهائي وتوثيق السجل...';

        fetch('/api/confirm-issuance', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            parcel_index: 0,
            draft_id: currentActiveDraftId,
            applicant_name: applicantName,
            national_id: nationalId,
            receipt_no: receiptNo,
            district: centerName,
            village: village,
            address: address,
            order_no: orderNo,
            deal_type: dealType,
            site_desc: siteDesc,
            survey_technician: techVal,
            system_officer: officerVal,
            parcel: activeParcel
          })
        })
        .then(res => res.json())
        .then(data => {
          if (data.success && data.token) {
            isCertificateConfirmed = true;
            activeParcel.security_token = data.token;

            // Auto-save the draft immediately with the confirmed token
            if (currentActiveDraftId) {
              saveCurrentDraft(false);
            }

            // تحديث كود الأمان على الشهادة لإزالة الكود التجريبي واستبداله بالكود الرسمي المعتمد
            const certTokElem = document.getElementById('certTokenPrintVal');
            const trialBadge = document.getElementById('certTrialBadge');
            if (certTokElem) {
              certTokElem.textContent = data.token;
              certTokElem.style.color = '#334155';
            }
            if (trialBadge) trialBadge.style.display = 'none';

            // تحديث كود التأمين في المرحلة 1
            const tokDisplay = document.getElementById('resSecurityToken');
            if (tokDisplay) {
              tokDisplay.className = 'token-active';
              tokDisplay.textContent = data.token;
            }

            // تحديث صورة الكروكي بالبصمة الرسمية (فقط إن لم تكن صورة مخصصة)
            if (data.croquis_url && !customUploadedImages.croquis) {
              const bustUrl = data.croquis_url + (data.croquis_url.includes('?') ? '&_t=' : '?_t=') + Date.now();
              const s1Croq = document.getElementById('stage1CroquisImg');
              const s2Croq = document.getElementById('imgCroquis');
              if (s1Croq) s1Croq.src = bustUrl;
              if (s2Croq) s2Croq.src = bustUrl;
            }

            icon.textContent = '✔️';
            text.textContent = 'تم اعتماد الشهادة وإصدار كود الأمان الرسمي بنجاح';
            btn.style.background = 'linear-gradient(135deg, #059669, #047857)';
            btn.style.cursor = 'default';
            btn.style.boxShadow = 'none';

            if (card) {
              card.style.borderColor = '#10b981';
              card.style.background = 'rgba(6, 95, 70, 0.2)';
            }
            if (msg) {
              msg.style.display = 'block';
              msg.innerHTML = `✔ تم إصدار كود الأمان الرسمي: <strong style="font-family: monospace; color: var(--accent-cyan); font-size: 13px;">${data.token}</strong><br>وثّق بالسجل السحابي بتاريخ: <strong>${data.confirmed_at}</strong>`;
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
            alert('خطأ أثناء الاعتماد وتوليد الكود: ' + (data.error || 'تعذر الاتصال'));
          }
        })
        .catch(err => {
          btn.disabled = false;
          icon.textContent = '🔒';
          text.textContent = 'إعادة محاولة الاعتماد';
          alert('خطأ في الاتصال بالسيرفر: ' + err.message);
        });
      });

      // طباعة الـ PDF الرسمية - متاحة حصراً بعد إتمام حفظ وتصدير المشروع
      function triggerPdfPrint() {
        if (!hasSavedCurrentPackage) {
          alert('⚠️ غير مسموح بطباعة الشهادة قبل حفظ وتصدير حزمة المشروع رسمياً!\nيرجى حفظ وتصدير حزمة المشروع أولاً.');
          switchStage(3);
          return;
        }

        switchStage(2);
        const citizenName = document.getElementById('valApplicantName').textContent.trim() || activeParcel?.applicant_name || 'مواطن';
        const center = document.getElementById('valCenter').textContent.trim() || activeParcel?.district || '';
        const prevTitle = document.title;
        const fileBase = center ? `${citizenName}-${center}` : citizenName;
        document.title = fileBase;
        setTimeout(() => {
          window.print();
          setTimeout(() => { document.title = prevTitle; }, 1200);
        }, 150);
      }

      // اعتراض اختصار الطباعة المباشر من لوحة المفاتيح (Ctrl+P / Cmd+P)
      window.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && (e.key === 'p' || e.key === 'P')) {
          if (!hasSavedCurrentPackage) {
            e.preventDefault();
            e.stopImmediatePropagation();
            alert('⚠️ غير مسموح بالطباعة قبل حفظ وتصدير حزمة المشروع رسمياً!\nيرجى الانتقال للمرحلة الثالثة وحفظ وتصدير المشروع أولاً.');
            switchStage(3);
          }
        }
      });

      // تصدير حزمة المشروع الكاملة من الباك إند
      document.getElementById('btnActionExportPackage').addEventListener('click', () => {
        if (!activeParcel) {
          alert('يرجى تحميل ملف الرفع المساحي أولاً');
          return;
        }

        const citizenName = document.getElementById('valApplicantName').textContent.trim() || activeParcel.applicant_name;
        const centerName = document.getElementById('valCenter').textContent.trim() || activeParcel.district || '';
        const fileBase = centerName ? `${citizenName}-${centerName}` : citizenName;

        const payload = {
          parcel_index: 0,
          draft_id: currentActiveDraftId,
          applicant_name: citizenName,
          district: centerName,
          certificate_html: buildStandaloneCertificateHtml(),
          survey_technician: document.getElementById('selSurveyTech').value,
          system_officer: document.getElementById('selSysOfficer').value,
          croquis_base64: document.getElementById('imgCroquis').src,
          satellite_base64: document.getElementById('imgSatellite').src,
          session_data: {
            draft_id: currentActiveDraftId,
            applicant_name: citizenName,
            receipt_no: document.getElementById('valReceiptNo').textContent.trim(),
            national_id: document.getElementById('valNationalId').textContent.trim(),
            district: centerName,
            village: document.getElementById('valVillage').textContent.trim(),
            address: document.getElementById('valAddress').textContent.trim(),
            area: document.getElementById('valArea').textContent.trim(),
            deal_type: document.getElementById('valDealType').textContent.trim(),
            site_desc: document.getElementById('valSiteDesc').textContent.trim(),
            order_no: document.getElementById('valOrderNo').textContent.trim(),
            survey_technician: document.getElementById('selSurveyTech').value,
            system_officer: document.getElementById('selSysOfficer').value,
            security_token: activeParcel.security_token || '',
            parcel: activeParcel,
            croquis_base64: document.getElementById('imgCroquis').src,
            satellite_base64: document.getElementById('imgSatellite').src,
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

        showLoading('تصدير حزمة المشروع الكاملة', `جاري إنشاء ملف PDF وحزمة المشروع لمجلد: ${fileBase}`);
        fetch('/api/export-package', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        }).then(res => res.json()).then(data => {
          hideLoading();
          if (data.success) {
            hasSavedCurrentPackage = true;
            currentActiveDraftId = null;
            refreshDraftsBadge();

            // فتح مجلد العميل تلقائياً في Windows Explorer
            if (data.folder_path) {
              fetch('/api/open-folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder_path: data.folder_path })
              });
            }

            // عرض نافذة تأكيد الحفظ والسؤال عن رغبة الطباعة الآن
            openPostSavePrintModal(data, fileBase);
          } else {
            showLoadingError('خطأ في تصدير الحزمة', data.error || 'تعذر التصدير');
          }
        }).catch(err => {
          showLoadingError('خطأ في الاتصال أثناء التصدير', err.message);
        });
      });

