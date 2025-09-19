#!/usr/bin/env python3
import os
import sys
import time
import signal
import psutil
import logging
import schedule
import subprocess
import threading
import json
from datetime import datetime
import shutil

# Konfigurera loggning för updater
logging.basicConfig(
    filename='updater.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# Lägg även till console logging
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

# Konfiguration
APP_SCRIPT = "app.py"
LOCK_FILE = "updater.lock"
BACKUP_DIR = "version_backup"
DATA_DIR = "data"
DB_BACKUP_DIR = "db_backup"

class UpdaterService:
    def __init__(self):
        self.app_process = None
        logger.info("UpdaterService initialiserad")

    def create_lock(self):
        """Skapa lock file för att förhindra parallella uppdateringar"""
        try:
            if os.path.exists(LOCK_FILE):
                logger.warning(f"Lock file {LOCK_FILE} existerar redan. Kontrollerar om process körs...")
                with open(LOCK_FILE, 'r') as f:
                    old_pid = int(f.read().strip())
                if psutil.pid_exists(old_pid):
                    logger.error(f"Updater process {old_pid} körs redan. Avbryter.")
                    return False
                else:
                    logger.info(f"Gammal lock file från död process {old_pid}. Tar bort.")
                    os.remove(LOCK_FILE)
            
            with open(LOCK_FILE, 'w') as f:
                f.write(str(os.getpid()))
            logger.info(f"Lock file skapad med PID {os.getpid()}")
            return True
        except Exception as e:
            logger.error(f"Fel vid skapande av lock file: {e}")
            return False

    def remove_lock(self):
        """Ta bort lock file"""
        try:
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
                logger.info("Lock file borttaget")
        except Exception as e:
            logger.error(f"Fel vid borttagning av lock file: {e}")

    def find_app_process(self):
        """Hitta app.py process"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline'] and len(proc.info['cmdline']) > 1:
                    if 'python' in proc.info['name'].lower() and APP_SCRIPT in ' '.join(proc.info['cmdline']):
                        logger.info(f"Hittade app.py process: PID {proc.info['pid']}")
                        return proc.info['pid']
            logger.info("Ingen app.py process hittad")
            return None
        except Exception as e:
            logger.error(f"Fel vid sökning efter app.py process: {e}")
            return None

    def stop_app_gracefully(self, pid, timeout=30):
        """Stoppa app.py gracefully med SIGTERM"""
        try:
            logger.info(f"Skickar SIGTERM till process {pid}")
            process = psutil.Process(pid)
            process.terminate()
            
            # Vänta på graceful shutdown
            logger.info(f"Väntar på graceful shutdown (max {timeout}s)")
            process.wait(timeout=timeout)
            logger.info("App.py stängdes gracefully")
            return True
            
        except psutil.TimeoutExpired:
            logger.warning(f"Process {pid} svarade inte på SIGTERM inom {timeout}s. Tvingar shutdown.")
            try:
                process.kill()
                process.wait(timeout=5)
                logger.info("Process tvångsstängd med SIGKILL")
                return True
            except Exception as e:
                logger.error(f"Kunde inte tvångsstänga process: {e}")
                return False
        except psutil.NoSuchProcess:
            logger.info("Process redan stängd")
            return True
        except Exception as e:
            logger.error(f"Fel vid graceful shutdown: {e}")
            return False

    def create_version_backup(self):
        """Skapa backup av nuvarande version"""
        try:
            if not os.path.exists(BACKUP_DIR):
                os.makedirs(BACKUP_DIR)
                logger.info(f"Skapade backup-mapp: {BACKUP_DIR}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(BACKUP_DIR, f"version_{timestamp}")
            
            # Kopiera viktiga filer
            files_to_backup = [APP_SCRIPT, "requirements.txt", "static", "templates"]
            if os.path.exists(DATA_DIR):
                files_to_backup.append(DATA_DIR)
            
            os.makedirs(backup_path)
            
            for item in files_to_backup:
                if os.path.exists(item):
                    dest = os.path.join(backup_path, item)
                    if os.path.isdir(item):
                        shutil.copytree(item, dest)
                        logger.info(f"Backupade mapp: {item}")
                    else:
                        shutil.copy2(item, dest)
                        logger.info(f"Backupade fil: {item}")
                else:
                    logger.warning(f"Kunde inte hitta: {item}")
            
            # Begränsa antal backuper (behåll 3 senaste)
            backups = [d for d in os.listdir(BACKUP_DIR) if d.startswith("version_")]
            backups.sort()
            if len(backups) > 3:
                for old_backup in backups[:-3]:
                    old_path = os.path.join(BACKUP_DIR, old_backup)
                    shutil.rmtree(old_path)
                    logger.info(f"Tog bort gammal backup: {old_backup}")
            
            logger.info(f"Version backup skapad: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Fel vid skapande av version backup: {e}")
            return None

    def check_git_version(self):
        """Kontrollera om det finns uppdateringar på GitHub"""
        try:
            logger.info("Startar versionsvalidering mot GitHub...")
            
            # Hämta lokal commit hash
            local_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                text=True, 
                cwd=os.getcwd()
            ).strip()
            logger.info(f"Lokal commit-hash: {local_commit}")
            
            # Fetch remote changes
            subprocess.run(
                ["git", "fetch", "origin"], 
                check=True, 
                cwd=os.getcwd(),
                capture_output=True
            )
            
            # Hämta remote commit hash
            remote_commit = subprocess.check_output(
                ["git", "rev-parse", "origin/main"], 
                text=True, 
                cwd=os.getcwd()
            ).strip()
            logger.info(f"Remote commit-hash (GitHub): {remote_commit}")
            
            if local_commit != remote_commit:
                logger.info("Ny version hittad på GitHub!")
                return True, local_commit, remote_commit
            else:
                logger.info("Lokala och remote versioner är identiska")
                return False, local_commit, remote_commit
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Fel vid Git-kommando: {e}")
            return False, None, None
        except Exception as e:
            logger.error(f"Oväntat fel vid versionsvalidering: {str(e)}")
            return False, None, None

    def perform_git_update(self):
        """Kör git pull för att uppdatera"""
        try:
            # Kontrollera om det finns lokala ändringar
            status = subprocess.check_output(
                ["git", "status", "--porcelain"], 
                text=True, 
                cwd=os.getcwd()
            ).strip()
            
            if status:
                logger.warning("Lokala ändringar detekterade:")
                logger.warning(status)
                logger.info("Försöker stasha ändringar...")
                
                # Stasha lokala ändringar
                subprocess.run(
                    ["git", "stash", "push", "-m", f"Auto-stash before update {datetime.now().isoformat()}"],
                    check=True,
                    cwd=os.getcwd(),
                    capture_output=True
                )
                logger.info("Lokala ändringar stashade")
            
            # Kör git pull
            logger.info("Kör 'git pull origin main'...")
            result = subprocess.run(
                ["git", "pull", "origin", "main"], 
                capture_output=True, 
                text=True, 
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                logger.info("Git pull lyckades:")
                logger.info(result.stdout)
                return True
            else:
                logger.error("Git pull misslyckades:")
                logger.error(result.stderr)
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Fel vid git update: {e}")
            return False
        except Exception as e:
            logger.error(f"Oväntat fel vid git update: {str(e)}")
            return False

    def start_app(self):
        """Starta app.py"""
        try:
            logger.info(f"Startar {APP_SCRIPT}...")
            
            # Starta app.py i bakgrunden
            process = subprocess.Popen(
                [sys.executable, APP_SCRIPT],
                cwd=os.getcwd(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Vänta lite för att säkerställa att processen startar
            time.sleep(2)
            
            if process.poll() is None:
                logger.info(f"App.py startad med PID {process.pid}")
                return True
            else:
                logger.error(f"App.py kunde inte startas (exit code: {process.returncode})")
                return False
                
        except Exception as e:
            logger.error(f"Fel vid start av app.py: {e}")
            return False

    def backup_database(self):
        """Skapa backup av databas innan uppdatering"""
        try:
            if not os.path.exists(DB_BACKUP_DIR):
                os.makedirs(DB_BACKUP_DIR)
            
            timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
            backup_filename = f"inventory-update-{timestamp}.json"
            backup_path = os.path.join(DB_BACKUP_DIR, backup_filename)
            
            data_file = os.path.join(DATA_DIR, "inventory.json")
            if os.path.exists(data_file):
                shutil.copy(data_file, backup_path)
                logger.info(f"Databas backup skapad: {backup_filename}")
                return True
            else:
                logger.warning("Ingen databas att backup:a")
                return True
                
        except Exception as e:
            logger.error(f"Fel vid databas backup: {e}")
            return False

    def run_update_check(self):
        """Kör en komplett uppdateringskontroll"""
        logger.info("=" * 50)
        logger.info("Startar schemalagd uppdateringskontroll")
        logger.info("=" * 50)
        
        if not self.create_lock():
            return
        
        try:
            # Kontrollera för uppdateringar
            has_update, local_hash, remote_hash = self.check_git_version()
            
            if not has_update:
                logger.info("Ingen uppdatering behövs")
                return
            
            logger.info("Påbörjar uppdateringsprocess...")
            
            # 1. Skapa backuper
            logger.info("Steg 1: Skapar backuper...")
            version_backup = self.create_version_backup()
            if not version_backup:
                logger.error("Kunde inte skapa version backup. Avbryter uppdatering.")
                return
            
            if not self.backup_database():
                logger.error("Kunde inte skapa databas backup. Avbryter uppdatering.")
                return
            
            # 2. Stoppa app.py
            logger.info("Steg 2: Stoppar app.py...")
            app_pid = self.find_app_process()
            if app_pid:
                if not self.stop_app_gracefully(app_pid):
                    logger.error("Kunde inte stoppa app.py. Avbryter uppdatering.")
                    return
            else:
                logger.info("App.py körs inte, fortsätter med uppdatering")
            
            # 3. Uppdatera kod
            logger.info("Steg 3: Uppdaterar kod från GitHub...")
            if not self.perform_git_update():
                logger.error("Git uppdatering misslyckades. Försöker starta app.py igen...")
                self.start_app()
                return
            
            # 4. Starta app.py igen
            logger.info("Steg 4: Startar app.py...")
            if self.start_app():
                logger.info("Uppdateringsprocess slutförd framgångsrikt!")
                logger.info(f"Uppdaterad från {local_hash} till {remote_hash}")
            else:
                logger.error("Kunde inte starta app.py efter uppdatering")
            
        except Exception as e:
            logger.error(f"Oväntat fel under uppdateringsprocess: {e}")
        finally:
            self.remove_lock()
            logger.info("=" * 50)
            logger.info("Uppdateringskontroll slutförd")
            logger.info("=" * 50)

    def schedule_weekly_updates(self):
        """Schemalägg veckovis uppdateringar"""
        logger.info("Schemaläggning: Varje måndag kl 02:00")
        schedule.every().monday.at("02:00").do(self.run_update_check)
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Kontrollera varje minut
            except KeyboardInterrupt:
                logger.info("Updater service stoppas av användare")
                break
            except Exception as e:
                logger.error(f"Fel i schemaläggare: {e}")
                time.sleep(60)

    def run_daemon(self):
        """Kör som daemon service"""
        logger.info("Startar UpdaterService som daemon")
        
        def signal_handler(signum, frame):
            logger.info(f"Mottagen signal {signum}. Stänger av gracefully...")
            self.remove_lock()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Starta schemaläggaren i separat tråd
        scheduler_thread = threading.Thread(target=self.schedule_weekly_updates, daemon=True)
        scheduler_thread.start()
        
        logger.info("UpdaterService daemon startad")
        
        try:
            # Håll huvudtråden levande
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Daemon stoppas")
        finally:
            self.remove_lock()

def main():
    updater = UpdaterService()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            # Kör en omedelbar uppdateringskontroll
            updater.run_update_check()
        elif sys.argv[1] == "--daemon":
            # Kör som daemon
            updater.run_daemon()
        else:
            print("Användning: python updater.py [--check|--daemon]")
            sys.exit(1)
    else:
        # Kör en omedelbar uppdateringskontroll som standard
        updater.run_update_check()

if __name__ == "__main__":
    main()