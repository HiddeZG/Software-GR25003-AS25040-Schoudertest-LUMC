import os
import json

#%% Data Opslag

script_map = os.path.dirname(os.path.abspath(__file__))
map = os.path.join(script_map, "Meetdata") 
filename = "data_file.json"
filename_2 = "data_file_ROM"
filename_3 = "alle_data"
folder_name = "Data_map"

folder_path = os.path.join(os.getcwd(), folder_name) 
os.makedirs(folder_path, exist_ok=True)

save_path = os.path.join(folder_path, filename)
save_path2 = os.path.join(folder_path,filename_2 )
save_path3 = os.path.join(folder_path, filename_3)

super_data = []
ROM_data = []

for submap in os.listdir(map):
    submap_path = os.path.join(map, submap)
    
    if os.path.isdir(submap_path):
    
        for bestand in os.listdir(submap_path):
            
            if bestand.endswith(".json"):
                bestand_path = os.path.join(submap_path, bestand)
                if os.path.getsize(bestand_path) ==0:
                    print(f"⏭ Leeg bestand overgeslagen: {bestand}")
                    continue
                
                with open(bestand_path, "r") as f:
                    data = json.load(f)
                    vereiste_sleutels = ["participant", "movement", "angle", "shoulder", "resistance", "repetitions"] #CCI gekozen hier weg te laten, omdat de andere keys altijd ingevuld moeten worden
                    if not all(sleutel in data for sleutel in vereiste_sleutels):
                        print(f"⏭ Overgeslagen is een ROM bestand, namelijk: {bestand}")
                        
                        ROM_data.append(data)
                        continue
                    data_gewenst = {                
                        "participant" : data["participant"],
                        "movement" : data["movement"],
                        "angle" : data["angle"],
                        "shoulder" : data["shoulder"],
                        "resistance" : data["resistance"],
                        "repetitions" : data["repetitions"],
                        "CCI" : float(data["CCI"])
                    }

                    super_data.append(data_gewenst)
                
                print(f"Geladen: {bestand_path}")
data_file = []

for data in super_data:
    participant = data['participant']
    shoulder = data["shoulder"]
    
    rom = next((r for r in ROM_data if r["participant"] == participant), None)
    if rom is None:
        print(f'Geen ROM data voor participant {participant}')
        ROM_gewild = {
            "anteflexion": None,
            "retroflexion" : None,
            "abduction" : None
        }
        combined = {**data, **ROM_gewild}
        data_file.append(combined)
        
        continue

    
    if data["shoulder"] == "Right" :
        
        ROM_gewild = {
            "anteflexion" : rom["anteflexion_rom_right"],
            "retroflexion" : rom["retroflexion_rom_right"],
            "abduction" : rom["abduction_rom_right"]
        }
        
    else:
        ROM_gewild = {
            "anteflexion" : rom["anteflexion_rom_left"],
            "retroflexion" : rom["retroflexion_rom_left"],
            "abduction" : rom["abduction_rom_left"]
        }
    combined = {**data, **ROM_gewild}
    data_file.append(combined)

with open(save_path, "w") as f:
    json.dump(super_data, f)
with open(save_path2, "w") as f:
    json.dump(ROM_data, f)
with open(save_path3, "w") as f:
    json.dump(data_file, f)


