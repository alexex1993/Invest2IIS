import time
import json
from pathlib import Path
from tinkoff.invest import Client
from typing import Optional, Dict, Any


class AccountStatus:
    def __init__(self, token: str, account_id: str, cache_time: int = 60, history_file: str = "status_history.json"):
        self.token = token
        self.account_id = account_id
        self.cache_time = cache_time  # время кэширования в секундах
        self.history_file = history_file
        self._last_update = 0
        self._total_amount: int = None
        self._total_currencies: int = None
        self._total_shares: int = None
        self._total_bonds: int = None
        self._total_etf: int = None
        self._previous_values: Optional[Dict[str, int]] = self._load_previous_values()

    def _load_previous_values(self) -> Dict[str, int]:
        """Загружает предыдущие значения из файла, если он существует."""
        if Path(self.history_file).exists():
            with open(self.history_file, "r") as f:
                return json.load(f)
        return {}

    def _save_current_values(self) -> None:
        """Сохраняет текущие значения в файл."""
        current_values = {
            "total_amount": self.total_amount,
            "total_currencies": self.total_currencies,
            "total_shares": self.total_shares,
            "total_bonds": self.total_bonds,
            "total_etf": self.total_etf,
            "timestamp": time.time()
        }
        with open(self.history_file, "w") as f:
            json.dump(current_values, f, indent=4)

    def _update_portfolio(self) -> None:
        """Обновляет данные портфеля, если прошло больше `cache_time` секунд."""
        current_time = time.time()
        if current_time - self._last_update > self.cache_time:
            with Client(self.token) as client:
                portfolio = client.operations.get_portfolio(account_id=self.account_id)
                self._total_amount = portfolio.total_amount_portfolio.units
                self._total_currencies = portfolio.total_amount_currencies.units
                self._total_shares = portfolio.total_amount_shares.units
                self._total_bonds = portfolio.total_amount_bonds.units
                self._total_etf = portfolio.total_amount_etf.units
            self._last_update = current_time
            self._save_current_values()  # Сохраняем новые значения

    @property
    def total_amount(self) -> int:
        self._update_portfolio()
        return self._total_amount

    @property
    def total_currencies(self) -> int:
        self._update_portfolio()
        return self._total_currencies

    @property
    def total_shares(self) -> int:
        self._update_portfolio()
        return self._total_shares

    @property
    def total_bonds(self) -> int:
        self._update_portfolio()
        return self._total_bonds

    @property
    def total_etf(self) -> int:
        self._update_portfolio()
        return self._total_etf

    def _format_value(self, value: int) -> str:
        """Форматирует число (разделитель тысяч, округление до 2 знаков)."""
        return f"*{value}*"

    def has_currencies_changed(self) -> bool:
        """
        Проверяет, изменилось ли значение total_currencies по сравнению с предыдущим.
        Возвращает:
            - True, если изменилось
            - False, если осталось прежним или нет предыдущих данных
        """
        previous_value = self._previous_values.get("total_currencies")
        current_value = self.total_currencies
        print(f"previous_value = {previous_value}, current_value = {current_value}")

        if previous_value is None:
            return False  # Нет предыдущих данных → считаем, что не изменилось

        return not (abs(current_value - previous_value) == 0)

    def _get_delta_str(self, current: int, previous: int) -> str:
        """Возвращает строку с дельтой (разницей) между текущим и предыдущим значением."""
        if previous is None:
            return ""
        delta = current - previous
        if delta > 0:
            return f"(+{self._format_value(delta)})"
        elif delta < 0:
            return f"({self._format_value(delta)})"
        else:
            return ""

    def __str__(self) -> str:
        self._update_portfolio()  # Обновляем данные перед выводом

        # Получаем текущие и предыдущие значения
        current_values = {
            "total_amount": self.total_amount,
            "total_currencies": self.total_currencies,
            "total_shares": self.total_shares,
            "total_bonds": self.total_bonds,
            "total_etf": self.total_etf,
        }

        # Формируем строку с дельтами
        lines = [
            f"Общая стоимость портфеля: {self._format_value(current_values['total_amount'])} {self._get_delta_str(current_values['total_amount'], self._previous_values.get('total_amount'))}",
            f"Стоимость облигаций: {self._format_value(current_values['total_bonds'])} {self._get_delta_str(current_values['total_bonds'], self._previous_values.get('total_bonds'))}",
            f"Стоимость акций: {self._format_value(current_values['total_shares'])} {self._get_delta_str(current_values['total_shares'], self._previous_values.get('total_shares'))}",
            f"Стоимость ETF: {self._format_value(current_values['total_etf'])} {self._get_delta_str(current_values['total_etf'], self._previous_values.get('total_etf'))}",
            f"Доступные денежные средства: {self._format_value(current_values['total_currencies'])} {self._get_delta_str(current_values['total_currencies'], self._previous_values.get('total_currencies'))}",
        ]

        # Обновляем предыдущие значения для следующего сравнения
        self._previous_values = current_values

        return "\n".join(lines)