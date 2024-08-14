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
import time
import mysql.connector
from mysql.connector import Error
from datetime import datetime

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
                    time.sleep(1)

                    query = """ 
                            SELECT programa_bloqueado
                            FROM usuario_programa 
                            JOIN programas ON usuario_programa.ID_programa = programas.ID_programa
                            WHERE ID_usuario = %s AND nombre_programa = %s
                    """
                    mycursor.execute(query, (user_id, nombre_programa))
                    result = mycursor.fetchone()

                    if result[0] == 1:
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

                    checkpoint = time.time()
                    diferencia = (checkpoint - tiempo_partida)

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
                        tiempo_nuevo = tiempo_utilizado_existente[0] + suma
                        mycursor.execute(
                            "UPDATE tiempo_utilizado "
                            "SET tiempo_utilizado = %s "
                            "WHERE ID_usuario_programa = %s AND solo_fecha = %s",
                            (tiempo_nuevo, result_ID_usuario_programa[0], solo_fecha)
                        )
                        self.db.commit()
                        print(f"Updated tiempo_utilizado: {tiempo_nuevo}")
                        print("stage 6")
                        suma = 0

                    else:
                        solo_hora = datetime.now().time()
                        mycursor.execute(
                            "INSERT INTO tiempo_utilizado (ID_usuario_programa, tiempo_utilizado, solo_hora, solo_fecha)"
                            "VALUES (%s,%s,%s,%s) ",
                            (result_ID_usuario_programa[0], suma, solo_hora, solo_fecha)
                        )
                        self.db.commit()

                        print("Registro de tiempo utilizado actualizado")
                        suma = 0




                except Exception as e:
                    print(f"Ocurrió un error: {e}")

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

class App:
    def __init__(self,root):
        self.root = root
        self.root.geometry('1200x700')
        self.db = Database(
            "localhost",
            "root",
            "8879576",
            "ev_interna"
        )

        self.user_id = 1

        self.monitor = Monitoreo_programa(user_id=self.user_id, blocked_programs=[])
        self.monitor_thread = threading.Thread(target=self.monitor.monitor, daemon=True)
        self.monitor_thread.start()

        self.left_frame_1 = customtkinter.CTkFrame(self.root, fg_color="transparent")
        self.left_frame_1.pack(side=LEFT, fill=Y, padx=10, pady=20)

        self.page1_frame = customtkinter.CTkFrame(self.root,fg_color="transparent")
        self.page2_frame = customtkinter.CTkFrame(self.root,fg_color="transparent")
        self.page3_frame = customtkinter.CTkFrame(self.root,fg_color="transparent")

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
        self.page1text = customtkinter.CTkLabel(master=self.page1_frame, text="Main Menu",
                                                font=('Montserrat Black', 60))
        self.page1text.pack(pady=12, padx=10)
        self.right_frame_1 = customtkinter.CTkFrame(self.page1_frame, fg_color="transparent")
        self.right_frame_1.pack(side=RIGHT, fill=Y, padx=10, pady=20)

        self.tree = Treeview(self.page1_frame, columns=("Program Name", "Time Used", "Date"), show='headings')
        self.tree.heading("Program Name", text="Program Name")
        self.tree.heading("Time Used", text="Time Used (Minutes)")
        self.tree.heading("Date", text="Date")
        self.tree.pack(side=LEFT, pady=50, padx=50, fill=BOTH, expand=True)

        refresh_button = customtkinter.CTkButton(master=self.right_frame_1, text="Refresh Button",command=self.refresh_info)
        refresh_button.pack(ipadx=10, ipady=10, padx=20, pady=10)

        date_button = customtkinter.CTkButton(master=self.right_frame_1, text="Choose Date", command=self.choose_date)
        date_button.pack(ipadx=10, ipady=10, padx=20)

    def configure_page2(self):
        self.page2text = customtkinter.CTkLabel(master=self.page2_frame, text="Bloqueo de programa",
                                                font=('Montserrat Black', 60))
        self.page2text.pack(pady=12, padx=10)

        self.right_frame_2 = customtkinter.CTkFrame(self.page2_frame, fg_color="transparent")
        self.right_frame_2.pack(side=RIGHT, fill=Y, padx=10, pady=20)
        self.right_frame_2.configure(width=200, height=300)

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

            # Create a checkbox for each program
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
        #confirm_button.pack(padx =20, pady=20, ipadx = 20, ipady = 20)
        confirm_button.place(x=500, y=200)

        delete_button = customtkinter.CTkButton(master=self.page2_frame, text="Delete Program Blocker", command=self.delete_selection, height=50, width=150)
        delete_button.place(x=500, y=275)
    def confirm_selection(self):
        selected_programs = []
        for program_name, check_var in self.check_vars.items():
            if check_var.get() == "on":
                selected_programs.append(program_name)

        # Now `selected_programs` contains the names of the programs that were checked.
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

    def delete_selection(self):
        selected_programs = []
        for program_name, check_var in self.check_vars.items():
            if check_var.get() == "on":
                selected_programs.append(program_name)

        # Now `selected_programs` contains the names of the programs that were checked.
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
    def configure_page3(self):
        self.page3text = customtkinter.CTkLabel(master=self.page3_frame, text="This is page 3", font=('InterVariable', 88))
        self.page3text.pack(pady=12, padx=10)
    def show_frame(self, frame):
        for f in [self.page1_frame, self.page2_frame, self.page3_frame]:
            f.pack_forget()

        frame.pack(fill="both", expand=True)

    def choose_date(self):
        date_dialog = customtkinter.CTkInputDialog(text = "Enter the date (YYYY-MM-DD): ", title= "Date Input")
        date_str = date_dialog.get_input()

        if date_str:
            try:
                selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                self.display_program_usage(self.user_id, selected_date)

            except ValueError:
                msg = CTkMessagebox(message="Invalid date",
                              option_1="Retry")
                if msg.get()== "Retry":
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
    def refresh_info(self):
        self.refresh_data()
        print("Data Refreshed")




if __name__ == "__main__":
    root = customtkinter.CTk()
    app = App(root)
    root.mainloop()




