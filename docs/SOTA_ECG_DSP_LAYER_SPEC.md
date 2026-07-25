# SOTA ECG Waveform Pan-Tompkins DSP Filtering Specification

This document specifies Butterworth bandpass noise filtering, Pan-Tompkins real-time QRS complex peak detection, and arrhythmia Heart Rate Variability (HRV) analysis standards.

```
┌─────────────────────────────────────────────────────────────┐
│          Butterworth Bandpass Noise Filtering (5-15Hz)       │
│  - Filters out high-frequency noise & muscle artifacts      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Pan-Tompkins Real-Time QRS Peak Detector           │
│  - Detects R-R intervals to identify arrhythmia spikes      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🫀 Key ECG DSP Standards

1. **Pan-Tompkins QRS Peak Detection (`process_ecg_stream`)**:
   - Analyzes continuous 12-lead ECG sensor streams in sub-microseconds.
2. **Real-Time Arrhythmia Alerting (`is_arrhythmia_detected`)**:
   - Triggers automated alerts when heart rates deviate outside normal boundaries (<60 or >100 BPM).
