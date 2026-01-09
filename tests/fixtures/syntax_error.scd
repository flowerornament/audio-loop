// Intentional syntax error in full NRT mode
(
var score;
var x = 1 +;  // syntax error here

score = Score([]);

score.recordNRT(
    outputFilePath: "__OUTPUT_PATH__",
    duration: 1.0,
    action: { 0.exit; }
);
)
