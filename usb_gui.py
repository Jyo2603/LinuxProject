import tkinter as tk
from tkinter import ttk
import time
import threading

PROC_PATH = "/proc/usb_monitor"

def read_usb_stats():
    try:
        with open(PROC_PATH, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading {PROC_PATH}:\n{str(e)}"

def update_stats():
    while True:
        stats = read_usb_stats()
        output_text.set(stats)
        time.sleep(1)

# Create GUI
root = tk.Tk()
root.title("USB Monitor - LKM Interface")
root.geometry("500x300")
root.configure(bg="#f0f0f0")

output_text = tk.StringVar()
label = ttk.Label(root, textvariable=output_text, justify="left", background="#f0f0f0", font=("Courier", 10))
label.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

# Run thread for continuous update
threading.Thread(target=update_stats, daemon=True).start()

root.mainloop()
