import customtkinter
from tkinter import *
from tkinter.ttk import Treeview, Style
from PIL import Image, ImageTk
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from CTkMessagebox import CTkMessagebox

customtkinter.set_appearance_mode('System')
customtkinter.set_appearance_mode('Red')

def configure_treeview_style():
    style = Style()
    style.configure('Treeview',
                    font=('Arial', 20))
    style.configure('Treeview.Heading',
                    font=('Arial', 20, 'bold'))

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

        #separator = Separator(root, orient='vertical')
        #separator.place(x=70, y=0, relheight=1)

        page1btn.pack(pady=10)
        page2btn.pack(pady=10)
        page3btn.pack(pady=10)

        self.page1text = customtkinter.CTkLabel(master=self.page1_frame, text="This is page 1", font=('InterVariable', 88))
        self.page2text = customtkinter.CTkLabel(master=self.page2_frame, text="This is page 2", font=('InterVariable', 88))
        self.page3text = customtkinter.CTkLabel(master=self.page3_frame, text="This is page 3", font=('InterVariable', 88))

        self.page1text.pack(pady=12, padx=10)
        self.page2text.pack(pady=12, padx=10)
        self.page3text.pack(pady=12, padx=10)
        #page1btn.place(x=10, y=10)
        #page2btn.place(x=10, y=80)
        #page3btn.place(x=10, y=150)

        self.page1text.pack(pady=12, padx=10)

        self.right_frame_1 = customtkinter.CTkFrame(self.page1_frame, fg_color= "transparent")
        self.right_frame_1.pack(side=RIGHT, fill=Y, padx = 10, pady=20)

        self.tree = Treeview(self.page1_frame, columns=("Program Name", "Time Used", "Date"), show='headings')
        self.tree.heading("Program Name", text="Program Name")
        self.tree.heading("Time Used", text="Time Used (Minutes)")
        self.tree.heading("Date", text="Date")
        self.tree.pack(side = LEFT, pady=50, padx=50, fill=BOTH, expand=True)

        refresh_button = customtkinter.CTkButton(master = self.right_frame_1, text="Refresh Button", command = self.refresh_info)
        refresh_button.pack(ipadx=10, ipady=10, padx=20,pady =10)

        date_button = customtkinter.CTkButton(master = self.right_frame_1, text="Choose Date", command = self.choose_date)
        date_button.pack(ipadx=10, ipady=10, padx=20)

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




