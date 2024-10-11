import tkinter
import customtkinter
from tkinter import *
from tkinter.ttk import Treeview, Style
from PIL import Image, ImageTk
import mysql.connector
import threading
from CTkMessagebox import CTkMessagebox
from win32gui import GetWindowText, GetForegroundWindow
import win32process
import psutil
import time, timedelta
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
from CTkScrollableDropdown import *
import winreg
import os




customtkinter.set_appearance_mode('System')
customtkinter.set_appearance_mode('Red')

def configure_treeview_style():
    style = Style()
    style.configure('Treeview',
                    font=('Trebuchet', 18),  # Font for treeview items
                    foreground='black',  # Text color
                    background='lightblue',  # Background color
                    rowheight=30,  # Row height
                    fieldbackground='white',  # Entry field background color
                    bordercolor='gray',  # Border color
                    relief='solid'  # Border style
                    )
    style.configure('Treeview.Heading',
                    font=('Trebuchet', 20, 'bold'),  # Font for header
                    foreground='black',  # Text color for header
                    background='black'  # Background color for header
                    )

    style.configure("Treeview.Heading", relief="solid")

    style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
    style.map("Treeview",
              background=[("selected", "blue")],
              foreground=[("selected", "white")])
class Monitoreo_programa:
    def __init__(self, user_id, blocked_programs):
        self.user_id = user_id
        self.blocked_programs = blocked_programs
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="8879576",
            database="ev_interna"
        )
        self.last_tiempo_partida = None
    def is_program_blocked(self, program_name, current_time):
        mycursor = self.db.cursor()
        query = """
            SELECT hora_inicial, hora_final
            FROM bloqueo_tiempo
            JOIN usuario_programa ON bloqueo_tiempo.ID_usuario_programa = usuario_programa.ID_usuario_programa
            JOIN programas ON usuario_programa.ID_programa = programas.ID_programa
            WHERE usuario_programa.ID_usuario = %s AND programas.nombre_programa = %s
        """

        mycursor.execute(query, (self.user_id, program_name))
        result = mycursor.fetchone()

        if result:
            hora_inicial, hora_final = result
            hora_inicial = (datetime.min + hora_inicial).time()
            hora_final = (datetime.min + hora_final).time()

            current_time = current_time.time()

            if hora_final < hora_inicial:
                return hora_inicial <= current_time or current_time <= hora_final
            else:
                return hora_inicial <= current_time <= hora_final
        return False
    def monitor(self):
        user_id = 1
        mycursor = self.db.cursor()
        suma = 0
        while True:
            tiempo_partida = time.time()
            ventana_fore = GetForegroundWindow()
            id, pid = win32process.GetWindowThreadProcessId(ventana_fore)

            if pid > 0:
                try:
                    proceso_actual = psutil.Process(pid)
                    nombre_programa = proceso_actual.name()
                    tiempo_actual = datetime.now()


                    if self.is_program_blocked(nombre_programa, tiempo_actual):
                        msg1 = CTkMessagebox(message="This program has been blocked for the current time period.",
                                             option_1 ="Ok",
                                             button_width=375)
                        if msg1.get() == "Ok":
                            proceso_actual.terminate()
                        continue

                    query = """ 
                            SELECT programa_bloqueado
                            FROM usuario_programa 
                            JOIN programas ON usuario_programa.ID_programa = programas.ID_programa
                            WHERE ID_usuario = %s AND nombre_programa = %s
                    """
                    mycursor.execute(query, (user_id, nombre_programa))
                    result = mycursor.fetchone()

                    if result and result[0] == 1:
                        msg1 = CTkMessagebox(message="This program has been blocked.",
                                             option_1="Ok",
                                             button_width=375)
                        if msg1.get() == "Ok":
                            proceso_actual.terminate()

                    mycursor.execute(
                        "SELECT ID_programa "
                        "FROM programas "
                        "WHERE nombre_programa = %s", (nombre_programa,)
                    )
                    program_id = mycursor.fetchone()
                    print("stage 1")

                    if program_id is None:
                        query_insertar = ("INSERT INTO programas (nombre_programa) "
                                          "VALUES(%s)")
                        mycursor.execute(query_insertar, (nombre_programa,))
                        self.db.commit()
                        print("stage 2")

                        mycursor.execute(
                            "SELECT ID_programa "
                            "FROM programas "
                            "WHERE nombre_programa = %s", (nombre_programa,)
                        )
                        program_id = mycursor.fetchone()

                    if program_id is not None:
                        mycursor.execute(
                            "SELECT ID_usuario_programa "
                            "FROM usuario_programa "
                            "WHERE ID_usuario = %s AND ID_programa = %s",
                            (user_id, program_id[0])
                        )
                        result_ID_usuario_programa = mycursor.fetchone()
                        print("stage 3")

                        if result_ID_usuario_programa is None:
                            query_insertar1 = ("INSERT INTO usuario_programa (ID_usuario,ID_programa) "
                                           "VALUES(%s,%s)")
                            mycursor.execute(query_insertar1, (user_id, program_id[0],))
                            self.db.commit()
                            print("stage 4")

                            mycursor.execute(
                            "SELECT ID_usuario_programa "
                            "FROM usuario_programa "
                            "WHERE ID_usuario = %s AND ID_programa = %s",
                            (user_id, program_id[0])
                            )
                            result_ID_usuario_programa = mycursor.fetchone()

                        if result_ID_usuario_programa is not None:
                            checkpoint = time.time()
                            if self.last_tiempo_partida is not None:
                                diferencia = checkpoint - self.last_tiempo_partida
                            else:
                                diferencia = checkpoint - tiempo_partida

                            suma += diferencia
                            solo_fecha = datetime.now().date()

                            mycursor.execute(
                            "SELECT tiempo_utilizado "
                            "FROM tiempo_utilizado "
                            "WHERE ID_usuario_programa = %s AND solo_fecha = %s",
                    (result_ID_usuario_programa[0], solo_fecha)
                            )
                            tiempo_utilizado_existente = mycursor.fetchone()
                            print("stage 5")

                            if tiempo_utilizado_existente:
                                tiempo_nuevo = timedelta(seconds=tiempo_utilizado_existente[0]) + timedelta(seconds=suma)
                                tiempo_nuevo_seconds = int(tiempo_nuevo.total_seconds())
                                mycursor.execute(
                            "UPDATE tiempo_utilizado "
                                    "SET tiempo_utilizado = %s "
                                    "WHERE ID_usuario_programa = %s AND solo_fecha = %s",
                            (tiempo_nuevo_seconds, result_ID_usuario_programa[0], solo_fecha)
                                    )
                                self.db.commit()
                                print(f"Updated tiempo_utilizado: {tiempo_nuevo_seconds}")
                                print("stage 6")
                                suma = 0


                            else:
                                solo_hora = datetime.now().time()
                                tiempo_utilizado_seconds = int(timedelta(seconds=suma).total_seconds())
                                mycursor.execute(
                        "INSERT INTO tiempo_utilizado (ID_usuario_programa, tiempo_utilizado, solo_hora, solo_fecha)"
                                "VALUES (%s,%s,%s,%s) ",
                        (result_ID_usuario_programa[0], tiempo_utilizado_seconds, solo_hora, solo_fecha)
                    )
                                self.db.commit()

                                print("Registro de tiempo utilizado actualizado")
                                suma = 0

                            self.last_tiempo_partida = checkpoint

                except Exception as e:
                    print(f"Ocurrió un error: {e}")
            time.sleep(1)
