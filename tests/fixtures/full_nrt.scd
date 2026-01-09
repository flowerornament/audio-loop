// Full NRT render test - 1 second of 440Hz sine
(
var score;

SynthDef(\test, { |out=0|
    Out.ar(out, SinOsc.ar(440) * 0.3 ! 2);
}).store;

score = Score([
    [0.0, [\s_new, \test, 1000, 0, 0]],
    [1.0, [\n_free, 1000]],
]);

score.recordNRT(
    outputFilePath: "__OUTPUT_PATH__",
    headerFormat: "WAV",
    sampleFormat: "int24",
    options: ServerOptions.new.numOutputBusChannels_(2),
    duration: 1.0,
    action: { "Done".postln; 0.exit; }
);
)
