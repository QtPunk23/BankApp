import sys
import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QLineEdit, QStackedWidget, QMessageBox, QDesktopWidget,
    QButtonGroup, QRadioButton, QGridLayout, QFormLayout
)
from PyQt5.QtCore import pyqtSignal, QRegExp
from PyQt5.QtGui import QDoubleValidator, QRegExpValidator


class Operation:
    def __init__(self, operation_type, amount):
        self.time = datetime.datetime.now()
        self.type = operation_type
        self.amount = amount


class Check:
    def __init__(self, full_name):
        self.full_name = full_name
        self.balance = 0.0
        self.operations = []

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.operations.append(Operation('deposit', amount))
        else:
            raise ValueError("Сумма должна быть положительной")

    def withdraw(self, amount):
        if amount <= self.balance and amount > 0:
            self.balance -= amount
            self.operations.append(Operation('withdraw', amount))
        elif amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        else:
            raise ValueError("Недостаточно средств на счёте")


class Credit:
    def __init__(self, amount, interest_rate, term_months, credit_type):
        self.amount = amount
        self.interest_rate = interest_rate / 100 / 12
        self.term_months = term_months
        self.credit_type = credit_type
        self.approved = False
        self.monthly_payment = None
        self.total_payment = None
        self.total_interest = None

    def calculate_payments(self):
        global monthly_payment
        if amount <= 0:
            raise ValueError("Сумма кредита должна быть положительной")
        if self.credit_type == 'annuity':
            # Формула аннуитетного платежа
            if self.interest_rate > 0:
                self.monthly_payment = (self.amount * self.interest_rate) / (
                        1 - (1 + self.interest_rate) ** -self.term_months)
            else:
                self.monthly_payment = self.amount / self.term_months
            self.total_payment = self.monthly_payment * self.term_months
            self.total_interest = self.total_payment - self.amount
        elif self.credit_type == 'differentiated':
            # Формула дифференцированного платежа
            principal_payment = self.amount / self.term_months
            self.total_payment = 0  # Общая сумма выплат по кредиту
            self.total_interest = 0  # Общая сумма выплат по процентам
            for month in range(1, self.term_months + 1):
                # Проценты начисляются на остаток долга
                interest_payment = (self.amount - (principal_payment * (month - 1))) * self.interest_rate
                monthly_payment = principal_payment + interest_payment
                self.total_payment += monthly_payment
                self.total_interest += interest_payment
            # Поскольку дифференцированные платежи изменяются, monthly_payment будет содержать последний платеж
            self.monthly_payment = monthly_payment
        else:
            raise ValueError("Неизвестный тип кредита")

    def apply(self):
        self.approved = True
        self.calculate_payments()


class Client:
    def __init__(self, full_name, phone_number):
        self.full_name = full_name
        self.phone_number = phone_number
        self.checks = []
        self.credits = []

    def create_check(self):
        new_check = Check(self.full_name)
        self.checks.append(new_check)
        return new_check

    def apply_for_credit(self, amount, interest_rate, term_months, credit_type):
        new_credit = Credit(amount, interest_rate, term_months, credit_type)
        self.credits.append(new_credit)
        return new_credit


# Реализация интерфейса

