// Verbos Harmonic Oscillator Emulation
// Based on the module used by Caterina Barbieri
// 8 sine harmonics + triangle/saw/square + scan/tilt controls

{
    arg freq = 110, // Base frequency
        // Individual harmonic amplitudes (0-1)
        h1 = 1.0, h2 = 0.8, h3 = 0.6, h4 = 0.5,
        h5 = 0.4, h6 = 0.3, h7 = 0.2, h8 = 0.15,
        // Spectral controls
        tilt = 0,      // -1 = low harmonics, +1 = high harmonics
        scanCenter = 4, // Which harmonic is centered (1-8)
        scanWidth = 8,  // How many harmonics are audible (1-8)
        // Mix
        harmonicMix = 1.0, // Amount of harmonic content
        sawMix = 0,        // Amount of sawtooth
        triMix = 0,        // Amount of triangle
        // Output
        amp = 0.3;

    var harmonicAmps, tiltedAmps, scannedAmps, finalAmps;
    var harmonics, harmMix;
    var saw, tri;
    var out;

    // Base harmonic amplitudes array
    harmonicAmps = [h1, h2, h3, h4, h5, h6, h7, h8];

    // Apply spectral tilt
    // tilt > 0 emphasizes higher harmonics, < 0 emphasizes lower
    tiltedAmps = harmonicAmps.collect { |amp, i|
        var harmonicNum = i + 1;
        var tiltFactor = (harmonicNum / 4.5).pow(tilt); // Center around harmonic 4-5
        amp * tiltFactor;
    };

    // Apply harmonic scan (bandpass-like window over harmonics)
    scannedAmps = tiltedAmps.collect { |amp, i|
        var harmonicNum = i + 1;
        var distance = (harmonicNum - scanCenter).abs;
        var windowAmp = (1 - (distance / (scanWidth / 2))).max(0);
        amp * windowAmp;
    };

    finalAmps = scannedAmps;

    // Generate 8 sine harmonics
    harmonics = 8.collect { |i|
        var harmonicNum = i + 1;
        var harmonicFreq = freq * harmonicNum;
        SinOsc.ar(harmonicFreq) * finalAmps[i];
    };

    // Mix harmonics
    harmMix = Mix(harmonics) * harmonicMix;

    // Classic waveforms for additional character
    saw = Saw.ar(freq) * sawMix;
    tri = LFTri.ar(freq) * triMix;

    // Final mix
    out = (harmMix + saw + tri) * amp;

    // Stereo with slight detune for width
    out = out + (SinOsc.ar(freq * 1.002) * finalAmps[0] * 0.1 * harmonicMix * amp);

    out ! 2;  // Stereo
}
