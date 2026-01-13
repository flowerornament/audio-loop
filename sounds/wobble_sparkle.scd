{
    var wobbleEnv = EnvGen.kr(Env([0, 0, 8, 6], [2, 1.5, 2.5])); // stable then wobble
    var freq = 440 + (SinOsc.kr(5) * wobbleEnv); // vibrato increases
    var main = SinOsc.ar(freq) * 0.4;
    var sparkle = Ringz.ar(Dust.ar(15), [2500, 3200, 4100], 0.05).sum * 0.08;
    var env = EnvGen.kr(Env([0, 1, 1, 0], [0.01, 5.5, 0.5]));
    (main + sparkle) * env ! 2
}
