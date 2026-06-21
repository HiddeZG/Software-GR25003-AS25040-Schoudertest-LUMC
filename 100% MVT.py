import nidaqmx
from nidaqmx.constants import AcquisitionType, TerminalConfiguration
import numpy as np
import tkinter as tk
from tkinter import simpledialog
from datetime import datetime
import os
import json
import scipy.signal
import threading

#%% GUI Condities

root = tk.Tk()

ptnr = simpledialog.askstring( "Participant Info",   "Participant number:", parent=root )
root.withdraw()

movement_options = {"Anteflexion":1, "Retroflexion":2}
angle_options = {"0 degrees":1, "15 degrees":2, "30 degrees":3}
shoulder_options = {"Right":1, "Left": 2}
resistance_options = {"30% MT":1, "100% MT":2}

repetitions_options = {"Rep 1": 1, "Rep 2": 2, "Rep 3": 3}
reverse_repetitions = {val:key for key,val in repetitions_options.items()}
all_options = {"movement": movement_options, 
               "angle": angle_options, 
               "shoulder": shoulder_options, 
               "resistance": resistance_options, 
               "repetitions": repetitions_options}

options = ["movement", "angle", "shoulder", "resistance", "repetitions"]
frame = tk.Toplevel(root)
frame.attributes('-topmost', True)
tk_vars = {}

for i in options: 
    tk.Label(frame, text=f"Choose {i}").pack(padx=20, pady=10)
    current_option = all_options[f"{i}"]
    reverse = {val:key for key,val in current_option.items()}
    tk_vars[i] = tk.IntVar(value=1)
    for text, val in current_option.items():
        tk.Radiobutton(frame, text=text, variable=tk_vars[i] , value=val).pack(anchor="w", padx=20)

def submit_choice():
    global choices
    choices = {}
    for i, current_option in all_options.items():
        reverse = {val: key for key, val in current_option.items()}
        number = tk_vars[i].get()
        choices[i] = reverse[number]
            
    print("All choices saved:", choices)
    frame.destroy()
    root.quit()

tk.Button(frame, text="Submit", command=submit_choice).pack(pady=10)

root.mainloop()   
root.destroy()
print("✅ Questions completed. Continuing…")

filename = f"measurements_{ptnr}_{choices['movement']}_{choices['angle']}_{choices['shoulder']}_{choices['resistance']}_{choices['repetitions']}.json"
folder_name = f"measurements_{ptnr}"

folder_path = os.path.join(os.getcwd(), folder_name) 
os.makedirs(folder_path, exist_ok=True)

save_path = os.path.join(folder_path, filename)

if os.path.exists(save_path):
    with open(save_path, 'r') as f:
        measurement_values = json.load(f)
else:
    measurement_values = {"participant": ptnr,
                        "movement": choices["movement"],
                        "angle": choices["angle"],
                        "shoulder": choices["shoulder"],
                        "resistance": choices["resistance"],
                        "repetitions": choices["repetitions"],
                        "data": []}


#%% Pre-Processing Functies

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

#%% Data Aqcuisitie 

device = "Dev2"
channels = ["1", "2", "3", "4","0"]
sample_rate = 1000  # Hz
n_channels = len(channels)
data_list = []
offset_list = []
measurement_phase = 1

window = tk.Tk()
window.title("Start MVIC measurement")

label = tk.Label(window, text="", font=("Arial", 12))
label.pack(pady=10)

countdown_label = tk.Label(window, text="", font=("Arial", 24), fg="blue")
countdown_label.pack(pady=5)

def update_countdown(seconds_left):
    if seconds_left > 0:
        countdown_label.config(text=f"{seconds_left} sec")
        window.after(1000, update_countdown, seconds_left - 1)
    else:
        countdown_label.config(text="✅ Ready!")

movement = choices["movement"]
angle = choices["angle"]
shoulder = choices["shoulder"]
resistance = choices["resistance"]
rep = choices["repetitions"]
key = f"{movement}_{angle}_{shoulder}_{resistance}_{rep}"

if measurement_phase == 1 and rep == "Rep 1" and movement == "Anteflexion":
    label.config(text="Druk op de knop voor de meting in rust")
    start_button_text = "▶ Start rustmeting"
else:
    label.config(text="Druk op de knop voor de krachtmeting")
    start_button_text = "▶ Start krachtmeting"

#%% Start Functie