class RegistrationWidget(QWidget):
    switch_to_main = pyqtSignal(Client)

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QFormLayout()

        name_validator = QRegExpValidator(QRegExp("^[а-яА-ЯёЁa-zA-Z\s]+$"))

        self.surname_input = QLineEdit()
        self.surname_input.setValidator(name_validator)
        self.name_input = QLineEdit()
        self.name_input.setValidator(name_validator)
        self.patronymic_input = QLineEdit()
        self.patronymic_input.setValidator(name_validator)

        # Валидатор для номера телефона
        phone_validator = QRegExpValidator(QRegExp("^\+7 9\d{0,9}$"))
        self.phone_input = QLineEdit("+7 9")
        self.phone_input.setValidator(phone_validator)
        self.phone_input.setMaxLength(13)

        layout.addRow('Фамилия', self.surname_input)
        layout.addRow('Имя', self.name_input)
        layout.addRow('Отчество', self.patronymic_input)
        layout.addRow('Номер телефона', self.phone_input)

        register_button = QPushButton('Зарегистрироваться')
        register_button.clicked.connect(self.register)

        layout.addRow(register_button)
        self.setLayout(layout)

    def register(self):
        full_name = f"{self.surname_input.text()} {self.name_input.text()} {self.patronymic_input.text()}"
        phone = self.phone_input.text()

        # Проверка ФИО
        if not all(x.isalpha() or x.isspace() for x in full_name):
            QMessageBox.warning(self, 'Ошибка', 'ФИО должно содержать только буквы')
            return
        if not (phone.startswith("+7 9") and len(phone) == 13 and phone[3:].isdigit()):
            QMessageBox.warning(self, 'Ошибка', 'Номер телефона должен быть в формате +7 9XX XXXXXXX')
            return

        client = Client(full_name, phone)
        client.create_check()

        QMessageBox.information(self, 'Регистрация', 'Вы успешно зарегистрированы!')
        self.switch_to_main.emit(client)


class MainWidget(QWidget):
    goToDeposit = pyqtSignal()
    goToWithdraw = pyqtSignal()
    goToCredit = pyqtSignal()
    updateBalance = pyqtSignal(str)

    def __init__(self, check):
        super().__init__()
        self.check = check
        layout = QVBoxLayout(self)
        self.balance_label = QLabel(f'Баланс счёта: {self.check.balance:.2f} руб.')
        layout.addWidget(self.balance_label)

        deposit_button = QPushButton('Пополнить счет')
        withdraw_button = QPushButton('Снять деньги')
        credit_button = QPushButton('Подать заявку на кредит')

        deposit_button.clicked.connect(self.goToDeposit.emit)
        withdraw_button.clicked.connect(self.goToWithdraw.emit)
        credit_button.clicked.connect(self.goToCredit.emit)

        layout.addWidget(deposit_button)
        layout.addWidget(withdraw_button)
        layout.addWidget(credit_button)

        self.setLayout(layout)

    def update_balance_label(self, balance):
        self.balance_label.setText(f'Баланс счёта: {balance:.2f} руб.')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = None
        self.stacked_widget = QStackedWidget()

        self.registration_widget = RegistrationWidget()
        self.registration_widget.switch_to_main.connect(self.display_main_window)

        self.stacked_widget.addWidget(self.registration_widget)

        self.setCentralWidget(self.stacked_widget)
        self.initUI()

    def initUI(self):
        self.resize(600, 450)
        self.center()
        self.setWindowTitle('Банковское приложение')

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def display_main_window(self, client):
        self.client = client
        # Создаем MainWidget с передачей текущего баланса клиента
        self.main_widget = MainWidget(client.checks[-1])

        # Подключаем сигналы к методам для отображения виджетов операций
        self.main_widget.goToDeposit.connect(self.display_deposit_widget)
        self.main_widget.goToWithdraw.connect(self.display_withdraw_widget)
        self.main_widget.goToCredit.connect(self.display_credit_widget)

        # Добавляем MainWidget в стек виджетов и делаем его текущим виджетом
        self.stacked_widget.addWidget(self.main_widget)
        self.stacked_widget.setCurrentWidget(self.main_widget)

    def display_deposit_widget(self):
        self.deposit_widget = DepositWidget(self.client.checks[-1])
        self.deposit_widget.return_to_main.connect(self.display_main_widget)
        self.deposit_widget.balance_updated.connect(self.main_widget.update_balance_label)
        self.stacked_widget.addWidget(self.deposit_widget)
        self.stacked_widget.setCurrentWidget(self.deposit_widget)

    def display_withdraw_widget(self):
        self.withdraw_widget = WithdrawWidget(self.client.checks[-1])
        self.withdraw_widget.return_to_main.connect(self.display_main_widget)
        self.withdraw_widget.balance_updated.connect(self.main_widget.update_balance_label)
        self.stacked_widget.addWidget(self.withdraw_widget)
        self.stacked_widget.setCurrentWidget(self.withdraw_widget)

    def display_credit_widget(self):
        self.credit_widget = CreditWidget(self.client)
        self.credit_widget.return_to_main.connect(self.display_main_widget)
        self.stacked_widget.addWidget(self.credit_widget)
        self.stacked_widget.setCurrentWidget(self.credit_widget)

    def display_main_widget(self):
        self.stacked_widget.setCurrentWidget(self.main_widget)

    def update_main_balance(self, balance):
        self.main_widget.update_balance_label(f'{balance:.2f}')


