from tkinter import ttk, Label, Button, Entry, StringVar, filedialog
from tkinter.messagebox import showinfo
import sys
import ctypes


class MyGUIClass:
    def __init__(self, master):
        self.master = master
        master.title("CDP Network Map")
        master.resizable(False, True)

        self.Site_details = ttk.Frame(master)
        self.Site_details.pack(padx=20, pady=10, fill='x', expand=True)

        self.label = Label(self.Site_details, text="Please Fill in the Required Fields!", font=("Arial Bold", 15))
        self.label.pack()

        self.SiteName_var = StringVar()
        self.Site_Name_label = Label(self.Site_details, text="\nSite_Name: (Required)", anchor="w")
        self.Site_Name_label.pack(fill='x', expand=True)
        self.Site_Name_entry = Entry(self.Site_details, textvariable=self.SiteName_var)
        self.Site_Name_entry.pack(fill='x', expand=True)
        self.Site_Name_entry.focus()

        self.Username_var = StringVar()
        self.Username_label = Label(self.Site_details, text="\nUsername: (Required)", anchor="w")
        self.Username_label.pack(fill='x', expand=True)
        self.Username_entry = Entry(self.Site_details, textvariable=self.Username_var)
        self.Username_entry.pack(fill='x', expand=True)

        self.password_var = StringVar()
        self.password_label = Label(self.Site_details, text="\nPassword: (Required)", anchor="w")
        self.password_label.pack(fill='x', expand=True)
        self.password_entry = Entry(self.Site_details, textvariable=self.password_var, show="*")
        self.password_entry.pack(fill='x', expand=True)

        self.IP_Address1_var = StringVar()
        self.IP_Address1_label = Label(self.Site_details, text="\nCore Switch 1: (Required)", anchor="w")
        self.IP_Address1_label.pack(fill='x', expand=True)
        self.IP_Address1_entry = Entry(self.Site_details, textvariable=self.IP_Address1_var)
        self.IP_Address1_entry.pack(fill='x', expand=True)

        self.IP_Address2_var = StringVar()
        self.IP_Address2_label = Label(self.Site_details, text="\nCore Switch 1: (Required)", anchor="w")
        self.IP_Address2_label.pack(fill='x', expand=True)
        self.IP_Address2_entry = Entry(self.Site_details, textvariable=self.IP_Address2_var)
        self.IP_Address2_entry.pack(fill='x', expand=True)

        self.FolderPath_var = StringVar()
        self.FolderPath_var = StringVar()
        self.FolderPath_label = Label(self.Site_details, text="\nResults file location: (Optional)", anchor="w")
        self.FolderPath_label.pack(fill='x', expand=True)
        self.browse_button = Button(self.Site_details, text="Browse Folder", command=self.get_folder_path, width=25)
        self.browse_button.pack(anchor="w")
        self.FolderPath_entry = Entry(self.Site_details, textvariable=self.FolderPath_var)
        self.FolderPath_entry.configure(state='disabled')
        self.FolderPath_entry.pack(fill='x', expand=True)

        self.JumpServer_var = StringVar()
        self.JumpServer_var.set("10.251.131.6")
        self.JumpServer_label = Label(self.Site_details, text="\nJumper Server:", anchor="w")
        self.JumpServer_label.pack(fill='x', expand=True)
        self.JumpServer = ttk.Combobox(self.Site_details,
                                       values=["MMFTH1V-MGMTS02", "AR31NOC"],
                                       state="readonly", textvariable=self.JumpServer_var,
                                       )
        self.JumpServer.current(0)
        self.JumpServer.pack(fill='x', expand=True)

        self.Debugging_var = StringVar()
        self.Debugging_var.set("Off")
        self.Debugging_label = ttk.Label(self.Site_details, text="\nDebugging:", anchor="w")
        self.Debugging_label.pack(fill='x', expand=True)
        self.Debugging = ttk.Combobox(self.Site_details, values=["Off", "On"], state="readonly",
                                      textvariable=self.Debugging_var)
        self.Debugging.current(0)
        self.Debugging.pack(fill='x', expand=True, pady=(0, 20))

        self.submit_button = Button(self.Site_details, text="Submit", command=self.check_empty, width=25)
        self.submit_button.pack(side="left", fill="x",)

        self.cancel_button = Button(self.Site_details, text="Cancel", command=self.quite_script, width=25)
        self.cancel_button.pack(side="right", fill="x")

    @staticmethod
    def greet():
        showinfo("Information", "Greetings!")

    @staticmethod
    def quite_script():
        sys.exit()

    def check_empty(self):
        if self.Username_var.get() == "":
            ctypes.windll.user32.MessageBoxW(0, f"A required field is empty\n"
                                                f"Please check and try again!", "Error",
                                             0x40000)
        elif self.password_var.get() == "":
            ctypes.windll.user32.MessageBoxW(0, f"A required field is empty\n"
                                                f"Please check and try again!", "Error",
                                             0x40000)
        elif self.IP_Address1_var.get() == "":
            ctypes.windll.user32.MessageBoxW(0, f"A required field is empty\n"
                                                f"Please check and try again!", "Error",
                                             0x40000)
        elif self.SiteName_var.get() == "":
            ctypes.windll.user32.MessageBoxW(0, f"A required field is empty\n"
                                                f"Please check and try again!", "Error",
                                             0x40000)
        else:
            pass

    def get_folder_path(self):
        folder_selected = filedialog.askdirectory()
        self.FolderPath_var.set(folder_selected)


# root = Tk()
# my_gui = MyGUIClass(root)
# root.mainloop()
