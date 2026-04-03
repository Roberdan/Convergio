//! Audio utility functions — resampling and channel conversion.

/// Convert interleaved stereo samples to mono by averaging pairs.
pub fn stereo_to_mono(stereo: &[i16]) -> Vec<i16> {
    stereo
        .chunks_exact(2)
        .map(|pair| ((pair[0] as i32 + pair[1] as i32) / 2) as i16)
        .collect()
}

/// Linear resample from source_rate to target_rate.
/// Uses simple linear interpolation — good enough for speech at small ratios.
pub fn resample(samples: &[i16], source_rate: u32, target_rate: u32) -> Vec<i16> {
    if source_rate == target_rate || samples.is_empty() {
        return samples.to_vec();
    }
    let ratio = source_rate as f64 / target_rate as f64;
    let out_len = (samples.len() as f64 / ratio) as usize;
    (0..out_len)
        .map(|i| {
            let src_pos = i as f64 * ratio;
            let idx = src_pos as usize;
            let frac = src_pos - idx as f64;
            if idx + 1 < samples.len() {
                let a = samples[idx] as f64;
                let b = samples[idx + 1] as f64;
                (a + frac * (b - a)) as i16
            } else {
                samples[idx.min(samples.len() - 1)]
            }
        })
        .collect()
}
