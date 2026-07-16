import os
import subprocess
import logging
from datetime import datetime
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def ping() -> str:
    return "pong"


@shared_task(name="apps.common.tasks.backup_db_and_send_to_telegram")
def backup_db_and_send_to_telegram():
    """Har kuni tunda DB backup oladi va Telegram ga yuboradi."""
    import requests
    from django.conf import settings as django_settings

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"inspectpro_backup_{ts}.sql.gz"
    filepath = f"/tmp/{filename}"

    db = django_settings.DATABASES["default"]

    try:
        # 1. pg_dump + gzip
        env = os.environ.copy()
        env["PGPASSWORD"] = db.get("PASSWORD", "")

        dump_cmd = [
            "pg_dump",
            "-h", db.get("HOST", "localhost"),
            "-p", str(db.get("PORT", "5432")),
            "-U", db.get("USER", "postgres"),
            "-d", db.get("NAME", ""),
            "--no-password",
        ]

        with open(filepath, "wb") as f:
            dump_proc = subprocess.Popen(dump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            gzip_proc = subprocess.Popen(["gzip", "-c"], stdin=dump_proc.stdout, stdout=f, stderr=subprocess.PIPE)
            dump_proc.stdout.close()
            gzip_out, gzip_err = gzip_proc.communicate()
            dump_proc.wait()

        if dump_proc.returncode != 0:
            logger.error(f"pg_dump failed: {dump_proc.stderr.read()}")
            return

        # 2. Telegram ga yuborish
        bot_token = os.getenv("TG_BACKUP_BOT_TOKEN")
        chat_id = os.getenv("TG_BACKUP_CHAT_ID")

        if not bot_token or not chat_id:
            logger.warning("TG_BACKUP_BOT_TOKEN yoki TG_BACKUP_CHAT_ID .env da yo'q")
            return

        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        caption = (
            f"InspectPro DB Backup\n"
            f"Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"Hajm: {file_size_mb:.2f} MB\n"
            f"Fayl: {filename}"
        )

        with open(filepath, "rb") as f:
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendDocument",
                data={"chat_id": chat_id, "caption": caption},
                files={"document": (filename, f, "application/gzip")},
                timeout=120,
            )

        if response.status_code != 200:
            logger.error(f"Telegram yuborish xatosi: {response.text}")
            return

        logger.info(f"Backup muvaffaqiyatli yuborildi: {filename}")

    except Exception as e:
        logger.error(f"Backup xatosi: {e}")

    finally:
        # 3. Lokal faylni o'chirish (muvaffaqiyatdan qat'iy nazar)
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Lokal backup o'chirildi: {filepath}")

