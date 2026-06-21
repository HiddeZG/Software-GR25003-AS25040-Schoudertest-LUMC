import nidaqmx
from nidaqmx.constants import AcquisitionType, TerminalConfiguration
import numpy as np
import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import json
import scipy.signal
import threading
from CCI import compute_cci

#%% GUI Condities

try:
    root.destroy()
except:
    pass

root = tk.Tk()
root.withdraw()

ptnr = simpledialog.askstring("Participant Info", "Participant number:", parent=root)

movement_options = {"Anteflexion": 1, "Retroflexion": 2}
angle_options = {"0 degrees": 1, "15 degrees": 2, "30 degrees": 3}
shoulder_options = {"Right": 1, "Left": 2}
resistance_options = {"30% MT": 1, "100% MT": 2}
repetitions_options = {"Rep 1": 1, "Rep 2": 2, "Rep 3": 3}

all_options = {
    "movement": movement_options, 
    "angle": angle_options, 
    "shoulder": shoulder_options, 
    "resistance": resistance_options, 
    "repetitions": repetitions_options
}
options = ["movement", "angle", "shoulder", "resistance", "repetitions"]

frame = tk.Toplevel(root)
frame.attributes('-topmost', True)

tk_vars = {}
choices = {} 

for i in options: 
    tk.Label(frame, text=f"Choose {i}").pack(padx=20, pady=5)
    current_option = all_options[i]
    tk_vars[i] = tk.IntVar(master=frame, value=1) 
    for text, val in current_option.items():
        tk.Radiobutton(frame, text=text, variable=tk_vars[i], value=val).pack(anchor="w", padx=20)

def submit_choice():
    for i, current_option in all_options.items():
        reverse = {val: key for key, val in current_option.items()}
        choices[i] = reverse[tk_vars[i].get()]
    frame.destroy()

tk.Button(frame, text="Submit", command=submit_choice).pack(pady=10)
frame.wait_window(frame) 

if not choices:
    print("❌ Selectie afgebroken door gebruiker.")
else:
    filename = f"measurements_{ptnr}_{choices['movement']}_{choices['angle']}_{choices['shoulder']}_{choices['resistance']}_{choices['repetitions']}.json"
    folder_name = f"measurements_{ptnr}"
    folder_path = os.path.join(os.getcwd(), folder_name) 
    os.makedirs(folder_path, exist_ok=True)
    save_path = os.path.join(folder_path, filename)

    offset_filename = f"measurements_{ptnr}_Anteflexion_{choices['angle']}_{choices['shoulder']}_100% MT_Rep 1.json"
    offset_path = os.path.join(folder_path, offset_filename)

    offset_key = f"Anteflexion_{choices['angle']}_{choices['shoulder']}_100% MT_Rep 1"

    if os.path.exists(offset_path):
        with open(offset_path, 'r') as f:
            offset_data_loaded = json.load(f)
            sleutel = "force_offset_median"

        if sleutel in offset_data_loaded:
            force_offset = offset_data_loaded["force_offset_median"]
            print(f"✅ Dynamische offset gevonden: {force_offset:.4f}")
        else:
            messagebox.showwarning(
                "Waarschuwing",
                f"'force_offset_median' niet gevonden onder key: {offset_key}"
            )

    if choices["resistance"] == "30% MT":
        gevonden_mt_waarden = []
        
        check_filename = f"measurements_{ptnr}_{choices['movement']}_{choices['angle']}_{choices['shoulder']}_100% MT_Rep 3.json"
        check_path = os.path.join(folder_path, check_filename)
        
        check_key = f"{choices['movement']}_{choices['angle']}_{choices['shoulder']}_100% MT_Rep 3"

        if os.path.exists(check_path):
            with open(check_path, 'r') as f:
                data_loaded = json.load(f)
                sleutel = "max_MT_nieuw_van_3_reps"
            
            if sleutel in data_loaded:
                gevonden_mt_waarden.append(
                    data_loaded["max_MT_nieuw_van_3_reps"]
                )

        if gevonden_mt_waarden:
            max_mt = gevonden_mt_waarden[0] 
            target_30 = max_mt * 0.3
            range_low = target_30 * 0.9625
            range_high = target_30 * 1.0375
            print(f"✅ Max MT gevonden in Rep 3: {max_mt:.2f}. Target 30%: {target_30:.2f} (Range: {range_low:.2f} - {range_high:.2f})")
        else:
            messagebox.showwarning("Waarschuwing", f"Geen 'max_MT_nieuw_van_3_reps' gevonden in het Rep 3 bestand voor participant {ptnr}.\nDe feedbackbalk heeft nu geen doelzone.")

    print("✅ Cel 1 afgerond. Ga naar Cel 2.")

