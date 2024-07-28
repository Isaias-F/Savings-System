from config import db, VONAGE_API_KEY, VONAGE_API_SECRET, VONAGE_PHONE_NUMBER
import vonage
from prettytable import PrettyTable

client = vonage.Client(key=VONAGE_API_KEY, secret=VONAGE_API_SECRET)
sms = vonage.Sms(client)


class Account:

    def __init__(self, accountNumber=0, client_name=None, deposit_amount=0, account_type=None):
        self.accountNumber = accountNumber
        self.client_name = client_name
        self.deposit_amount = deposit_amount
        self.account_type = account_type

    def create_account(self):
        self.accountNumber = int(input("Enter your account number: "))
        self.client_name = input("Enter Client Name: ")
        self.account_type = input("Enter Account Type [D/C]: ")
        self.deposit_amount = int(input("Enter Deposit Amount: "))
        pin = int(input("Enter a 4-digit PIN: "))
        cursor = db.cursor()
        cursor.execute(
            f"INSERT INTO accounts (account_num, client_name, account_type, amount) VALUES ({self.accountNumber}, '{self.client_name}', '{self.account_type}', {self.deposit_amount})")
        cursor.execute(f"INSERT INTO users (account_num, pin) VALUES ({self.accountNumber}, {pin})")
        print(f"Account {self.accountNumber} created")
        print("Your account number is: ", self.accountNumber)


def send_sms(to_phone_number, message):
    responseData = sms.send_message(
        {
            "from": VONAGE_PHONE_NUMBER,
            "to": to_phone_number,
            "text": message,
        }
    )

    if responseData["messages"][0]["status"] == "0":
        print("Message sent successfully.")
    else:
        print(f"Message failed with error: {responseData['messages'][0]['error-text']}")


def splash():
    print("\t\t\t\t**********************")
    print("\t\t\t\t\t  ATM SYSTEM")
    print("\t\t\t\t**********************")

    input("Press Enter To Contiune: ")


def main_menu():
    def get_account_number_and_pin():
        account_num = int(input("Enter your account number: "))
        pin = int(input("Enter Your PIN: "))
        return account_num, pin

    options = {
        1: create_account,
        2: lambda: authenticate_and_execute(deposit_withdraw, 1),
        3: lambda: authenticate_and_execute(deposit_withdraw, 2),
        4: lambda: authenticate_and_execute(display_balance),
        5: display_accounts,
        6: lambda: authenticate_and_execute(delete_account),
        7: lambda: authenticate_and_execute(modify_account),
        8: lambda: authenticate_and_execute(display_transaction_history),
        9: exit
    }

    def authenticate_and_execute(action, *args):
        account_num, pin = get_account_number_and_pin()
        if authenticate_user(account_num, pin):
            action(account_num, *args)

    while True:
        print("\tMAIN MENU")
        print("\t1. NEW ACCOUNT")
        print("\t2. DEPOSIT AMOUNT")
        print("\t3. WITHDRAW AMOUNT")
        print("\t4. BALANCE ENQUIRY")
        print("\t5. ALL ACCOUNT HOLDER LIST")
        print("\t6. CLOSE AN ACCOUNT")
        print("\t7. MODIFY AN ACCOUNT")
        print("\t8. TRANSACTION HISTORY")
        print("\t9. EXIT")
        option = int(input("Enter Your Option: "))

        action = options.get(option)
        if action:
            action()
        else:
            print("Invalid Option")


def create_account():
    account = Account()
    account.create_account()


def display_accounts():
    cursor = db.cursor()
    cursor.execute(f"SELECT account_num FROM accounts")
    get_data = cursor.fetchall()
    if get_data:
        print("Account Numbers:")
        i = 0
        for _ in get_data:
            print(get_data[i][0])
            i += 1
    else:
        print("No Accounts Found")


def display_balance(account_num):
    cursor = db.cursor()
    cursor.execute(f"SELECT amount FROM accounts WHERE account_num = {account_num}")
    get_data = cursor.fetchone()
    if get_data:
        print("Your balance is: ", get_data[0])
    else:
        print("No data with this account number")


def deposit_withdraw(account_num, option):
    global new_amount
    cursor = db.cursor()
    cursor.execute(f"SELECT amount FROM accounts WHERE account_num = {account_num}")
    get_data = cursor.fetchone()
    if get_data:
        phone_number = '525539857822'
        amount = int(input("Enter Amount: "))
        if option == 1:
            new_amount = amount + get_data[0]
            log_transaction(account_num, 'deposit', amount)
            send_sms(phone_number, f"Depósito exitoso de ${amount}. Total de: ${new_amount}. ")
        elif option == 2:
            if amount > get_data[0]:
                print("You cannot withdraw more than your balance")
                return
            new_amount = get_data[0] - amount
            log_transaction(account_num, 'withdraw', amount)
            send_sms(phone_number, f"Retiro exitoso de ${amount}. Total de: ${new_amount}. ")
        print("Your balance is: ", new_amount)
        cursor.execute(f"UPDATE accounts SET amount = {new_amount} WHERE account_num = {account_num}")
    else:
        print("The account does not exist")


def delete_account(account_num):
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM accounts WHERE account_num = {account_num}")
    get_data = cursor.fetchone()
    if get_data:
        cursor.execute(f"DELETE FROM accounts WHERE account_num = {account_num}")
        print("Your account has been deleted")
    else:
        print("No Accounts Found")


def modify_account(account_num):
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM accounts WHERE account_num = {account_num}")
    get_data = cursor.fetchone()
    if get_data:
        client_name = input("Enter Client Name: ")
        account_type = input("Enter Account Type [D/C]: ")
        deposit_amount = int(input("Enter Deposit Amount: "))
        cursor.execute(
            f"UPDATE accounts SET client_name = '{client_name}', account_type = '{account_type}', amount = {deposit_amount} WHERE account_num = {account_num}")
        print("Your account has been modified")
    else:
        print("No data with this account number")


def log_transaction(account_num, transaction_type, amount):
    cursor = db.cursor()
    cursor.execute("INSERT INTO transactions (account_num, transaction_type, amount) VALUES (%s, %s, %s)",
                   (account_num, transaction_type, amount))


def display_transaction_history(account_num):
    cursor = db.cursor()
    cursor.execute(
        f"SELECT id, transaction_type, amount, timestamp FROM transactions WHERE account_num = {account_num}")
    get_data = cursor.fetchall()

    if get_data:
        table = PrettyTable()
        table.field_names = ["Transaction ID", "Type", "Amount", "Timestamp"]
        print("Transaction History:")
        for transaction in get_data:
            table.add_row(transaction)
            # print(f"{transaction[2]} - {transaction[0]}: {transaction[1]}")
        print(table)
    else:
        print("No transactions found for this account")


def authenticate_user(account_num, pin: int):
    cursor = db.cursor()
    cursor.execute(f"SELECT pin FROM users WHERE account_num = {account_num}")
    result = cursor.fetchone()
    if result and int(result[0]) == pin:
        return True
    else:
        print("Authentication failed. Incorrect PIN.")
        return False


if __name__ == '__main__':
    splash()
    main_menu()
