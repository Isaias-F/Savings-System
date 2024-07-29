import os
from datetime import datetime, timedelta
import random
from config import db, VONAGE_API_KEY, VONAGE_API_SECRET, VONAGE_PHONE_NUMBER
import vonage
from prettytable import PrettyTable
from fpdf import FPDF
import matplotlib.pyplot as plt

client = vonage.Client(key=VONAGE_API_KEY, secret=VONAGE_API_SECRET)    # Cliente para SMS
sms = vonage.Sms(client)


class Account:  # Clase de la cuenta

    def __init__(self, accountNumber=0, client_name=None, deposit_amount=0, account_type=None):
        self.accountNumber = accountNumber
        self.client_name = client_name
        self.deposit_amount = deposit_amount
        self.account_type = account_type

    def generate_account_number(self):  # Generador de numeros de cuenta
        return random.randint(000000, 999999)

    def create_account(self):   # Creador de cuenta
        cursor = db.cursor()
        while True: # Genera y revisa si ya hay un num registrado y obtiene otro nuevo
            self.accountNumber = self.generate_account_number()
            cursor.execute(f"SELECT account_num FROM accounts WHERE account_num = {self.accountNumber}")
            if cursor.fetchone() is None:
                break

        self.client_name = input("Nombre del cliente: ")
        self.account_type = input("Tipo de cuenta [D/C]: ")
        self.deposit_amount = int(input("Cantidad a depositar: "))
        pin = int(input("PIN de 4 digitos: "))
        cursor.execute(
            f"INSERT INTO accounts (account_num, client_name, account_type, amount) VALUES ({self.accountNumber}, '{self.client_name}', '{self.account_type}', {self.deposit_amount})")
        cursor.execute(f"INSERT INTO users (account_num, pin) VALUES ({self.accountNumber}, {pin})")
        print(f"Cuenta creada!")
        print("Numero de cuenta: ", self.accountNumber)
        print("Tipo de cuenta: ", self.account_type)
        print("Cantidad depositada: ", self.deposit_amount)
        print("PIN de acceso: ", pin)


class PDF(FPDF):
    def header(self):   # Titulo del reporte
        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, 'Reporte de transacciones', 0, 1, 'C')
        issue_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cell(0, 10, f"Fecha de emisión: {issue_date}", 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(10)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 10, body)
        self.ln()


def get_last_month_range(): # Obtiene los días del mes anterior para el reporte
    today = datetime.today()
    first_day_this_month = today.replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)
    first_day_last_month = last_day_last_month.replace(day=1)
    return first_day_last_month, last_day_last_month


def create_pie_chart(deposit_count, withdraw_count, account_num):   # Crea el grafico
    labels = 'Deposits', 'Withdrawals'
    sizes = [deposit_count, withdraw_count]
    colors = ['#4CAF50', '#F44336']
    explode = (0.1, 0)  # Explode the 1st slice (Deposits)

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=140)
    plt.axis('equal')

    # Save the pie chart as an image file
    plt.savefig(f'pie_chart_{account_num}.png')
    plt.close()


def create_transaction_report(account_num): # Crea el reporte en PDF
    start_date, end_date = get_last_month_range()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM transactions WHERE account_num = {account_num} AND timestamp BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}' ORDER BY timestamp DESC")
    transactions = cursor.fetchall()

    if transactions:
        deposit_count = 0 # Contador de transacciones
        withdraw_count = 0

        pdf = PDF()
        pdf.add_page()
        pdf.chapter_title(f'Transacciones No. Cuenta: {account_num} - {start_date.strftime("%Y-%m-%d")} a {end_date.strftime("%Y-%m-%d")}')

        body = ""
        for transaction in transactions: # Cuerpo del PDF
            trans_id, acc_num, trans_type, amount, timestamp = transaction
            body += f"ID: {trans_id}\n"
            body += f"Tipo: {trans_type}\n"
            body += f"Cantidad: ${amount}\n"
            body += f"Fecha: {timestamp}\n"
            body += "-" * 50 + "\n"

            if trans_type == "deposit": # Suma las operaciones
                deposit_count += 1
            elif trans_type == "withdraw":
                withdraw_count += 1

        pdf.chapter_body(body)  # Agrega la data
        create_pie_chart(deposit_count, withdraw_count, account_num) # Crea el gráfico
        pdf.add_page()  # Agrega pagina
        pdf.chapter_title("Resumen de transacciones")
        pdf.image(f'pie_chart_{account_num}.png', x=10, y=50, w=150) # Agrega la imagen
        pdf.output(f'transactions_report_{account_num}.pdf') # Genera el PDF82
        os.remove('pie_chart_' + str(account_num) + '.png') # Borra la imagen del gráfico
        print("Reporte generado exitosamente.")
    else:
        print("Sin transacciones encontradas.")


