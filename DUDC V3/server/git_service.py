"""
GitHub Update Service
=====================
Checks remote repository for updates and executes git pull safely.
"""

import os
import shutil
import subprocess
from typing import Dict, Any
from .config import APP_DIR


def get_git_repo_root() -> str:
    parent_dir = os.path.dirname(APP_DIR)
    if os.path.exists(os.path.join(parent_dir, ".git")):
        return parent_dir
    if os.path.exists(os.path.join(APP_DIR, ".git")):
        return APP_DIR
    return parent_dir


def check_git_updates() -> Dict[str, Any]:
    repo_root = get_git_repo_root()
    git_bin = shutil.which("git")
    if not git_bin:
        return {
            "success": False,
            "error": "أداة Git غير مثبتة على هذا النظام أو غير مضافة لـ PATH."
        }

    try:
        fetch_res = subprocess.run(
            [git_bin, "fetch", "origin", "main"],
            cwd=repo_root, capture_output=True, text=True, timeout=8
        )
        if fetch_res.returncode != 0:
            return {
                "success": False,
                "error": f"تعذر الاتصال بـ GitHub: {fetch_res.stderr.strip() or fetch_res.stdout.strip()}"
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "انتهت مهلة الاتصال بخادم GitHub. يرجى التحقق من اتصال الإنترنت."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"خطأ أثناء فحص GitHub: {str(e)}"
        }

    try:
        local_hash = subprocess.check_output(
            [git_bin, "rev-parse", "--short", "HEAD"],
            cwd=repo_root, text=True
        ).strip()

        remote_hash = subprocess.check_output(
            [git_bin, "rev-parse", "--short", "origin/main"],
            cwd=repo_root, text=True
        ).strip()

        local_raw = subprocess.check_output(
            [git_bin, "log", "-1", "--pretty=format:%h|||%s|||%cr|||%an|||%b"],
            cwd=repo_root, text=True, encoding='utf-8'
        ).strip().split('|||')
        current_commit = {
            "hash": local_raw[0] if len(local_raw) > 0 else local_hash,
            "subject": local_raw[1] if len(local_raw) > 1 else "",
            "date": local_raw[2] if len(local_raw) > 2 else "",
            "author": local_raw[3] if len(local_raw) > 3 else "",
            "body": local_raw[4].strip() if len(local_raw) > 4 else ""
        }

        if local_hash == remote_hash:
            return {
                "success": True,
                "update_available": False,
                "current_commit": current_commit,
                "message": "أنت تعمل على أحدث إصدار متوفر حالياً."
            }

        log_out = subprocess.check_output(
            [git_bin, "log", "HEAD..origin/main", "--pretty=format:%h|||%s|||%cr|||%an|||%b<<<ENTRY>>>"],
            cwd=repo_root, text=True, encoding='utf-8'
        )

        incoming = []
        for item in log_out.split("<<<ENTRY>>>"):
            item = item.strip()
            if not item:
                continue
            parts = item.split("|||")
            incoming.append({
                "hash": parts[0].strip() if len(parts) > 0 else "",
                "subject": parts[1].strip() if len(parts) > 1 else "",
                "date": parts[2].strip() if len(parts) > 2 else "",
                "author": parts[3].strip() if len(parts) > 3 else "",
                "body": parts[4].strip() if len(parts) > 4 else ""
            })

        return {
            "success": True,
            "update_available": True,
            "count": len(incoming),
            "commits": incoming,
            "current_commit": current_commit,
            "remote_hash": remote_hash,
            "latest_subject": incoming[0]["subject"] if incoming else "",
            "latest_body": incoming[0]["body"] if incoming else ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"فشل قراءة سجل التحديثات: {str(e)}"
        }


def perform_git_update() -> Dict[str, Any]:
    repo_root = get_git_repo_root()
    git_bin = shutil.which("git")
    if not git_bin:
        return {"success": False, "error": "أداة Git غير متوفرة على هذا النظام."}

    try:
        pull_res = subprocess.run(
            [git_bin, "pull", "origin", "main"],
            cwd=repo_root, capture_output=True, text=True, timeout=30, encoding='utf-8'
        )
        if pull_res.returncode != 0:
            err_msg = (pull_res.stderr or pull_res.stdout or "").strip()
            if any(k in err_msg.lower() for k in ("overwritten by merge", "commit your changes", "stash", "local changes")):
                subprocess.run(
                    [git_bin, "stash"],
                    cwd=repo_root, capture_output=True, text=True, timeout=15, encoding='utf-8'
                )
                pull_res = subprocess.run(
                    [git_bin, "pull", "origin", "main"],
                    cwd=repo_root, capture_output=True, text=True, timeout=30, encoding='utf-8'
                )

        if pull_res.returncode != 0:
            subprocess.run(
                [git_bin, "checkout", "--", "."],
                cwd=repo_root, capture_output=True, text=True, timeout=15, encoding='utf-8'
            )
            pull_res = subprocess.run(
                [git_bin, "pull", "origin", "main"],
                cwd=repo_root, capture_output=True, text=True, timeout=30, encoding='utf-8'
            )

        if pull_res.returncode != 0:
            return {
                "success": False,
                "error": f"فشل السحب من GitHub: {pull_res.stderr.strip() or pull_res.stdout.strip()}"
            }

        new_raw = subprocess.check_output(
            [git_bin, "log", "-1", "--pretty=format:%h|||%s|||%cr|||%an|||%b"],
            cwd=repo_root, text=True, encoding='utf-8'
        ).strip().split('|||')
        new_commit = {
            "hash": new_raw[0] if len(new_raw) > 0 else "",
            "subject": new_raw[1] if len(new_raw) > 1 else "",
            "date": new_raw[2] if len(new_raw) > 2 else "",
            "author": new_raw[3] if len(new_raw) > 3 else "",
            "body": new_raw[4].strip() if len(new_raw) > 4 else ""
        }

        return {
            "success": True,
            "message": "تم تحديث المنظومة بنجاح إلى أحدث إصدار!",
            "commit": new_commit,
            "pull_output": pull_res.stdout.strip()
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "استغرق التحديث وقتاً طويلاً وتجاوز المهلة المحددة."}
    except Exception as e:
        return {"success": False, "error": f"حدث خطأ أثناء التحديث: {str(e)}"}
