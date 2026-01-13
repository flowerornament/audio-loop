{
    var freq = 440;
    var detune = 0.008;
    var osc1 = Saw.ar(freq);
    var osc2 = Saw.ar(freq * (1 + detune));
    var osc3 = Pulse.ar(freq * 0.5, 0.3) * 0.5;
    var mix = (osc1 + osc2 + osc3) / 2.5;
    var filt = MoogFF.ar(mix, 1800, 2.5);
    var env = EnvGen.ar(Env.adsr(0.01, 0.2, 0.7, 0.3), gate: 1);
    var vibrato = SinOsc.kr(5, 0, 0.02, 1);
    filt * env * 0.4 ! 2
}