def send_sms(to_phone_number, message): # Envía SMS de las transacciones
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
    print("\t\t\t\t\tSAVINGS SYSTEM")
    print("\t\t\t\t**********************")


def main_menu():    # Menu principal
    def get_account_number_and_pin():   # Lector de cuenta y pin
        account_num = int(input("Ingresa tu numero de cuenta: "))
        pin = int(input("Ingresa tu PIN: "))
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
        9: lambda: authenticate_and_execute(create_transaction_report),
        0: exit
    }

    def authenticate_and_execute(action, *args):
        account_num, pin = get_account_number_and_pin() # Autentificador y ejecutor de funciones
        if authenticate_user(account_num, pin):
            action(account_num, *args)

    while True:
        print("\tMENU")
        print("\t1. NUEVA CUENTA")
        print("\t2. DEPOSITAR")
        print("\t3. RETIRAR")
        print("\t4. AHORRO EN CAJITA")
        print("\t5. MOSTRAR CUENTAS")
        print("\t6. BORRAR Y CERRAR CUENTA")
        print("\t7. MODIFICAR CUENTA")
        print("\t8. HISTORIAL DE TRANSACCIONES")
        print("\t9. GENERAR REPORTE DE TRANSACCIONES")
        print("\t0. SALIR")
        option = int(input("Ingresa la opcion [0-9]: "))

        action = options.get(option)    # Optiene la opcion
        if action:
            action()
        else:
            print("Opcion invalida")


def create_account():   # Crea la cuenta
    account = Account()
    account.create_account()


def display_accounts(): # Muestra todas las cuentas
    cursor = db.cursor()
    cursor.execute(f"SELECT account_num FROM accounts")
    get_data = cursor.fetchall()
    if get_data:
        print("Cuentas registradas:")
        i = 0
        for _ in get_data:
            print(get_data[i][0])
            i += 1
    else:
        print("No hay cuentas registradas")


def display_balance(account_num):   # Muestra el dinero en la cajita
    cursor = db.cursor()
    cursor.execute(f"SELECT amount FROM accounts WHERE account_num = {account_num}")
    get_data = cursor.fetchone()
    if get_data:
        print("Tu dinero disponible es: $", get_data[0])
    else:
        print("No hay datos con ese numero de cuenta")


def deposit_withdraw(account_num, option):  # Depositar o retirar
    global new_amount
    cursor = db.cursor()
    cursor.execute(f"SELECT amount FROM accounts WHERE account_num = {account_num}")
    get_data = cursor.fetchone()
    if get_data:  # Obtiene los datos
        phone_number = '1234567890'  # Numero de telefono a enviar el SMS
        amount = int(input("Ingresa la cantidad a depositar/retirar: "))
        if option == 1:  # Si es depositar
            new_amount = amount + get_data[0]
            log_transaction(account_num, 'deposit', amount)  # Registra al historial de transacciones
            #   send_sms(phone_number, f"Depósito exitoso de ${amount}. Total de: ${new_amount}. ")  ENVIA EL SMS
        elif option == 2:  # Si es retirar
            if amount > get_data[0]:
                print("No puedes retirar más de lo disponible en tu cuenta")
                return
            new_amount = get_data[0] - amount
            log_transaction(account_num, 'withdraw', amount)  # Registra al historial de transacciones
            #   send_sms(phone_number, f"Retiro exitoso de ${amount}. Total de: ${new_amount}. ")   ENVIA SMS
        print("Tu cantidad disponible es: $", new_amount)
        cursor.execute(f"UPDATE accounts SET amount = {new_amount} WHERE account_num = {account_num}")
    else:
        print("La cuenta no existe")