def start_acquisition():
    global measurement_phase
    start_btn.config(state=tk.DISABLED)
    duration = 2 if measurement_phase == 1 and rep == "Rep 1" and movement == "Anteflexion" else 5
    update_countdown(duration)

    def acquire():
        global measurement_phase 
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
            if measurement_phase == 1 and rep == "Rep 1" and movement == "Anteflexion": 
                current_duration = 2 
                label.config(text="Druk op de knop voor de meting in rust")
            else:
                current_duration = 5 
                label.config(text="Druk op de knop voor de krachtmeting")

            print(f"⏳ Recording started for {current_duration} seconds...")

            try:
                start_time = datetime.now()
                while (datetime.now() - start_time).total_seconds() < current_duration:
                    values = task.read(number_of_samples_per_channel=500)
                    values = np.array(values).T
                    if measurement_phase == 1 and rep == "Rep 1" and movement == "Anteflexion":
                        for v in values:
                            offset_list.append(v)
                    else:
                        
                        for v in values:
                            data_list.append(v)

                print(f"⏳ Recording started for {current_duration} seconds...")

            except Exception as e:
                print(f"⚠️ Error during acquisition: {e}")
            finally:
                task.stop()

                if measurement_phase == 1 and rep == "Rep 1" and movement == "Anteflexion":
                    print("Offsetmeting klaar")
                    measurement_phase = 2
                    label.config(text = "Druk op de knop voor de krachtmeting")
                    start_btn.config(state=tk.NORMAL, text="▶ Kracht zetten")
                else:
                    print("meting klaar")
                    window.quit()

    threading.Thread(target=acquire, daemon=True).start()

start_btn = tk.Button(
    window,
    text=start_button_text,
    font=("Arial", 14),
    bg="green",
    fg="white",
    command=start_acquisition
)

start_btn.pack(pady=10)

window.mainloop()
window.destroy()

#%% Signalen Preprocessen

data = np.array(data_list)

if rep == "Rep 1" and movement == "Anteflexion":
    force_offset = np.array(offset_list)[:,4]
    force_offset_median = np.median(force_offset)
    

else:
    rep1 = "Rep 1"

    filename_ophalen_offset = (
        f"measurements_{ptnr}_Anteflexion_{choices['angle']}_"
        f"{choices['shoulder']}_{choices['resistance']}_{rep1}.json"
    )

    folder_name_ophalen_offset = f"measurements_{ptnr}"

    folder_path_ophalen_offset = os.path.join(
        os.getcwd(),
        folder_name_ophalen_offset
    )

    offset_path = os.path.join(
        folder_path_ophalen_offset,
        filename_ophalen_offset
    )

    with open(offset_path, 'r') as f:
        measurement_values_offset = json.load(f)

    force_offset_median = np.array(
        measurement_values_offset["force_offset_median"]
    )
    
emg_filtered = filter_emg(data[:,:4])
force_raw = data[:,4]
force = np.abs(force_raw - force_offset_median)
window_size = 100

#%% MVIC Opslaan per Meting

if shoulder == "Right":
    AD_channel = emg_filtered[:,0]
    PD_channel = emg_filtered[:,1]
    AD_moving_avg = np.convolve(AD_channel, np.ones(window_size)/window_size, mode='valid')
    mvic_AD = np.max(AD_moving_avg)
    PD_moving_avg = np.convolve(PD_channel, np.ones(window_size)/window_size, mode='valid')
    mvic_PD = np.max(PD_moving_avg)
    Max_Kracht = np.max(force / 0.2)
    raw_emg_ad = data[:,0].tolist()
    raw_emg_pd = data[:,1].tolist()
    filtered_emg_ad = emg_filtered[:,0].tolist()
    filtered_emg_pd = emg_filtered[:,1].tolist()
    force_1 = force/0.2

    print(f"\n📈 MVIC value ({key}) \n anterior deltoid: {mvic_AD} \n posterior deltoid: {mvic_PD} \n maximum torque: {Max_Kracht} " )
    measurement_values = {
        "participant": ptnr,
        "movement": choices["movement"],
        "angle": choices["angle"],
        "shoulder": choices["shoulder"],
        "resistance": choices["resistance"],
        "repetitions": choices["repetitions"],
        "mvic_AD": float(mvic_AD),
        "mvic_PD": float(mvic_PD),
        "Max_kracht": float(Max_Kracht),
        "force_offset_median" : float(force_offset_median),
        "raw_emg_pd" : raw_emg_pd,
        "raw_emg_ad" : raw_emg_ad ,
        "filtered_emg_ad" :  filtered_emg_ad,
        "filtered_emg_pd" :  filtered_emg_pd,
        "force" : force_1.tolist()

    }
    
    raw_emg_ad = data[:,0].tolist()
    raw_emg_pd = data[:,1].tolist()
    filtered_emg_ad = emg_filtered[:,0].tolist()
    filtered_emg_pd = emg_filtered[:,1].tolist()

