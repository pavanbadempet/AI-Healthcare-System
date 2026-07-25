# SOTA DICOM SIMD Decompression & WebGL PACS Specification

This document specifies SIMD 16-bit DICOM pixel array decompression, Hounsfield Unit (HU) windowing, and WebGL 3D volumetric rendering standards.

```
┌─────────────────────────────────────────────────────────────┐
│          SIMD 16-Bit DICOM Pixel Array Decompression        │
│  - Decodes DICOM slices in parallel with SIMD instructions  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          WebGL / WebGPU 3D Volumetric Mesh Ray-Casting      │
│  - Renders interactive 3D CT/MRI volumetric meshes          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🩻 Key DICOM & WebGL Standards

1. **SIMD DICOM Pixel Array Decompression (`decompress_dicom_slice`)**:
   - Decodes 16-bit CT/MRI pixel buffers using SIMD instructions for sub-millisecond per-slice decoding.
2. **Hounsfield Unit Windowing (`hounsfield_min`, `hounsfield_max`)**:
   - Maps raw 16-bit attenuation values to standard Hounsfield Units (-1000 Air to +3000 Bone).
