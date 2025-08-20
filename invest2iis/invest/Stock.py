import os
import logging
from tinkoff.invest import Client
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)
logger = logging.getLogger(__name__)


# Ваш токен и ID счета
TOKEN = os.getenv('TINKOFF_TOKEN')
ACCOUNT_ID = os.getenv('TINKOFF_ACCOUNT_ID')


START_INVEST = datetime(2025, 7, 24)


class Stock():
    @classmethod
    def delta_days(cls):
        delta_days: float = (datetime.today() - START_INVEST).days
        return delta_days

    @classmethod
    def calculate_stock_yield(cls):
        # Проверка ACCOUNT_ID
        if not isinstance(ACCOUNT_ID, str) or not ACCOUNT_ID:
            logger.error(f"Invalid ACCOUNT_ID: {ACCOUNT_ID}. It must be a non-empty string.")
            raise ValueError(f"Invalid ACCOUNT_ID: {ACCOUNT_ID}. It must be a non-empty string.")

        with Client(TOKEN) as client:
            try:
                # 1. Получение портфеля
                portfolio = client.operations.get_portfolio(account_id=ACCOUNT_ID)

                # 2. Фильтрация акций (instrument_type == "share")
                stocks = [pos for pos in portfolio.positions if pos.instrument_type == "share"]
                if not stocks:
                    logger.error("Акции в портфеле не найдены.")
                    return

                # 3. Получение текущих цен
                figis = [stock.figi for stock in stocks]
                last_prices = client.market_data.get_last_prices(figi=figis).last_prices
                price_map = {price.figi: price.price.units + price.price.nano / 1_000_000_000 for price in last_prices}

                # 4. Получение цен закрытия за предыдущий день
                yesterday = datetime.now() - timedelta(days=1)
                price_map_yesterday = {}
                for figi in figis:
                    candles = client.market_data.get_candles(
                        figi=figi,
                        from_=yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
                        to=yesterday.replace(hour=23, minute=59, second=59, microsecond=999999),
                        interval=4  # 1-day candles
                    ).candles
                    if candles:
                        # Берем цену закрытия последней свечи
                        price_map_yesterday[figi] = candles[-1].close.units + candles[-1].close.nano / 1_000_000_000
                    else:
                        price_map_yesterday[figi] = 0.0  # Если нет данных, устанавливаем 0

                # 5. Сбор данных по акциям
                stock_data = []
                for stock in stocks:
                    instrument = client.instruments.share_by(id=stock.figi, id_type=1).instrument
                    ticker = instrument.ticker
                    name = instrument.name
                    quantity = stock.quantity.units
                    avg_buy_price = stock.average_position_price.units + stock.average_position_price.nano / 1_000_000_000
                    current_price = price_map.get(stock.figi, 0.0)
                    previous_close = price_map_yesterday.get(stock.figi, 0.0)
                    total_value = quantity * current_price  # Общая стоимость акций
                    yield_percent = ((current_price - avg_buy_price) / avg_buy_price) * 100.0 if avg_buy_price > 0 else 0.0
                    daily_yield = ((current_price - previous_close) / previous_close) * 100.0 if previous_close > 0 else 0.0
                    daily_yield_rub = (current_price - previous_close) * quantity  # Дневная доходность в рублях

                    stock_data.append({
                        "ticker": ticker,
                         "name": name[:15],
                        "quantity": quantity,
                        "avg_buy_price": avg_buy_price,
                        "current_price": current_price,
                        "total_value": total_value,
                        "yield_percent": yield_percent,
                        "daily_yield": daily_yield,
                        "daily_yield_rub": daily_yield_rub
                    })

                # 6. Сортировка по доходности (yield_percent) в порядке убывания
                stock_data.sort(key=lambda x: x["daily_yield"], reverse=True)
                all_data = f"\nДень {cls.delta_days()}.\n\n"
                all_data += f"{'Тикер':<7} {'Наименование':<15} {'За всё время':<10}   {'За сегодня':<10}\n"
                all_data += "-" * 50 + "\n"

                for data in stock_data:
                    all_data += f"${data['ticker']:<7} {data['name']:<15} {data['yield_percent']:>10.2f}% {data['daily_yield']:>10.2f}% \n"

                return all_data

            except Exception as e:
                logger.error(f"Ошибка при получении портфеля, цен или свечей: {str(e)}")
                raise


if __name__ == "__main__":
    Stock.calculate_stock_yield()