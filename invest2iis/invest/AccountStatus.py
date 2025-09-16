import time
import json
from pathlib import Path
from tinkoff.invest import Client
from datetime import datetime
from tinkoff.invest.utils import now
from typing import Optional, Dict, Any
from tinkoff.invest.schemas import OperationType

START_INVEST = datetime(2025, 7, 24)


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
        self._total_coupons: int = None
        self._total_dividend: float = None
        self._previous_values: Optional[Dict[str, int]] = self._load_previous_values()

    @property
    def delta_days(self):
        delta_days: float = (datetime.today() - START_INVEST).days
        return delta_days

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
            "total_coupons": self.total_coupons,
            "total_dividend": self.total_dividend,
            "timestamp": time.time()
        }
        with open(self.history_file, "w") as f:
            json.dump(current_values, f, indent=4)

    def _update_portfolio(self) -> None:
        """Обновляет данные портфеля, если прошло больше `cache_time` секунд."""
        current_time = time.time()
        if current_time - self._last_update > self.cache_time:
            with Client(self.token) as client:
                total_coupons: float = 0.0  # Купоны
                total_input: float = 0.0
                total_dividend: float = 0.0
                operations = client.operations.get_operations(account_id=self.account_id, from_=datetime(2025, 7, 1), to=now()).operations
                unique_op_types = set()

                for operation in operations:
                    payment = operation.payment.units + (operation.payment.nano / 1000000000.0) # Сумма операции в рублях
                    op_type = operation.operation_type
                    unique_op_types.add(op_type)
                    if op_type == OperationType.OPERATION_TYPE_COUPON:
                        total_coupons += payment

                    if op_type == OperationType.OPERATION_TYPE_DIVIDEND:
                        total_dividend += payment

                    if op_type == OperationType.OPERATION_TYPE_INPUT:
                        total_input += payment

                portfolio = client.operations.get_portfolio(account_id=self.account_id)

                #years = float(self.delta_days) / 365.0
                #cagr = (float(portfolio.total_amount_portfolio.units) / total_input) ** (1.0 / float(years)) - 1.0
                #prc_interest_year = cagr * 100.0

                self._total_amount = portfolio.total_amount_portfolio.units
                self._total_currencies = portfolio.total_amount_currencies.units
                self._total_shares = portfolio.total_amount_shares.units
                self._total_bonds = portfolio.total_amount_bonds.units
                self._total_etf = portfolio.total_amount_etf.units
                self._total_coupons = round(total_coupons, 2)
                self._total_dividend = round(total_dividend, 2)
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

    @property
    def total_coupons(self) -> int:
        self._update_portfolio()
        return self._total_coupons

    @property
    def total_dividend(self) -> float:
        self._update_portfolio()
        return self._total_dividend

    def _format_value(self, value) -> str:
        """Форматирует число (разделитель тысяч, округление до 2 знаков)."""
        return f"*{round(value, 1):,}*".replace(",", " ")

    def has_currencies_changed(self) -> bool:
        """
        Проверяет, изменилось ли значение total_currencies по сравнению с предыдущим.
        Возвращает:
            - True, если изменилось
            - False, если осталось прежним или нет предыдущих данных
        """
        previous_value = self._previous_values.get("total_currencies")
        current_value = self.total_currencies

        if previous_value is None:
            return False  # Нет предыдущих данных → считаем, что не изменилось

        return not (abs(current_value - previous_value) == 0)

    def _get_delta_str(self, current: int, previous: int) -> str:
        """Возвращает строку с дельтой (разницей) между текущим и предыдущим значением."""
        if previous is None:
            return ""
        delta = current - previous
        if delta > 0:
            return f"(+{self._format_value(round(delta,1))})"
        elif delta < 0:
            return f"({self._format_value(round(delta,1))})"
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
            "total_coupons": self.total_coupons,
            "total_dividend": self.total_dividend
        }

        # Формируем строку с дельтами
        lines = [
            f"Общая стоимость портфеля: {self._format_value(current_values['total_amount'])} {self._get_delta_str(current_values['total_amount'], self._previous_values.get('total_amount'))}",
            f"Стоимость облигаций: {self._format_value(current_values['total_bonds'])} {self._get_delta_str(current_values['total_bonds'], self._previous_values.get('total_bonds'))}",
            f"Стоимость акций: {self._format_value(current_values['total_shares'])} {self._get_delta_str(current_values['total_shares'], self._previous_values.get('total_shares'))}",
            f"Стоимость фондов: {self._format_value(current_values['total_etf'])} {self._get_delta_str(current_values['total_etf'], self._previous_values.get('total_etf'))}",
            f"Купонов выплачено: {self._format_value(current_values['total_coupons'])} {self._get_delta_str(current_values['total_coupons'], self._previous_values.get('total_coupons'))}",
            f"Дивидендов выплачено: {self._format_value(current_values['total_dividend'])} {self._get_delta_str(current_values['total_dividend'], self._previous_values.get('total_dividend'))}",
            f"Доступные денежные средства: {self._format_value(current_values['total_currencies'])} {self._get_delta_str(current_values['total_currencies'], self._previous_values.get('total_currencies'))}",
        ]

        # Обновляем предыдущие значения для следующего сравнения
        self._previous_values = current_values

        return "\n".join(lines)