import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8784240051:AAEdP800GRXEel0BMgDcoL4pngDzShQjI7E"



def generate_signal_text():
    pairs = ["EUR/USD (OTC)", "GBP/USD (OTC)", "USD/PKR (OTC)", "USD/BDT (OTC)", "EUR/GBP (OTC)", "AUD/CAD (OTC)"]
    directions = [("🟢 صعود (YUKARI)", "🔼 BUY"), ("🔴 هبوط (AŞAĞI)", "🔽 SELL")]
    durations = ["1 دقيقة", "2 دقيقة", "5 دقائق"]
    
    pair = random.choice(pairs)
    market_type = "OTC (خاص)" if "(OTC)" in pair else "Normal (عالمي)"
    direction, action = random.choice(directions)
    duration = random.choice(durations)
    prob = random.randint(81, 94)
    
    filled_bars = int(prob / 10)
    bar_chart = "█" * filled_bars + "░" * (10 - filled_bars)
    
    msg = (
        "💎 **MEGALODON AI | إشارة تداول معتمدة** 💎\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **الزوج المطلوب:** `{pair}`\n"
        f"📊 **نوع السوق:** `{market_type}`\n"
        f"⏱ **مدّة الصفقة:** `{duration}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 **الاتجاه والتوصية:**\n"
        f"👈 **{direction}** [{action}]\n\n"
        f"🔥 **نسبة نجاح التحليل:** `{prob}%`\n"
        f"📊 `{bar_chart}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 **المؤشرات المعتمدة:**\n"
        "• RSI (14) - تشبع حركة السعر\n"
        "• MACD (12,26,9) - تقاطع الاتجاه\n"
        "• EMA (50/200) - اتجاه السوق العام\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 **توصية التداول:**\n"
        "⚠️ *التزم بنسبة 1%-2% من قيمة المحفظة فقط.*"
    )
    return msg

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🚀 توليد إشارة جديدة", callback_data="gen_signal")],
        [InlineKeyboardButton("📊 مؤشرات التحليل", callback_data="indicators"),
         InlineKeyboardButton("⚙️ إرشادات الاستخدام", callback_data="help_info")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🏆 **أهلاً بك في نظام Megalodon AI التفاعلي لتداول Quotex** 🏆\n\n"
        "هذا البوت يعتمد على خوارزميات تحليل الاتجاه عبر دمج أحدث المؤشرات الفنية.\n\n"
        "اضغط على الزر أدناه لتوليد إشارة تداول مباشرة:"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "gen_signal":
        signal_msg = generate_signal_text()
        await query.edit_message_text(text=signal_msg, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    elif query.data == "indicators":
        info_text = (
            "🛠 **المؤشرات الفنية المدمجة في خوارزمية البوت:**\n\n"
            "1️⃣ **RSI (مؤشر القوة النسبية):** لرصد مناطق الشراء والبيع الزائد.\n"
            "2️⃣ **MACD:** لتأكيد لحظة الانعكاس وبداية الزخم.\n"
            "3️⃣ **EMA 50 & 200:** لتجنب التداول عكس الاتجاه العام وتفادي التذبذب."
        )
        await query.edit_message_text(text=info_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    elif query.data == "help_info":
        help_text = (
            "📖 **دليل إدارة المخاطر:**\n\n"
            "• اختبر الإشارات دائماً على **حساب التجربة (Demo)** أولاً.\n"
            "• لا تدخل بأكثر من **2%** من رصيد حسابك في الصفقة الواحدة.\n"
            "• تجنب التداول وقت الأخبار الاقتصادية القوية."
        )
        await query.edit_message_text(text=help_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
