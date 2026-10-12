import os
from telegram import Bot

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    message = "🚀 مرحباً فيصل! البوت يعمل بنجاح من مستودعك الخاص. جاهز للخطوة التالية."
    bot.send_message(chat_id=CHAT_ID, text=message)
    print("تم إرسال رسالة الاختبار.")

if __name__ == '__main__':
    main()
