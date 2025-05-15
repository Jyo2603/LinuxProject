import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

PROC_PATH = "/proc/usb_monitor"

# Global counters
plugged = 0
unplugged = 0
last_power_path = None

def read_usb_stats():
    global plugged, unplugged, last_power_path
    try:
        with open(PROC_PATH, "r") as f:
            data = f.readlines()
            for line in data:
                if "Plugged in count" in line:
                    plugged = int(line.strip().split(":")[1])
                if "Unplugged count" in line:
                    unplugged = int(line.strip().split(":")[1])
                if "Power Control at" in line:
                    last_power_path = line.strip().split(": ", 1)[1]
            return ''.join(data)
    except Exception as e:
        return f"Error reading {PROC_PATH}:\n{str(e)}"

def update_gui():
    prev = ""
    while True:
        stats = read_usb_stats()
        if output_text.get() != stats:
            output_text.set(stats)
            notify_change(stats)
            update_chart()
        time.sleep(1)

def toggle_power_mode():
    global last_power_path
    if not last_power_path or not os.path.exists(last_power_path):
        messagebox.showerror("Error", f"Power control path missing:\n{last_power_path}")
        return
    try:
        with open(last_power_path, "r") as f:
            current_mode = f.read().strip()
        new_mode = "on" if current_mode == "auto" else "auto"
        with open(last_power_path, "w") as f:
            f.write(new_mode)
        messagebox.showinfo("Power Toggled", f"Power mode set to '{new_mode}'")
    except PermissionError:
        messagebox.showerror("Permission Denied", "Try: sudo chmod o+w " + last_power_path)
    except Exception as e:
        messagebox.showerror("Error", f"Toggle failed:\n{str(e)}")


def export_stats():
    stats = output_text.get()
    file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file:
        with open(file, "w") as f:
            f.write(stats)
        messagebox.showinfo("Exported", f"Saved to {file}")

def notify_change(stats):
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
    chart_ax.set_ylim(0, max(plugged, unplugged) + 2)
    chart_ax.set_title("USB Plug/Unplug Count")
    chart_ax.set_ylabel("Count")
    canvas.draw()

# GUI setup
root = tk.Tk()
root.title("USB Monitor – LKM Dashboard")
root.geometry("600x500")

frame = ttk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

output_text = tk.StringVar()
label = ttk.Label(frame, textvariable=output_text, justify="left", font=("Courier", 10))
label.pack(fill=tk.X, pady=5)

btn_frame = ttk.Frame(root)
btn_frame.pack(pady=5)

ttk.Button(btn_frame, text="Toggle Power Mode", command=toggle_power_mode).grid(row=0, column=0, padx=10)
ttk.Button(btn_frame, text="Export Stats", command=export_stats).grid(row=0, column=1, padx=10)

# Matplotlib chart
fig, chart_ax = plt.subplots(figsize=(4, 2.5))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(pady=10)

# Background thread
threading.Thread(target=update_gui, daemon=True).start()

root.mainloop()
