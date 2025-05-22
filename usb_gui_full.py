import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

PROC_PATH = "/proc/usb_monitor"

# Global state
plugged = 0
unplugged = 0
last_type = ""
last_power = ""
output_lines = ""
is_running = True

def read_usb_stats():
    global plugged, unplugged, last_type, last_power, output_lines
    try:
        with open(PROC_PATH, "r") as f:
            data = f.readlines()
            output_lines = ''.join(data)
            for line in data:
                if "Plugged in count" in line:
                    plugged = int(line.strip().split(":")[1])
                if "Unplugged count" in line:
                    unplugged = int(line.strip().split(":")[1])
                if "Device Type" in line:
                    last_type = line.strip().split(":")[1].strip()
                if "Device Max Power" in line:
                    last_power = line.strip().split(":")[1].strip()
            return output_lines
    except Exception as e:
        return f"Error reading {PROC_PATH}:\n{str(e)}"

def update_gui():
    while is_running:
        stats = read_usb_stats()
        if output_text.get() != stats:
            output_text.set(stats)
            notify_change(stats)
            update_chart()
        time.sleep(1)

def toggle_power_mode():
    global last_power_path
    try:
        with open(PROC_PATH, "r") as f:
            for line in f:
                if "Power Control at" in line:
                    path = line.strip().split(": ", 1)[1]
                    last_power_path = path
        if not os.path.exists(last_power_path):
            messagebox.showerror("Error", f"Power control path not found:\n{last_power_path}")
            return
        with open(last_power_path, "r") as f:
            current = f.read().strip()
        new_mode = "on" if current == "auto" else "auto"
        with open(last_power_path, "w") as f:
            f.write(new_mode)
        messagebox.showinfo("Power Mode Toggled", f"New mode: {new_mode}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def export_stats():
    file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file:
        with open(file, "w") as f:
            f.write(output_lines)
        messagebox.showinfo("Exported", f"Saved to {file}")

def notify_change(stats):
    if not root.winfo_exists():
        return
    lines = stats.splitlines()
    for line in lines:
        if "Plugged in count" in line:
            count = int(line.split(":")[1].strip())
            if count > notify_change.last_plug:
                root.after(100, lambda: messagebox.showinfo("USB Monitor", "USB Device Plugged In"))
            notify_change.last_plug = count
        if "Unplugged count" in line:
            count = int(line.split(":")[1].strip())
            if count > notify_change.last_unplug:
                root.after(100, lambda: messagebox.showwarning("USB Monitor", "USB Device Unplugged"))
            notify_change.last_unplug = count
notify_change.last_plug = 0
notify_change.last_unplug = 0

def update_chart():
    chart_ax.clear()
    chart_ax.bar(["Plugged", "Unplugged"], [plugged, unplugged], color=["green", "red"])
    chart_ax.set_ylim(0, max(2, plugged + unplugged))
    chart_ax.set_title("USB Plug/Unplug Count", fontsize=10)
    chart_ax.set_ylabel("Count", fontsize=9)
    canvas.draw()

def on_quit():
    global is_running
    is_running = False
    root.destroy()

# --- GUI Setup ---
root = tk.Tk()
root.title("USB Monitor – LKM Dashboard")
root.geometry("620x530")
root.configure(bg="#f4f4f4")

style = ttk.Style()
style.configure("TButton", padding=6, font=("Segoe UI", 9))
style.configure("TLabel", font=("Courier", 10))

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

output_text = tk.StringVar()
output_label = ttk.Label(main_frame, textvariable=output_text, justify="left", anchor="w", background="white", relief="solid")
output_label.pack(fill=tk.BOTH, expand=False, pady=10, ipady=6)

info_frame = ttk.Frame(main_frame)
info_frame.pack(pady=5)
ttk.Label(info_frame, text="Device Type: ").grid(row=0, column=0, sticky='w')
ttk.Label(info_frame, textvariable=tk.StringVar(value=last_type)).grid(row=0, column=1, sticky='w', padx=10)
ttk.Label(info_frame, text="Max Power: ").grid(row=0, column=2, sticky='w')
ttk.Label(info_frame, textvariable=tk.StringVar(value=last_power)).grid(row=0, column=3, sticky='w', padx=10)

btn_frame = ttk.Frame(main_frame)
btn_frame.pack(pady=10)
ttk.Button(btn_frame, text="Toggle Power Mode", command=toggle_power_mode).grid(row=0, column=0, padx=10)
ttk.Button(btn_frame, text="Export Stats", command=export_stats).grid(row=0, column=1, padx=10)
ttk.Button(btn_frame, text="Quit", command=on_quit).grid(row=0, column=2, padx=10)

# Chart
fig, chart_ax = plt.subplots(figsize=(4.8, 2.5))
canvas = FigureCanvasTkAgg(fig, master=main_frame)
canvas.get_tk_widget().pack(pady=10)

threading.Thread(target=update_gui, daemon=True).start()

root.mainloop()
