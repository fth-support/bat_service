import os
import sys
import subprocess
import json
import ctypes
import winreg
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
import threading
import time

CONFIG_FILE = "config.json"
APP_NAME = "ServiceGuard"
EXE_PATH = sys.executable

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

class ServiceGuardApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} Control Panel")
        self.root.geometry("400x350")
        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)
        
        self.bat_process = None
        self.load_config()
        self.setup_ui()
        
        # เริ่มต้น Tray Icon
        self.create_tray_icon()
        
        # รัน Batch ทันทีถ้ามี Path ค้างไว้
        if self.config.get("bat_path"):
            self.run_batch()

        # Update Status Loop
        self.update_status_loop()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f: self.config = json.load(f)
        else:
            self.config = {"bat_path": ""}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f)

    def setup_ui(self):
        tk.Label(self.root, text="Service Guard Configuration", font=("Arial", 14, "bold")).pack(pady=10)

        # Status Frame
        status_frame = tk.LabelFrame(self.root, text=" System Status ", padx=10, pady=10)
        status_frame.pack(fill="x", padx=20)

        self.lbl_file = tk.Label(status_frame, text="File: Not Selected", fg="red")
        self.lbl_file.pack(anchor="w")

        self.lbl_status = tk.Label(status_frame, text="Status: Stopped", fg="gray")
        self.lbl_status.pack(anchor="w")

        # Action Buttons
        tk.Button(self.root, text="Browse .bat File", command=self.browse_file, width=20).pack(pady=5)
        tk.Button(self.root, text="Run Service Now", command=self.run_batch, width=20, bg="#e1f5fe").pack(pady=5)
        
        # Startup Button
        self.btn_startup = tk.Button(self.root, text="Enable Auto Startup", command=self.toggle_startup, width=20)
        self.btn_startup.pack(pady=5)
        self.check_startup_status()

        tk.Label(self.root, text="(Closing this window will hide it to system tray)", font=("Arial", 8), fg="gray").pack(side="bottom", pady=10)

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Batch Files", "*.bat")])
        if path:
            self.config["bat_path"] = path
            self.save_config()
            self.update_ui_status()

    def toggle_startup(self):
        key = winreg.HKEY_CURRENT_USER
        sub_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(key, sub_key, 0, winreg.KEY_ALL_ACCESS) as reg_key:
                if self.is_startup_enabled():
                    winreg.DeleteValue(reg_key, APP_NAME)
                    messagebox.showinfo("Startup", "Auto Startup Disabled")
                else:
                    winreg.SetValueEx(reg_key, APP_NAME, 0, winreg.REG_SZ, f'"{EXE_PATH}"')
                    messagebox.showinfo("Startup", "Auto Startup Enabled")
            self.check_startup_status()
        except Exception as e:
            messagebox.showerror("Error", f"Could not change startup settings: {e}")

    def is_startup_enabled(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except: return False

    def check_startup_status(self):
        if self.is_startup_enabled():
            self.btn_startup.config(text="Disable Auto Startup", fg="red")
        else:
            self.btn_startup.config(text="Enable Auto Startup", fg="green")

    def run_batch(self):
        path = self.config.get("bat_path")
        if path and os.path.exists(path):
            # รันแบบซ่อนหน้าต่าง
            self.bat_process = subprocess.Popen(f'cmd /c "{path}"', shell=True, creationflags=0x08000000)
            messagebox.showinfo("Execution", "Batch file started in background.")
        else:
            messagebox.showwarning("Warning", "Please select a valid .bat file first.")

    def update_ui_status(self):
        path = self.config.get("bat_path")
        if path and os.path.exists(path):
            self.lbl_file.config(text=f"File: {os.path.basename(path)}", fg="green")
        else:
            self.lbl_file.config(text="File: Missing or Not Selected", fg="red")

        if self.bat_process and self.bat_process.poll() is None:
            self.lbl_status.config(text="Status: Running", fg="blue")
        else:
            self.lbl_status.config(text="Status: Idle/Stopped", fg="gray")

    def update_status_loop(self):
        self.update_ui_status()
        self.root.after(2000, self.update_status_loop)

    def create_tray_icon(self):
        img = Image.new('RGB', (64, 64), color=(0, 150, 136))
        d = ImageDraw.Draw(img)
        d.rectangle([10, 10, 54, 54], fill=(255, 255, 255))
        
        menu = (item('Open Control Panel', self.show_window), item('Exit', self.quit_app))
        self.icon = pystray.Icon(APP_NAME, img, APP_NAME, menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def hide_window(self):
        self.root.withdraw()

    def show_window(self):
        self.root.deiconify()

    def quit_app(self):
        self.icon.stop()
        self.root.quit()

if __name__ == "__main__":
    if is_admin():
        app = ServiceGuardApp()
        app.root.mainloop()
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
