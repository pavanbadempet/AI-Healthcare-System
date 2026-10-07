# Systemic Cardio-Renal Digital Twin Model

## Coupled Ordinary Differential Equations (ODEs)
Modeling hemodynamic interactions between mean arterial pressure ($MAP$), glomerular filtration rate ($GFR$), and renin-angiotensin-aldosterone feedback loops:

$$\frac{d(MAP)}{dt} = \frac{CO \cdot TPR - MAP}{\tau_{baro}}$$

$$\frac{d(GFR)}{dt} = k_f \cdot (P_{gc} - P_{bs} - \sigma \cdot (\pi_{gc} - \pi_{bs}))$$

These equations are integrated using 4th-order Runge-Kutta numerical solvers to simulate drug dosage response curves.
