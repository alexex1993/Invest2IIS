import multiprocessing
from bot import run_bot
from cron import run_cron

if __name__ == '__main__':
    # Создаем процессы для bot и cron
    bot_process = multiprocessing.Process(target=run_bot)
    cron_process = multiprocessing.Process(target=run_cron)

    # Запускаем процессы
    bot_process.start()
    cron_process.start()

    # Ожидаем завершения процессов (опционально)
    bot_process.join()
    cron_process.join()