#pywin32

from win32gui import GetWindowText, GetForegroundWindow
import win32process
import psutil
import time
import mysql.connector
from datetime import datetime
from pywinauto import Application


mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="8879576",
        database="mydb"
    )

mycursor = mydb.cursor()
proceso_anterior = None
suma = 0
diferencia = 0.0

while True:
    tiempo_partida = time.time()
    ventana_fore = GetForegroundWindow()
    id, pid = win32process.GetWindowThreadProcessId(ventana_fore)

    if pid > 0:
        try:
            proceso_actual = psutil.Process(pid)
            nombre_programa = proceso_actual.name()

            time.sleep(1)

            print("stage 1")

            mycursor.execute(
                "SELECT time_spent, date_only "
                "FROM first "
                "WHERE program_name = %s AND date_only = CURDATE()",
                (nombre_programa,)
            )

            result = mycursor.fetchone()

            if result is None:
                insert_query = ("INSERT INTO first (program_name) "
                                "VALUES (%s)")

                name_to_search = nombre_programa

                mycursor.execute(insert_query, (name_to_search,))
                mydb.commit()
                print("stage 2")

            elif result[1] == datetime.today().date():
                '''
                if nombre_programa == "chrome.exe":
                    app = Application(backend='uia')
                    app.connect(title_re=".*Chrome.*")
                    element_name = "Address and search bar"
                    dlg = app.top_window()
                    url = dlg.child_window(title=element_name, control_type="Edit").get_value()
                    print(url)
                    time.sleep(1)

                if nombre_programa == "Opera.exe":
                    app = Application(backend='uia')
                    app.connect(title_re=".*Opera.*")
                    element_name = "Address field"
                    dlg = app.top_window()
                    url = dlg.child_window(title=element_name, control_type="Edit").get_value()
                    print(url)
                    time.sleep(1)
                '''

                print("stage 3")
                checkpoint = time.time()
                diferencia = (checkpoint - tiempo_partida)

                suma += diferencia

                time_value = result[0]
                mycursor.execute(
                    "UPDATE first "
                    "SET time_spent = %s "
                    "WHERE program_name = %s and date_only = %s",
                    (time_value + suma, nombre_programa, datetime.today().date())
                )

                mydb.commit()
                proceso_anterior = proceso_actual
                suma = 0

                print(nombre_programa, "%.1f" % suma)


            elif result[1] != datetime.today().date():
                print("stage 4")
                insert_query = ("INSERT INTO first (program_name) "
                                "VALUES (%s)")

                name_to_search = nombre_programa

                mycursor.execute(insert_query, (name_to_search,))

                print("elif")

                mydb.commit()



            else:
                print("Error?")

        except psutil.NoSuchProcess:
            print("Programa desconocido.")

    else:
        print("PID Invalido:", pid)


'''
greeting = tk.Label(text=(nombre_programa, "%.1f" % suma))
        greeting.pack()
        window.mainloop()
        
def nombre_programa(ventana):
    id, pid = win32process.GetWindowThreadProcessId(ventana)
    proceso = psutil.Process(pid)
    return proceso.name()


while True:
    ventana = GetForegroundWindow()
    nombre = nombre_programa(ventana)
    print(nombre)
    time.sleep(5)



import pygetwindow as gw
import psutil
import time

def get_program_name(window):
    proceso = psutil.Process(window.pid)
    return proceso.name()

while True:
    ventana_activa = gw.getActiveWindow()
    programa_activo = get_program_name(ventana_activa)
    titulo = ventana_activa.title

    programa_anterior = None
    ventana_actual = titulo

    if titulo != programa_anterior:
        programa_anterior = programa_activo

    print(programa_activo)
    time.sleep(5)
'''