class DepositWidget(QWidget):
    return_to_main = pyqtSignal()
    balance_updated = pyqtSignal(float)  # Сигнал для обновления баланса

    def __init__(self, check):
        super().__init__()
        self.check = check
        self.layout = QVBoxLayout(self)

        self.balance_label = QLabel(f'Текущий баланс: {self.check.balance:.2f} руб.')
        self.layout.addWidget(self.balance_label)

        # Кнопка возврата в главное меню
        return_button = QPushButton('Вернуться в главное меню', self)
        return_button.clicked.connect(self.return_to_main.emit)
        self.layout.addWidget(return_button)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00 руб")
        self.amount_input.setValidator(QDoubleValidator(0.0, 9999999.99, 2))
        deposit_button = QPushButton('Пополнить', self)
        deposit_button.clicked.connect(self.deposit)

        self.layout.addWidget(QLabel('Введите сумму для пополнения:'))
        self.layout.addWidget(self.amount_input)
        self.layout.addWidget(deposit_button)

    def deposit(self):
        try:
            amount_str = self.amount_input.text()
            amount = self.validate_amount(amount_str)
            if amount is None:
                return
            self.check.deposit(amount)
            self.balance_updated.emit(self.check.balance)  # Эмитируем сигнал с новым балансом
            QMessageBox.information(self, 'Успех', f'Счет пополнен на {amount} руб.')
            self.balance_label.setText(f'Текущий баланс: {self.check.balance:.2f} руб.')  # Обновляем баланс
        except ValueError as e:
            QMessageBox.warning(self, 'Ошибка', str(e))
        except Exception as e:
            QMessageBox.critical(self, 'Непредвиденная ошибка', str(e))
        finally:
            self.amount_input.clear()

    def validate_amount(self, amount_str):
        try:
            amount = float(amount_str)
            if "," in amount_str:
                raise ValueError
            return amount
        except ValueError:
            QMessageBox.warning(self, 'Ошибка', 'Используйте точку в качестве разделителя')
            return None


# Класс WithdrawWidget
class WithdrawWidget(QWidget):
    return_to_main = pyqtSignal()
    balance_updated = pyqtSignal(float)

    def __init__(self, check):
        super().__init__()
        self.check = check
        self.layout = QVBoxLayout(self)

        self.balance_label = QLabel(f'Текущий баланс: {self.check.balance:.2f} руб.')
        self.layout.addWidget(self.balance_label)

        # Кнопка возврата в главное меню
        return_button = QPushButton('Вернуться в главное меню', self)
        return_button.clicked.connect(self.return_to_main.emit)
        self.layout.addWidget(return_button)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        self.amount_input.setValidator(QDoubleValidator(0.0, 9999999.99, 2))
        withdraw_button = QPushButton('Снять', self)
        withdraw_button.clicked.connect(self.withdraw)

        self.layout.addWidget(QLabel('Введите сумму для снятия:'))
        self.layout.addWidget(self.amount_input)
        self.layout.addWidget(withdraw_button)

    def withdraw(self):
        try:
            amount_str = self.amount_input.text()
            amount = self.validate_amount(amount_str)
            if amount is None:
                return
            self.check.withdraw(amount)
            self.balance_updated.emit(self.check.balance)  # Эмитируем сигнал с новым балансом
            QMessageBox.information(self, 'Успех', f'С {amount} руб. снято со счета.')
            self.balance_label.setText(f'Текущий баланс: {self.check.balance:.2f} руб.')  # Обновляем баланс
        except ValueError as e:
            QMessageBox.warning(self, 'Ошибка', str(e))
        except Exception as e:
            QMessageBox.critical(self, 'Непредвиденная ошибка', str(e))
        finally:
            self.amount_input.clear()

    def validate_amount(self, amount_str):
        try:
            amount = float(amount_str)
            if "," in amount_str:
                raise ValueError
            return amount
        except ValueError:
            QMessageBox.warning(self, 'Ошибка', 'Используйте точку в качестве разделителя')
            return None


