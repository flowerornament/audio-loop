// Runtime error - undefined variable in full NRT mode
(
var score;

unknownVariable.postln;

score = Score([]);

score.recordNRT(
    outputFilePath: "__OUTPUT_PATH__",
    duration: 1.0,
    action: { 0.exit; }
);
)
