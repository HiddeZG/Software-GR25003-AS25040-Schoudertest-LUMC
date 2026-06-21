import os
import json
import numpy as np
from CCI import compute_cci

#%%

hoofdmap = "Meetdata"

for submap in os.listdir(hoofdmap):
    submap_path = os.path.join(hoofdmap, submap)

    print(f"\nParticipant-map: {submap_path}")
    print(os.listdir(hoofdmap))
    for bestand in os.listdir(submap_path):
        print(f"  Bestand: {bestand}") 

        if not (bestand.endswith(".json") and "100_ MT" in bestand):
            continue

        bestand_path = os.path.join(submap_path, bestand)

        with open(bestand_path, "r") as f:
            data = json.load(f)

        participant = data["participant"]
        movement = data["movement"]
        angle = data["angle"]
        shoulder = data["shoulder"]
        resistance = data["resistance"]
        repetitions = data["repetitions"]

        anterior_mvic = f"measurements_{participant}_Anteflexion_{angle}_{shoulder}_100_ MT_Rep 3.json"
        posterior_mvic = f"measurements_{participant}_Retroflexion_{angle}_{shoulder}_100_ MT_Rep 3.json"
        
        print(f"  Zoekt naar: '{anterior_mvic}'")
        print(f"  Bestanden in map: {os.listdir(submap_path)}")

        anterior_path = os.path.join(submap_path, anterior_mvic)
        posterior_path = os.path.join(submap_path, posterior_mvic)

        if not os.path.exists(anterior_path):
            print(f"❌ Geen anterior MVIC-bestand gevonden: {anterior_mvic}")
            continue

        if not os.path.exists(posterior_path):
            print(f"❌ Geen posterior MVIC-bestand gevonden: {posterior_mvic}")
            continue

        with open(anterior_path, "r") as f:
            anterior_data = json.load(f)

        with open(posterior_path, "r") as f:
            posterior_data = json.load(f)

        mvic_A = anterior_data["max_MVIC_nieuw_van_3_reps"]
        mvic_P = posterior_data["max_MVIC_nieuw_van_3_reps"]

        filtered_ad = np.array(data["Filtered EMG AD"])
        filtered_pd = np.array(data["Filtered EMG PD"])

        filtered_ad_norm = filtered_ad / mvic_A
        filtered_pd_norm = filtered_pd / mvic_P

        CCI_t, CCI = compute_cci(movement, filtered_ad_norm, filtered_pd_norm)

        data["CCI"] = float(CCI)
        data["CCI_t"] = CCI_t.tolist()

        with open(bestand_path, "w") as f:
            json.dump(data, f, indent=4)

        print(f"✅ CCI toegevoegd aan: {bestand}")