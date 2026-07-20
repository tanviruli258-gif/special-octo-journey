const ffmpeg = require("fluent-ffmpeg");
const ffmpegPath = require("ffmpeg-static");

ffmpeg.setFfmpegPath(ffmpegPath);

function convertTo3GP(input, output) {
    return new Promise((resolve, reject) => {
        ffmpeg(input)
            .videoCodec("h263")
            .audioCodec("amr_nb")
            .size("176x144")
            .videoBitrate("256k")
            .audioBitrate("12.2k")
            .audioChannels(1)
            .audioFrequency(8000)
            .format("3gp")
            .on("end", () => {
                resolve(output);
            })
            .on("error", (err) => {
                reject(err);
            })
            .save(output);
    });
}

module.exports = {
    convertTo3GP
};
