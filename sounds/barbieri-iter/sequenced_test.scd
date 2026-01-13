// Barbieri-style sequenced harmonic oscillator
// Pattern with negative counterpoint (random gate subtraction)

{
    var tempo = 4;  // Steps per second (120 BPM / 2)
    var clock = Impulse.kr(tempo);

    // Pitch pattern - simple pentatonic-ish sequence (as MIDI notes)
    // She often uses limited pitch sets, modal/minimalist approach
    var pitchPattern = [60, 62, 65, 67, 69, 72, 74, 77, 79, 81, 72, 69, 67, 65, 62, 60];
    var numSteps = pitchPattern.size;

    // Step counter
    var step = Stepper.kr(clock, 0, 0, numSteps - 1);
    var freq = Select.kr(step, pitchPattern).midicps;

    // NEGATIVE COUNTERPOINT: Random gate subtraction
    // Instead of adding notes, we START with all notes and randomly remove some
    var gateProb = 0.75;  // 75% chance each note plays
    var gate = TRand.kr(0, 1, clock) < gateProb;

    // Harmonic oscillator (8 harmonics)
    var harmonics = 8.collect { |i|
        var harmonicNum = i + 1;
        var harmonicFreq = freq * harmonicNum;
        // Spectral tilt toward upper harmonics for brightness
        var amp = 1 / harmonicNum.pow(0.7);  // Less rolloff than natural
        SinOsc.ar(harmonicFreq) * amp;
    };

    var harmMix = Mix(harmonics);

    // Simple envelope triggered by gate
    var env = EnvGen.ar(
        Env.perc(0.005, 0.3, 1, -4),  // Short attack, medium decay
        gate * clock
    );

    // Low Pass Gate emulation - filter follows amplitude
    var lpgFreq = env.linexp(0, 1, 200, 8000);
    var filtered = LPF.ar(harmMix, lpgFreq);

    var out = filtered * env * 0.3;

    out ! 2;
}