root.destroy()

movement = choices["movement"]
angle = choices["angle"]
shoulder = choices["shoulder"]
resistance = choices["resistance"]
rep = choices["repetitions"]
key = f"{movement}_{angle}_{shoulder}_{resistance}_{rep}"

mvic_filename_posterior = f"measurements_{ptnr}_Retroflexion_{choices['angle']}_{choices['shoulder']}_100% MT_Rep 3.json"
mvic_folder_name = f"measurements_{ptnr}"
mvic_dir_posterior = os.path.join(os.getcwd(), mvic_folder_name)  
load_path_posterior = os.path.join(mvic_dir_posterior, mvic_filename_posterior)

mvic_filename_anterior = f"measurements_{ptnr}_Anteflexion_{choices['angle']}_{choices['shoulder']}_100% MT_Rep 3.json"
mvic_folder_name = f"measurements_{ptnr}"
mvic_dir_anterior = os.path.join(os.getcwd(), mvic_folder_name)  
load_path_anterior = os.path.join(mvic_dir_anterior, mvic_filename_anterior)

if os.path.exists(load_path_anterior):
    with open(load_path_anterior, 'r') as f:
        mvic_data_anterior = json.load(f)
    print("Loaded MVIC values:")
    
else:
    print(f"❌ No MVIC file anterior found for participant {ptnr}")

if os.path.exists(load_path_posterior):
    with open(load_path_posterior, 'r') as f:
        mvic_data_posterior = json.load(f)
    print("Loaded MVIC values:")
   
else:
    print(f"❌ No MVIC file posterior found for participant {ptnr}")

rep3 = "Rep 3"
key_anterior = f"Anteflexion_{angle}_{shoulder}_100% MT_{rep3}"
key_posterior = f"Retroflexion_{angle}_{shoulder}_100% MT_{rep3}"

mvic_A = mvic_data_anterior["max_MVIC_nieuw_van_3_reps"]
print(mvic_A)
mvic_P = mvic_data_posterior["max_MVIC_nieuw_van_3_reps"]
print(mvic_P)

#%% Live Feedback 

