/**
 * DUDC V3.5 - Visual In-App Folder Explorer & Directory Manager (folder_explorer.js)
 * ===================================================================================
 * 100% Web-Native, Zero-Shell, Zero-PowerShell folder navigation.
 * Solves all freeze, AppLocker, antivirus, and background-window issues on all machines.
 */

var explorerCurrentPath = '';
var explorerCanWrite = true;
var quickLocationsCache = null;

// Initialize folder explorer
async function initFolderExplorer() {
  await fetchQuickLocations();
  setupPathInputListeners();
}

async function fetchQuickLocations() {
  try {
    const res = await fetch('/api/quick-locations');
    const data = await res.json();
    if (data.success) {
      quickLocationsCache = data;
      renderQuickPills(data);
    }
  } catch (err) {
    console.warn('[FolderExplorer] Could not load quick locations:', err);
  }
}

function renderQuickPills(data) {
  const container = document.getElementById('quickLocationPillsContainer');
  const modalContainer = document.getElementById('modalQuickLocationPills');

  const html = [];
  if (data.locations) {
    data.locations.forEach(loc => {
      html.push(`<button type="button" class="btn-pill-loc" onclick="applyQuickPath('${escapeJsStr(loc.path)}')">
        <span>${loc.icon}</span> ${escapeHtml(loc.name)}
      </button>`);
    });
  }
  if (data.drives) {
    data.drives.forEach(drv => {
      html.push(`<button type="button" class="btn-pill-loc btn-pill-drive" onclick="applyQuickPath('${escapeJsStr(drv.path)}')">
        <span>${drv.icon}</span> ${escapeHtml(drv.label)}
      </button>`);
    });
  }

  const pillsHtml = html.join('');
  if (container) container.innerHTML = pillsHtml;
  if (modalContainer) modalContainer.innerHTML = pillsHtml;
}

