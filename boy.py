import os
import asyncio
import requests
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Your Bot Token
TOKEN = "8422894521:AAFPziHw_g7dbsfTpybl87Mq3L70LoRVCSg"

def download_tiktok_video(url: str) -> str:
    """Downloads the TikTok video using yt-dlp and returns the file path."""
    ydl_opts = {
        'outtmpl': 'tiktok_%(id)s.%(ext)s',
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'noplaylist': True,
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

def upload_to_catbox(filepath: str) -> str:
    """Uploads the file to Catbox.moe and returns the direct permanent link."""
    url = "https://catbox.moe/user/api.php"
    data = {"reqtype": "fileupload"}
    
    with open(filepath, "rb") as f:
        files = {"fileToUpload": f}
        response = requests.post(url, data=data, files=files)
    
    if response.status_code == 200:
        return response.text.strip()
    else:
        raise Exception(f"Catbox upload failed with status {response.status_code}")

async def tiktok_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /tiktok command."""
    if not context.args:
        await update.message.reply_text("Please provide a TikTok video link.\nUsage: `/tiktok <link>`", parse_mode="Markdown")
        return
    
    url = context.args[0]
    processing_msg = await update.message.reply_text("⏳ Downloading video, please wait...")
    
    loop = asyncio.get_event_loop()
    filename = None
    
    try:
        filename = await loop.run_in_executor(None, download_tiktok_video, url)
        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        
        if file_size_mb < 50.0:
            await update.message.reply_text("📤 Size is under 50MB. Uploading directly...")
            with open(filename, 'rb') as video_file:
                await update.message.reply_video(video=video_file, caption="Here is your video!")
        else:
            await update.message.reply_text(f"📦 Video is {file_size_mb:.1f} MB (Over 50MB).\nUploading to Catbox.moe...")
            catbox_url = await loop.run_in_executor(None, upload_to_catbox, filename)
            await update.message.reply_text(f"✅ Here is your direct download link:\n{catbox_url}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ An error occurred: {str(e)}")
        
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)
        try:
            await processing_msg.delete()
        except:
            pass

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("tiktok", tiktok_command))
    print("Bot is running!")
    app.run_polling()

if __name__ == "__main__":
    main()