elif shoulder == "Left":
    AD_channel = emg_filtered[:, 2]
    PD_channel = emg_filtered[:,3]
    AD_moving_avg = np.convolve(AD_channel, np.ones(window_size)/window_size, mode='valid')
    mvic_AD = np.max(AD_moving_avg)
    PD_moving_avg = np.convolve(PD_channel, np.ones(window_size)/window_size, mode='valid')
    mvic_PD = np.max(PD_moving_avg)
    Max_Kracht = np.max(force / 0.2)
    raw_emg_ad = data[:,2].tolist()
    raw_emg_pd = data[:,3].tolist()
    filtered_emg_ad = emg_filtered[:,2].tolist()
    filtered_emg_pd = emg_filtered[:,3].tolist()
    force_1 = force/0.2

    print(f"\n📈 MVIC value ({key}) \n anterior deltoid: {mvic_AD} \n posterior deltoid: {mvic_PD} \n maximum torque: {Max_Kracht}")
    measurement_values = {
        "participant": ptnr,
        "movement": choices["movement"],
        "angle": choices["angle"],
        "shoulder": choices["shoulder"],
        "resistance": choices["resistance"],
        "repetitions": choices["repetitions"],
        "mvic_AD": float(mvic_AD),
        "mvic_PD": float(mvic_PD),
        "Max_kracht": float(Max_Kracht),
        "force_offset_median" : float(force_offset_median),
        "raw_emg_pd" : raw_emg_pd,
        "raw_emg_ad" : raw_emg_ad ,
        "filtered_emg_ad" :  filtered_emg_ad,
        "filtered_emg_pd" :  filtered_emg_pd,
        "force" : force_1.tolist()
    } 

    raw_emg_ad = data[:,2].tolist()
    raw_emg_pd = data[:,3].tolist()
    filtered_emg_ad = emg_filtered[:,2].tolist()
    filtered_emg_pd = emg_filtered[:,3].tolist()
    
#%% MVIC Opslaan 

if choices["repetitions"] == "Rep 3" and choices["resistance"] == "100% MT":
    print("\n🔄 Rep 3 voltooid! Automatische berekening van de maximale Max_Kracht start...")
    mt_values = []
    MVIC_values = []
    
    
    mt_values.append(measurement_values["Max_kracht"])
    print(f"   -> Rep 3: Max_Kracht = {measurement_values['Max_kracht']}")
    if movement == "Anteflexion": 
        MVIC_values.append(measurement_values["mvic_AD"])
    elif movement == "Retroflexion": 
        MVIC_values.append(measurement_values["mvic_PD"])
        
    for r in ["Rep 1", "Rep 2"]:
        check_filename = f"measurements_{ptnr}_{choices['movement']}_{choices['angle']}_{choices['shoulder']}_{choices['resistance']}_{r}.json"
        check_path = os.path.join(folder_path, check_filename)
        
        if os.path.exists(check_path):
            with open(check_path, 'r') as f:
                rep_data = json.load(f)
                
                valkracht = rep_data["Max_kracht"]
                mt_values.append(valkracht)
                print(f"   -> {r}: Max_kracht = {valkracht}")

                if movement == "Anteflexion": 
                    MVIC_rep_values = rep_data["mvic_AD"]
                elif movement == "Retroflexion": 
                    MVIC_rep_values = rep_data["mvic_PD"]
                MVIC_values.append(MVIC_rep_values)
        else:
            print(f"⚠️ Waarschuwing: {check_filename} niet gevonden. Heb je de volgorde correct aangehouden?")

    if mt_values:
        max_mt_nieuw = max(mt_values)
        print("\n" + "="*50)
        print("MAXIMAAL RESULTAAT (100% MT):")
        print(f"De allerhoogste MT_nieuw over de 3 metingen is: {max_mt_nieuw}")
        print("="*50 + "\n")
        
        measurement_values["max_MT_nieuw_van_3_reps"] = float(max_mt_nieuw)

    if MVIC_values:
        max_MVIC_nieuw = max(MVIC_values)
        
        measurement_values["max_MVIC_nieuw_van_3_reps"] = float(max_MVIC_nieuw)

measurement_values["Raw EMG AD"] = raw_emg_ad
measurement_values["Raw EMG PD"] = raw_emg_pd
measurement_values["Filtered EMG AD"] = filtered_emg_ad
measurement_values["Filtered EMG PD"] = filtered_emg_pd

with open(save_path, 'w') as f:
    json.dump(measurement_values, f, indent=4)

print(f"✅ MVIC values saved to {filename}")