# Software-GR25003-AS25040-Schoudertest-LUMC-
This software has been developed to measure co-contraction indices (CCI's) of the anterior deltoid (AD) and posterior deltoid (PD) using surface EMG (sEMG) data during isometric contractions in forward flexion (FF) and backward flexion (BF) with varying exeterd torque (ET) and angles of abduction (AOA). This software has specifically been developed to measure co-contraction in Obstetric Brachial Plexus Injury (OBPI) patients. 

This GitHub builds upon existing software: 
_van der Hart, S., Pelk, C., Swanenberg, B., & Vlug, S. (2025). Developing a real-time sEMG-biofeedback
prototype to stimulate co-contraction of the shoulder adductors during abductor contraction in subacromial pain
syndrome rehabilitation. TU Delft / LUMC._

**The Features that were built upon**
- General User Interface to select specific contraction indices
- Acquisition and processing of multi-channel sEMG data via NI-DAQ hardware
- Data storage in JSON files

**Self Developed Features**
- Real-time validation of sEMG signals
- Acquisition and processing of torque data
- Live feedback of ET measurements
- Shape-based CCI calculations 

**Instructions**
1. Run the validation.py to validate the acquired sEMG signals
2. Aqcuire sEMG and ET data during isometric contractions by running 100% MVT.py
3. Run the 30% MVT.py file to provide real-time ET feedback, store sEMG data and simultaneously calculate CCI's with the function from CCI.py
4. Calculate the CCI's of 100% MVT ET measurements afterwards by running CCI 100% MVT.py
5. Store data in a structured way by running Data Storage.py

**Citation**
If you use or build upon this code, please cite the earlier mentioned and:
_Zalbouti, N., Zuidgeest, H., Vruggink, B., Overdevest, J. (2026). Developing a sEMG Measurement Setup for Deltoid Co-Contraction in Obstetric Brachial Plexus Injury. TU Delft / LUMC_

