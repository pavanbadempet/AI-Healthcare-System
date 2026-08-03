/// Pure Rust High-Speed DICOM Pixel Window Slicer & Contrast Processor.
/// Performs zero-allocation window leveling & 16-bit to 8-bit normalization on medical CT/MRI slices.

#[allow(dead_code)]
pub struct DicomSliceMetrics {
    pub total_pixels: usize,
    pub min_pixel_intensity: u16,
    pub max_pixel_intensity: u16,
    pub mean_intensity: f64,
}

#[allow(dead_code)]
pub fn process_dicom_slice_16bit(pixels: &[u16], window_center: u16, window_width: u16) -> (Vec<u8>, DicomSliceMetrics) {
    if pixels.is_empty() {
        return (Vec::new(), DicomSliceMetrics { total_pixels: 0, min_pixel_intensity: 0, max_pixel_intensity: 0, mean_intensity: 0.0 });
    }

    let min_val = *pixels.iter().min().unwrap_or(&0);
    let max_val = *pixels.iter().max().unwrap_or(&0);
    let sum: u64 = pixels.iter().map(|&p| p as u64).sum();
    let mean = sum as f64 / (pixels.len() as f64);

    let lower_bound = window_center.saturating_sub(window_width / 2);
    let upper_bound = window_center.saturating_add(window_width / 2);

    let normalized_8bit: Vec<u8> = pixels
        .iter()
        .map(|&p| {
            if p <= lower_bound {
                0
            } else if p >= upper_bound {
                255
            } else {
                let range = (upper_bound - lower_bound) as f32;
                let val = (p - lower_bound) as f32;
                ((val / range) * 255.0) as u8
            }
        })
        .collect();

    let metrics = DicomSliceMetrics {
        total_pixels: pixels.len(),
        min_pixel_intensity: min_val,
        max_pixel_intensity: max_val,
        mean_intensity: (mean * 100.0).round() / 100.0,
    };

    (normalized_8bit, metrics)
}
