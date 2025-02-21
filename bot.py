import logging
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, filters, CommandHandler, MessageHandler, CallbackContext, ConversationHandler
from datetime import datetime
from gspread_formatting import *
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
    headers = ["Username", "Tanggal", "Kategori", "Deskripsi", "Jumlah", "Total"]
    worksheet.append_row(headers)

    print(f"Sheet baru '{today_date}' telah dibuat.")
else:
    # Jika sudah ada, gunakan sheet yang ada
    worksheet = spreadsheet.worksheet(today_date)
    print(f"Sheet '{today_date}' sudah ada.")


CATEGORY, AMOUNT = range(2)
# Fungsi start
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [["income", "outcome"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("👋 Halo! Pilih Kategori Transaksi:", reply_markup=reply_markup)
    return CATEGORY
    # await update.message.reply_text("👋 Halo! Kirim laporan dalam format:\n📌 `Deskripsi, Jumlah`")

async def handle_category(update: Update, context: CallbackContext) -> None:
    category = update.message.text
    if category in ["income", "outcome"]:
        context.user_data["category"] = category
        await update.message.reply_text(f"Kamu memilih {category}, silahkan lanjutkan transaksi")
        return AMOUNT
    else:
        await update.message.reply_text("⚠️ Format salah. Gunakan: [income, outcome]")
        return CATEGORY

# Fungsi untuk menambahkan laporan keuangan
async def add_report(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    user = update.message.from_user
    username = user.username if user.username else user.first_name  # Gunakan username atau nama pertama

    try:
        category = context.user_data.get("category", "Unknown")
        description, amount = text.split(", ")
        date = datetime.today().strftime('%Y-%m-%d')
        worksheet.append_row([username, date, category, description, int(amount)])  # Tambahkan username di kolom pertama
        await update.message.reply_text("✅ Laporan berhasil ditambahkan!")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("⚠️ Format salah. Gunakan: Tanggal, Deskripsi, Jumlah")
        return AMOUNT

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Transaksi dibatalkan.")
    return ConversationHandler.END

# Main function
def main():
    app = Application.builder().token(os.getenv("TELE_BOT")).build()
    # app.add_handler(CommandHandler("start", start))
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category))
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_report))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CATEGORY:[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category)],
            AMOUNT:[MessageHandler(filters.TEXT & ~filters.COMMAND, add_report)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