def delete_account(account_num):    # Borrar cuentas
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM accounts WHERE account_num = {account_num}")
    get_data = cursor.fetchone()
    if get_data:
        cursor.execute(f"DELETE FROM accounts WHERE account_num = {account_num}")
        print("Tu cuenta ha sido eliminada")
    else:
        print("Cuenta no encontrada")


def modify_account(account_num):    # Modificar cuenta
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM accounts WHERE account_num = {account_num}")
    get_data = cursor.fetchone()
    if get_data:
        client_name = input("Ingresa tu nombre: ")
        account_type = input("Ingresa el tipo de cuenta [D/C]: ")
        deposit_amount = int(input("Ingresa la cantidad en tu cajita: "))
        cursor.execute(
            f"UPDATE accounts SET client_name = '{client_name}', account_type = '{account_type}', amount = {deposit_amount} WHERE account_num = {account_num}")
        print("Los datos han sido modificados!")
    else:
        print("No hay datos para este numero de cuenta")


def log_transaction(account_num, transaction_type, amount):  # Enviar historial de transacciones
    cursor = db.cursor()
    cursor.execute("INSERT INTO transactions (account_num, transaction_type, amount) VALUES (%s, %s, %s)",
                   (account_num, transaction_type, amount))


def display_transaction_history(account_num):   # Mostrar historial de transacciones
    cursor = db.cursor()
    cursor.execute(
        f"SELECT id, transaction_type, amount, timestamp FROM transactions WHERE account_num = {account_num}")
    get_data = cursor.fetchall()

    if get_data:
        table = PrettyTable()   # Crea la tabla
        table.field_names = ["Transaction ID", "Type", "Amount", "Timestamp"]  # Titulos de las columnas
        print("Historial de transacciones:")
        for transaction in get_data:
            table.add_row(transaction)  # Inserta los datos
        print(table)  # Imprime la tabla
    else:
        print("Sin transacciones encontradas")


def authenticate_user(account_num, pin: int):  # Autentificar usuario y bloqueo de cuenta
    cursor = db.cursor()
    cursor.execute(f"SELECT pin, failed_attempts, account_locked FROM users WHERE account_num = {account_num}")
    result = cursor.fetchone()
    if not result:  # Si no hay cuenta
        print("Cuenta no existente")
        return False

    stored_pin, failed_attempts, account_locked = result  # Obtiene los datos de la db
    if account_locked == 1:  # Si la cuenta esta bloqueada
        print("Cuenta bloqueada debido a maximos intentos de ingreso")
        print("Contacta a soporte para solicitar el desbloqueo")
        return False

    if stored_pin == pin:  # Si el pin es correcto, ejecuta programa y resetea intentos
        cursor.execute(f"UPDATE users SET failed_attempts = 0 WHERE account_num = {account_num}")
        return True
    else:
        failed_attempts += 1  # Suma intento
        if failed_attempts == 3:  # Si el intento llega a tres
            cursor.execute(f"UPDATE users SET account_locked = 1 WHERE account_num = {account_num}")  # Bloquea en DB
            print("Tu cuenta ha sido bloqueada por máximo de intentos de ingreso")
            print("Contacta a soporte para solicitar el desbloqueo")
        else:  # Si menor a tres pero es incorrecto, suma intento
            cursor.execute(f"UPDATE users SET failed_attempts = {failed_attempts} WHERE account_num = {account_num}")
            print(f"PIN incorrecto. Tienes {3 - failed_attempts} intentos restantes")
        return False


if __name__ == '__main__':
    splash()
    main_menu()