if 'choices' in locals() and choices:
    try:
        if 'root' not in locals() or not root.winfo_exists():
            root = tk.Tk()
            root.withdraw()
    except Exception:
        root = tk.Tk()
        root.withdraw()

    window = tk.Toplevel(root)
    window.title("30% MVIC Feedback & Acquisitie")
    window.geometry("450x600")

    label = tk.Label(window, text="Breng de krachtmeter in de groene zone:", font=("Arial", 12))
    label.pack(pady=10)

    live_force_label = tk.Label(window, text="Huidige Kracht: 0.00", font=("Arial", 14, "bold"))
    live_force_label.pack()

    canvas_width = 100
    canvas_height = 300
    canvas = tk.Canvas(window, width=canvas_width, height=canvas_height, bg="#ddd")
    canvas.pack(pady=20)

    max_scale = max(target_30 * 2, 10.0)

    def force_to_y(force_val):
        pct = min(max(force_val / max_scale, 0.0), 1.0)
        return canvas_height - (pct * canvas_height)

    y_high = force_to_y(range_high)
    y_low = force_to_y(range_low)
    canvas.create_rectangle(0, y_high, canvas_width, y_low, fill="#9bf6ff", outline="")
    canvas.create_text(canvas_width/2, (y_high+y_low)/2, text="30% Zone", fill="#004e64", font=("Arial", 9, "bold"))

    balk = canvas.create_rectangle(15, canvas_height, canvas_width-15, canvas_height, fill="orange")
    countdown_label = tk.Label(window, text="", font=("Arial", 22), fg="blue")
    countdown_label.pack(pady=5)

    device = "Dev2"
    channels = ["1", "2", "3", "4", "0"] 
    sample_rate = 1000

    running = True
    acquisition_started = False
    measurement_valid = False
    data_list = []
    failed_samples = 0
    max_failed_samples = 500 

    def abort_measurement():
        global acquisition_started, running, measurement_valid, data_list
        acquisition_started = False
        running = False
        measurement_valid = False 
        data_list = [] 
        messagebox.showerror("Meting Mislukt", "Langer dan 0.5s onafgebroken buiten de range! De meting is gereset.")
        try:
            window.quit()
            window.destroy()
        except:
            pass

    def update_gui_feedback(current_force):
        if not window.winfo_exists() or not running:
            return
            
        live_force_label.config(text=f"Huidige Kracht: {current_force:.2f}")
        y_val = force_to_y(current_force)
        canvas.coords(balk, 15, y_val, canvas_width-15, canvas_height)
        
        in_zone = (range_low <= current_force <= range_high)
            
        if in_zone:
            canvas.itemconfig(balk, fill="#4cc9f0")
            if not acquisition_started:
                start_btn.config(state=tk.NORMAL, bg="green")
        else:
            canvas.itemconfig(balk, fill="orange")
            if not acquisition_started:
                start_btn.config(state=tk.DISABLED, bg="grey")

    def live_stream():
        global data_list, acquisition_started, running, failed_samples, measurement_valid
        try:
            with nidaqmx.Task() as task:
                for ch in channels:
                    task.ai_channels.add_ai_voltage_chan(f"{device}/ai{ch}", terminal_config=TerminalConfiguration.DIFF)
                task.timing.cfg_samp_clk_timing(rate=sample_rate, sample_mode=AcquisitionType.CONTINUOUS)
                task.start()
                
                while running:
                    try:
                        values = task.read(number_of_samples_per_channel=50)
                        values = np.array(values).T
                        
                        force_raw_last = values[-1, 4]
                        current_force_last = np.abs(force_raw_last - force_offset) / 0.2
                        current_force_last = np.abs(force_raw_last - force_offset) / 0.2
                        
                        if running and window.winfo_exists():
                            window.after(0, update_gui_feedback, current_force_last)
                        
                        if acquisition_started and running:
                            for v in values:
                                data_list.append(v)
                                
                                sample_force = np.abs(v[4] - force_offset) / 0.2
                                sample_force = np.abs(v[4] - force_offset) / 0.2
                                sample_in_zone = (range_low <= sample_force <= range_high)
                                
                                if not sample_in_zone:
                                    failed_samples += 1
                                    if failed_samples > max_failed_samples:
                                        running = False
                                        acquisition_started = False
                                        measurement_valid = False
                                        window.after(0, abort_measurement)
                                        break
                                else:
                                    failed_samples = 0 
                                    
                    except Exception:
                        break
                task.stop()
        except Exception as ni_err:
            print(f"⚠️ NI-kaart verbindingsfout: {ni_err}")

    threading.Thread(target=live_stream, daemon=True).start()

    def update_countdown(seconds_left):
        global measurement_valid, running, acquisition_started
        if not running:
            return
        if seconds_left > 0 and acquisition_started and window.winfo_exists():
            countdown_label.config(text=f"Meten... {seconds_left} sec")
            window.after(1000, update_countdown, seconds_left - 1)
        elif acquisition_started and window.winfo_exists():
            acquisition_started = False 
            countdown_label.config(text="✅ Klaar!")
            measurement_valid = True  
            window.after(500, lambda: [window.quit(), window.destroy()])

    def start_acquisition():
        global acquisition_started, failed_samples, data_list
        data_list = []
        failed_samples = 0
        acquisition_started = True
        start_btn.config(state=tk.DISABLED, bg="grey")
        update_countdown(5)

    start_btn = tk.Button(window, text="▶ Start 5s Meting", font=("Arial", 14), bg="grey", fg="white", state=tk.DISABLED, command=start_acquisition)
    start_btn.pack(pady=15)

    def on_closing():
        global running, measurement_valid, data_list
        running = False
        measurement_valid = False
        data_list = []
        window.quit()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()
    running = False
    print("✅ Cel 2 afgerond. Ga naar Cel 3.")

