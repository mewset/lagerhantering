import os
import sys
import time
import signal
import psutil
import logging
import schedule
import subprocess
import threading
from datetime import datetime
from typing import Optional, Tuple

from services.backup_service import BackupService


class UpdaterService:
    def __init__(self, app_script: str, lock_file: str, backup_service: BackupService, logger: logging.Logger):
        self.app_script = app_script
        self.lock_file = lock_file
        self.backup_service = backup_service
        self.logger = logger
        self.app_process = None

    def create_lock(self) -> bool:
        try:
            if os.path.exists(self.lock_file):
                self.logger.warning(f"Lock file {self.lock_file} existerar redan. Kontrollerar om process körs...")
                with open(self.lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                if psutil.pid_exists(old_pid):
                    self.logger.error(f"Updater process {old_pid} körs redan. Avbryter.")
                    return False
                else:
                    self.logger.info(f"Gammal lock file från död process {old_pid}. Tar bort.")
                    os.remove(self.lock_file)

            with open(self.lock_file, 'w') as f:
                f.write(str(os.getpid()))
            self.logger.info(f"Lock file skapad med PID {os.getpid()}")
            return True
        except Exception as e:
            self.logger.error(f"Fel vid skapande av lock file: {e}")
            return False

    def remove_lock(self) -> None:
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
                self.logger.info("Lock file borttaget")
        except Exception as e:
            self.logger.error(f"Fel vid borttagning av lock file: {e}")

    def find_app_process(self) -> Optional[int]:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline'] and len(proc.info['cmdline']) > 1:
                    if ('python' in proc.info['name'].lower() and
                        self.app_script in ' '.join(proc.info['cmdline'])):
                        self.logger.info(f"Hittade app.py process: PID {proc.info['pid']}")
                        return proc.info['pid']
            self.logger.info("Ingen app.py process hittad")
            return None
        except Exception as e:
            self.logger.error(f"Fel vid sökning efter app.py process: {e}")
            return None

    def stop_app_gracefully(self, pid: int, timeout: int = 30) -> bool:
        from utils.exceptions import ProcessManagementError

        try:
            self.logger.info(f"Skickar SIGTERM till process {pid}")
            process = psutil.Process(pid)
            process.terminate()

            self.logger.info(f"Väntar på graceful shutdown (max {timeout}s)")
            process.wait(timeout=timeout)
            self.logger.info("App.py stängdes gracefully")
            return True

        except psutil.TimeoutExpired:
            self.logger.warning(f"Process {pid} svarade inte på SIGTERM inom {timeout}s. Tvingar shutdown.")
            try:
                process.kill()
                process.wait(timeout=5)
                self.logger.info("Process tvångsstängd med SIGKILL")
                return True
            except Exception as e:
                self.logger.error(f"Kunde inte tvångsstänga process: {e}")
                raise ProcessManagementError(pid, "force kill", str(e))
        except psutil.NoSuchProcess:
            self.logger.info("Process redan stängd")
            return True
        except ProcessManagementError:
            raise
        except Exception as e:
            self.logger.error(f"Fel vid graceful shutdown: {e}")
            raise ProcessManagementError(pid, "graceful shutdown", str(e))

    def check_git_version(self) -> Tuple[bool, Optional[str], Optional[str]]:
        from utils.exceptions import GitOperationError

        try:
            self.logger.info("Startar versionsvalidering mot GitHub...")

            local_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                text=True,
                cwd=os.getcwd()
            ).strip()
            self.logger.info(f"Lokal commit-hash: {local_commit}")

            subprocess.run(
                ["git", "fetch", "origin"],
                check=True,
                cwd=os.getcwd(),
                capture_output=True
            )

            remote_commit = subprocess.check_output(
                ["git", "rev-parse", "origin/main"],
                text=True,
                cwd=os.getcwd()
            ).strip()
            self.logger.info(f"Remote commit-hash (GitHub): {remote_commit}")

            if local_commit != remote_commit:
                self.logger.info("Ny version hittad på GitHub!")
                return True, local_commit, remote_commit
            else:
                self.logger.info("Lokala och remote versioner är identiska")
                return False, local_commit, remote_commit

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Fel vid Git-kommando: {e}")
            raise GitOperationError("version check", str(e))
        except Exception as e:
            self.logger.error(f"Oväntat fel vid versionsvalidering: {str(e)}")
            raise GitOperationError("version check", str(e))

    def perform_git_update(self) -> bool:
        from utils.exceptions import GitOperationError

        try:
            status = subprocess.check_output(
                ["git", "status", "--porcelain"],
                text=True,
                cwd=os.getcwd()
            ).strip()

            if status:
                self.logger.warning("Lokala ändringar detekterade:")
                self.logger.warning(status)
                self.logger.info("Försöker stasha ändringar...")

                subprocess.run(
                    ["git", "stash", "push", "-m", f"Auto-stash before update {datetime.now().isoformat()}"],
                    check=True,
                    cwd=os.getcwd(),
                    capture_output=True
                )
                self.logger.info("Lokala ändringar stashade")

            self.logger.info("Kör 'git pull origin main'...")
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )

            if result.returncode == 0:
                self.logger.info("Git pull lyckades:")
                self.logger.info(result.stdout)
                return True
            else:
                self.logger.error("Git pull misslyckades:")
                self.logger.error(result.stderr)
                raise GitOperationError("pull", result.stderr)

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Fel vid git update: {e}")
            raise GitOperationError("update", str(e))
        except GitOperationError:
            raise
        except Exception as e:
            self.logger.error(f"Oväntat fel vid git update: {str(e)}")
            raise GitOperationError("update", str(e))

    def start_app(self) -> bool:
        try:
            self.logger.info(f"Startar {self.app_script}...")

            process = subprocess.Popen(
                [sys.executable, self.app_script],
                cwd=os.getcwd(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            time.sleep(2)

            if process.poll() is None:
                self.logger.info(f"App.py startad med PID {process.pid}")
                return True
            else:
                self.logger.error(f"App.py kunde inte startas (exit code: {process.returncode})")
                return False

        except Exception as e:
            self.logger.error(f"Fel vid start av app.py: {e}")
            return False

    def run_update_check(self) -> None:
        from utils.exceptions import GitOperationError, ProcessManagementError, BackupError

        self.logger.info("=" * 50)
        self.logger.info("Startar schemalagd uppdateringskontroll")
        self.logger.info("=" * 50)

        if not self.create_lock():
            return

        try:
            has_update, local_hash, remote_hash = self.check_git_version()

            if not has_update:
                self.logger.info("Ingen uppdatering behövs")
                return

            self.logger.info("Påbörjar uppdateringsprocess...")

            self.logger.info("Steg 1: Skapar backuper...")
            version_backup = self.backup_service.create_version_backup(
                "version_backup",
                [self.app_script, "requirements.txt", "static", "templates", "data"]
            )
            if not version_backup:
                self.logger.error("Kunde inte skapa version backup. Avbryter uppdatering.")
                return

            if not self.backup_service.backup_for_update():
                self.logger.error("Kunde inte skapa databas backup. Avbryter uppdatering.")
                return

            self.logger.info("Steg 2: Stoppar app.py...")
            app_pid = self.find_app_process()
            if app_pid:
                if not self.stop_app_gracefully(app_pid):
                    self.logger.error("Kunde inte stoppa app.py. Avbryter uppdatering.")
                    return
            else:
                self.logger.info("App.py körs inte, fortsätter med uppdatering")

            self.logger.info("Steg 3: Uppdaterar kod från GitHub...")
            if not self.perform_git_update():
                self.logger.error("Git uppdatering misslyckades. Försöker starta app.py igen...")
                self.start_app()
                return

            self.logger.info("Steg 4: Startar app.py...")
            if self.start_app():
                self.logger.info("Uppdateringsprocess slutförd framgångsrikt!")
                self.logger.info(f"Uppdaterad från {local_hash} till {remote_hash}")
            else:
                self.logger.error("Kunde inte starta app.py efter uppdatering")

        except GitOperationError as e:
            self.logger.error(f"Git-fel under uppdateringsprocess: {e}")
        except ProcessManagementError as e:
            self.logger.error(f"Process management-fel under uppdateringsprocess: {e}")
        except BackupError as e:
            self.logger.error(f"Backup-fel under uppdateringsprocess: {e}")
        except Exception as e:
            self.logger.error(f"Oväntat fel under uppdateringsprocess: {e}")
        finally:
            self.remove_lock()
            self.logger.info("=" * 50)
            self.logger.info("Uppdateringskontroll slutförd")
            self.logger.info("=" * 50)

    def schedule_weekly_updates(self) -> None:
        self.logger.info("Schemaläggning: Varje måndag kl 02:00")
        schedule.every().monday.at("02:00").do(self.run_update_check)

        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                self.logger.info("Updater service stoppas av användare")
                break
            except Exception as e:
                self.logger.error(f"Fel i schemaläggare: {e}")
                time.sleep(60)

    def run_daemon(self) -> None:
        self.logger.info("Startar UpdaterService som daemon")

        def signal_handler(signum, frame):
            self.logger.info(f"Mottagen signal {signum}. Stänger av gracefully...")
            self.remove_lock()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        scheduler_thread = threading.Thread(target=self.schedule_weekly_updates, daemon=True)
        scheduler_thread.start()

        self.logger.info("UpdaterService daemon startad")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Daemon stoppas")
        finally:
            self.remove_lock()