from win32gui import GetWindowText, GetForegroundWindow
import win32process
import psutil
import time
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from pywinauto import Application


def login():
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="8879576",
            database="ev_interna"
        )

        mycursor = mydb.cursor()
        gmail = input("Type in your gmail")
        password = input("Type in your password")
        try:
            mycursor.execute(
                "SELECT ID_usuario "
                "FROM usuarios "
                "WHERE email = %s AND contraseña = %s",
                (gmail, password,)
            )
            mydb.commit()

            result = mycursor.fetchone()
            if result == None:
                print("Something is Incorrect, Try Again")
            else:
                user_id = result[0]
                print(user_id)
                return user_id
        except Error as e:
            print(f"Error executing query: {e}")

    except Error as e:
        print(f"Error executing query: {e}")

def sign_up():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="8879576",
        database="ev_interna"
    )

    mycursor = mydb.cursor()

    nombre = input("Name: ")
    apellido = input("Last Name: ")
    correo_input = input("Enter your gmail: ")
    rol_familia = input("Rol Familiar")
    contra_input = input("Enter your password: ")
    contra_input2 = input("Re enter your password")
    try:
        if contra_input == contra_input2:
            mycursor.execute(
                "INSERT INTO usuarios (nombre, apellido, email, contraseña, rol) "
                "VALUES(%s,%s,%s,%s,%s);",
                (nombre, apellido, correo_input, contra_input, rol_familia,)
            )
            mydb.commit()
            print("Success")
        else:
            print("Password Not compatible")
    except Error as e:
        print(f"Error inserting record: {e}")
def program(user_id):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="8879576",
        database="ev_interna"
    )

    mycursor = mydb.cursor()
    proceso_anterior = None
    suma = 0
    diferencia = 0.0
    while True:
        while True:
            tiempo_partida = time.time()
            ventana_fore = GetForegroundWindow()
            id, pid = win32process.GetWindowThreadProcessId(ventana_fore)

            if pid > 0:
                try:
                    proceso_actual = psutil.Process(pid)
                    nombre_programa = proceso_actual.name()
                    time.sleep(1)

                    mycursor.execute(
                        "SELECT ID_programa "
                        "FROM programas "
                        "WHERE nombre_programa = %s", (nombre_programa,)
                    )
                    result_id = mycursor.fetchone()
                    print("stage 1")

                    if result_id is None:
                        query_insertar = ("INSERT INTO programas (nombre_programa) "
                                          "VALUES(%s)")
                        mycursor.execute(query_insertar, (nombre_programa,))
                        mydb.commit()
                        print("stage 2")

                        mycursor.execute(
                            "SELECT ID_programa "
                            "FROM programas "
                            "WHERE nombre_programa = %s", (nombre_programa,)
                        )
                        result_id = mycursor.fetchone()

                        mycursor.execute(
                            "SELECT ID_usuario_programa "
                            "FROM usuario_programa "
                            "WHERE ID_usuario = %s AND ID_programa = %s",
                            (user_id, result_id[0])
                        )
                        result_ID_usuario_programa = mycursor.fetchone()
                        print("stage 3")

                        if result_ID_usuario_programa is None:
                            query_insertar1 = ("INSERT INTO usuario_programa (ID_usuario,ID_programa) "
                                               "VALUES(%s,%s)")
                            mycursor.execute(query_insertar1, (user_id, result_id[0],))
                            mydb.commit()
                            print("stage 4")

                        checkpoint = time.time()
                        diferencia = (checkpoint - tiempo_partida)

                        suma += diferencia

                        mycursor.execute(
                            "UPDATE tiempo_utilizado "
                            "SET tiempo_utilizado = %s "
                            "WHERE ID_usuario_programa = %s and solo_fecha = %s",
                            (result_ID_usuario_programa, )
                        )








                except Exception as e:
                    print(f"Ocurrió un error: {e}")

while True:
    log_or_sign = int(input("1 Log In 2 Sign Up 3 Exit"))
    if log_or_sign == 1:
        login()
    if log_or_sign == 2:
        sign_up()
    if log_or_sign == 3:
        break