function escapeJsStr(str) {
  return (str || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

function applyQuickPath(pathStr) {
  const dirInput = document.getElementById('outputDirInput');
  if (dirInput) {
    dirInput.value = pathStr;
  }
  saveOutputDir(pathStr);
  if (document.getElementById('folderExplorerModalBackdrop')?.style.display === 'flex') {
    navigateToPath(pathStr);
  }
}

// Open visual explorer modal
window.openFolderExplorerModal = async function(initialPath) {
  const modal = document.getElementById('folderExplorerModalBackdrop');
  if (!modal) return;

  const curVal = initialPath || document.getElementById('outputDirInput')?.value || '';
  modal.style.display = 'flex';

  if (!quickLocationsCache) {
    await fetchQuickLocations();
  } else {
    renderQuickPills(quickLocationsCache);
  }

  await navigateToPath(curVal);
};

window.closeFolderExplorerModal = function() {
  const modal = document.getElementById('folderExplorerModalBackdrop');
  if (modal) modal.style.display = 'none';
};

// Navigate to a directory in visual explorer
async function navigateToPath(targetPath) {
  const statusEl = document.getElementById('explorerLoadingStatus');
  const listEl = document.getElementById('explorerFoldersGrid');
  const pathInp = document.getElementById('explorerCurrentPathInput');
  const upBtn = document.getElementById('btnExplorerUp');
  const permBadge = document.getElementById('explorerPermBadge');

  if (statusEl) statusEl.style.display = 'block';
  if (listEl) listEl.innerHTML = '<div style="color:var(--text-muted); padding:20px; text-align:center;">⏳ جاري جلب المجلدات...</div>';

  try {
    const res = await fetch('/api/browse-directory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: targetPath })
    });
    const data = await res.json();

    if (!data.success && data.error) {
      if (listEl) {
        listEl.innerHTML = `<div style="color:#f87171; padding:20px; text-align:center;">
          ⚠️ ${escapeHtml(data.error)}
          <br><button type="button" class="btn btn-glass" style="margin-top:10px;" onclick="navigateToPath('')">العودة إلى سطح المكتب الافتراضي</button>
        </div>`;
      }
      return;
    }

    explorerCurrentPath = data.current_path;
    explorerCanWrite = data.can_write;

    if (pathInp) pathInp.value = explorerCurrentPath;

    if (upBtn) {
      upBtn.disabled = !data.parent_path;
      upBtn.onclick = () => data.parent_path && navigateToPath(data.parent_path);
    }

    if (permBadge) {
      if (data.can_write) {
        permBadge.innerHTML = '✔ مجلد صالح للكتابة';
        permBadge.className = 'perm-badge perm-badge-ok';
      } else {
        permBadge.innerHTML = '⚠️ للقراءة فقط (غير قابل للحفظ)';
        permBadge.className = 'perm-badge perm-badge-warn';
      }
    }

    renderExplorerFolders(data.subdirectories || []);
  } catch (err) {
    if (listEl) {
      listEl.innerHTML = `<div style="color:#f87171; padding:20px; text-align:center;">فشل الاتصال: ${escapeHtml(err.message)}</div>`;
    }
  } finally {
    if (statusEl) statusEl.style.display = 'none';
  }
}

function renderExplorerFolders(subdirs) {
  const listEl = document.getElementById('explorerFoldersGrid');
  if (!listEl) return;

  if (subdirs.length === 0) {
    listEl.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 36px 20px; text-align: center; color: var(--text-muted);">
        <div style="font-size: 32px; margin-bottom: 8px; opacity: 0.6;">📂</div>
        <div style="font-size: 13px; font-weight: 600;">هذا المجلد لا يحتوي على مجلدات فرعية</div>
        <div style="font-size: 11.5px; opacity: 0.7; margin-top: 4px;">يمكنك اختيار هذا المجلد مباشرة أو إنشاء مجلد جديد بداخله</div>
      </div>
    `;
    return;
  }

  const items = subdirs.map(item => `
    <div class="explorer-folder-card" onclick="navigateToPath('${escapeJsStr(item.path)}')" title="${escapeHtml(item.name)}">
      <span class="folder-icon">📁</span>
      <span class="folder-name">${escapeHtml(item.name)}</span>
    </div>
  `);

  listEl.innerHTML = items.join('');
}

// Confirm and select current path from visual explorer
window.confirmExplorerSelection = function() {
  if (!explorerCurrentPath) return;

  const dirInput = document.getElementById('outputDirInput');
  if (dirInput) {
    dirInput.value = explorerCurrentPath;
  }

  saveOutputDir(explorerCurrentPath);
  closeFolderExplorerModal();

  const statusEl = document.getElementById('outputDirStatus');
  if (statusEl) {
    statusEl.innerHTML = '✔ تم تحديد مجلد حفظ الشهادات بنجاح: ' + escapeHtml(explorerCurrentPath);
    setTimeout(() => { if (statusEl) statusEl.textContent = ''; }, 4500);
  }
};

// Create new folder prompt
window.promptCreateNewFolder = async function() {
  if (!explorerCurrentPath) {
    alert('يرجى الانتقال إلى مسار أولاً');
    return;
  }

  const folderName = prompt('أدخل اسم المجلد الجديد:');
  if (!folderName || !folderName.trim()) return;

  try {
    const res = await fetch('/api/create-directory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        parent_path: explorerCurrentPath,
        folder_name: folderName.trim()
      })
    });
    const data = await res.json();
    if (data.success) {
      await navigateToPath(data.folder_path);
    } else {
      alert('فشل إنشاء المجلد: ' + (data.error || 'خطأ غير معروف'));
    }
  } catch (err) {
    alert('تعذر إنشاء المجلد: ' + err.message);
  }
};

// Real-time path input validation
function setupPathInputListeners() {
  const dirInput = document.getElementById('outputDirInput');
  if (!dirInput) return;

  let debounceTimer = null;
  dirInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      validatePathInUI(dirInput.value.trim());
    }, 400);
  });
}

async function validatePathInUI(pathStr) {
  const statusEl = document.getElementById('outputDirStatus');
  if (!statusEl) return;

  if (!pathStr) {
    statusEl.textContent = '';
    return;
  }

  try {
    const res = await fetch('/api/validate-path', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: pathStr })
    });
    const data = await res.json();

    if (data.valid) {
      if (data.can_write) {
        statusEl.innerHTML = `<span style="color:#34d399;">✔ ${escapeHtml(data.message)}</span>`;
      } else {
        statusEl.innerHTML = `<span style="color:#fbbf24;">⚠️ ${escapeHtml(data.message)}</span>`;
      }
    } else {
      statusEl.innerHTML = `<span style="color:#f87171;">✕ ${escapeHtml(data.message)}</span>`;
    }
  } catch (err) {
    statusEl.textContent = '';
  }
}

// Native Windows OS dialog picker with instant feedback & auto-fallback
window.browseOutputDirNative = async function() {
  const statusEl = document.getElementById('outputDirStatus');
  const dirInput = document.getElementById('outputDirInput');
  const curDir = dirInput ? dirInput.value.trim() : '';

  if (statusEl) {
    statusEl.innerHTML = '⏳ جاري فتح مستعرض ويندوز... (إذا لم تظهر النافذة، يمكنك استخدام <a href="javascript:void(0)" onclick="openFolderExplorerModal()" style="color:#38bdf8;text-decoration:underline;font-weight:bold;">المستعرض المدمج هنا</a>)';
  }

  try {
    const res = await fetch('/api/browse-output-dir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initial_dir: curDir })
    });
    const data = await res.json();

    if (data.success && data.folder_path) {
      if (dirInput) dirInput.value = data.folder_path;
      outputDir = data.folder_path;
      if (statusEl) {
        statusEl.innerHTML = '✔ تم تحديد المجلد بنجاح: ' + escapeHtml(data.folder_path);
        setTimeout(() => { if (statusEl) statusEl.textContent = ''; }, 4000);
      }
    } else {
      if (statusEl) {
        statusEl.innerHTML = 'لم يتم تحديد مسار جديد. <a href="javascript:void(0)" onclick="openFolderExplorerModal()" style="color:#38bdf8;text-decoration:underline;">فتح المستعرض المدمج</a>';
        setTimeout(() => { if (statusEl) statusEl.textContent = ''; }, 6000);
      }
    }
  } catch (err) {
    if (statusEl) {
      statusEl.innerHTML = 'تعذر تشغيل مستعرض ويندوز. <a href="javascript:void(0)" onclick="openFolderExplorerModal()" style="color:#38bdf8;text-decoration:underline;font-weight:bold;">اضغط هنا لفتح المستعرض المدمج السلس</a>';
    }
  }
};

// Aliases for backward compatibility
window.browseOutputDir = window.openFolderExplorerModal;

// Run initialization on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  initFolderExplorer();
});
