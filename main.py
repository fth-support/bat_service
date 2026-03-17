import os
import sys
import subprocess
import json
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

CONFIG_FILE = "config.json"
PASSWORD = "1234" # คุณสามารถเปลี่ยนรหัสผ่านตรงนี้ได้

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class ServiceGuard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.load_config()
        self.icon = None

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {"bat_path": ""}

    def save_config(self, path):
        self.config["bat_path"] = path
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)

    def run_batch_silent(self, icon=None, item=None):
        bat_path = self.config.get("bat_path")
        if bat_path and os.path.exists(bat_path):
            # รัน cmd แบบซ่อนหน้าต่างสนิท (0x08000000 = CREATE_NO_WINDOW)
            subprocess.Popen(f'cmd /c "{bat_path}"', shell=True, creationflags=0x08000000)
        else:
            if icon: # ถ้ากดจากเมนูแล้วไม่มีไฟล์ให้เตือน
                messagebox.showwarning("Error", "ไม่พบไฟล์ .bat โปรดตั้งค่า Path ใหม่")

    def check_password(self):
        answer = simpledialog.askstring("Password Required", "กรุณาใส่รหัสผ่านเพื่อดำเนินการ:", show='*')
        return answer == PASSWORD

    def select_path(self, icon, item):
        if self.check_password():
            path = filedialog.askopenfilename(title="เลือกไฟล์ .bat", filetypes=[("Batch Files", "*.bat")])
            if path:
                self.save_config(path)
                messagebox.showinfo("Success", f"ตั้งค่าไฟล์สำเร็จ:\n{path}")
        else:
            messagebox.showerror("Denied", "รหัสผ่านไม่ถูกต้อง")

    def exit_prog(self, icon, item):
        if self.check_password():
            icon.stop()
            self.root.quit()
        else:
            messagebox.showerror("Denied", "รหัสผ่านไม่ถูกต้อง")

    def create_tray_icon(self):
        # สร้าง Icon สี่เหลี่ยมสีน้ำเงิน (คุณสามารถเปลี่ยนเป็นไฟล์ .ico ของคุณเองได้ในอนาคต)
        img = Image.new('RGB', (64, 64), color=(0, 120, 215))
        d = ImageDraw.Draw(img)
        d.text((10, 20), "SVC", fill=(255, 255, 255))

        menu = (
            item('Run Service Now', self.run_batch_silent),
            item('Settings (Change Path)', self.select_path),
            item('Exit', self.exit_prog)
        )
        self.icon = pystray.Icon("ServiceGuard", img, "Service Guard (Admin Mode)", menu)
        
        # Auto-run batch ทันทีที่เปิดโปรแกรมครั้งแรก
        if self.config["bat_path"]:
            self.run_batch_silent()
            
        self.icon.run()

if __name__ == "__main__":
    if is_admin():
        app = ServiceGuard()
        app.create_tray_icon()
    else:
        # ถ้าไม่มีสิทธิ์ Admin ให้เปิดตัวเองใหม่ด้วยสิทธิ์ Admin
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
