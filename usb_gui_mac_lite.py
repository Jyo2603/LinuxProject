import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import subprocess
import os

# Global counters
plugged = 0
unplugged = 0
last_power_path = "/dev/null"

def read_usb_stats():
    global plugged, unplugged, last_power_path
    try:
        output = subprocess.check_output(["system_profiler", "SPUSBDataType"], text=True)
        is_usb_present = "USB" in output and ("Mass Storage" in output or "USB Type-C" in output)

        if is_usb_present and not read_usb_stats.last_state:
            plugged += 1
            read_usb_stats.last_state = True
        elif not is_usb_present and read_usb_stats.last_state:
            unplugged += 1
            read_usb_stats.last_state = False

        return f"USB Monitor (macOS Lite Mode)\n\nPlugged in count: {plugged}\nUnplugged count: {unplugged}\nPower Control at: {last_power_path}"
    except Exception as e:
        return f"Error fetching USB info:\n{str(e)}"

read_usb_stats.last_state = False

def update_gui():
    while True:
        stats = read_usb_stats()
        output_text.set(stats)
        notify_change(stats)
        time.sleep(1)

def toggle_power_mode():
    messagebox.showinfo("Unsupported", "Power control is not supported on macOS.")

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

# GUI setup
root = tk.Tk()
root.title("USB Monitor – macOS Lite")
root.geometry("500x400")

frame = ttk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

output_text = tk.StringVar()
output_text.set("Monitoring USB Type-C device...\n")
label = ttk.Label(frame, textvariable=output_text, justify="left", font=("Courier", 10))
label.pack(fill=tk.BOTH, expand=True, pady=5)

btn_frame = ttk.Frame(root)
btn_frame.pack(pady=10)

ttk.Button(btn_frame, text="Toggle Power Mode", command=toggle_power_mode).grid(row=0, column=0, padx=10)
ttk.Button(btn_frame, text="Export Stats", command=export_stats).grid(row=0, column=1, padx=10)

# Background thread
threading.Thread(target=update_gui, daemon=True).start()

root.mainloop()
