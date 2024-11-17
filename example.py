import os

class BankAccount:
    def __init__(self, account_number, initial_balance):
        self.account_number = account_number
        self.balance = initial_balance
        self.transaction_history = []

    def deposit_money(self, amount):
        self.balance += amount
        self.transaction_history.append(f"Deposit: ${amount}")
        return self.balance

    def withdraw_money(self, amount):
        if amount <= self.balance:
            self.balance -= amount
            self.transaction_history.append(f"Withdrawal: ${amount}")
            return True
        return False

def calculate_interest_rate(credit_score, loan_amount):
    base_rate = 5.0
    credit_factor = (800 - credit_score) / 100
    amount_factor = loan_amount / 10000

    final_rate = base_rate + credit_factor + amount_factor
    return round(final_rate, 2)


def clear_term():
    os.system("clear")


# Global variables and usage example
minimum_balance = 100
service_charge = 25
transaction_limit = 1000

# Create an account and perform operations
my_account = BankAccount("12345", 500)
current_balance = my_account.deposit_money(300)
withdrawal_success = my_account.withdraw_money(200)

if current_balance > minimum_balance:
    interest = calculate_interest_rate(720, current_balance)
    print(f"Your interest rate would be: {interest}%")
