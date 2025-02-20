import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, filters, CommandHandler, MessageHandler, CallbackContext
from datetime import datetime
from gspread_formatting import *
import os
from dotenv import load_dotenv

load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)

# Autentikasi Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(os.getenv("GOOGLE_CRED"), scope)
client = gspread.authorize(creds)

# Buka Spreadsheet
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # Ganti dengan ID Spreadsheet kamu
spreadsheet = client.open_by_key(SPREADSHEET_ID)  # Gunakan sheet pertama

today_date = datetime.now().strftime("%Y-%m-%d")

# Cek apakah sheet sudah ada
existing_sheets = [sheet.title for sheet in spreadsheet.worksheets()]

if today_date not in existing_sheets:
    # Jika belum ada, buat sheet baru
    worksheet = spreadsheet.add_worksheet(title=today_date, rows="100", cols="10")

    # Tambahkan header ke baris pertama
    headers = ["Username", "Tanggal", "Deskripsi", "Jumlah", "Total"]
    worksheet.append_row(headers)

    fmt = cellFormat(
        numberFormat={"type": "CURRENCY", "pattern": "Rp#,##0"}
    )

    # Format seluruh kolom D dan E ke IDR
    format_cell_range(worksheet, "D:E", fmt)

    print(f"Sheet baru '{today_date}' telah dibuat.")
else:
    # Jika sudah ada, gunakan sheet yang ada
    worksheet = spreadsheet.worksheet(today_date)
    print(f"Sheet '{today_date}' sudah ada.")

# Fungsi untuk menambahkan laporan keuangan
async def add_report(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    user = update.message.from_user
    username = user.username if user.username else user.first_name  # Gunakan username atau nama pertama

    try:
        description, amount = text.split(", ")
        date = datetime.today().strftime('%Y-%m-%d')
        worksheet.append_row([username, date, description, int(amount)])  # Tambahkan username di kolom pertama
        await update.message.reply_text("✅ Laporan berhasil ditambahkan!")
    except ValueError:
        await update.message.reply_text("⚠️ Format salah. Gunakan: Tanggal, Deskripsi, Jumlah")

# Fungsi start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("👋 Halo! Kirim laporan dalam format:\n📌 `Deskripsi, Jumlah`")

# Main function
def main():
    app = Application.builder().token(os.getenv("TELE_BOT")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_report))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
