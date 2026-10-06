/**
 * DUDC V4.0 - Stage 2: Studio Live Preview, Typography & Watermark (stage2.js)
 */

      /* ==========================================================================
         المرحلة 2: المزامنة من المرحلة 1 إلى استوديو التحرير
         ========================================================================== */
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

      function syncStage1ToStage2(force = false) {
        if (!activeParcel) return;

        // Sync any current DOM edits into activeParcel first
        if (!force && typeof syncDomToActiveParcel === 'function') {
          syncDomToActiveParcel();
        }

        // Only overwrite elements if forced OR if currently blank/placeholder
        const nameEl = document.getElementById('valApplicantName');
        if (force || !nameEl.textContent.trim() || nameEl.textContent.trim() === 'لا يوجد بيانات متاحة' || nameEl.textContent.trim() === '--') {
          nameEl.textContent = activeParcel.applicant_name || 'لا يوجد بيانات متاحة';
        }
        
        const rcpEl = document.getElementById('valReceiptNo');
        if (force || !rcpEl.textContent.trim() || rcpEl.textContent.trim() === 'لا يوجد بيانات متاحة' || rcpEl.textContent.trim() === '--') {
          const rcp = (activeParcel.receipt_no && String(activeParcel.receipt_no).trim() !== '0') ? String(activeParcel.receipt_no).trim() : '';
          rcpEl.textContent = rcp ? toArabicNumerals(rcp) : 'لا يوجد بيانات متاحة';
        }
        
        const nidEl = document.getElementById('valNationalId');
        if (force || !nidEl.textContent.trim() || nidEl.textContent.trim() === 'لا يوجد بيانات متاحة' || nidEl.textContent.trim() === '--') {
          const nid = (activeParcel.national_id && String(activeParcel.national_id).trim() !== '0') ? String(activeParcel.national_id).trim() : '';
          nidEl.textContent = nid ? toArabicNumerals(nid) : 'لا يوجد بيانات متاحة';
        }
        
        const centerEl = document.getElementById('valCenter');
        if (force || !centerEl.textContent.trim() || centerEl.textContent.trim() === 'لا يوجد بيانات متاحة' || centerEl.textContent.trim() === '--') {
          centerEl.textContent = activeParcel.district || 'لا يوجد بيانات متاحة';
        }

        const vilEl = document.getElementById('valVillage');
        if (force || !vilEl.textContent.trim() || vilEl.textContent.trim() === '--------' || vilEl.textContent.trim() === '--') {
          vilEl.textContent = activeParcel.village || '--------';
        }

        const addrEl = document.getElementById('valAddress');
        if (force || !addrEl.textContent.trim() || addrEl.textContent.trim() === 'لا يوجد بيانات متاحة' || addrEl.textContent.trim() === '--') {
          addrEl.textContent = activeParcel.address || activeParcel.village || 'لا يوجد بيانات متاحة';
        }
        
        const areaEl = document.getElementById('valArea');
        if (force || !areaEl.textContent.trim() || areaEl.textContent.trim() === '-- م²' || areaEl.textContent.trim() === '--') {
          const areaVal = (parseFloat(activeParcel.calculated_area_m2) || 0).toFixed(2);
          areaEl.textContent = `${toArabicNumerals(areaVal)} م²`;
        }

        const orderEl = document.getElementById('valOrderNo');
        if (force || !orderEl.textContent.trim() || orderEl.textContent.trim() === 'لا يوجد بيانات متاحة' || orderEl.textContent.trim() === '--') {
          if (savedTextDefaults && savedTextDefaults['valOrderNo'] && savedTextDefaults['valOrderNo'].html) {
            orderEl.innerHTML = savedTextDefaults['valOrderNo'].html;
          } else {
            const rawOrder = activeParcel.request_no || activeParcel.order_no || '';
            const reqNo = (rawOrder && String(rawOrder).trim() !== '0') ? String(rawOrder).trim() : '';
            orderEl.textContent = reqNo ? `${toArabicNumerals(reqNo)}s` : 'لا يوجد بيانات متاحة';
          }
        }

        const dealEl = document.getElementById('valDealType');
        if (force || !dealEl.textContent.trim() || dealEl.textContent.trim() === '--') {
          dealEl.textContent = activeParcel.transaction_type || activeParcel.deal_type || 'إنشاء';
        }

        const siteEl = document.getElementById('valSiteDesc');
        if (force || !siteEl.textContent.trim() || siteEl.textContent.trim() === '--') {
          siteEl.textContent = activeParcel.site_status || activeParcel.site_desc || 'أرض فضاء';
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

        // كود التأمين: إما الكود الرسمي المعتمد إذا تم تأكيده بالخطوة 3، أو كود تجريبي لضبط الطباعة بالاستوديو
        const certTokElem = document.getElementById('certTokenPrintVal');
        const trialBadge = document.getElementById('certTrialBadge');
        if (certTokElem) {
          if (activeParcel && activeParcel.security_token) {
            certTokElem.textContent = activeParcel.security_token;
            certTokElem.style.color = '#334155';
            if (trialBadge) trialBadge.style.display = 'none';
          } else {
            certTokElem.textContent = TRIAL_TOKEN;
            certTokElem.style.color = '#64748b';
            if (trialBadge) trialBadge.style.display = 'inline-block';
          }
        }

        // مزامنة الصورتين مع الاستوديو (سواء كانت صورة مخصصة مرفوعة أو معاينة افتراضية)
        if (customUploadedImages.croquis || (activeParcel && activeParcel.croquis_base64)) {
          document.getElementById('imgCroquis').src = customUploadedImages.croquis || activeParcel.croquis_base64;
        } else {
          const s1Croq = document.getElementById('stage1CroquisImg');
          if (s1Croq && s1Croq.src && !s1Croq.src.endsWith('/') && s1Croq.src !== window.location.href) {
            document.getElementById('imgCroquis').src = s1Croq.src;
          }
        }

        if (customUploadedImages.satellite || (activeParcel && activeParcel.satellite_base64)) {
          document.getElementById('imgSatellite').src = customUploadedImages.satellite || activeParcel.satellite_base64;
        } else {
          const s1Sat = document.getElementById('stage1SatImg');
          if (s1Sat && s1Sat.src && !s1Sat.src.endsWith('/') && s1Sat.src !== window.location.href) {
            document.getElementById('imgSatellite').src = s1Sat.src;
          }
        }

        // بناء جدول الحدود والإحداثيات بالدمج الرأسي الدقيق (فقط إذا كان فارغاً أو إجباري)
        const coordsTbody = document.getElementById('certCoordsTbody');
        if (force || !coordsTbody || coordsTbody.children.length === 0) {
          buildCertCoordsTable();
        }
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

      // شريط أدوات النصوص العائم المثبت عمودياً يسار الشاشة (Vertical Frosted Editor)
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
      const fltCloseToolbar = document.getElementById('fltCloseToolbar');
      let activeEditableElement = null;

      function showFloatingToolbar(el) {
        if (!el) return;
        activeEditableElement = el;
        if (floatingToolbar) floatingToolbar.classList.add('active');

        const comp = window.getComputedStyle(el);
        if (fltFontSizeVal) fltFontSizeVal.textContent = `${parseInt(comp.fontSize) || 12}px`;
        if (fltBold) {
          const isBold = comp.fontWeight === 'bold' || parseInt(comp.fontWeight) >= 700;
          fltBold.classList.toggle('active', isBold);
        }
        if (fltFontFamily) {
          const f = comp.fontFamily;
          if (f.includes('Arial')) fltFontFamily.value = "'Arial', sans-serif";
          else if (f.includes('Cairo')) fltFontFamily.value = "'Cairo', sans-serif";
          else if (f.includes('Amiri')) fltFontFamily.value = "'Amiri', serif";
        }
      }

      function hideFloatingToolbar() {
        if (floatingToolbar) floatingToolbar.classList.remove('active');
        activeEditableElement = null;
      }

      // منع فقدان التحديد عند النقر على أدوات الشريط العائم
      if (floatingToolbar) {
        floatingToolbar.addEventListener('mousedown', (e) => {
          if (e.target.tagName !== 'SELECT' && e.target.tagName !== 'OPTION') {
            e.preventDefault();
          }
        });
      }

      // تفعيل الشريط العائم فور تحديد أي نص داخل صفحة الشهادة (Activation on Text Selection)
      function checkSelectionAndActivate() {
        const sel = window.getSelection();
        if (sel && !sel.isCollapsed && sel.toString().trim().length > 0) {
          let node = sel.anchorNode;
          if (node && node.nodeType === 3) node = node.parentElement;
          if (node && certPage && certPage.contains(node)) {
            const editable = node.isContentEditable ? node : (node.closest('[contenteditable="true"]') || node);
            if (editable) {
              showFloatingToolbar(editable);
            }
          }
        }
      }

      certPage.addEventListener('mouseup', checkSelectionAndActivate);
      certPage.addEventListener('keyup', checkSelectionAndActivate);
      document.addEventListener('selectionchange', () => {
        const sel = window.getSelection();
        if (sel && !sel.isCollapsed && sel.toString().trim().length > 0) {
          let node = sel.anchorNode;
          if (node && node.nodeType === 3) node = node.parentElement;
          if (node && certPage && certPage.contains(node)) {
            const editable = node.isContentEditable ? node : (node.closest('[contenteditable="true"]') || node);
            if (editable) {
              showFloatingToolbar(editable);
            }
          }
        }
      });

      // زر إغلاق الشريط
      if (fltCloseToolbar) {
        fltCloseToolbar.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          hideFloatingToolbar();
        });
      }

      // إخفاء الشريط عند النقر بالماوس خارج الشريط وخارج التحديد
      document.addEventListener('mousedown', (e) => {
        if (floatingToolbar && !floatingToolbar.contains(e.target)) {
          setTimeout(() => {
            const sel = window.getSelection();
            if (!sel || sel.isCollapsed || sel.toString().trim().length === 0) {
              hideFloatingToolbar();
            }
          }, 120);
        }
      });

      // إخفاء الشريط بزر الهروب Escape
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && floatingToolbar && floatingToolbar.classList.contains('active')) {
          hideFloatingToolbar();
        }
      });

      if (fltFontFamily) {
        fltFontFamily.addEventListener('change', () => {
          if (activeEditableElement) activeEditableElement.style.fontFamily = fltFontFamily.value;
        });
      }
      if (fltFontInc) {
        fltFontInc.addEventListener('click', () => {
          if (activeEditableElement) {
            const s = Math.min(36, (parseInt(window.getComputedStyle(activeEditableElement).fontSize) || 12) + 1);
            activeEditableElement.style.fontSize = `${s}px`;
            if (fltFontSizeVal) fltFontSizeVal.textContent = `${s}px`;
          }
        });
      }
      if (fltFontDec) {
        fltFontDec.addEventListener('click', () => {
          if (activeEditableElement) {
            const s = Math.max(8, (parseInt(window.getComputedStyle(activeEditableElement).fontSize) || 12) - 1);
            activeEditableElement.style.fontSize = `${s}px`;
            if (fltFontSizeVal) fltFontSizeVal.textContent = `${s}px`;
          }
        });
      }
      if (fltBold) {
        fltBold.addEventListener('click', () => {
          if (!activeEditableElement) return;
          const sel = window.getSelection();
          if (sel && !sel.isCollapsed && activeEditableElement.contains(sel.anchorNode)) {
            document.execCommand('bold', false, null);
            const isBold = document.queryCommandState('bold');
            fltBold.classList.toggle('active', isBold);
          } else {
            const comp = window.getComputedStyle(activeEditableElement);
            const isBold = activeEditableElement.style.fontWeight === 'bold' || comp.fontWeight === 'bold' || parseInt(comp.fontWeight) >= 700;
            activeEditableElement.style.fontWeight = isBold ? 'normal' : 'bold';
            fltBold.classList.toggle('active', !isBold);
          }
        });
      }

      function applyTextColor(color) {
        if (!activeEditableElement) return;
        const sel = window.getSelection();
        if (sel && !sel.isCollapsed && activeEditableElement.contains(sel.anchorNode)) {
          document.execCommand('styleWithCSS', false, true);
          document.execCommand('foreColor', false, color);
        } else {
          activeEditableElement.style.color = color;
        }
      }

      if (fltColorBlue) {
        fltColorBlue.addEventListener('click', () => applyTextColor('#365F91'));
      }
      if (fltColorBlack) {
        fltColorBlack.addEventListener('click', () => applyTextColor('#000000'));
      }

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
            customUploadedImages.croquis = croppedUrl;
            if (activeParcel) activeParcel.croquis_base64 = croppedUrl;
          } else {
            document.getElementById('imgSatellite').src = croppedUrl;
            customUploadedImages.satellite = croppedUrl;
            if (activeParcel) activeParcel.satellite_base64 = croppedUrl;
          }
          closeModal();
        };
      });

      // ==========================================================================
      // محرك حفظ واستعادة الإعدادات الافتراضية الشاملة (Layout + النصوص والتنسيقات)
      // ==========================================================================
      // (savedTextDefaults تم تعريفها بالأعلى)

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