#%% Data Opslag

def lowpass(data, cutoff, fs, poles=4):
    sos = scipy.signal.butter(N=poles, Wn=cutoff, btype='low', fs=fs, output='sos')
    return scipy.signal.sosfiltfilt(sos, data, axis=0)

def moving_rms(data, window_ms, fs):
    w = int(window_ms/1000 * fs) or 1
    sq = data**2
    kernel = np.ones(w) / w
    rms = np.empty_like(data)
    for ch in range(data.shape[1]):
        ms = np.convolve(sq[:, ch], kernel, mode='same')
        rms[:, ch] = np.sqrt(ms)
    return rms

def highpass(data, cutoff, fs, poles=4):
    sos = scipy.signal.butter(N=poles,Wn=cutoff,btype='high', fs=fs,output='sos')
    return scipy.signal.sosfiltfilt(sos, data, axis=0)

def filter_emg(data):
    emg_hp = highpass(data, cutoff=20, fs=1000)  
    emg_filtered = lowpass(emg_hp, cutoff=450, fs=1000) 
    emg_rms = moving_rms(emg_filtered, window_ms=100, fs=1000) 
    
    return emg_rms

if 'measurement_valid' in locals() and measurement_valid and len(data_list) > 0:
    print("✅ Succesvolle meting! Ruwe data exporteren...")
    data = np.array(data_list)
    emg_filtered = filter_emg(data[:,:4])

    if choices["shoulder"] == "Right":
        raw_emg_ad = data[:, 0].tolist()  
        raw_emg_pd = data[:, 1].tolist()  
        filtered_emg_ad = emg_filtered[:,0].tolist()
        filtered_emg_pd = emg_filtered[:,1].tolist()
        filtered_emg_ad_Normaliseert = emg_filtered[:,0] / mvic_A
        filtered_emg_pd_Normaliseert = emg_filtered[:,1]/ mvic_P
        CCI_t, CCI = compute_cci(movement, filtered_emg_ad_Normaliseert , filtered_emg_pd_Normaliseert)   

    else:
        raw_emg_ad = data[:, 2].tolist()  
        raw_emg_pd = data[:, 3].tolist()  
        filtered_emg_ad = emg_filtered[:,2].tolist()
        filtered_emg_pd = emg_filtered[:,3].tolist()
        filtered_emg_ad_Normaliseert = emg_filtered[:,2] / mvic_A
        filtered_emg_pd_Normaliseert = emg_filtered[:,3]/ mvic_P
        CCI_t, CCI = compute_cci(movement, filtered_emg_ad_Normaliseert , filtered_emg_pd_Normaliseert)  
   
    force_calibrated = ((np.abs(data[:, 4] - force_offset)) / 0.2).tolist()

    measurement_values = {
        "participant": ptnr,
        "movement": choices["movement"],
        "angle": choices["angle"],
        "shoulder": choices["shoulder"],
        "resistance": choices["resistance"],
        "repetitions": choices["repetitions"],
        "CCI" : CCI,
        "Raw EMG AD" : raw_emg_ad,
        "Raw EMG PD" : raw_emg_pd,
        "Filtered EMG AD" : filtered_emg_ad,
        "Filtered EMG PD" : filtered_emg_pd,
        "CCI_t" : CCI_t.tolist(),
        "force_calibrated" : force_calibrated
        }
    
    with open(save_path, 'w') as f:
        json.dump(measurement_values, f, indent=4)
    print(f"💾 Ruwe data succesvol opgeslagen in: {filename}")
else:
    print("❌ Meting mislukt, afgebroken of handmatig gesloten. Er is GEEN data opgeslagen.")

try:
    root.destroy()
except:
    pass

