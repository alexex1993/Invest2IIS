import os
import time
import logging
import telebot
from dotenv import load_dotenv
from invest2iis.invest.AccountStatus import AccountStatus

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def run_cron():
    load_dotenv()

    TOKEN = os.getenv('TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')
    TINKOFF_TOKEN = os.getenv('TINKOFF_TOKEN')
    TINKOFF_ACCOUNT_ID = os.getenv('TINKOFF_ACCOUNT_ID')

    if not TOKEN or not CHAT_ID or not TINKOFF_TOKEN or not TINKOFF_ACCOUNT_ID:
        raise ValueError("Переменные не установлены в файле .env")

    # Инициализация бота
    bot = telebot.TeleBot(TOKEN)

    # Создаем экземпляр AccountStatus
    account = AccountStatus(token=TINKOFF_TOKEN, account_id=TINKOFF_ACCOUNT_ID, history_file="cron_history.json")

    while True:
        try:
            if account.has_currencies_changed():
                status_message = str(account)
                bot.send_message(CHAT_ID, f"{status_message}", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            bot.send_message(CHAT_ID,"⚠️ Произошла ошибка при получении данных")

        time.sleep(31)


if __name__ == "__main__":
    run_cron()