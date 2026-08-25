/// Native static scaler parameters and affine transformation routines.
/// Replaces scikit-learn preprocessing pipelines with zero-allocation static vector math.

pub const KIDNEY_OFFSET: [f32; 24] = [
    44.79999923706055, 77.33333587646484, 1.0176666975021362, 1.5333333015441895,
    0.46666666865348816, 0.06666667014360428, 0.2666666805744171, 0.20000000298023224,
    0.0, 147.3333282470703, 39.86666488647461, 3.299999952316284,
    132.86666870117188, 3.8399999141693115, 12.920000076293945, 40.266666412353516,
    8053.33349609375, 4.613333225250244, 0.3333333432674408, 0.4000000059604645,
    0.0, 0.20000000298023224, 0.20000000298023224, 0.2666666805744171,
];

pub const KIDNEY_SCALE: [f32; 24] = [
    0.0622701533138752, 0.08464989811182022, 152.69598388671875, 0.6875239014625549,
    0.8307731747627258, 4.008918762207031, 2.2613351345062256, 2.5,
    1.0, 0.009268976747989655, 0.042163118720054626, 0.17356647551059723,
    0.0786040872335434, 1.536220908164978, 0.43987324833869934, 0.13387522101402283,
    0.0005866989376954734, 1.3799266815185547, 2.1213202476501465, 2.041241407394409,
    1.0, 2.5, 2.5, 2.2613351345062256,
];

pub const LIVER_OFFSET: [f32; 10] = [
    45.0, 1.0, 0.6931471824645996, 0.30000001192092896,
    5.332718849182129, 3.5835189819335938, 42.0, 6.5,
    3.0999999046325684, 0.6418538689613342,
];

pub const LIVER_SCALE: [f32; 10] = [
    0.043478261679410934, 1.0, 1.4426950216293335, 0.9090909361839294,
    1.8857671022415161, 1.0084303617477417, 0.01587301678955555, 0.6666666865348816,
    0.8333333134651184, 4.7324042320251465,
];

pub const LUNGS_OFFSET: [f32; 15] = [
    0.5242718458175659, 62.67313766479492, 0.5631067752838135, 0.5695793032646179,
    0.4983818829059601, 0.5016181468963623, 0.5048543810844421, 0.6731391549110413,
    0.5566343069076538, 0.5566343069076538, 0.5566343069076538, 0.5792880058288574,
    0.6407766938209534, 0.469255656003952, 0.5566343069076538,
];

pub const LUNGS_SCALE: [f32; 15] = [
    2.0023605823516846, 0.12199576944112778, 2.016122817993164, 2.019650936126709,
    2.0000104904174805, 2.0000104904174805, 2.000094175338745, 2.131896495819092,
    2.0129544734954834, 2.0129544734954834, 2.0129544734954834, 2.0256307125091553,
    2.084320068359375, 2.003791570663452, 2.0129544734954834,
];

/// Generic affine vector scaling: (X[i] - offset[i]) * scale[i]
#[inline(always)]
pub fn scale_vector<const N: usize>(input: &[f32; N], offset: &[f32; N], scale: &[f32; N]) -> [f32; N] {
    let mut out = [0.0f32; N];
    for i in 0..N {
        out[i] = (input[i] - offset[i]) * scale[i];
    }
    out
}

/// Preprocesses 24 features for Chronic Kidney Disease model.
#[inline(always)]
pub fn preprocess_kidney(input: &[f32; 24]) -> [f32; 24] {
    scale_vector(input, &KIDNEY_OFFSET, &KIDNEY_SCALE)
}

/// Preprocesses 10 features for Liver Disease model.
/// Applies log1p on columns: Total_Bilirubin(2), Alk_Phos(4), ALT(5), Alb_Glob_Ratio(9)
/// prior to affine scaling.
#[inline(always)]
pub fn preprocess_liver(input: &[f32; 10]) -> [f32; 10] {
    let mut transformed = *input;
    transformed[2] = (1.0 + transformed[2].max(0.0)).ln();
    transformed[4] = (1.0 + transformed[4].max(0.0)).ln();
    transformed[5] = (1.0 + transformed[5].max(0.0)).ln();
    transformed[9] = (1.0 + transformed[9].max(0.0)).ln();
    scale_vector(&transformed, &LIVER_OFFSET, &LIVER_SCALE)
}

/// Preprocesses 15 features for Lung Disease model.
#[inline(always)]
pub fn preprocess_lungs(input: &[f32; 15]) -> [f32; 15] {
    scale_vector(input, &LUNGS_OFFSET, &LUNGS_SCALE)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_kidney_scaler_identity() {
        let raw = [
            45.0, 80.0, 1.020, 1.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 120.0, 36.0, 1.2, 138.0, 4.4, 15.4, 44.0,
            7800.0, 5.2, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        ];
        let scaled = preprocess_kidney(&raw);
        assert_eq!(scaled.len(), 24);
        assert!((scaled[0] - (45.0 - KIDNEY_OFFSET[0]) * KIDNEY_SCALE[0]).abs() < 1e-6);
        assert!((scaled[11] - (1.2 - KIDNEY_OFFSET[11]) * KIDNEY_SCALE[11]).abs() < 1e-6);
    }

    #[test]
    fn test_liver_scaler_log1p() {
        let raw = [50.0, 1.0, 1.2, 0.4, 150.0, 40.0, 45.0, 6.8, 3.5, 1.0];
        let scaled = preprocess_liver(&raw);
        assert_eq!(scaled.len(), 10);
        let expected_tb = ((1.2f32 + 1.0).ln() - LIVER_OFFSET[2]) * LIVER_SCALE[2];
        assert!((scaled[2] - expected_tb).abs() < 1e-6);
    }

    #[test]
    fn test_lungs_scaler() {
        let raw = [1.0, 60.0, 2.0, 2.0, 1.0, 1.0, 2.0, 2.0, 1.0, 2.0, 1.0, 2.0, 2.0, 1.0, 2.0];
        let scaled = preprocess_lungs(&raw);
        assert_eq!(scaled.len(), 15);
        assert!((scaled[0] - (1.0 - LUNGS_OFFSET[0]) * LUNGS_SCALE[0]).abs() < 1e-6);
    }
}