# Класс CreditWidget
class CreditWidget(QWidget):
    return_to_main = pyqtSignal()

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.layout = QGridLayout(self)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00 руб")
        self.amount_input.setValidator(QDoubleValidator(0.0, 9999999.99, 2))
        self.layout.addWidget(QLabel('Введите сумму кредита'), 0, 0)
        self.layout.addWidget(self.amount_input, 0, 1, 1, 3)

        # Радио кнопки для процентной ставки
        self.rate_group = QButtonGroup(self)
        rate_3 = QRadioButton("3%")
        rate_7 = QRadioButton("7%")
        rate_12 = QRadioButton("12%")
        self.rate_group.addButton(rate_3, 3)
        self.rate_group.addButton(rate_7, 7)
        self.rate_group.addButton(rate_12, 12)
        self.layout.addWidget(rate_3, 1, 1)
        self.layout.addWidget(rate_7, 1, 2)
        self.layout.addWidget(rate_12, 1, 3)
        rate_3.setChecked(True)  # Установим 3% как стандартное значение

        # Радио кнопки для срока кредита
        self.term_group = QButtonGroup(self)
        term_6 = QRadioButton("6 месяцев")
        term_12 = QRadioButton("12 месяцев")
        term_24 = QRadioButton("24 месяца")
        self.term_group.addButton(term_6, 6)
        self.term_group.addButton(term_12, 12)
        self.term_group.addButton(term_24, 24)
        self.layout.addWidget(term_6, 2, 1)
        self.layout.addWidget(term_12, 2, 2)
        self.layout.addWidget(term_24, 2, 3)
        term_6.setChecked(True)  # Установим 6 месяцев как стандартное значение

        # Радио кнопки для типа кредита
        self.type_group = QButtonGroup(self)
        annuity_payment = QRadioButton("Аннуитетный")
        differentiated_payment = QRadioButton("Дифференцированный")
        self.type_group.addButton(annuity_payment, 1)
        self.type_group.addButton(differentiated_payment, 2)
        self.layout.addWidget(annuity_payment, 3, 1)
        self.layout.addWidget(differentiated_payment, 3, 2)
        annuity_payment.setChecked(True)  # Установим аннуитетный как стандартное значение

        # Кнопка подачи заявки на кредит
        apply_button = QPushButton('Рассчитать ежемесячный платеж')
        apply_button.clicked.connect(self.calculate_monthly_payment)
        self.layout.addWidget(apply_button, 4, 0, 1, 4)

        # Кнопка для возврата в главное меню
        return_button = QPushButton('Вернуться в главное меню')
        return_button.clicked.connect(self.return_to_main.emit)
        self.layout.addWidget(return_button, 5, 0, 1, 4)

    def calculate_monthly_payment(self):
        amount = float(self.amount_input.text())
        interest_rate = float(self.rate_group.checkedButton().text().strip('%'))
        term_months = self.term_group.checkedId()
        credit_type = self.type_group.checkedButton().text()

        # Расчет аннуитетного платежа
        if credit_type == 'Аннуитетный':
            monthly_interest_rate = interest_rate / 100 / 12
            annuity_ratio = (monthly_interest_rate * (1 + monthly_interest_rate) ** term_months) / \
                            ((1 + monthly_interest_rate) ** term_months - 1)
            monthly_payment = amount * annuity_ratio
        # Расчет дифференцированного платежа (просто берем первый месяц для примера)
        else:
            principal_payment = amount / term_months
            monthly_interest_payment = (amount * (interest_rate / 100 / 12))
            monthly_payment = principal_payment + monthly_interest_payment

        QMessageBox.information(self, 'Расчет ежемесячного платежа',
                                f"При следующем кредитном плане ежемесячный платеж составит : {monthly_payment:.2f} руб.")


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
