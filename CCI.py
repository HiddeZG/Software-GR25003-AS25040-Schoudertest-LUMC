import numpy as np
import math

#%% Shape-based CCI Formule

# NEMG1 als Agonist
# NEMG2 als Antagonist

def CCI_formula(NEMG1, NEMG2):
    return (NEMG2)/(NEMG2 + NEMG1 + 1*math.exp(-8)* 100)

def compute_cci(movement, emg_AD, emg_PD):
    if movement == "Anteflexion":
        return CCI_formula(emg_AD, emg_PD), np.mean(CCI_formula(emg_AD, emg_PD)) 
    elif movement == "Retroflexion":
        return CCI_formula(emg_PD, emg_AD), np.mean(CCI_formula(emg_PD, emg_AD))