class Database:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def connect(self):
        return mysql.connector.connect(
            host = self.host,
            user = self.user,
            password = self.password,
            database = self.database
        )
    def fetch_program_usage (self, user_id, selected_date):
        try:
            mydb = self.connect()
            mycursor = mydb.cursor()
            query = (
                "SELECT programas.nombre_programa, tiempo_utilizado.tiempo_utilizado, tiempo_utilizado.solo_fecha "
                "FROM programas "
                "JOIN usuario_programa ON programas.ID_programa = usuario_programa.ID_programa "
                "JOIN tiempo_utilizado ON usuario_programa.ID_usuario_programa = tiempo_utilizado.ID_usuario_programa "
                "WHERE usuario_programa.ID_usuario = %s AND solo_fecha =%s "
                "ORDER BY tiempo_utilizado.tiempo_utilizado DESC"

            )
            mycursor.execute(query,(user_id, selected_date))
            result = mycursor.fetchall()
            return result
        except Error as e:
            print(f"Error fetching data: {e}")
            return []
class Login:
    def __init__(self,root):
        self.root = root
        self.root.geometry('400x400')
        self.db = Database(
            "localhost",
            "root",
            "8879576",
            "ev_interna"
        )



        self.titulo_login = customtkinter.CTkLabel(self.root, text="Login",
                                                font=('Montserrat Black', 48))
        self.titulo_login.pack(pady=20)

        entrada_frame = customtkinter.CTkFrame(self.root,fg_color="transparent")
        entrada_frame.pack(pady=10)

        self.entrada_label = customtkinter.CTkLabel(entrada_frame, text=("Ingrese correo"))
        self.entrada_label.pack(side= "left",padx=5)

        self.entrada_usuario = customtkinter.CTkEntry(entrada_frame,width=200)
        self.entrada_usuario.pack(side= "left",padx=5)

        contrasena_frame = customtkinter.CTkFrame(self.root,fg_color="transparent")
        contrasena_frame.pack(pady=10)

        self.contrasena_label = customtkinter.CTkLabel(contrasena_frame, text=("Ingrese Contraseña"))
        self.contrasena_label.pack(side= "left",padx=5)

        self.entrada_clave = customtkinter.CTkEntry(contrasena_frame, show="*",width=200)
        self.entrada_clave.pack(side= "left",padx=5)

        self.boton_login = customtkinter.CTkButton(self.root, text="Login", command=self.funcion_login)
        self.boton_login.pack(pady = 30)

        self.boton_ir_registro = customtkinter.CTkButton(self.root, text="No tengo cuenta",
                                                      command=self.ir_registro)
        self.boton_ir_registro.pack(pady=5)

        self.incorrecto = customtkinter.CTkLabel(self.root, text="", fg_color="transparent", text_color="red")
        self.incorrecto.pack()

    def funcion_login(self):
        contrasena = self.entrada_clave.get()
        correo_usuario= self.entrada_usuario.get()

        mydb = self.db.connect()
        mycursor = mydb.cursor()

        mycursor.execute("SELECT ID_usuario "
                         "FROM usuarios "
                         "WHERE email= %s AND contraseña= %s",
                         (correo_usuario,contrasena)

        )
        ID_usuario = mycursor.fetchone()

        if ID_usuario == None:
            self.incorrecto.configure(text="Campo Ingresado Incorrecto")
        else:
            self.incorrecto.configure(text="")
            print("ID Usuario:", ID_usuario)
            self.root.withdraw()
            main_app = App(customtkinter.CTkToplevel(), ID_usuario[0])
    def ir_registro(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        pagina_login = Registro(self.root)
class Registro:
    def __init__(self, root):
        self.root = root
        self.root.geometry('400x600')
        self.db = Database(
            "localhost",
            "root",
            "8879576",
            "ev_interna"
        )

        self.titulo_registro = customtkinter.CTkLabel(self.root, text="Registrarse",
                                                      font=('Montserrat Black', 48))
        self.titulo_registro.pack(pady=20)

        entrada_frame = customtkinter.CTkFrame(self.root, fg_color="transparent")
        entrada_frame.pack(pady=10)

        self.nombre_label = customtkinter.CTkLabel(entrada_frame, text=("Ingrese su nombre"))
        self.nombre_label.pack(padx=5, fill="x")

        self.nombre_usuario = customtkinter.CTkEntry(entrada_frame, width=200)
        self.nombre_usuario.pack(padx=5, fill="x")

        self.apellido_label = customtkinter.CTkLabel(entrada_frame, text=("Ingrese su Apellido"))
        self.apellido_label.pack(padx=5, fill="x")

        self.apellido_usuario = customtkinter.CTkEntry(entrada_frame, width=200)
        self.apellido_usuario.pack(padx=5, fill="x")

        self.entrada_label = customtkinter.CTkLabel(entrada_frame, text=("Ingrese correo"))
        self.entrada_label.pack(padx=5, fill="x")

        self.entrada_usuario = customtkinter.CTkEntry(entrada_frame, width=200)
        self.entrada_usuario.pack(padx=5, fill="x")

        contrasena_frame = customtkinter.CTkFrame(self.root, fg_color="transparent")
        contrasena_frame.pack(pady=10, fill="x")

        self.contrasena_label = customtkinter.CTkLabel(contrasena_frame, text=("Ingrese Contraseña"))
        self.contrasena_label.pack(padx=5, fill="x")

        self.entrada_clave = customtkinter.CTkEntry(contrasena_frame, show="*", width=200)
        self.entrada_clave.pack(padx=5)

        self.contrasena_label1 = customtkinter.CTkLabel(contrasena_frame, text=("Vuelva a introducir la contraseña"))
        self.contrasena_label1.pack(padx=5, fill="x")

        self.entrada_clave1 = customtkinter.CTkEntry(contrasena_frame, show="*", width=200)
        self.entrada_clave1.pack(padx=5)

        self.rol_familiar = customtkinter.CTkLabel(contrasena_frame, text=("Rol Familiar"))
        self.rol_familiar.pack(padx=5)

        self.option_menu = customtkinter.CTkOptionMenu(contrasena_frame, values=["Padre", "Hijo"])
        self.option_menu.pack(pady=5)

        self.boton_registro = customtkinter.CTkButton(self.root, text="Registrarse", command=self.funcion_registro)
        self.boton_registro.pack(pady=5)

        self.boton_ir_login = customtkinter.CTkButton(self.root, text="Ya tengo una cuenta",
                                                      command=self.ir_login)
        self.boton_ir_login.pack(pady=5)

        self.incorrecto = customtkinter.CTkLabel(self.root, text="", fg_color="transparent", text_color="red")
        self.incorrecto.pack()
    def funcion_registro(self):
        if self.entrada_clave == self.entrada_clave1:
            nombre = self.nombre_usuario.get()
            apellido = self.apellido_usuario.get()
            correo_usuario = self.entrada_usuario.get()
            contrasena = self.entrada_clave.get()
            rol = self.rol_familiar.get()

            mydb = self.db.connect()
            mycursor = mydb.cursor()

            mycursor.execute("INSERT INTO usuarios (nombre, apellido, email, contraseña, rol)  "
                             "VALUES (%s,%s, %s,%s, %s) ",
                             (nombre, apellido, correo_usuario, contrasena,rol)
                             )
            mydb.commit()

            self.incorrecto.configure(text="Registrado con éxito", text_color="green")

            mycursor.execute("SELECT ID_usuario "
                             "FROM usuarios "
                             "WHERE email = %s", (correo_usuario,))
            ID_usuario = mycursor.fetchone()

            if ID_usuario:
                self.root.withdraw()
                main_app = App(tkinter.Toplevel(), ID_usuario[0])
            else:
                None

        else:
            self.incorrecto.configure(text="Las contraseñas no coinciden", text_color="green")
    def ir_login(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        pagina_login = Login(self.root)
class App:
    def __init__(self,root, user_id):
        self.root = root
        self.user_id = user_id
        self.root.geometry('1200x700')
        self.db = Database(
            "localhost",
            "root",
            "8879576",
            "ev_interna"
        )

        self.monitor = Monitoreo_programa(user_id=self.user_id, blocked_programs=[])
        self.monitor_thread = threading.Thread(target=self.monitor.monitor, daemon=True)
        self.monitor_thread.start()

        self.left_frame_1 = customtkinter.CTkFrame(self.root, fg_color="transparent")
        self.left_frame_1.pack(side=LEFT, fill=Y, padx=10, pady=20)

        self.page1_frame = customtkinter.CTkFrame(self.root,fg_color="transparent")
        self.page2_frame = customtkinter.CTkFrame(self.root,fg_color="transparent")
        self.page3_frame = customtkinter.CTkFrame(self.root,fg_color="transparent")
        self.page4_frame = customtkinter.CTkFrame(self.root,fg_color="transparent")
        self.page5_frame = customtkinter.CTkFrame(self.root,fg_color="transparent")

        self.setup_ui()

        self.show_frame(self.page1_frame)
        self.display_program_usage(self.user_id)

        self.refresh_interval = 60000
        self.refresh_data()


    def setup_ui(self):
        configure_treeview_style()
        image_width = 35
        image_height = 35

        style = Style()

        pie_image = Image.open("imaged/pie_chart.png").resize((image_width, image_height))
        pie_photo = customtkinter.CTkImage(pie_image)

        calendar_image = Image.open("imaged/calendar.png").resize((image_width, image_height))
        calendar_photo = customtkinter.CTkImage(calendar_image)

        check_image = Image.open("imaged/checklist.png").resize((image_width, image_height))
        check_photo = customtkinter.CTkImage(check_image)

        page1btn = customtkinter.CTkButton(master = self.left_frame_1, image=pie_photo, command=self.page1, text="",width=50, height=50)
        page2btn =customtkinter.CTkButton(master = self.left_frame_1, image=calendar_photo, command=self.page2, text="",width=50, height=50)
        page3btn = customtkinter.CTkButton(master = self.left_frame_1, image=check_photo, command=self.page3, text="",width=50, height=50)

        page1btn.pack(pady=10)
        page2btn.pack(pady=10)
        page3btn.pack(pady=10)


        self.configure_page1()
        self.configure_page2()
        self.configure_page3()


    def configure_page1(self):
        self.page1text = customtkinter.CTkLabel(master=self.page1_frame, text="Menú Principal",
                                                font=('Montserrat Black', 60))
        self.page1text.pack(pady=12, padx=10)
        self.right_frame_1 = customtkinter.CTkFrame(self.page1_frame, fg_color="transparent")
        self.right_frame_1.pack(side=RIGHT, fill=Y, padx=10, pady=20)

        self.tree = Treeview(self.page1_frame, columns=("Nombre del Programa", "Tiempo Utilizado", "Fecha"), show='headings')
        self.tree.heading("Nombre del Programa", text="Nombre del Programa")
        self.tree.heading("Tiempo Utilizado", text="Tiempo Utilizado (minutos)")
        self.tree.heading("Fecha", text="Fecha")
        self.tree.pack(side=LEFT, pady=50, padx=50, fill=BOTH, expand=True)

        refresh_button = customtkinter.CTkButton(master=self.right_frame_1, text="Refrescar",command=self.refresh_info)
        refresh_button.pack(ipadx=10, ipady=10, padx=20, pady=10)

        date_button = customtkinter.CTkButton(master=self.right_frame_1, text="Filtrar por fecha", command=self.choose_date)
        date_button.pack(ipadx=10, ipady=10, padx=20)
    def configure_page2(self):
        self.page2text = customtkinter.CTkLabel(master=self.page2_frame, text="Bloqueo de programa",
                                                font=('Montserrat Black', 60))
        self.page2text.pack(pady=12, padx=10)

        self.right_frame_2 = customtkinter.CTkFrame(self.page2_frame, fg_color="transparent")
        self.right_frame_2.pack(side=RIGHT, fill=Y, padx=10, pady=20)
        self.right_frame_2.pack_propagate(False)
        self.right_frame_2.configure(width=400, height=500)

        mydb = self.db.connect()
        mycursor = mydb.cursor()
        mycursor.execute("SELECT programas.nombre_programa "
                         "FROM programas "
                         "JOIN usuario_programa ON programas.ID_programa = usuario_programa.ID_programa "
                         "WHERE usuario_programa.ID_usuario = %s ",
                         (self.user_id, ))
        programs = mycursor.fetchall()

        self.check_vars = {}

        scroll_frame = customtkinter.CTkScrollableFrame(master=self.page2_frame, width=300, height=400)
        scroll_frame.place(x=100, y=200)

        for program in programs:
            program_name = program[0]

            check_var = customtkinter.StringVar(value="off")
            self.check_vars[program_name] = check_var
            checkbox = customtkinter.CTkCheckBox(master=scroll_frame,
                                                 text=program_name,
                                                 variable=check_var,
                                                 onvalue="on",
                                                 offvalue="off"
                                                 )
            checkbox.pack(anchor=W,fill=Y, padx=20, pady=5,)

        confirm_button = customtkinter.CTkButton(master=self.page2_frame, text="Confirm Program Selection", command=self.confirm_selection, height=50, width=150)
        confirm_button.place(x=100, y=630)

        delete_button = customtkinter.CTkButton(master=self.page2_frame, text="Delete Program Blocker", command=self.delete_selection, height=50, width=150)
        delete_button.place(x=300, y=630)

        mycursor.execute("SELECT programas.nombre_programa "
                         "FROM programas "
                         "JOIN usuario_programa ON programas.ID_programa = usuario_programa.ID_programa "
                         "WHERE usuario_programa.ID_usuario = %s AND usuario_programa.programa_bloqueado = 1",
                         (self.user_id,))
        blocked_programs = mycursor.fetchall()

        self.tree2 = Treeview(self.right_frame_2, columns=("blocked_programs"), show='headings')
        self.tree2.heading("blocked_programs", text="Programas bloqueados")
        self.tree2.pack(side=RIGHT, pady=50, padx=50, fill=BOTH, expand=True)

        for program in blocked_programs:
            self.tree2.insert("", "end", values=(program[0],))
    def confirm_selection(self):
        selected_programs = []
        for program_name, check_var in self.check_vars.items():
            if check_var.get() == "on":
                selected_programs.append(program_name)

        print("Selected Programs:", selected_programs)
        mydb = self.db.connect()
        mycursor = mydb.cursor()
        update_query  = """
                         UPDATE usuario_programa 
                         SET programa_bloqueado = 1
                         WHERE ID_usuario = %s AND ID_programa= (
                            SELECT ID_programa 
                            FROM programas 
                            WHERE nombre_programa = %s) """

        for program_name in selected_programs:
            mycursor.execute(update_query,(self.user_id, program_name))

        mydb.commit()

        mydb = self.db.connect()
        mycursor = mydb.cursor()
        mycursor.execute("SELECT programas.nombre_programa "
                         "FROM programas "
                         "JOIN usuario_programa ON programas.ID_programa = usuario_programa.ID_programa "
                         "WHERE usuario_programa.ID_usuario = %s AND usuario_programa.programa_bloqueado = 1",
                         (self.user_id,))
        blocked_programs = mycursor.fetchall()

        for item in self.tree2.get_children():
            self.tree2.delete(item)

        for program in blocked_programs:
            self.tree2.insert("", "end", values=(program[0],))
    def delete_selection(self):
        selected_programs = []
        for program_name, check_var in self.check_vars.items():
            if check_var.get() == "on":
                selected_programs.append(program_name)

        print("Selected Programs:", selected_programs)
        mydb = self.db.connect()
        mycursor = mydb.cursor()
        update_query = """
                                UPDATE usuario_programa 
                                SET programa_bloqueado = 0
                                WHERE ID_usuario = %s AND ID_programa= (
                                   SELECT ID_programa 
                                   FROM programas 
                                   WHERE nombre_programa = %s) """

        for program_name in selected_programs:
            mycursor.execute(update_query, (self.user_id, program_name))
            mydb.commit()

        mydb = self.db.connect()
        mycursor = mydb.cursor()
        mycursor.execute("SELECT programas.nombre_programa "
                         "FROM programas "
                         "JOIN usuario_programa ON programas.ID_programa = usuario_programa.ID_programa "
                         "WHERE usuario_programa.ID_usuario = %s AND usuario_programa.programa_bloqueado = 1",
                         (self.user_id,))
        blocked_programs = mycursor.fetchall()

        for item in self.tree2.get_children():
            self.tree2.delete(item)

        for program in blocked_programs:
            self.tree2.insert("", "end", values=(program[0],))
    def search_blocked_programs(self):
        mydb = self.db.connect()
        mycursor = mydb.cursor()

        mycursor.execute("SELECT programas.nombre_programa "
                         "FROM programas "
                         "JOIN usuario_programa ON programas.ID_programa = usuario_programa.ID_programa "
                         "WHERE usuario_programa.ID_usuario = %s ",
                         (self.user_id,))
        programs = mycursor.fetchall()
    def configure_page3(self):
        for widget in self.page5_frame.winfo_children():
            widget.destroy()
        mydb = self.db.connect()
        mycursor = mydb.cursor()
        self.page3_label = customtkinter.CTkLabel(self.page3_frame, text="Bloqueo por tiempo",
                                                  font=('Montserrat Black', 48))
        self.page3_label.pack(padx=15, pady=20)

        horas = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
        minutos = [str(i) for i in range(1, 60)]

        hora_label = customtkinter.CTkLabel(self.page3_frame, text="Tiempo Inicial")
        hora_label.pack(padx=15, pady=15)

        desde_seleccion_hora = customtkinter.CTkOptionMenu(self.page3_frame, width=240)
        desde_seleccion_hora.pack(padx=15, pady=10)
        desde_seleccion_hora.set("Seleccione la hora inicial")
        CTkScrollableDropdown(desde_seleccion_hora, values=horas)

        desde_seleccion_minuto = customtkinter.CTkOptionMenu(self.page3_frame, width=240)
        desde_seleccion_minuto.pack(padx=10, pady=15)
        desde_seleccion_minuto.set("Seleccione el minuto inicial")
        CTkScrollableDropdown(desde_seleccion_minuto, values=minutos)

        pm_am = customtkinter.CTkSegmentedButton(self.page3_frame, values=["AM", "PM"])
        pm_am.pack(padx=15, pady=15)

        hora_label = customtkinter.CTkLabel(self.page3_frame, text="Seleccione la hora final de bloqueo")
        hora_label.pack(padx=15, pady=15)

        hasta_seleccion_hora = customtkinter.CTkOptionMenu(self.page3_frame, width=240)
        hasta_seleccion_hora.pack(padx=15, pady=15)
        hasta_seleccion_hora.set("Seleccione la hora final de bloqueo")
        CTkScrollableDropdown(hasta_seleccion_hora, values=horas)

        hasta_seleccion_minuto = customtkinter.CTkOptionMenu(self.page3_frame, width=240)
        hasta_seleccion_minuto.pack(padx=10, pady=15)
        hasta_seleccion_minuto.set("Seleccione el minuto final de bloqueo")
        CTkScrollableDropdown(hasta_seleccion_minuto, values=minutos)

        pm_am_final = customtkinter.CTkSegmentedButton(self.page3_frame, values=["AM", "PM"])
        pm_am_final.pack(padx=15, pady=15)

        def convertir_24_hora(hour, am_pm):
            hour = int(hour)
            if am_pm == "PM" and hour != 12:
                hour += 12
            elif am_pm == "AM" and hour == 12:
                hour = 0
            return f"{hour:02d}"

        def confirm_selected_programs():
            self.selected_programs = []
            for program_name, check_var in self.check_vars.items():
                if check_var.get() == "on":
                    self.selected_programs.append(program_name)

            print("Selected Programs:", self.selected_programs)
            self.show_frame(self.page3_frame)

        def final_confirm():
            if not hasattr(self, 'selected_programs') or not self.selected_programs:
                print("Ningun programa seleccionado. Porfavor seleccione programas.")
                return
            hora_inicial = desde_seleccion_hora.get()
            minuto_inicial = desde_seleccion_minuto.get()
            hora_final = hasta_seleccion_hora.get()
            minuto_final = hasta_seleccion_minuto.get()

            am_pm_inicial = pm_am.get()
            am_pm_final = pm_am_final.get()

            hora_inicial_24 = convertir_24_hora(hora_inicial, am_pm_inicial)
            hora_final_24 = convertir_24_hora(hora_final, am_pm_final)

            tiempo_inicial = f"{hora_inicial_24}:{int(minuto_inicial):02d}:00"
            tiempo_final = f"{hora_final_24}:{int(minuto_final):02d}:00"

            mydb = self.db.connect()
            mycursor = mydb.cursor()
            select_query = """
                        SELECT usuario_programa.ID_usuario_programa
                        FROM usuario_programa
                        JOIN usuarios ON usuario_programa.ID_usuario = usuarios.ID_usuario
                        JOIN programas ON usuario_programa.ID_programa = programas.ID_programa
                        WHERE usuarios.ID_usuario = %s
                        AND programas.nombre_programa = %s
                    """

            for program_name in self.selected_programs:
                mycursor.execute(select_query, (self.user_id, program_name))
                result = mycursor.fetchone()

                if result:
                    ID_usuario_programa = result[0]
                    insert_query = """
                                INSERT INTO bloqueo_tiempo (ID_usuario_programa, hora_inicial, hora_final)
                                VALUES (%s, %s, %s)
                            """

                    mycursor.execute(insert_query, (ID_usuario_programa, tiempo_inicial, tiempo_final))

            mydb.commit()
            print("Database updated successfully.")


        def get_installed_programs():
            self.show_frame(self.page4_frame)

            for widget in self.page4_frame.winfo_children():
                widget.destroy()
            mydb = self.db.connect()
            mycursor = mydb.cursor()

            mycursor.execute("SELECT programas.nombre_programa "
                             "FROM programas "
                             "JOIN usuario_programa ON programas.ID_programa = usuario_programa.ID_programa "
                             "WHERE usuario_programa.ID_usuario = %s ",
                             (self.user_id,))
            programs = mycursor.fetchall()

            self.check_vars = {}

            scroll_frame = customtkinter.CTkScrollableFrame(master=self.page4_frame, width=500, height=500)
            scroll_frame.pack(padx=10, pady=10)

            for program in programs:
                program_name = program[0]
                check_var = customtkinter.StringVar(value="off")
                self.check_vars[program_name] = check_var
                checkbox = customtkinter.CTkCheckBox(master=scroll_frame,
                                                     text=program_name,
                                                     variable=check_var,
                                                     onvalue="on",
                                                     offvalue="off"
                                                     )
                checkbox.pack(anchor=W, padx=20, pady=5)

            self.page4_frame.tkraise()
            back_button = customtkinter.CTkButton(self.page4_frame, text="Back",
                                                  command=lambda: self.show_frame(self.page3_frame))
            back_button.pack(pady=10)

            confirm_button2 =customtkinter.CTkButton(self.page4_frame, text="Confirmar selección", command=confirm_selected_programs)
            confirm_button2.pack(pady=10)

        def convert_to_12_hour(time_24h):
            # Check if the input is a timedelta object
            if isinstance(time_24h, timedelta):
                # Extract the total seconds and convert to hours, minutes, seconds
                total_seconds = int(time_24h.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_24h = f"{hours:02}:{minutes:02}:{seconds:02}"

            time_obj = datetime.strptime(time_24h, "%H:%M:%S")
            return time_obj.strftime("%I:%M %p")

        def confirm_time_delete():
            self.selected_programs = []
            for program_name, check_var in self.check_vars.items():
                if check_var.get() == "on":
                    self.selected_programs.append(program_name)

                    query_select_id = """
                    SELECT up.ID_usuario_programa
                    FROM usuario_programa up
                    JOIN programas p ON up.ID_programa = p.ID_programa
                    WHERE up.ID_usuario = %s AND p.nombre_programa = %s
                    """

                    mycursor.execute(query_select_id, (self.user_id, program_name))
                    result = mycursor.fetchone()

                    if result:
                        id_usuario_programa = result[0]
                        query_delete ="""
                        DELETE FROM bloqueo_tiempo
                        WHERE ID_usuario_programa = %s
                        """

                        mycursor.execute(query_delete, (id_usuario_programa,))
                        mydb.commit()


            print("Selected Programs:", self.selected_programs)
            self.show_frame(self.page3_frame)


        def get_time_section():
            self.show_frame(self.page5_frame)

            for widget in self.page5_frame.winfo_children():
                widget.destroy()

            mydb = self.db.connect()
            mycursor = mydb.cursor()

            delete_title = customtkinter.CTkLabel(self.page5_frame, text="Time Blocking Information", font=('Montserrat Black',48))
            delete_title.pack(padx=15, pady=15)

            scroll_frame = customtkinter.CTkScrollableFrame(master=self.page5_frame, width=500, height=600)
            scroll_frame.pack(padx=10, pady =10)

            query ="""
            SELECT p.nombre_programa, bt.hora_inicial, bt.hora_final
            FROM bloqueo_tiempo bt
            JOIN usuario_programa up ON bt.ID_usuario_programa = up.ID_usuario_programa
            JOIN programas p ON up.ID_programa = p.ID_programa
            WHERE up.ID_usuario = %s
            ORDER BY bt.hora_inicial
            """

            mycursor.execute(query, (self.user_id,))
            blocked_programas = mycursor.fetchall()

            if not blocked_programas:
                no_data_label = customtkinter.CTkLabel(scroll_frame, text="No blocked programs found.")
                no_data_label.pack(padx=10, pady=10)

            else:
                self.check_vars = {}

                for program in blocked_programas:

                    program_name, start_time, end_time = program

                    program_name = program[0]

                    check_var = customtkinter.StringVar(value="off")
                    self.check_vars[program_name] = check_var
                    checkbox = customtkinter.CTkCheckBox(master=scroll_frame,
                                                         text=program_name,
                                                         variable=check_var,
                                                         onvalue="on",
                                                         offvalue="off"
                                                         )
                    checkbox.pack(anchor=W, fill=Y, padx=20, pady=5, )

                    start_time_12h = convert_to_12_hour(start_time)
                    end_time_12h = convert_to_12_hour(end_time)

                    program_frame = customtkinter.CTkFrame(scroll_frame)
                    program_frame.pack(fill="x", padx=5, pady=5)

                    #program_label = customtkinter.CTkLabel(program_frame, text=f"Program: {program_name}")
                    #program_label.pack(anchor="w", padx=5, pady=2)

                    time_label = customtkinter.CTkLabel(program_frame,
                                                        text=f"Blocked from {start_time_12h} to {end_time_12h}")
                    time_label.pack(anchor="w", padx=5, pady=2)

                back_button = customtkinter.CTkButton(self.page5_frame, text="Back",
                                                      command=lambda: self.show_frame(self.page3_frame))
                back_button.pack(pady=10)

                confirm_delete_button = customtkinter.CTkButton(self.page5_frame, text="Confirmar", command=confirm_time_delete)
                confirm_delete_button.pack(padx=10, pady=10)


        program_selection_button = customtkinter.CTkButton(self.page3_frame, text="Selección de programa", command=get_installed_programs)
        program_selection_button.pack(padx=15, pady=15)

        confirm_button = customtkinter.CTkButton(self.page3_frame, text="Confirmar selección", command=final_confirm)
        confirm_button.pack(padx=15, pady=15)

        delete_time_button = customtkinter.CTkButton(self.page3_frame, text="Borrar margen de tiempo", command=get_time_section)
        delete_time_button.pack(padx=15, pady=15)
        def find_executable_name(install_location):
            for root, dirs, files in os.walk(install_location):
                for file in files:
                    if file.endswith(".exe"):
                        return file
            return None
    def show_frame(self, frame):
        for f in [self.page1_frame, self.page2_frame, self.page3_frame, self.page4_frame, self.page5_frame]:
            f.pack_forget()

        frame.pack(fill="both", expand=True)
    def choose_date(self):
        fecha_dialog = customtkinter.CTkInputDialog(text = "Ingrese la fecha (YYYY-MM-DD): ", title= "Entrada Fecha")
        fecha_str = fecha_dialog.get_input()

        if fecha_str:
            try:
                selected_date = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                self.display_program_usage(self.user_id, selected_date)

            except ValueError:
                msg = CTkMessagebox(message="Fecha invalida",
                              option_1="Reintentar")
                if msg.get()== "Reintentar":
                    self.choose_date()
    def display_program_usage(self, user_id, selected_date=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if selected_date is None:
            selected_date = datetime.now().date()

        data = self.db.fetch_program_usage(user_id,selected_date)
        total_time_used = 0
        for row in data:
            program_name, time_used, date = row
            time_used_minutes = time_used // 60
            new_program_name = program_name.replace(".exe","")
            if time_used_minutes > 0:
                self.tree.insert("", "end", values=(new_program_name.capitalize(), time_used_minutes, date))
                total_time_used += time_used_minutes
            else:
                self.tree.insert("", "end", values=(new_program_name.capitalize(), "<0", date))

        self.tree.insert("", "end", values=("Total Time", total_time_used,""))
    def refresh_data(self):
        self.display_program_usage(self.user_id)
        self.root.after(self.refresh_interval, self.refresh_data)
    def page1(self):
        self.show_frame(self.page1_frame)
        self.display_program_usage(self.user_id)
    def page2(self):
        self.show_frame(self.page2_frame)
    def page3(self):
        self.show_frame(self.page3_frame)
    def page4(self):
        self.show_frame(self.page4_frame)
    def page5(self):
        self.show_frame(self.page5_frame)

    def refresh_info(self):
        self.refresh_data()
        print("Data Refreshed")


if __name__ == "__main__":
    root = customtkinter.CTk()
    app = Registro(root)
    root.mainloop()