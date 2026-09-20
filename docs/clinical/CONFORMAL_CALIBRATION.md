# Split Conformal Prediction for Clinical Risk Modeling

## Mathematical Formulation
Split conformal prediction provides mathematically rigorous, finite-sample coverage guarantees without parametric distributional assumptions:

$$\mathbb{P}(Y_{n+1} \in \hat{C}(X_{n+1})) \ge 1 - lpha$$

## Clinical Calibration Workflow
1. Split available annotated patient cohort into training set ($D_{train}$) and calibration set ($D_{cal}$).
2. Fit classification model (CatBoost / Deep Ensembles) on $D_{train}$.
3. Compute non-conformity scores on $D_{cal}$: $s_i = 1 - \hat{p}(y_i \mid x_i)$.
4. Compute empirical quantile $\hat{q} = 	ext{Quantile}\left(s, rac{\lceil (n+1)(1-lpha) ceil}{n}ight)$.
5. Output prediction sets containing all candidate clinical diagnoses exceeding probability threshold.
