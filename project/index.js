require("dotenv").config();

const { Telegraf } = require("telegraf");
const axios = require("axios");
const fs = require("fs-extra");
const path = require("path");
const { v4: uuidv4 } = require("uuid");

const bot = new Telegraf(process.env.BOT_TOKEN);

const TEMP_DIR = process.env.TEMP_DIR || "./temp";

fs.ensureDirSync(TEMP_DIR);

bot.start(async (ctx) => {
    await ctx.reply(
`🎬 MP4 ➜ 3GP Converter Bot

📤 Send me any MP4 video.

I will convert it to 3GP and send it back automatically.`
    );
});

bot.on("video", async (ctx) => {
    try {

        const video = ctx.message.video;

        await ctx.reply("⏳ Downloading your video...");

        const file = await ctx.telegram.getFile(video.file_id);

        const fileUrl =
            `https://api.telegram.org/file/bot${process.env.BOT_TOKEN}/${file.file_path}`;

        const id = uuidv4();

        const input = path.join(TEMP_DIR, `${id}.mp4`);
        const output = path.join(TEMP_DIR, `${id}.3gp`);

        const response = await axios({
            url: fileUrl,
            method: "GET",
            responseType: "stream"
        });

        const writer = fs.createWriteStream(input);

        response.data.pipe(writer);

        await new Promise((resolve, reject) => {
            writer.on("finish", resolve);
            writer.on("error", reject);
        });

        await ctx.reply("✅ Download complete.\n🎞 Converting to 3GP...");

        // এখানে converter.js থেকে convertTo3GP() কল করা হবে

    } catch (err) {
        console.error(err);
        await ctx.reply("❌ Failed to process your video.");
    }
});

bot.launch();

console.log("✅ Bot Started...");
