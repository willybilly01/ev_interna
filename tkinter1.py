import customtkinter
from tkinter import *
from tkinter.ttk import Treeview, Style, Separator
from PIL import Image, ImageTk
import mysql.connector
from mysql.connector import Error
from datetime import datetime

customtkinter.set_appearance_mode('System')
customtkinter.set_appearance_mode('Red')

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

    def fetch_program_usage (self, user_id):
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
            mycursor.execute(query,(user_id, datetime.now().date()))
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

        self.setup_ui()
        self.user_id = 1
        self.display_program_usage(self.user_id)

        self.refresh_interval = 60000
        self.refresh_data()

    def setup_ui(self):
        image_width = 35
        image_height = 35

        style = Style()
        pie_image = Image.open("imaged/pie_chart.png").resize((image_width, image_height))
        pie_photo = customtkinter.CTkImage(pie_image)

        calendar_image = Image.open("imaged/calendar.png").resize((image_width, image_height))
        calendar_photo = customtkinter.CTkImage(calendar_image)

        check_image = Image.open("imaged/checklist.png").resize((image_width, image_height))
        check_photo = customtkinter.CTkImage(check_image)

        page1btn = customtkinter.CTkButton(root, image=pie_photo, command=self.page1, text="",width=50, height=50)
        page2btn =customtkinter.CTkButton(root, image=calendar_photo, command=self.page2, text="",width=50, height=50)
        page3btn = customtkinter.CTkButton(root, image=check_photo, command=self.page3, text="",width=50, height=50)

        #separator = Separator(root, orient='vertical')
        #separator.place(x=70, y=0, relheight=1)

        page1btn.pack(ipadx=7, ipady=10, padx=(20, 0))
        page2btn.pack(ipadx=7, ipady=10, padx=20)
        page3btn.pack(ipadx=7, ipady=10, padx=20)

        self.page1text = customtkinter.CTkLabel(master=root, text="This is page 1", font=('InterVariable', 88))
        self.page2text = customtkinter.CTkLabel(master=root, text="This is page 2", font=('InterVariable', 88))
        self.page3text = customtkinter.CTkLabel(master=root, text="This is page 3", font=('InterVariable', 88))

        page1btn.place(x=10, y=10)
        page2btn.place(x=10, y=80)
        page3btn.place(x=10, y=150)

        self.page1text.pack(pady=12, padx=10)

        self.tree = Treeview(self.root, columns=("Program Name", "Time Used", "Date"), show='headings')
        self.tree.heading("Program Name", text="Program Name")
        self.tree.heading("Time Used", text="Time Used (Minutes)")
        self.tree.heading("Date", text="Date")
        self.tree.pack(pady=20, padx=20)

    def display_program_usage(self, user_id):
        for item in self.tree.get_children():
            self.tree.delete(item)
        data = self.db.fetch_program_usage(user_id)
        total_time_used = 0
        for row in data:
            program_name, time_used, date = row
            time_used_minutes = time_used // 60
            new_program_name = program_name.replace(".exe","")
            if time_used_minutes > 0:
                self.tree.insert("", "end", values=(new_program_name.capitalize(), time_used_minutes, date))
                total_time_used += time_used_minutes

        self.tree.insert("", "end", values=("Total Time", total_time_used,""))


    def refresh_data(self):
        self.display_program_usage(self.user_id)
        self.root.after(self.refresh_interval, self.refresh_data)

    def page1(self):
        self.page2text.pack_forget()
        self.page3text.pack_forget()
        self.page1text.pack(pady=12, padx=10)
        self.tree.pack(pady=20, padx=20)

    def page2(self):
        self.page1text.pack_forget()
        self.page3text.pack_forget()
        self.page2text.pack(pady=12, padx=10)
        self.tree.pack_forget()

    def page3(self):
        self.page1text.pack_forget()
        self.page2text.pack_forget()
        self.page3text.pack(pady=12, padx=10)
        self.tree.pack_forget()



if __name__ == "__main__":
    root = customtkinter.CTk()
    app = App(root)
    root.mainloop()




