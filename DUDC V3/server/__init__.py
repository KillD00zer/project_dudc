"""
DUDC V3 Modular Server Package
==============================
"""

from .config import (
    APP_DIR,
    INDEX_HTML,
    SAMPLE_FILE,
    DEFAULTS_FILE,
    DRAFTS_DIR,
    TEMP_ASSETS_DIR,
    ASSETS_DIR,
    open_folder_picker,
    save_persistent_config,
    load_saved_config,
    validate_or_fallback_output_dir,
    get_safe_default_output_dir,
)
from .pdf_service import export_certificate_pdf
from .git_service import check_git_updates, perform_git_update
from .drafts_service import list_drafts, save_draft, load_draft, delete_draft, ensure_base64_image
from .session_manager import SESSION_MANAGER, SessionManager
from .handlers import handle_get, handle_post

__all__ = [
    "APP_DIR",
    "INDEX_HTML",
    "SAMPLE_FILE",
    "DEFAULTS_FILE",
    "DRAFTS_DIR",
    "TEMP_ASSETS_DIR",
    "ASSETS_DIR",
    "open_folder_picker",
    "save_persistent_config",
    "load_saved_config",
    "validate_or_fallback_output_dir",
    "get_safe_default_output_dir",
    "export_certificate_pdf",
    "check_git_updates",
    "perform_git_update",
    "list_drafts",
    "save_draft",
    "load_draft",
    "delete_draft",
    "ensure_base64_image",
    "SESSION_MANAGER",
    "SessionManager",
    "handle_get",
    "handle_post",
]
