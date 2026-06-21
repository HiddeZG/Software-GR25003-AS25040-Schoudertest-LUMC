import nidaqmx
from nidaqmx.constants import AcquisitionType, TerminalConfiguration
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from tkinter import simpledialog
from datetime import datetime
import os
import json
import threading
from collections import deque

#%% Realtime EMG Signaal 

window = tk.Tk()
window.title("Start Validatie meting")

label = tk.Label(window, text="Druk op de knop om Validatie te starten (20 seconden):", font=("Arial", 12))
label.pack(pady=10)

countdown_label = tk.Label(window, text="", font=("Arial", 24), fg="blue")
countdown_label.pack(pady=5)

def update_countdown(seconds_left):
    if seconds_left > 0:
        countdown_label.config(text=f"{seconds_left} sec")
        window.after(1000, update_countdown, seconds_left - 1)
    else:
        countdown_label.config(text="✅ Klaar!")

device = "Dev2"
channels = ["1", "2", "3", "4", "0"]
sample_rate = 1000 
n_channels = len(channels)
data_list = []

buffer_size = 5000

emg_buffer_1 = deque(maxlen = buffer_size) 
emg_buffer_2 = deque(maxlen = buffer_size)
emg_buffer_3 = deque(maxlen = buffer_size)
emg_buffer_4 = deque(maxlen = buffer_size)

def start_acquisition():
    start_btn.config(state=tk.DISABLED)
    update_countdown(20)

    def acquire():
        with nidaqmx.Task() as task:
            for ch in channels:
                task.ai_channels.add_ai_voltage_chan(
                    f"{device}/ai{ch}",
                    terminal_config=TerminalConfiguration.DIFF
                )
            task.timing.cfg_samp_clk_timing(
                rate=sample_rate,
                sample_mode=AcquisitionType.CONTINUOUS,
            )

            task.start()
            print("⏳ Recording started for 10 seconds...")

            plt.ion()
            fig, axs = plt.subplots(4,1)
            line1, = axs[0].plot([])
            line2, = axs[1].plot([])
            line3, = axs[2].plot([])
            line4, = axs[3].plot([])

            axs[0].set_title("Realtime EMG anterior right")
            axs[0].set_xlabel("Samples")
            axs[0].set_ylabel("Voltage")
            axs[1].set_title("Realtime EMG Posterior right")
            axs[1].set_xlabel("Samples")
            axs[1].set_ylabel("Voltage")
            axs[2].set_title("Realtime EMG anterior left")
            axs[2].set_ylabel("Voltage")
            axs[3].set_title("Realtime EMG posterior left")
            axs[3].set_xlabel("Samples")
            axs[3].set_ylabel("Voltage")

            axs[0].set_ylim(-1,1)
            axs[1].set_ylim(-1.5,1.5)
            axs[2].set_ylim(-1,1)
            axs[3].set_ylim(-1.5,1.5)

            try:
                start_time = datetime.now()
                while (datetime.now() - start_time).total_seconds() < 20:
                    values = task.read(number_of_samples_per_channel=100)
                    values = np.array(values).T
                    for v in values:
                        data_list.append(v)
                        emg_buffer_1.append(v[0])
                        emg_buffer_2.append(v[1])
                        emg_buffer_3.append(v[2])
                        emg_buffer_4.append(v[3])

                    line1.set_data(range(len(emg_buffer_1)), list(emg_buffer_1))
                    axs[0].set_xlim(0, buffer_size)
                    line2.set_data(range(len(emg_buffer_2)), list(emg_buffer_2))
                    axs[1].set_xlim(0, buffer_size)
                    line3.set_data(range(len(emg_buffer_3)), list(emg_buffer_3))
                    axs[2].set_xlim(0, buffer_size)
                    line4.set_data(range(len(emg_buffer_4)), list(emg_buffer_4))
                    axs[3].set_xlim(0, buffer_size)

                    plt.pause(0.01) 

                print("🛑 Recording auto-stopped after 20 seconds.")

            except Exception as e:
                print(f"⚠️ Error during acquisition: {e}")
            finally:
                task.stop()
                plt.close('all')
                window.quit()

    threading.Thread(target=acquire, daemon=True).start()

start_btn = tk.Button(window, text="▶ Start meting", font=("Arial", 14), bg="green", fg="white", command=start_acquisition)
start_btn.pack(pady=10)

window.mainloop()
window.destroy()

#%% GUI Invullen RoM

root = tk.Tk()

ptnr   = simpledialog.askstring( "Participant Info",   "Participant number:", parent=root )
root.withdraw()

anteflexion_rom_right = simpledialog.askstring( "Participant Info",   "Anteflexion ROM right(degrees):", parent=root )
abduction_rom_right = simpledialog.askstring( "Participant Info",   "Abduction ROM right (degrees):", parent=root )
retroflexion_rom_right   = simpledialog.askstring( "Participant Info",   "Retroflexion ROM right (degrees):", parent=root )

anteflexion_rom_left = simpledialog.askstring( "Participant Info",   "Anteflexion ROM left (degrees):", parent=root )
abduction_rom_left = simpledialog.askstring( "Participant Info",   "Abduction ROM left (degrees):", parent=root )
retroflexion_rom_left   = simpledialog.askstring( "Participant Info",   "Retroflexion ROM left (degrees):", parent=root )
root.withdraw()

print("✅ Questions completed. Continuing…")

filename = f"measurements_{ptnr}_ROM.json"
folder_name = f"measurements_{ptnr}"

folder_path = os.path.join(os.getcwd(), folder_name) 
os.makedirs(folder_path, exist_ok=True)

save_path = os.path.join(folder_path, filename)
if os.path.exists(save_path):
    with open(save_path, 'r') as f:
        measurement_values = json.load(f)
else:
    measurement_values = {"participant": ptnr,
                          "anteflexion_rom_right": anteflexion_rom_right,
                          "abduction_rom_right": abduction_rom_right,
                          "retroflexion_rom_right": retroflexion_rom_right,
                          "anteflexion_rom_left": anteflexion_rom_left,
                          "abduction_rom_left": abduction_rom_left,
                          "retroflexion_rom_left": retroflexion_rom_left}
    
with open(save_path, 'w') as f:
    json.dump(measurement_values, f, indent=4)
print("✅ Measurement values saved to", save_path)
