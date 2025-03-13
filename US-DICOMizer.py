#import initial libraries
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Menu, font
from tkinter.messagebox import askyesno
from tkinter.scrolledtext import ScrolledText

import os
import webbrowser
import shutil
import subprocess
from threading import Thread
#import threading
import sys
from ctypes import windll
import configparser
import random
import re
import logging
from datetime import datetime
import time
from time import strftime

'''
Ορίζω ως Patient's ID το filename
δε σβήνω τα X0...Y1 αλλα τα ενημερώνω
Προσθήκη του about window
αλλαγή της συνάρτησης για το άνοιγμα weblink
'''

version = "4.14"
temp_output_dir = None
zcount = 0
#app_dir = os.path.join(os.environ['USERPROFILE'],".anonymizer")
#output_dir = os.path.join(os.environ['USERPROFILE'],".anonymizer\output")
#output_dir = os.path.normpath(output_dir)
#print(temp_output_dir)
#initialize confing file

#δημιουργία του app directory στο profil του χρήστη για windows OS
app_directory = os.path.join(os.environ['USERPROFILE'],".anonymizer")
os.makedirs(app_directory, exist_ok=True)

#καθορισμός του path για το settints.ini αρχείου
settings_file_path = os.path.join(app_directory, "settings.ini")

def create_settings_file(settings_file_path):
    # Έλεγχος αν το αρχείο settings.ini υπάρχει
    if not os.path.exists(settings_file_path):
        #για να παίρνει τον σωστό φάκελο του κάθε χρήστη
        files_output_path = os.path.join(app_directory, "output")
        with open(settings_file_path, 'w') as file:
            file.write(f"""
[settings]
user_can_change_compression_level = yes
compression_level = 85
output_path = {files_output_path}
show_imageJ_button = no
convert_all_to_jpeg = yes
patient_s_ID = keep

[crop_area]
x0_value = 10
y0_value = 0
x1_value = 990
y1_value = 1000

[tags_to_del]
Instance Creation Date = 0008,0012
Instance Creation Time = 0008,0013
Study Date = 0008,0020
Series Date = 0008,0021
Acquisition Date = 0008,0022
Content Date = 0008,0023
Acquisition DateTime = 0008,002A
Study Time = 0008,0030
Series Time = 0008,0031
Acquisition Time = 0008,0032
Content Time = 0008,0033
Institurion Name = 0008,0080
Referring Physician's Name = 0008,0090
Consulting Physician Name = 0008,0090C
Station Name = 0008,1010
Study Description = 0008,1030
Institutional Deparment Name = 0008,1040
Physician(s) of Record = 0008,1048
Performing Physician's Name = 0008,1070
Referenced performed procedure step = 0008,1111
Referenced sop class uid = 0008,1150
Referenced sop instance uid = 0008,1155
Patient's Name = 0010,0010
Patient's Birth Date = 0010,0030
Patient's Birth Time = 0010,0032
Patient Birth Date In Alternative Calendar = 0010,0033
Patient's sex = 0010,0040
Patient comments = 0010,4000
Device Serial Number = 0018,1000
;Software Versions = 0018,1020
Protocol Name = 0018,1030
Study ID = 0020,0010
Lossy Image Compression Ratio = 0028,2112
Study Comments = 0032,4000
Performed Procedure Step Start Date = 0040,0244
Performed Procedure Step Start Time = 0040,0245
Performed Procedure Step ID = 0040,0253
Performed Procedure Step Description = 0040,0254
Comments on the Performed Procedure Step = 0040,0280
Unknown Date = 200D,2637
Unknown Time = 200D,2638

[tag_values]
tag_values = ("none","CFVr-L", "CFV-L", "CFVr-R", "CFV-R","GSVr-L", "GSV-L", "GSVr-R", "GSV-R","FVr-L", "FV-L", "FVr-R", "FV-R","FV-Dr-L", "FV-D-L", "FV-Dr-R", "FV-D-R","PVr-L", "PV-L", "PVr-R", "PV-R","OPT-L", "OPT-R")

[tags_link]
tags_link = bmi.med.duth.gr

[devices]
device0 = [20093],[330,58,890,817],[195,58,1020,733]
device1 = [292a20205232012773],[252,51,686,720],[252,51,686,720]
device2 = [441366981],[52,90,970,726],[38,55,760,566]
device3 = [LS7X00334],[290,120,840,895],[290,120,840,895]
device4 = [370002158],[133,76,720,593],[133,76,720,593]
device5 = [EPIQ 7G_2.0.3.398],[357,69,644,560],[278,50,519,560]
device6 = [EPIQ 7G_2.0.1.256],[278,50,519,560],[278,50,519,560]    
device7 = [379046942],[207,52,519,560],[207,52,592,569]
device8 = [LOGIQS7XDclear2.0:R4.2.56],[432,46,1009,827],[432,46,1009,827]
""")
        
        messagebox.showinfo("Settings file", "File settings.ini created with default values.")

#την καλώ για αρχικοποίηση του settings.ini
create_settings_file(settings_file_path)



#output_path = os.path.join(os.environ['USERPROFILE'],".anonymizer\output")
output_path = os.path.join(app_directory,"output")
os.makedirs(output_path, exist_ok=True)
output_path = os.path.normpath(output_path)

def config_logging():
    #ρύθμιση του logger
    #logs_directory = "dicom_app_logs" #φτιάχνει φάκελο στο ιδιο path με το .py αρχείο
    logs_directory = os.path.join(app_directory,"dicom_app_logs")
    os.makedirs(logs_directory, exist_ok=True)

    logger = logging.getLogger('dicom_app')
    if not logger.handlers: #για να μήν φορτώνει πολλαπλα handlers κάθε φορά που εκτελείτε
        log_file_path = os.path.join(logs_directory, "{}_dicom_app.log".format(strftime('%Y%m%d')))
        logging.basicConfig(filename=log_file_path, encoding='utf-8', level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S')
    return logger

config_logging()
logger = logging.getLogger('dicom_app')
logger.info('app started')

def console_message(message, level="info"):
    timestamp = datetime.now().strftime("%m/%d/%Y %I:%M:%S")
    formatted_message = f"{timestamp} - {level.upper()} - {message}"

    if level == "error":
        logger.error(message)  #για καταγραφή σφάλματος
    elif level == "debug":
        logger.debug(message)  #καταγραφή debug
    else:
        logger.info(message)  #καταγραφή πληροφορίας
    
    console.insert("end", formatted_message + "\n")  #για την εμφάνιση στο ScrolledText
    console.see("end")#για να είναι ορατό το τελευταίο μήνυμα


config = configparser.ConfigParser()

try:
    config.read(settings_file_path)
except Exception as e:
    #console_message("error while reading settings.ini file", level="error")
    messagebox.showerror("Read settings.ini", f"{e}.")
        

'''
#------------- INITIALIZE -------------
#ελέγχω ότι είναι εγκατεστημένες οι απαραίτητες βιβλιοθήκες
def check_and_install(package_name):
    try:
        __import__(package_name)
        #messagebox.showinfo("Package Check", f"{package_name} is already installed.")
    except ImportError:
        messagebox.showwarning("Package Check", f"{package_name} is not installed.")
        response = messagebox.askyesno("Package is not installed.", f"Install {package_name}?")
        if response:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                messagebox.showinfo("Package Installation", f"{package_name} has been successfully installed.")
            except Exception as e:
                messagebox.showerror("Package Installation Failed", f"Failed to install {package_name}. Error: {str(e)}")
        else:
            messagebox.showinfo("Package Installation", f"Skipping installation of {package_name}.")

def check_required_packages():
    #root.withdraw()
    required_packages = {
        "pydicom": "pydicom",
        "SimpleITK": "SimpleITK",
        "PIL": "PIL",
        
        "numpy": "numpy",
        "matplotlib": "matplotlib",
        "--pre scikit-image": "--pre scikit-image"
    }
    
    for module, package in required_packages.items():
        check_and_install(package)

check_required_packages()
'''

try:
    #import libraries
    import zipfile
    import pydicom
    #from pydicom.pixels.processing import convert_color_space
    from pydicom.pixels.utils import get_nr_frames, pixel_array
    from pydicom.encaps import encapsulate, get_frame
    from pydicom.uid import UID
    from pydicom.dataelem import DataElement
    import uuid
    #import SimpleITK as sitk
    from PIL import Image, ImageTk, ImageDraw
    import numpy as np
    import matplotlib.pyplot as plt
    #from skimage import io
    import io
    
except Exception as e:
    messagebox.showerror("Error", f"An error occurred: {str(e)}")
    logger.error(f"while import some libraries: {str(e)}")
    sys.exit(1)#κλείνει η εφαρμογή μετά το μήνυμα
    
'''
*** first need to install ***
pip install pydicom
pip install Pillow
pip install numpy
pip install matplotlib

maybe
pip install --upgrade scipy
pip install numpy==1.26.0
pip install numpy<2

'''

def settings():
    global output_path, output_path_text, compression_entry, x0_entry, y0_entry, x1_entry, y1_entry
    #logger = logging.getLogger('dicom_app')  # Ανάκτηση του ίδιου logger
    
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.iconbitmap(r'icon.ico')
    settings_window.geometry("450x450")#Πλάτος x Ύψος

    try:
        compression_level = config['settings'].get('compression_level', '100')#ανάγνωση τιμής απο το ini αρχείο , εκχόρηση default value
        #output_path = config['settings'].get('output_path', 'C:/')
        
        settings_01 = ttk.Frame(settings_window)
        settings_01.pack()

        compression_level_label = ttk.Label(settings_01, text="Compression level (0-95): ")
        compression_level_label.grid(column=0, row=0, sticky="w")

        user_can_change_compression_level = config['settings'].get('user_can_change_compression_level', 'no')
        if user_can_change_compression_level == "yes":
            compression_entry = ttk.Entry(settings_01, width=2)
            compression_entry.grid(column=1, row=0, sticky="w")
            compression_entry.insert(0,compression_level)
        else:
            compression_entry = ttk.Entry(settings_01, width=2)
            compression_entry.grid(column=1, row=0, sticky="w")
            compression_entry.insert(0,compression_level)
            compression_entry.config(state="disabled")
            
        output_path_settings_label = ttk.Label(settings_01, text=f"Output path")
        output_path_settings_label.grid(column=0, row=1, sticky="w")

        output_path_settings_btn = ttk.Button(settings_01, text="Change", command=select_output_folder)
        output_path_settings_btn.grid(column=1, row=1, sticky="w")

        output_path_text = ScrolledText(settings_01, height=3, width=40, wrap=tk.WORD)
        output_path_text.grid(column=0, row=2, columnspan=2, sticky="nsew")
        output_path_text.insert(tk.END, output_path)
        output_path_text.configure(state='disabled')

        '''
        settings_02 = ttk.LabelFrame(settings_window, text="Custom crop area")
        settings_02.pack()

        #ανάγνωση των τιμών της ενότητας [crop_area]  απο το ini αρχείo
        x0_value = config['crop_area'].get('x0_value', '0')
        y0_value = config['crop_area'].get('y0_value', '0')
        x1_value = config['crop_area'].get('x1_value', '1000')
        y1_value = config['crop_area'].get('y1_value', '1000')

        x0_label = ttk.Label(settings_02, text="X0: ")
        x0_label.grid(column=0, row=0)
        x0_entry = ttk.Entry(settings_02, width=4)
        x0_entry.grid(column=1, row=0, padx=30)
        x0_entry.insert(0,x0_value)

        y0_label = ttk.Label(settings_02, text="Y0: ")
        y0_label.grid(column=2, row=0)
        y0_entry = ttk.Entry(settings_02, width=4)
        y0_entry.grid(column=3, row=0)
        y0_entry.insert(0,y0_value)

        x1_label = ttk.Label(settings_02, text="X1: ")
        x1_label.grid(column=0, row=1)
        x1_entry = ttk.Entry(settings_02, width=4)
        x1_entry.grid(column=1, row=1)
        x1_entry.insert(0,x1_value)

        y1_label = ttk.Label(settings_02, text="Y1: ")
        y1_label.grid(column=2, row=1)
        y1_entry = ttk.Entry(settings_02, width=4)
        y1_entry.grid(column=3, row=1)
        y1_entry.insert(0,y1_value)
        '''
        #νεο frame
        settings_03 = ttk.LabelFrame(settings_window, text="Devices and crop areas")
        settings_03.pack(fill="x", pady=10)

        #κατασκευη του listbox
        devices_listbox = tk.Listbox(settings_03, height=6, width=70)
        devices_listbox.grid(row=0, column=0)

        #δημιουργία του Scrollbar
        devices_listbox_v_scrollbar = tk.Scrollbar(settings_03, orient="vertical", command=devices_listbox.yview)
        devices_listbox_v_scrollbar.grid(row=0, column=1, sticky="ns")

        #σύνδεση του scrollbar με το listbox
        devices_listbox.config(yscrollcommand=devices_listbox_v_scrollbar.set)

        #εμφάνιση των συσκευών από το ini αρχείο
        for key in config['devices']:
       
            device_info = config['devices'][key].split('],')
        
            #aνάγνωση του sn και των περιοχών crop
            device_sn = device_info[0].strip('[]')
            crop_areas = [list(map(int, area.strip('[]').split(','))) for area in device_info[1:]]#με το [1:] αφαιρώ το SN και επιστρέφω μόνοα τις περιοχες crop
            #με το map(int, ...) μετατρέπω κάθε στοιχείο της περιοχής crop από string σε ακέραιο αριθμό integer

            #προσθέτω στο Listbox κάθε περιοχή crop
            for i, area in enumerate(crop_areas):
                x0, y0, x1, y1 = area
                if i == 0:
                    devices_listbox.insert(tk.END, f"SN: {device_sn}, Singleframe area: X0: {x0}, Y0: {y0}, X1: {x1}, Y1: {y1}")
                elif i == 1:
                    devices_listbox.insert(tk.END, f"SN: {device_sn}, Multiframe  area: X0: {x0}, Y0: {y0}, X1: {x1}, Y1: {y1}")

        settings_04 = ttk.Frame(settings_window)
        settings_04.pack(fill='x')

        separator = ttk.Separator(settings_04, orient='horizontal')
        separator.pack(fill='x')

        open_settings_folder_command = 'explorer.exe ' + app_directory
        
        settings_folder_btn = ttk.Button(settings_04, text="Settings folder", command=lambda: os.system(open_settings_folder_command))
        settings_folder_btn.pack(padx=5, side="left")
        
        save_btn = ttk.Button(settings_04, text="Save", command=lambda: save_settings(settings_window))
        save_btn.pack(padx=5, side="left")

        console_message("settings loaded", level="info")
    except Exception as e:
        console_message(f"load settings, an error occurred: {str(e)}",level="error")
        return
        
def del_unzipped_folders():
    folder_pattern = r"^temp_unzipped_files_0\d+$"
    for folder_name in os.listdir(output_path):
        if re.match(folder_pattern, folder_name):
            folder_to_del = os.path.join(output_path, folder_name)
            # Ελέγχει αν είναι φάκελος
            if os.path.isdir(folder_to_del):
            # Διαγραφή του φακέλου και των περιεχομένων του
                shutil.rmtree(folder_to_del)
    
def select_output_folder():
    global output_path, output_path_text, save_path_label
    
    #επιλογή φακέλου
    new_output_path = filedialog.askdirectory()
    if not new_output_path:
        return

    output_path = os.path.normpath(new_output_path) #ενημέρωση της global μεταβλητής
    
    #print(output_path)

    #ενημέρωση του output_path_text στο scrolled text
    output_path_text.configure(state='normal') #κάνω το scrolledtext editable
    output_path_text.delete(1.0, tk.END) #διαγράφω περιεχόμενο
    output_path_text.insert(tk.END, output_path) #προσθέτω το νέο path
    output_path_text.configure(state='disabled') #το κάνω μη επεξεργάσιμο

    #save_path_label.config(text=output_path)

    save_path_text.configure(state='normal') #κάνω το scrolledtext editable
    save_path_text.delete(1.0, tk.END) #διαγράφω περιεχόμενο
    save_path_text.insert(tk.END, output_path) #προσθέτω το νέο path
    save_path_text.configure(state='disabled')

       
def save_settings(settings_window):
    global config, compression_entry, output_path #,x0_entry, y0_entry, x1_entry, y1_entry
    
    compression_level = compression_entry.get()
    #output_path = output_path

    '''
    x0_value = x0_entry.get()
    y0_value = y0_entry.get()
    x1_value = x1_entry.get()
    y1_value = y1_entry.get()
    '''
    if not compression_level.isdigit() or not (0 <= int(compression_level) <= 95):
        messagebox.showerror("Error", "Please enter a valid compression level between 0 and 95.")
        return
    
    #ενημέρωση των τιμών στο config object
    config['settings']['compression_level'] = compression_level
    config['settings']['output_path'] = output_path

    '''
    config['crop_area']['x0_value'] = x0_value
    config['crop_area']['y0_value'] = y0_value
    config['crop_area']['x1_value'] = x1_value
    config['crop_area']['y1_value'] = y1_value 
    '''
    
    #αποθήκευση των τιμών στο αρχείο settings.ini
    with open(settings_file_path, 'w') as configfile:
        config.write(configfile)

    settings_window.destroy()

    messagebox.showinfo("Success", "Settings saved successfully!\nRestart the application to apply them")
    console_message("Settings saved",level="info")

    root.quit()
    root.destroy()

#ρύθμιση του στυλ για τα κουμπιά
def configure_style():
    s = ttk.Style()

    font_size=8
    s.configure("Treeview.Heading", font=("Segoe UI", font_size),
                rowheight=int(font_size*1.8))
    
    s.configure("Treeview", font=("Segoe UI", font_size),
                rowheight=int(font_size*1.8))
                #fieldbackground="black", foreground="white")
    
    s.configure('anon.TButton', 
                background='#00CD66',
                foreground='black',
                justify='center',
                font=("Segoe UI", 10),
                padding=6)
    s.map('anon.TButton', 
          background=[('active', '#96CDCD'), ('pressed', '#90EE90'), ('disabled', '#4D4D4D')],
          foreground=[('disabled', '#8E8E8E')],
          relief=[('pressed', 'sunken'), ('!pressed', 'raised')]
          )

    s = ttk.Style()
    s.configure('small.TButton', 
                background='#E0E0E0',
                foreground='black',
                justify='center',
                font=("Segoe UI", 8))
    s.map('small.TButton', 
          background=[('active', '#96CDCD'), ('pressed', '#90EE90')],
          foreground=[('disabled', '#8E8E8E')],
          relief=[('pressed', 'sunken'), ('!pressed', 'raised')]
          )

    s = ttk.Style()
    s.configure('preview.TButton', 
                background='#007FFF',
                foreground='black',
                justify='center',
                font=("Segoe UI", 8))
    s.map('preview.TButton', 
          background=[('active', '#96CDCD'), ('pressed', '#90EE90')],
          foreground=[('disabled', '#aa49f8')],
          relief=[('pressed', 'sunken'), ('!pressed', 'raised')]
          )
    
    s = ttk.Style()
    s.configure('clear.TButton', 
                background='#FF0000',
                foreground='black',
                justify='center',
                font=("Segoe UI", 8))
    s.map('clear.TButton', 
          background=[('active', '#F08080'), ('pressed', '#F08080')],
          foreground=[('disabled', '#F08080')],
          relief=[('pressed', 'sunken'), ('!pressed', 'raised')]
          )
    s = ttk.Style()
    s.configure('apply.TButton', 
                background='#4F94CD',
                foreground='black',
                justify='center',
                font=("Segoe UI", 8))
    s.map('apply.TButton', 
          background=[('active', '#BFEFFF'), ('pressed', '#F08080')],
          #foreground=[('disabled', '#F08080')],
          foreground=[('disabled', '#8E8E8E')],
          relief=[('pressed', 'sunken'), ('!pressed', 'raised')]
          )


# ------ ΑΡΧΗ ------ load_file() -----------------------
#Συνάρτηση για επιλογή μεμονομένου αρχείου
def load_file():
    # Ανάγνωση του αρχείου DICOM με file dialog
    file_path = filedialog.askopenfilename(title="Open single DICOM file")
    #print("Selected file:", file_path)  # for debug

    if not file_path:
        return
    #το .normpath βάζει slash όπως ορίζει το OS για να είναι συμβατό με όλα τα λειτουργικα σύστημα
    file_path = os.path.normpath(file_path)
    # Άνοιγμα του αρχείου
    try:
        ds = pydicom.dcmread(file_path, stop_before_pixels=True)# stop_before_pixels=True παράμετρος που δέ φορτώνει την εικόνα
        # τη βάζω άν θέλω να φέρω μόνο τα tags, σε αυτή τη συνάρτηση δε χρειάζομαι την εικόνα
        
        # Έλεγχος αν το αρχείο είναι τύπου DICOM
        if ds is None:
            console_message("not loaded dicom file from filedialog, file is not DICOM, see the Exception error",level="error")
            raise pydicom.errors.InvalidDicomError
            
        #Προσθήκη του αρχείου στο Treeview
        add_to_selected(file_path)
        #print(ds)
        console_message("loaded dicom file successfully from filedialog", level="info")
        
    
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}\n\nSelect another file")
        console_message(f"An error occurred: {str(e)}",level="error")
        return

def load_folder():
    global temp_output_dir
    # Παράθυρο επιλογής φακέλου
    if temp_output_dir is None:
        folder_path = filedialog.askdirectory()
    else:
        folder_path = temp_output_dir
    
    try:
        print(folder_path)  # for debug
        if not folder_path:
            return  # Αν δεν επιλεχθεί φάκελος, επιστρέφει
        
        dicom_files = []
        
        #αναζήτηση όλων των αρχείων στον φάκελο
        for f in os.listdir(folder_path):
            file_path = os.path.join(folder_path, f)
            
            #έλεγχος αν είναι αρχείο
            if os.path.isfile(file_path):
                try:
                    #προσπάθεια ανάγνωσης του αρχείου ως DICOM
                    ds = pydicom.dcmread(file_path, stop_before_pixels=True)
                    dicom_files.append(os.path.normpath(file_path))  # Κανονικοποίηση του μονοπατιού
                    
                except pydicom.errors.InvalidDicomError:
                    #print(f"{f} is not DICOM, skipped")  #το αρχείο δεν είναι DICOM
                    console_message(f"{f} is not DICOM, skipped",level="debug")
                    continue

        total_files = len(dicom_files)
        #print(f"Total DICOM files found: {total_files}")
        console_message(f"Total DICOM files found: {total_files}",level="info")

        if total_files == 0:
            messagebox.showinfo("No DICOM files", "No DICOM files were found in the selected folder.")
            console_message("No DICOM files were found in the selected folder",level="debug")
            return
        
        #προσθήκη των DICOM αρχείων στο treeview
        for file_path in dicom_files:
            add_to_selected(file_path)

        console_message("loaded dicom files successfully from folder with filedialog",level="info")
        temp_output_dir = None
    
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}\n\nPlease select another folder.")
        console_message(f"An error occurred: {str(e)}",level="error")
# ------ ΤΕΛΟΣ ------ load_file() -----------------------


def add_to_selected(file_path):
    file_name = os.path.basename(file_path) #παίρνω μόνο το όνομα του αρχείου

    #Λήψη όλων των αρχείων που υπάρχουν στο Treeview, με το [1] παιρνω το file_path
    all_files_in_tree = [selected_files_treeview.item(item, "values")[1] for item in selected_files_treeview.get_children()]

    if file_path in all_files_in_tree:
        messagebox.showwarning("Warning", f"The file '{file_name}' is already in the list.")
        return #αν το αρχείο υπάρχει ήδη δε θα προστεθεί ξανά
    
    #προσθήκη του ονόματος του αρχείου στο tv αν δεν υπάρχει ήδη
    selected_files_treeview.insert("", "end", values=(file_name,file_path))

    #ειλογή όλων των εγγραφών των εγγραφών του tv κατά τη φόρτωση
    #for item in selected_files_treeview.get_children():
        #selected_files_treeview.selection_add(item)
        #print("added: ", file_name,"File path", file_path)
    console_message(f"loaded dicom file with name: {file_name}",level="debug")

def list_files_from_dir(output_directory):
    for filename in os.listdir(output_directory):
        file_path = os.path.join(output_directory, filename)
        file_path = os.path.normpath(file_path)
        add_to_anonymized(file_path)

def add_to_anonymized(file_path):
    file_name = os.path.basename(file_path) #παίρνω μόνο το όνομα του αρχείου

    #Λήψη όλων των αρχείων που υπάρχουν στο reeview, με το [1] παιρνω το file_path
    all_files_in_tree = [anonimyzed_files_treeview.item(item, "values")[1] for item in anonimyzed_files_treeview.get_children()]

    if file_path in all_files_in_tree:
        messagebox.showwarning("Warning", f"The file '{file_name}' is already in the list.")
        return #αν το αρχείο υπάρχει ήδη δε θα προστεθεί ξανά
    
    #προσθήκη του ονόματος του αρχείου στο tv αν δεν υπάρχει ήδη
    anonimyzed_files_treeview.insert("", "end", values=(file_name,file_path))

    #ειλογή όλων των εγγραφών των εγγραφών του tv κατά τη φόρτωση
    #for item in selected_files_treeview.get_children():
        #selected_files_treeview.selection_add(item)
        #print("added: ", file_name,"File path", file_path)
    console_message(f"loaded dicom file with name: {file_name}",level="debug")

#συνάρτηση που καλείται όταν πατηθεί το κουμπί Add
def add_selected_file_to_ordered():
    #λήψη του επιλεγμένου αρχείου από το tv
    selected_items = selected_files_treeview.selection()
    
    if len(selected_items) == 0: #Έλεγχος αν δεν έχει επιλεγεί κάποιο αρχείο
        messagebox.showwarning("Warning", "Please select a file to add.")
        return
    
    if len(selected_items) > 1: #Έλεγχος αν έχουν επιλεγεί περισσότερα από ένα αρχεία
        messagebox.showwarning("Warning", "Please select only one file to add.")
        return

    #Λήψη του file_name και του file_path από το επιλεγμένο στοιχείο
    file_name = selected_files_treeview.item(selected_items[0], "values")[0]
    file_path = selected_files_treeview.item(selected_items[0], "values")[1]

    ds = pydicom.dcmread(file_path, stop_before_pixels=True)
    num_of_frames = get_nr_frames(ds)
    
    #έλεγχος αν το αρχείο υπάρχει ήδη στο ordered_files_treeview
    all_files_from_ordered = [ordered_files_treeview.item(item, "values")[1] for item in ordered_files_treeview.get_children()]

    if file_path in all_files_from_ordered:
        messagebox.showwarning("Warning", f"The file '{file_name}' is already in the ordered list.")
        return  #το αρχείο υπάρχει ήδη, δεν το ξανά προσθέτουμε

    tag_value = "none"
    x0_value = 0
    y0_value = 0
    x1_value = 0
    y1_value = 0
    applied = 0
    
    #προσθήκη του αρχείου στο ordered_files_treeview αν δεν υπάρχει ήδη
    ordered_files_treeview.insert("", "end", values=(file_name, file_path, tag_value,
                                                     x0_value, y0_value,
                                                     x1_value, y1_value, num_of_frames, applied))#περνάω τις μεταβλητές, εμφανίζω μόνο το file_name

    #αφαίρεση του αρχείου από το selected_files_treeview
    selected_files_treeview.delete(selected_items[0])

    files_in_ordered = len(ordered_files_treeview.get_children())
    frame_1.config(text=f"{files_in_ordered} Ordered files")
    

    #δημιουργία του log msg
    console_message(f"moved {file_name} from selected_files_treeview to ordered_files_treeview",level="debug")

def add_all_from_selected_file_to_ordered():
    #λήψη όλων των  αρχείων από το selected_files_treeview
    selected_items = selected_files_treeview.get_children()
    
    if len(selected_items) == 0:
        messagebox.showwarning("Move files", "There are no files to add.")
        return

    #μεταφορά όλων των αρχείων στο ordered_files_treeview
    for item in selected_items:
        file_name = selected_files_treeview.item(item, "values")[0]
        file_path = selected_files_treeview.item(item, "values")[1]

        ds = pydicom.dcmread(file_path, stop_before_pixels=True)
        num_of_frames = get_nr_frames(ds)
        
        #έλεγχος αν το αρχείο υπάρχει ήδη στο ordered_files_treeview
        all_files_from_ordered = [ordered_files_treeview.item(child, "values")[1] for child in ordered_files_treeview.get_children()]

        if file_path in all_files_from_ordered:
           continue  #αν το αρχείο υπάρχει ήδη το παραλείπει
        
        tag_value = "none"
        x0_value = 0
        y0_value = 0
        x1_value = 0
        y1_value = 0
        applied = 0
        
        ordered_files_treeview.insert("", "end", values=(file_name, file_path, tag_value,
                                                         x0_value, y0_value,
                                                         x1_value, y1_value, num_of_frames, applied))#προσθήκη του αρχείου στο ordered_files_treeview

        console_message(f"moved {file_name} from selected_files_treeview to ordered_files_treeview", level="debug")

    #αφαίρεση όλων των τιμών από το selected_files_treeview
    selected_files_treeview.delete(*selected_items)
    
    files_in_ordered = len(ordered_files_treeview.get_children())
    frame_1.config(text=f"{files_in_ordered} Ordered files")

    messagebox.showinfo("Success", "All selected files have been added to the ordered list.")

#Συνάρτηση που καλείται όταν πατηθεί το κουμπί remove
def from_ordered_to_selected_file():
    #λήψη των επιλεγμένων αρχείων από το Treeview
    selected_items = ordered_files_treeview.selection()

    if len(selected_items) == 0:  #Έλεγχος αν δεν έχει επιλεγεί κάποιο αρχείο
        messagebox.showwarning("Warning", "Please select a file to add.")
        return
    
    if len(selected_items) > 1:  #Έλεγχος αν έχουν επιλεγεί περισσότερα από ένα αρχεία
        messagebox.showwarning("Warning", "Please select only one file to add.")
        return

    #Λήψη του file_name και του file_path από το επιλεγμένο στοιχείο
    file_name = ordered_files_treeview.item(selected_items[0], "values")[0]
    file_path = ordered_files_treeview.item(selected_items[0], "values")[1]
    
    #Έλεγχος αν το αρχείο υπάρχει ήδη στο selected_files_treeview
    all_files_in_selected = [selected_files_treeview.item(item, "values")[1] for item in selected_files_treeview.get_children()]

    #αν το αρχείο υπάρχει ήδη, δεν το προσθέτει
    if file_path in all_files_in_selected:
        messagebox.showwarning("Warning", f"The file '{file_name}' is already in the selected list.")
        return
    
    #προσθήκη του αρχείου στο ordered_files_treeview αν δεν υπάρχει ήδη
    selected_files_treeview.insert("", "end", values=(file_name, file_path))

    #αφαίρεση του αρχείου από το selected_files_treeview
    ordered_files_treeview.delete(selected_items[0])

    #logger.debug(f"moved {selected_items[0]} from ordered_files_treeview to selected__files_treeview")
    #για να περάσει κατευθείαν στον logger χωρίς να το τυπώσω στο textbox

    files_in_ordered = len(ordered_files_treeview.get_children())
    frame_1.config(text=f"{files_in_ordered} Ordered files")
    
    console_message(f"moved {file_name} from ordered_files_treeview to selected__files_treeview",level="debug")

def clear_treeview():
    answer = askyesno(title='Confirmation',
                    message='Are you sure that you want\nto remove the selected files?')
    if answer:
        items = selected_files_treeview.get_children()
        
        #Διαγραφή όλων των στοιχείων
        for item in items:
            selected_files_treeview.delete(item)
            
    #logger.debug("cleared the selected_files_treeview")
    #για να περάσει κατευείαν στον logger χωρίς να το τυπώσω στο textbox
            
    console_message("cleared the values from selected_files_treeview",level="debug")

#εκτελείτε κάθε φορά οιυ ξεκινάει μια νέα ανωνυμοποίηση

def clear_anon_treeview():
    if tree_flag == 1:
        preview_frame.destroy()
        info_frame.destroy()
        tags_tree_frame.destroy()
        
    items = anonimyzed_files_treeview.get_children()
    for item in items:
        anonimyzed_files_treeview.delete(item)
        
#την εκτελούμε όταν θελουμε να ακυρώσουμε μια ανωνυμοποίηση
# δε θα την κάνουμε δηλ export σε ZIP
def clear_anon_treeview2():
    if tree_flag == 1:
        preview_frame.destroy()
        info_frame.destroy()
        tags_tree_frame.destroy()
        
    items = anonimyzed_files_treeview.get_children()
    for item in items:
        anonimyzed_files_treeview.delete(item)

    id_entry_entry.config(state="normal", text="")
    id_entry_entry.delete(0, "end")
    anonymize_button["state"] = "normal"
    del_forlders()

def preview_selected_file(treeview, source_stage):
    frame_2.configure(text=f"Image preview from {source_stage}")

    #Λήψη του επιλεγμένου αρχείου από το TV που έχει δοθεί ως παράμετρος
    selected_item = treeview.focus()
    #επιτρέφει ('I001',) με len = 1
    
    #selected_item = treeview.selection()
    #επιτρέφει I001 με len = 4

    if not selected_item:  #Έλεγχος αν δεν έχει επιλεγεί κάποιο αρχείο
        messagebox.showwarning("Warning", "Please select a file to preview.")
        return

    '''
    #ver > 2.60 δεν απαιτείτε καθώς εφαρμόζω selectmode="broswe" κατα τη δημιουργία του treeview
    if len(selected_item) > 1:  #Έλεγχος αν έχουν επιλεγεί περισσότερα από ένα αρχεία
        messagebox.showwarning("Warning", "Please select only one file to preview.")
        return
    '''

    tree_values = treeview.item(selected_item, "values")
    file_path = tree_values[1]
    #print(tree_values[7])

    #αν το preview δε προερχετε απο την ordeder list κανω την μεταβλητη
    #tag_value κενή για να μή σκάσει η συνάρηση preview_file, αλλιως ειναι none
    if (len(tree_values)) > 2:
        tag_value = tree_values[2]
    else:
        tag_value = ""
        
    preview_file_thread = Thread(target=preview_file, args=(file_path, source_stage, tag_value, selected_item, treeview))
    
    #Κλήση της συνάρτησης preview_file με το επιλεγμένο file_path και απο ποίο treeview τη κάλεσα

    #Κληση χωρίς threading
    #preview_file(file_path, source_stage)

    #αν εισάγω μονο το Thread, from threading import Trhead
    preview_file_thread.start()
    
    #αν εισάγω όλη τη βιβλιοθήκη, import threading
    #preview_file_thread = threading.Thread(target=preview_file, args=(file_path, source_stage))

    #preview_file_thread.join()

def load_zip_and_display():
    #global zcount
    zip_file_path = filedialog.askopenfilename(title="Open ZIP archive", filetypes=[("ZIP files", "*.zip")])
    #print("Selected file:", zip_file_path)

    if not zip_file_path:
        #print("No file selected.")
        return
    
    loading_popup = popup_message("Load zip", "loading...\nPlease wait.")
    def apply_load_zip_and_display():
        global zcount
        try:
            console_message("try to read zipped files",level="debug")
            with zipfile.ZipFile(zip_file_path, 'a') as archive:
                #archive.printdir()# print for debug
                dicom_files = []

                for file in archive.namelist():#διαβλαζω το κάθε αρχείο απο τη namelist
                    with archive.open(file) as f:
                        try:# ελέγχω αν το αρχείο είναι τύπου dicom. ακόμη και αν δεν εχει κατάληξη .dcm
                            ds = pydicom.dcmread(f)
                            dicom_files.append(file)
                        except pydicom.errors.InvalidDicomError as e:
                            #print(f"{file} is not a valid DICOM file, skipped")
                            console_message(f"skipped non valid dicom file, {e}",level="error")
                            continue
                
                if not dicom_files:
                    #print("No DICOM files found in the ZIP archive.")
                    return

                console_message(f"Total DICOM files found: {len(dicom_files)}", level="debug")

                #δημιουργία temp φακέλου για την αποθήκευση DICOM αρχείων απο zip folder
                global temp_output_dir, output_path
                #output_dir = os.path.join(os.getcwd(), "temp_dicom_files")
                #παίρνω το τρέχον path απο εκεί που τρέχει και το python αρχείο
                #print("in zip, ", output_path)
                zcount += 1
                temp_output_dir = os.path.join(output_path, f"temp_unzipped_files_0{zcount}")
                os.makedirs(temp_output_dir, exist_ok=True)
                temp_output_dir = os.path.normpath(temp_output_dir)
                #print("Temp output: ",temp_output_dir)

                #αποθήκευση κάθε DICOM αρχείου στον φάκελο "temp_dicom_files"
                countZ = 0
                for dicom_file in dicom_files:
                   
                    unziped_file_path = os.path.join(temp_output_dir, os.path.basename(dicom_file))
                    #print("Unzipped file path: ", unziped_file_path)
                    with archive.open(dicom_file) as file:
                        with open(unziped_file_path, 'wb') as output_file:
                            output_file.write(file.read())
                            countZ += 1
                    console_message(f"Total saved files to temp folder: {countZ}", level="debug")

            load_folder()
            loading_popup.destroy()
            file_count = sum(len(files) for _, _, files in os.walk(output_path))
            foot_label1.config(text=f"{file_count} files\nat temp folder")

        except zipfile.BadZipFile as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}\n\nSelect another file")
            console_message(f"An error occurred: {str(e)} Select another file", level="error")

    apply_load_zip_and_display_thread = Thread(target=apply_load_zip_and_display, args=())
    apply_load_zip_and_display_thread.start()

# ------ ΤΕΛΟΣ ------ zip load_file() -----------------------

def move_up():
    selected_items = ordered_files_treeview.selection()
    for item in selected_items:
        current_index = ordered_files_treeview.index(item)
        if current_index > 0:  #Έλεγχος ότι δεν είμαστε ήδη στο πρώτο στοιχείο
            ordered_files_treeview.move(item, ordered_files_treeview.parent(item), current_index - 1)

def move_down():
    selected_items = ordered_files_treeview.selection()
    for item in reversed(selected_items):  #Χρησιμοποιούμε reversed για να μην υπάρχουν συγκρούσεις στη μετακίνηση
        current_index = ordered_files_treeview.index(item)
        total_items = len(ordered_files_treeview.get_children())
        if current_index < total_items - 1:  #Έλεγχος ότι δεν είμαστε ήδη στο τελευταίο στοιχείο
            ordered_files_treeview.move(item, ordered_files_treeview.parent(item), current_index + 1)


#αρχικοποίηση μεταβλητής
tree_flag = 0
    
#Συνάρτηση όπου ανοίγει το αρχείο DICOM και διαβάζει τα tags και την εικόνα
def preview_file(file_path, source_stage, tag_value, selected_item, treeview):
    global tree_flag, tags_tree_frame, preview_frame, info_frame, ds, img_label, video_slider, current_frame_index, crop_values_apply_btn # Χρήση των global μεταβλητών
    #loading_popup = popup_message("Preview", "loading...\nPlease wait.")#, delay=2000
    #ελεγχος αν υπάρχει ήδη frame και διαγραφή τους
    if tree_flag == 1:
        preview_frame.destroy()
        info_frame.destroy()
        tags_tree_frame.destroy()
    #print("tag_value: ",tag_value)
    #print(type(tag_value))
    tree_flag = 1
    ds = pydicom.dcmread(file_path) #ανάγνωση του αρχείου DICOM
    num_frames = get_nr_frames(ds)

    if 'PixelData' in ds:
        columnsNo = ds[0x0028,0x0011].value
        rowsNo = ds[0x0028,0x0010].value
    else:
        columnsNo=0
        rowsNo=0
    
    console_message("read a DICOM file in def preview_file function",level="debug")
    
    #frame_2.grid_columnconfigure(0, weight=1)
    frame_3.grid_columnconfigure(0, weight=1)
    # ------- Frame με τα tags -------
    tags_tree_frame = tk.Frame(frame_3)#Σταθερό πλάτος και ύψος , width=50, height=400
    tags_tree_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew") 
    tags_tree_frame.grid_columnconfigure(0, weight=1)

    #sυνάρτηση για να αντιγράφει μόνο το περιεχόμενο του κελιού
    def copy_cell_to_clipboard(content):
        root = tk.Tk()
        root.withdraw() 
        root.clipboard_clear()
        root.clipboard_append(content)
        root.update()
        root.destroy()
        #print(f"cell content: {content}")

    #Συνάρτηση για να αντιγράφει όλη τη γραμμή
    def copy_line_to_clipboard(content):
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear() #καθαρισμός του clipboard απο προηγούμενο copy
        root.clipboard_append("\t".join(content))  # Προσθήκη όλων των περιεχομένων της γραμμής στο clipboard
        root.update()   #Ενημέρωση του clipboard
        root.destroy()  #σβηνει το μενού
        #print(f"line content: {'\t'.join(content)}")

    def on_right_click(event):
        item = tags_treeview.identify('item', event.x, event.y)
        if item:
            selected_values = tags_treeview.item(item, "values")
                
            #κατασκευή του  menu για το δεξί κλικ
            menu = tk.Menu(root, tearoff=0)
            menu.add_command(label="Copy Tag", command=lambda: copy_cell_to_clipboard(selected_values[0]))#Αντιγραφή μόνο της 1ης στήλης
            menu.add_command(label="Copy Name", command=lambda: copy_cell_to_clipboard(selected_values[1]))  
            menu.add_command(label="Copy Value", command=lambda: copy_cell_to_clipboard(selected_values[2]))
            menu.add_command(label="Copy Line", command=lambda: copy_line_to_clipboard(selected_values))#Αντιγραφή όλης της γραμμής
            menu.post(event.x_root, event.y_root)
            #print(f"x: {event.x_root}, y: {event.y_root}")
    
    # Δημιουργία του treeview
    tags_treeview = ttk.Treeview(tags_tree_frame, columns=("Tag", "Name", "Value"),
                                 show="headings", selectmode="browse", height=34)                               
    tags_treeview.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    
    #κατασκευή των scrollbars
    tags_tree_v_scrollbar = tk.Scrollbar(tags_tree_frame, orient="vertical",
                                         command=tags_treeview.yview)  
    tags_tree_v_scrollbar.grid(row=0, column=1, sticky="ns")
    tags_treeview.configure(yscrollcommand=tags_tree_v_scrollbar.set)

    tags_tree_h_scrollbar = tk.Scrollbar(tags_tree_frame, orient="horizontal",
                                         command=tags_treeview.xview)  
    tags_tree_h_scrollbar.grid(row=1, column=0, sticky="ew")
    tags_treeview.configure(xscrollcommand=tags_tree_h_scrollbar.set)
    
    #στήλες και των επικεφαλίδες του treeview
    tags_treeview.heading("Tag", text="Tag")
    tags_treeview.column("Tag", width=65, anchor='center', stretch=False)#Μικρότερο πλάτος για το tag

    tags_treeview.heading("Name", text="Name")
    tags_treeview.column("Name", width=200, anchor='w', stretch=False)#Σταθερό πλάτος για το name

    tags_treeview.heading("Value", text="Value", anchor='w')
    tags_treeview.column("Value", width=350, anchor='w', stretch=False)#Μεγαλύτερο πλάτος για ενεργοποίηση του οριζόντιου scrollbar
    tags_treeview.bind("<Button-3>", on_right_click)
    
    def load_tags():
    #προσθήκη των tags από τα metadata στο treeview
        console_message("start to read all elements from the DICOM file",level="debug")
    
        #print("---- METADATA ----")
        if hasattr( ds, 'file_meta'):
            tag=""
            value=""
            name = "MetaData"
            tags_treeview.insert("", "end", values=(tag, name, value))
            for elem in ds.file_meta:
                tag = elem.tag
                name = elem.name
                keyword = elem.keyword
                value = str(elem.value)[:200] + "..." if len(str(elem.value)) > 200 else str(elem.value)
                
                #print(keyword,value)
                #print(elem)
                    
                if elem.VR == "UI":  #για να φέρω τις περιργαφες πχ JPEG basilene 1
                    uid_description = UID(value).name if UID(value).is_valid else "Unknown UID"
                    if uid_description != value:
                        value = f"{value} ({uid_description})"  #προσθήκη της περιγραφής στην τιμή, αν διαφέρει με το value
                tags_treeview.insert("", "end", values=(tag, name, value))

        tag=""
        value=""
        name = "DataSet"
        tags_treeview.insert("", "end", values=(tag, name, value))            
        for elem in ds.iterall():
            tag = elem.tag
            #print(tag)
            #print(type(tag)) # <class 'pydicom.tag.BaseTag'>
            name = elem.name
            keyword = elem.keyword
            value = str(elem.value)[:200] + "..." if len(str(elem.value)) > 200 else str(elem.value)  #περικοπή μεγάλων strings
            if elem.VR == "UI":  #για να φέρω τις περιργαφες πχ JPEG basilene 1
                #print(keyword,value)
                #print(elem)
                uid_description = UID(value).name if UID(value).is_valid else "Unknown UID"
                if uid_description != value:
                    value = f"{value} ({uid_description})"
            if elem.VR == "SQ":
                    value = "---- Sequence ----"
            tags_treeview.insert("", "end", values=(tag, name, value))
        console_message("Done, all elements from the DICOM file has readed",level="debug")
    
    load_tags_thread = Thread(target=load_tags).start()
    
    # --------- Frame με την εικόνα ---------
    preview_frame = tk.Frame(frame_2, height=30)
    preview_frame.grid(padx=0, pady=0, row=0, column=0, sticky="nsew")
    preview_frame.grid_columnconfigure(0, weight=1)

    # με 2Πλό κλίκ επάνω στην εικόνα την κάνω Plot
    preview_frame.bind('<Double-Button-1>', lambda: plot_image(pixel_array(ds, index=current_frame_index), source_stage))

    info_frame = tk.Frame(frame_2)
    info_frame.grid(padx=0, pady=5, row=1, column=0, sticky="nsew")
    info_frame.grid_columnconfigure(1, weight=1)

    # ------- Δημιουργία του Combobox για το Tag -------
    if source_stage == "Ordered files":

        sel_tag_frame = tk.Frame(info_frame)
        sel_tag_frame.grid(padx=0, pady=0, row=1, column=1, sticky="nsew")

        #ρύθμιση του πλέγματος για το sel_tag_frame
        sel_tag_frame.grid_rowconfigure(0, weight=1)
        sel_tag_frame.grid_rowconfigure(1, weight=1)
        sel_tag_frame.grid_columnconfigure(0, weight=1)

        web_link_str = config.get("tags_link", "tags_link")

        select_tag_label = tk.Label(sel_tag_frame,
                                    text="Select tag:", font=("Segoe UI", 8, "underline"),
                                    fg="blue", cursor="hand2")
        select_tag_label.grid(row=0, column=0, padx=5, pady=0)
        select_tag_label.bind("<Button-1>", lambda e: open_web_link(web_link_str))

        try:
            #διαβάζω τις τιμές απο το settings.ini και τις μετατρέπω σε λίστα
            tag_values_str = config.get("tag_values", "tag_values")
            
            tag_values = eval(tag_values_str)#το μετατρέπω σε tuple
            #print(type(tag_values))
            #print(len(tag_values))
            
            tag_combobox = ttk.Combobox(sel_tag_frame, width=7, state="readonly") 
            tag_combobox['values'] = tag_values
            tag_combobox.grid(row=1, column=0, padx=5, pady=0)
            tag_combobox.set(tag_value)
        except Exception as e:
            console_message("error while reading tag values from settings.ini", level="error")
            messagebox.showerror("Read tag_values", f"{e}.")

        #print(len(tag_combobox['values']))
        #tags_len = len(tag_combobox['values'])
        #print(tags_len)     

        #print(web_link_str)
        #ελέγχω αν το dicom αρχείο  ειναι single ή multi frame
        if num_frames > 1:
            #frames = ds.pixel_array
            is_multiframe = True
        else:
            #frames = ds.pixel_array.reshape(1, *ds.pixel_array.shape)
            is_multiframe = False

        #διαβάζω το SN από το dicom αρχείο (απο το tag 0018,1000 με name Device Serial Number)
        device_sn = ds.get((0x0018, 0x1000), None)  #αν δεν υπάρχει SN επιστρέψει None
        software_ver = ds.get((0x0018, 0x1020), None)  #αν δεν υπάρχει tag επιστρέψει None
        model_name = ds.get((0x0008, 0x1090), None)
        station_name = ds.get((0x0008, 0x1010), None)
        
        #print("model name: ", model_name)
        #print("station name: ", station_name)

        crop_identifier = None
        if device_sn:
            crop_identifier = device_sn.value
            console_message(f"Found SN: {device_sn}", level="info")
        elif software_ver:
            crop_identifier = software_ver.value
            console_message(f"Found software version: {software_ver}", level="info")
        elif model_name:
            crop_identifier = model_name.value
            console_message(f"Found model name: {model_name}", level="info")
        elif station_name:
            crop_identifier = station_name.value
            console_message(f"Found station name: {station_name}", level="info")
        else:
            console_message(f"No relative data (SN, software version, model name, or station name) found in DICOM file", level="warning")
            
        #Ανάγνωση των τιμών X0, Y0, X1, Y1 από το INI αρχείο για το συγκεκριμένο SN
        try:
            #Αναζήτηση της συσκευής από το αρχείο INI
            device_key = None
            for key in config['devices']:
                if config['devices'][key].split('],')[0].strip('[]') == crop_identifier:
                    device_key = key
                    #print("Device key: ", device_key)
                    break
                
            if device_key is not None:
                crop_identifier_status = 1
                device_info = config['devices'][device_key].split('],')
                #print("Device info: ", device_info)
                
                crop_areas = [list(map(int, area.strip('[]').split(','))) for area in device_info[1:]]
                #print("Crop Options all: ", crop_areas)
                #print("Crop Options 1 (single frame}: ", crop_areas[0])
                #print("Crop Options 2 (multi frame}: ", crop_areas[1])
                
                if is_multiframe and len(crop_areas) > 1:
                    selected_crop = crop_areas[1]  #Επιλογή από τη θέση 2 αν είναι multiframe
                    #ανάθεση των τιμών crop
                    crop_x0, crop_y0, crop_x1, crop_y1= selected_crop
                else:
                    selected_crop = crop_areas[0]  #Επιλογή από τη θέση 1 αν είναι single frame
                    #ανάθεση των τιμών crop
                    crop_x0, crop_y0, crop_x1, crop_y1 = selected_crop

                console_message(f"Found identifier: {crop_identifier}, Crop area: {selected_crop}", level="info")
                #αυτό στο τέλος να το βγάλω
            
            else:
                crop_identifier_status = 0
                #αν το SN δεν υπάρχει στο INI, skip και εμφανίζει μήνυμα
                console_message(f"SN {device_sn} not found in ini, file skipped", level="warning")
                messagebox.showerror("Read crop area", f"crop identifier {crop_identifier} not found in ini.\nAdd the device SN and crop areas to settings file.\nOr apply manual crop.")
                #crop_x0, crop_y0, crop_x1, crop_y1 = [0, 0, columnsNo, rowsNo]
                #selected_crop = [0, 0, columnsNo, rowsNo]

                try:
                    sequence_element = ds[0x0018, 0x6011]
                    sequence = sequence_element.value
                    item = sequence[0]
                    #print(item[0x0018, 0x6018].value)
                    #print("item 00018,6018:",type(item[0x0018, 0x6018].value))

                    crop_x0 = item[0x0018, 0x6018].value
                    crop_y0 = item[0x0018, 0x601a].value
                    crop_x1 = item[0x0018, 0x601c].value
                    crop_y1 = item[0x0018, 0x601e].value
                except:
                    crop_x0, crop_y0, crop_x1, crop_y1 = [0, 0, columnsNo, rowsNo]

                selected_crop = crop_x0, crop_y0, crop_x1, crop_y1

        except Exception as e:
            crop_identifier_status = 0
            #αν οι τιμές δεν είναι σωστά περασμένες skip και εμφανίζει μήνυμα
            console_message(f"Failed to read crop data for identifier {crop_identifier}: {str(e)}", level="error")
            messagebox.showerror("Read crop area", f"Error while reading crop data for identifier  {crop_identifier}: {str(e)}.\nCheck settings file or apply manual crop.")
            #crop_x_start, crop_y_start, crop_x_end, crop_y_end = [0, 0, columnsNo, rowsNo]#αναθέλω τιμές για όλη την εικόνα

            #αναθέλω τιμές για την περιοχή βάση των tag που υπάρχουν
            crop_x0 = item[0x0018, 0x6018].value
            crop_y0 = item[0x0018, 0x601a].value
            crop_x1 = item[0x0018, 0x601c].value
            crop_y1 = item[0x0018, 0x601e].value
            selected_crop = crop_x0, crop_y0, crop_x1, crop_y1

        #διαβάζω τις τιμές x0,x1,y0,y1
        current_values = treeview.item(selected_item, "values")
        
        if all(int(value) == 0 for value in current_values[3:7]):
            crop_x_start, crop_y_start, crop_x_end, crop_y_end =  selected_crop
        else:
            crop_x_start, crop_y_start, crop_x_end, crop_y_end = current_values[3:7]

        crop_info_frame = tk.LabelFrame(info_frame, text="Crop area", font=("Segoe UI", 8), height=35)
        crop_info_frame.grid(row=1, column=0, sticky="nsew")

        x0_label = tk.Label(crop_info_frame, text="X_min", font=("Segoe UI", 8))
        x0_label.grid(row=0, column=0, sticky="nsew")

        crop_x_start_var = tk.IntVar(value=crop_x_start)
        x0_spnb = tk.Spinbox(crop_info_frame, textvariable=crop_x_start_var, width = 4,
                             from_=0, to=columnsNo)
        x0_spnb.grid(row=0, column=1, sticky="nsew")
        
        y0_label = tk.Label(crop_info_frame, text="Y_min", font=("Segoe UI", 8))
        y0_label.grid(row=0, column=2, sticky="nsew")

        crop_y_start_var = tk.IntVar(value=crop_y_start)
        y0_spnb = tk.Spinbox(crop_info_frame, textvariable=crop_y_start_var, width = 4,
                             from_=0, to=rowsNo)
        y0_spnb.grid(row=0, column=3, sticky="nsew")

        x1_label = tk.Label(crop_info_frame, text="X_max", font=("Segoe UI", 8))
        x1_label.grid(row=1, column=0, sticky="nsew")

        crop_x_end_var = tk.IntVar(value=crop_x_end)
        x1_spnb = tk.Spinbox(crop_info_frame, textvariable=crop_x_end_var, width = 4,
                             from_=0, to=columnsNo)
        x1_spnb.grid(row=1, column=1, sticky="nsew")

        y1_label = tk.Label(crop_info_frame, text="Y_max", font=("Segoe UI", 8))
        y1_label.grid(row=1, column=2, sticky="nsew")

        crop_y_end_var = tk.IntVar(value=crop_y_end)
        y1_spnb = tk.Spinbox(crop_info_frame, textvariable=crop_y_end_var, width = 4,
                             from_=0, to=rowsNo)
        y1_spnb.grid(row=1, column=3, sticky="nsew")
        
        applied_value = int(current_values[8])
        
        #print("applied_value: ",applied_value)
        crop_values = {
                "x0": x0_spnb,
                "y0": y0_spnb,
                "x1": x1_spnb,
                "y1": y1_spnb
                }
        #print(type(crop_values))

        def crop_callback(var, index, mode, variable):
            try:
                apply_crop_frames(crop_values)
            except Exception as e:
                messagebox.showerror("Error", f"{e}")

        #παρακολούθηση μεταβλητών
        crop_x_start_var.trace_add("write", lambda var, index, mode: crop_callback(var, index, mode, crop_x_start_var))
        crop_y_start_var.trace_add("write", lambda var, index, mode: crop_callback(var, index, mode, crop_y_start_var))
        crop_x_end_var.trace_add("write", lambda var, index, mode: crop_callback(var, index, mode, crop_x_end_var))
        crop_y_end_var.trace_add("write", lambda var, index, mode: crop_callback(var, index, mode, crop_y_end_var))

        highlightNo = 0
        def apply_crop_values(treeview, selected_item, crop_values, highlightNo, var_apply, is_multiframe):
            apply_var=var_apply.get()#apply to all

            if apply_var==1:
                response = messagebox.askyesno("Apply to all?", "Do you want to apply this\ncrop area to all files?")
                if response =="yes":
                    return
            
            #λαμβάνω τις τιμές απο το λεξικό
            x0 = crop_values["x0"].get()
            y0 = crop_values["y0"].get()
            x1 = crop_values["x1"].get()
            y1 = crop_values["y1"].get()
            

            '''
            print("crop value x0: ", x0)
            print("crop value y0: ", y0)
            print("crop value x1: ", x1)
            print("crop value y1: ", y1)
            '''
                
            #print("treeview: ", treeview)
            #print("selected item", selected_item)
# ************** ΕΔΩ ισως πρεπει να βαλω else ************
            if apply_var == 0:
                #παίρνω τις τιμές της γραμμής
                current_values = treeview.item(selected_item, "values")
                #print(current_values)
                
                #πρέπει να έχω μία λίστα από το current_values για να την ενημερώσω
                updated_values = list(current_values)
                    
                #ενημέρωση των θέσεων 3, 4, 5, 6 με τις τιμές x0, y0, x1, y1
                updated_values[3] = x0
                updated_values[4] = y0
                updated_values[5] = x1
                updated_values[6] = y1

                applied_value = 1
                updated_values[8] = applied_value
                
                    
                #ενημέρωση της γραμμής στο treeview
                treeview.item(selected_item, values=updated_values)
                
                #για να αλλάξω το χρώμα σε πράσινο
                update_image_with_crop_area(
                                frame_index=current_frame_index,
                                crop_x_start=x0,
                                crop_y_start=y0,
                                crop_x_end=x1,
                                crop_y_end=y1,
                                applied_value=1
                                )

                #current_values = treeview.item(selected_item, "values")
                treeview.tag_configure(f"highlight_{highlightNo}", background="lightgreen")
                treeview.item(selected_item, tags=(f"highlight_{highlightNo}",))
                highlightNo += 1
            else:
                    
                #για την κάθε γραμμή του treeview
                tree_values = treeview.item(selected_item, "values")
                file_path = tree_values[1]
                #print(tree_values[7])
                #print(is_multiframe)
                if is_multiframe == True:
                    for item in treeview.get_children():
                        #λαμβάνω τις τιμές της γραμμής
                        current_values = treeview.item(item, "values")
                        updated_values = list(current_values)
                        if int(current_values[7]) > 1:
                            #print(current_values[7])
                            updated_values[3] = x0
                            updated_values[4] = y0
                            updated_values[5] = x1
                            updated_values[6] = y1

                            applied_value = 1
                            updated_values[8] = applied_value

                            treeview.item(item, values=tuple(updated_values))
                            treeview.tag_configure(f"highlight_{highlightNo}", background="lightgreen")
                            treeview.item(item, tags=(f"highlight_{highlightNo}",))
                            highlightNo += 1
                        else:
                            pass
                else:
                    for item in treeview.get_children():
                        #λαμβάνω τις τιμές της γραμμής
                        current_values = treeview.item(item, "values")
                        updated_values = list(current_values)
                        if int(current_values[7]) == 1:#αν ειναι sigle frame
                            #print(current_values[7])
                            updated_values[3] = x0
                            updated_values[4] = y0
                            updated_values[5] = x1
                            updated_values[6] = y1

                            applied_value = 1
                            updated_values[8] = applied_value

                            treeview.item(item, values=tuple(updated_values))
                            treeview.tag_configure(f"highlight_{highlightNo}", background="lightgreen")#46dcb2
                            treeview.item(item, tags=(f"highlight_{highlightNo}",))
                            highlightNo += 1
                        else:
                            pass

        def apply_crop_frames(crop_values):#εκτελειτε όταν πατάει το spinbox button
            #λαμβάνω τις τιμές απο το λεξικό
            x0 = crop_values["x0"].get()
            y0 = crop_values["y0"].get()
            x1 = crop_values["x1"].get()
            y1 = crop_values["y1"].get()

            #για να αλλάξω το χρώμα σε κοκκινο
            update_image_with_crop_area(
                                    frame_index=current_frame_index,
                                    crop_x_start=x0,
                                    crop_y_start=y0,
                                    crop_x_end=x1,
                                    crop_y_end=y1,
                                    applied_value=0
                                    )

      
        def add_to_devices(crop_values, crop_identifier):
            global settings_file_path
            try:
                #λαμβάνω τις τιμές απο το λεξικό
                x0 = crop_values["x0"].get()
                y0 = crop_values["y0"].get()
                x1 = crop_values["x1"].get()
                y1 = crop_values["y1"].get()

                config = configparser.ConfigParser()
                config.read(settings_file_path)

                timestamp = datetime.now().strftime("%y%m%d%H%M%S")
                new_device_key = f"added{timestamp}" 

                if "devices" not in config:#σε περίπτωση που σβηστεί, το ξανα δημιουργώ
                    config["devices"] = {}

                new_device_value = f"[{crop_identifier}],[{x0},{y0},{x1},{y1}],[{x0},{y0},{x1},{y1}]"
                config["devices"][new_device_key] = new_device_value
                
                #αποθήκευση των τιμών στο αρχείο settings.ini
                with open(settings_file_path, 'w') as configfile:
                    config.write(configfile)

                messagebox.showinfo("Add device",f"Crop areas added to settings file as {new_device_key}\nwith values {new_device_value}\nRestart the app to make effect.")
            except Exception as e:
                messagebox.showerror("Add device",f"Error: {e}")
                
        
        crop_values_apply_btn = ttk.Button(crop_info_frame, text="Apply", style="apply.TButton",
                                           command= lambda: apply_crop_values(treeview, selected_item, crop_values, highlightNo, var_apply, is_multiframe))
        crop_values_apply_btn.grid(row=0, column=4, padx=3, sticky="w")

        var_apply = tk.IntVar()
        apply_to_all_cb = tk.Checkbutton(crop_info_frame, text="to all", variable=var_apply, onvalue=1, offvalue=0)
        apply_to_all_cb.grid(row=0, column=5, padx=0, sticky="w")

        crop_values_add_btn = ttk.Button(crop_info_frame, text="+ to settings", style="small.TButton",
                                           command= lambda: add_to_devices(crop_values, crop_identifier))
        crop_values_add_btn.grid(row=1, column=4, padx=3, sticky="w")
        #print(crop_identifier_status)
        if crop_identifier_status == 0:
            crop_values_add_btn["state"] = "normal"
        else:
            crop_values_add_btn["state"] = "disabled"
                                           
        #συνάρτηση για ενημέρωση του tag στο Treeview
        def update_tag(event,  treeview, selected_item):
            new_tag = tag_combobox.get()
            current_values = treeview.item(selected_item, "values")
            #print(current_values)
            #print(type(current_values))#tuple, δε μπορει να επεξεργαστεί

            updated_values = list(current_values)#για να το επεξεργαστώ
            updated_values[2] = new_tag
            treeview.item(selected_item, values=tuple(updated_values))
            '''
            if new_tag != "none":
                treeview.tag_configure("highlight", background="#f9f871")
                treeview.item(selected_item, tags=("highlight",))
            else:
                treeview.item(selected_item, tags=())
            '''

        #Σύνδεση του Combobox με την αλλαγή
        tag_combobox.bind("<<ComboboxSelected>>", lambda event: update_tag(event, treeview, selected_item))
            
    #έλεγχος αν το αρχείο DICOM περιέχει δεδομένα εικόνας
    if 'PixelData' in ds:
        try:
            console_message("try to read pixel data from the DICOM file",level="debug")
            #num_frames = get_nr_frames(ds)
            
            #δημιουργία του slider για τα frames
            if num_frames == 1:
                video_slider = tk.Scale(info_frame, from_=0, to=num_frames-1,label="Video Slider",
                                    orient=tk.HORIZONTAL,
                                    activebackground="#33A1C9",
                                    font=("Segoe UI", 8),
                                    command=lambda val: update_image(int(val)))#θέλει μετατροπή σε integer 
            else:

                if source_stage == "Ordered files":
                    video_slider = tk.Scale(info_frame, from_=0, to=num_frames-1,label="Video Slider",
                                        orient=tk.HORIZONTAL,
                                        activebackground="#33A1C9",
                                        font=("Segoe UI", 8),
                                        command=lambda val: update_image_with_crop_area(int(val),crop_x_start, crop_y_start, crop_x_end, crop_y_end, applied_value))#θέλει μετατροπή σε integer 

                else:
                    video_slider = tk.Scale(info_frame, from_=0, to=num_frames-1,label="Video Slider",
                                    orient=tk.HORIZONTAL,
                                    activebackground="#33A1C9",
                                    font=("Segoe UI", 8),
                                    command=lambda val: update_image(int(val)))#θέλει μετατροπή σε integer 
                    
            video_slider.grid(row=0, column=0, columnspan=2, sticky="nsew")

            if num_frames >= 1000:
                video_slider.config(tickinterval=100)
            elif num_frames >= 700:
                video_slider.config(tickinterval=70)
            elif num_frames >= 450:
                video_slider.config(tickinterval=50)
            elif num_frames >= 280:
                video_slider.config(tickinterval=40)
            elif num_frames >= 160:
                video_slider.config(tickinterval=20)
            else:
                video_slider.config(tickinterval=5)

            #Δημιουργία Label για την εμφάνιση της εικόνας
            img_label = tk.Label(preview_frame)
            img_label.grid(row=0, column=0)
            
            def show_image_on_dclick():#συνάρτηση για να κάνει plot την εκόνα όταν ο χρήστης κάνει 2πλο κλικ επάνω της
                plot_image(pixel_array(ds, index=current_frame_index), source_stage)

            img_label.bind("<Double-1>", lambda event: show_image_on_dclick())
            '''
            plot_button = ttk.Button(info_frame, text="Show image", style="small.TButton",
                                     command=lambda: plot_image(pixel_array(ds, index=current_frame_index), source_stage))
            plot_button.grid(row=2, column=0, padx=5, pady=0, sticky="w")
            '''
            '''
            show_imageJ_button = config['settings'].get('show_imageJ_button', 'no')
            #print("show_imageJ_button: ",show_imageJ_button)
            if show_imageJ_button == "yes":
                edit_button = ttk.Button(info_frame, text="Open in ImageJ", style="small.TButton",
                                         command=lambda: edit_image(file_path))
                edit_button.grid(row=2, column=1, padx=0, pady=0, sticky="w")
            '''
            #if ds.PhotometricInterpretation == "MONOCHROME1":
                #image.convert("L")
            image_info_frame = ttk.LabelFrame(info_frame, text="Image info",  height=35)#font=("Segoe UI", 8),
            image_info_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

            dimension_label = tk.Label(image_info_frame, text=f"Columns: {columnsNo}, Rows: {rowsNo}  |  {ds[0x0028, 0x0101].name}: {ds[0x0028, 0x0101].value}  |  Number of Frames: {num_frames}", font=("Segoe UI", 8))
            dimension_label.grid(row=0, column=0, sticky="w")

            separator = ttk.Separator(image_info_frame, orient='horizontal')
            separator.grid(row=1, column=0, sticky="nsew")

            p_interpretation_label = tk.Label(image_info_frame,
                                              text=f"{ds[0x0028, 0x0004].name}: {ds[0x0028, 0x0004].value}",
                                              font=("Segoe UI", 8))
            p_interpretation_label.grid(row=2, column=0, sticky="w")

            separator = ttk.Separator(image_info_frame, orient='horizontal')
            separator.grid(row=3, column=0, sticky="nsew")
            
            #Εμφάνιση της πλήρης διάδρομής του αρχείου 
            filepath_label_font = font.Font(family="Segoe UI", size=7)
            filepath_label = ScrolledText(image_info_frame, height=1, width=80, wrap=tk.WORD)
            filepath_label.grid(row=4, column=0, sticky="sew")
            filepath_label.insert(tk.END, file_path)
            filepath_label.configure(font=filepath_label_font)
            filepath_label.configure(state='disabled')

            if source_stage == "Ordered files":
                update_image_with_crop_area(0, crop_x_start, crop_y_start, crop_x_end, crop_y_end, applied_value)
            else:
                update_image(0)
            
            console_message("DICOM file readed",level="debug")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while displaying the image: {str(e)}")
            console_message(f"An error occurred while displaying the image: {str(e)}",level="error")
    
    else:
        # αν το Dicom δεν περιέχει εικόνα εμφανίζει ανάλογο μήνυμα
        tk.Label(preview_frame, text="No image data found").pack()
        console_message("No image data found at the DICOM file",level="debug")

    #loading_popup.destroy()
    
    
def popup_message(title, message): #, delay=2000
    #νέο παραθύρο
    popup = tk.Toplevel()
    popup.title(title)
    popup.geometry("350x100")

    #ορίζω τη θέση του popup παραθύρου
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    #print(root_x, root_y)
    popup.geometry("+%d+%d" %(root_x+00,root_y+200))
    
    label = ttk.Label(popup, text=message, font=("Segoe UI", 14))
    label.pack(padx=20, pady=20)
    
    #κλείσιμο του παραθύρου μετά από delay
    #popup.after(delay, popup.destroy)

    return popup

'''    
#χρήση της simpleITK
def edit_image(file_path):
    #ανάγνωση της εικόνας
    image = sitk.ReadImage(file_path)
    #Εμφάνιση της εικόνας με το imageJ
    sitk.Show(image, f"{file_path}", debugOn=True)        
'''

def plot_image(image, source_stage):
    plt.title(f"DICOM image from {source_stage}")
    plt.xlabel("Columns")
    plt.ylabel("Rows")
    plt.imshow(image, cmap='gray', vmin=0, vmax=255)#cmap=plt.cm.bone
    #plt.colorbar()
    plt.show()

def update_image_with_crop_area(frame_index, crop_x_start, crop_y_start, crop_x_end, crop_y_end, applied_value):
    global img_label, ds, current_frame_index

    current_frame_index = int(frame_index)

    #print(crop_x_start, crop_y_start, crop_x_end, crop_y_end)
    
    frame = pixel_array(ds, index=current_frame_index)#Λαβμάνω τη θέση του slider (var) και το εκχωχώ ως frame_index, καλώ το συσκεκριμένο frame
    #print("frame.dtype: ", frame.dtype)
    #Μετατροπή του frame σε εικόνα χρησιμοποιώντας το PIL, αν χρειαστεί
    num_frames = get_nr_frames(ds)
    '''
    if num_frames == 1:
        frame = ds.pixel_array.reshape(1, *ds.pixel_array.shape)
    '''           

    if frame.dtype != np.uint8:
        frame = np.uint8(frame)
    
    img = Image.fromarray(frame).convert("RGB")#κάνω convert γιατι αν ειναι MONOCHROME2 δε ξεχωρίζει

    #ελέγχω αν οι τιμές crop area ειναι έγκυρες
    #print("prin to try: ",applied_value)
    #print(type(applied_value))
    try:
        #σχεδίαση του crop area στην εικόνα
        draw = ImageDraw.Draw(img)
        rect_coords = (int(crop_x_start), int(crop_y_start), int(crop_x_end), int(crop_y_end))
        outline_color = "green" if applied_value==1 else "red"#is_applied or 
        draw.rectangle(rect_coords, outline=outline_color, width=5)
        crop_values_apply_btn.config(state="enable")
    except Exception as e:
    #except ValueError as e:#παιζει κ αυτό
        width, height = img.size
        center_x, center_y = width // 2, height // 2
        X_size = 50
        draw.line((center_x - X_size, center_y - X_size, center_x + X_size, center_y + X_size), fill="red", width=5)
        draw.line((center_x - X_size, center_y + X_size, center_x + X_size, center_y - X_size), fill="red", width=5)
        crop_values_apply_btn.config(state="disabled")
        #messagebox.showerror("Crop area error", f"{e}")
    max_width = 351
    max_height = 271
    
    #υπολογιζω το aspect ratio - αναλογία λαμβάνω απ ευθείας τις τιμές heigth-1 / width-0
    image_aspect_ratio = img.size[1] / img.size[0]
    #print("img.size[0]: ", img.size[0])
    if img.size[0] > max_width:#πέρνω απ ευθείας το πλάτος
        new_width = max_width
        new_height = int(new_width * image_aspect_ratio)#πρέπει να είναι ακαίρεος
        image = img.resize((new_width, new_height))#προσφέρει καλύτερη εικόνα , Image.ANTIALIAS remove at PIL 10 / use , Image.LANCZOS (δεν ειδα διαφορά
    #print("test start")
        
    #Εάν το ύψος είναι μεγαλύτερο από το μέγιστο επιτρεπόμενο ύψος
    #print("img.size[1]: ", img.size[1])
    if img.size[1] > max_height:#πέρνω απ ευθείας το ύψος
        new_height = max_height
        new_width = int(new_height / image_aspect_ratio)
        
        #resize με βάση το ύψος
        image = img.resize((new_width, new_height), Image.LANCZOS)
    else: 
        image = img

    img_tk = ImageTk.PhotoImage(image)#χρήση της ImageTk.PhotoImage απο την PIL
    #del img#ίσως εδω βοηθάει τον garbage collector στη διαχείρηση μνήμης. ίσως ειναι περιττό

    #ενημέρωση της εικόνας στο Label με το αντικειμενο PhotoImage
    img_label.config(image=img_tk)
    img_label.image = img_tk  #αν δε μπεί αυτό χάνετε η εικόνα απο το label


#Συνάρτηση για ενημέρωση της εικόνας ανάλογα με το frame
def update_image(frame_index):
    global img_label, ds, current_frame_index

    current_frame_index = int(frame_index)
    
    frame = pixel_array(ds, index=current_frame_index)#Λαβμάνω τη θέση του slider (var) και το εκχωχώ ως frame_index, καλώ το συσκεκριμένο frame
    #print("frame.dtype: ", frame.dtype)
    #Μετατροπή του frame σε εικόνα χρησιμοποιώντας το PIL, αν χρειαστεί
    num_frames = get_nr_frames(ds)
    '''
    if num_frames == 1:
        frame = ds.pixel_array.reshape(1, *ds.pixel_array.shape)
    '''           

    if frame.dtype != np.uint8:
        frame = np.uint8(frame)
    
    img = Image.fromarray(frame)
 
    max_width = 351
    max_height = 271
    
    #υπολογιζω το aspect ratio - αναλογία λαμβάνω απ ευθείας τις τιμές heigth-1 / width-0
    image_aspect_ratio = img.size[1] / img.size[0]
    #print("img.size[0]: ", img.size[0])
    if img.size[0] > max_width:#πέρνω απ ευθείας το πλάτος
        new_width = max_width
        new_height = int(new_width * image_aspect_ratio)#πρέπει να είναι ακαίρεος
        image = img.resize((new_width, new_height))#προσφέρει καλύτερη εικόνα , Image.ANTIALIAS remove at PIL 10 / use , Image.LANCZOS (δεν ειδα διαφορά
    #print("test start")
    # Εάν το ύψος είναι μεγαλύτερο από το μέγιστο επιτρεπόμενο ύψος
    #print("img.size[1]: ", img.size[1])
    if img.size[1] > max_height:#πέρνω απ ευθείας το ύχος
        new_height = max_height
        new_width = int(new_height / image_aspect_ratio)
        
        # Κάνουμε resize με βάση το ύψος
        image = img.resize((new_width, new_height), Image.LANCZOS)
        #print("test stop")
    else: 
        image = img
        #print("image = img")
        #print(image.size)
        
    
    img_tk = ImageTk.PhotoImage(image)#χρήση της ImageTk.PhotoImage απο την PIL
    #del img#ίσως εδω βοηθάει τον garbage collector στη διαχείρηση μνήμης. ίσως ειναι περιττό

    #ενημέρωση της εικόνας στο Label με το αντικειμενο PhotoImage
    img_label.config(image=img_tk)
    img_label.image = img_tk  #αν δε μπεί αυτό χάνετε η εικόνα απο το label

def anonymize_selected_files():

    def apply_anonymization():
        
        #λαμβάνω όλα τα στοιχεία από το ordered_files_treeview
        selected_items = ordered_files_treeview.get_children()
        if len(selected_items) == 0:
            messagebox.showinfo("No files",
                                "Not ordered files.")
            return

        try:
            #διαβάζω τις τιμές απο το settings.ini και τις μετατρέπω σε λίστα
            tag_values_str = config.get("tag_values", "tag_values")
            tag_values = eval(tag_values_str)#το μετατρέπω σε tuple
            tags_len = len(tag_values)
            
        except Exception as e:
            console_message("error while reading tag values from settings.ini", level="error")
            messagebox.showerror("Read tag_values", f"{e}.")
            return
    
        #ελέγχω αν σε όλα τα στοιχεία έχω περάσει το tag και οι περιοχές crop δεν ειναι 0,0,0,0
        for item in selected_items:
            item_values = ordered_files_treeview.item(item, "values")
            if tags_len == 0:
                if item_values[3:7] == ("0", "0", "0", "0"):
                    messagebox.showerror("Crop area missing",
                                         "Apply crop area for all files.")
                    return
            else:
                if item_values[2] == "none" or item_values[3:7] == ("0", "0", "0", "0"):
                    messagebox.showerror("Crop area missing",
                                         "Apply crop area/tag for all files.")
                    return

        
        #πέρνω την τιμή από το id_entry_entry
        patient_id_entry_value = id_entry_entry.get()
        
        if patient_id_entry_value=="":
            messagebox.showerror("Patient's ID error",
                                 "Give Patient's ID")
            return
        
        if not re.match("^[A-Za-z0-9_-]+$", patient_id_entry_value):
            messagebox.showerror("Patient's ID error",
                                 "Patient ID contains invalid characters")
            return

        clear_anon_treeview()

        loading_popup = popup_message("Anonymize", "Anonymization in process....\nPlease wait.")
        console_message("start anonymization stage 1 (load files)",level="debug")
        
        #δημιουργία του φακέλου αν δεν υπάρχει
        #output_directory = f"{output_path}/anonymized_{patient_id_entry_value}"
        global files_folder
        files_folder = f"anonymized_{patient_id_entry_value}"

        #print("in anonymize_selected_files: ", output_path)
        output_directory = os.path.join(output_path, files_folder)
        os.makedirs(output_directory, exist_ok=True)

        fileNo = 0
        #anonymize_popup = popup_message("Anonymize", "Anonymize files...\nPlease wait.")#, delay=3000
        #για κάθε στοιχείο στο Treeview πέρνω το file path απο τη στήλη και εκτελεί τη συνάρτηση ανωνυμοποίησης
        for item in selected_items:
            file_path = ordered_files_treeview.item(item, "values")[1]
            tag_value = ordered_files_treeview.item(item, "values")[2]

            #ανάθεση των τιμών crop
            crop_x_start = int(ordered_files_treeview.item(item, "values")[3])
            crop_y_start = int(ordered_files_treeview.item(item, "values")[4])
            crop_x_end = int(ordered_files_treeview.item(item, "values")[5])
            crop_y_end = int(ordered_files_treeview.item(item, "values")[6])

            fileNo += 1

            anonymize_file(file_path, tag_value, fileNo, output_directory, files_folder,
                           crop_x_start, crop_y_start, crop_x_end, crop_y_end)#περνάω και ορίσματα
            #anonymize_file_thread = Thread(target=anonymize_file, args=(file_path, fileNo, output_directory, files_folder))
            #anonymize_file_thread.start()

            #διαγράφή του στοιχείου από το Treeview μετά την ανωνυμοποίηση και ενημέρωση του συνολικού αριθμού
            ordered_files_treeview.delete(item)
            files_in_ordered = len(ordered_files_treeview.get_children())
            frame_1.config(text=f"{files_in_ordered} Ordered files")
        
        list_files_from_dir(output_directory)
        
        loading_popup.destroy()

        id_entry_entry.config(state="disabled")
        anonymize_button["state"] = "disabled"

        if tree_flag == 1:
            preview_frame.destroy()
            info_frame.destroy()
            tags_tree_frame.destroy()
        
        messagebox.showinfo("Anonymization", "Task completed.")
        console_message("anonymization completed",level="debug")

        file_count = sum(len(files) for _, _, files in os.walk(output_path))
        foot_label1.config(text=f"{file_count} files\nat temp folder")

    apply_anonymization_thread = Thread(target=apply_anonymization, args=())
    apply_anonymization_thread.start()

#εκτελειτε για κάθε ένα αρχείο ξεχωριστά        
def anonymize_file(file_path, tag_value, fileNo, output_directory, files_folder, crop_x_start, crop_y_start, crop_x_end, crop_y_end):
    console_message(f"start anonymization for fileNo: {fileNo}",level="debug")
    
    try:
        dicom_file = file_path
        ds = pydicom.dcmread(dicom_file)
        num_frames = get_nr_frames(ds)
        #print(ds.file_meta.TransferSyntaxUID, ds.file_meta.TransferSyntaxUID.name)
        
        #if ds.file_meta.TransferSyntaxUID.is_implicit_VR:
            #ds.decompress()  # Χρησιμοποίησε αυτό για να διαχειριστείς Implicit VR σωστά

        #if ds.file_meta.TransferSyntaxUID.is_implicit_VR:
            #ds.decompress() #ισως να μη χρειάζετε

        #ελέγχω αν το dicom αρχείο  ειναι single ή multi frame
        if num_frames > 1:
            console_message(f"read frames for fileNo: {fileNo}",level="debug")
            frames = ds.pixel_array
            is_multiframe = True
        else:
            frames = ds.pixel_array.reshape(1, *ds.pixel_array.shape)
            is_multiframe = False

        '''
        #Αν το PhotometricInterpretation είναι YBR_FULL_422 η YBR_FULL, αλλάζει σε RGB
        if ds.PhotometricInterpretation == 'YBR_FULL_422':
            frames = convert_color_space(arr=frames, current='YBR_FULL_422', desired='RGB')#ή (frames, 'YBR_FULL_422', 'RGB')
        if ds.PhotometricInterpretation == 'YBR_FULL':
            frames = convert_color_space(arr=frames, current='YBR_FUL', desired='RGB')#ή (frames, 'YBR_FULL_422', 'RGB')
        '''
        
        transf_syntax = ds.file_meta.TransferSyntaxUID.name
        
        #υπολογίζω το ύψος, πλατος του νέου αρχείου
        crop_width = crop_x_end - crop_x_start
        crop_height = crop_y_end - crop_y_start
                
        #εφαρμογή του crop - ορισμός της περιοχής που θα κρατήσω
        
        cropped_frames = []
        for i, frame in enumerate(frames):
            #print(frame.shape)
            cropped_frame = frame[crop_y_start:crop_y_start + crop_height, crop_x_start:crop_x_start + crop_width]
            cropped_frames.append(cropped_frame)#συγκεντρώνω σε μία λίστα όλα τα cropped frames
        
        #εναλλακτικά       
        #cropped_frames = frames[:, crop_y_start:crop_y_start + crop_height, crop_x_start:crop_x_start + crop_width]
        
        #διαβάζω τις ρυθμίσεις απο το settings.ini
        user_can_change_compression_level = config['settings'].get('user_can_change_compression_level', 'no')
        #print("user_can_change_compression_level: ", user_can_change_compression_level)

        compression_level = config['settings'].get('compression_level', '100')
        #print("compression_level: ", compression_level)

        convert_all_to_jpeg = config['settings'].get('convert_all_to_jpeg', 'yes')
        #print("convert_all_to_jpeg: ",convert_all_to_jpeg)

        #εφαρμογή σε jpeg ή οχι (default=yes)
        if convert_all_to_jpeg == "yes":
            #print("will convert_all_to_jpeg")

            #εφαρμόζει συμπίεση jpeg
            jpeg_data_list = []
            if user_can_change_compression_level == "yes":
                quality_value = compression_level
            else:
                quality_value = 100

            console_message(f"start crop image for fileNo: {fileNo}",level="debug")
            #print("quality_value: ",quality_value)
            for cropped_frame in cropped_frames:
                image = Image.fromarray(cropped_frame)
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=int(quality_value), subsampling=0, optimize=True)
                jpeg_data_list.append(buffer.getvalue())
            
            ds.PixelData = encapsulate(jpeg_data_list)
            #ds.PixelData = b''.join(jpeg_data_list)  # Συνένωση όλων των encapsulated frames
            console_message(f"encapsulate finish for fileNo: {fileNo}",level="debug")
            
            #εφαρμογή σωστών τιμών στα tags
            ds.file_meta.TransferSyntaxUID = UID("1.2.840.10008.1.2.4.50") #εφαρμογή του Transfer Syntax UID  JPEG Baseline 1
            ds[0x0028, 0x2110] = DataElement(0x00282110, 'CS', "01")           #Lossy Image Compression 0 όχι / 1 ναί
            ds[0x0028, 0x2114] = DataElement(0x00282114, 'LO', "ISO_10918_1")  #Lossy Image Compression Method
            #ds[0x0028, 0x2112] = DataElement(0x00282112, 'DS', "5")            #για συμπίεση 85
            ds[0x0008, 0x0008].value = ["DERIVED", "SECONDARY", "LOSSY", "CROPPED", "COMPRESSED"]

        else:
            #άν δεν εφαρμόσω συμπίεση αλλάζω μόνο τις απαραιτητες τιμές στο tag 0008,0008
            ds[0x0008, 0x0008].value[0] = "DERIVED"
            ds[0x0008, 0x0008].value[1] = "SECONDARY"
            if transf_syntax == "Explicit VR Little Endian":
                cropped_frames_array = np.array(cropped_frames)
                ds.PixelData = cropped_frames_array.tobytes()#μετατροπή του πίνακα σε bytes
                ds.file_meta.TransferSyntaxUID = ds.file_meta.TransferSyntaxUID
                if ds.PhotometricInterpretation == "MONOCHROME2":
                    pass
                else:
                    ds.PhotometricInterpretation = "RGB"
                ds.is_implicit_VR = False

            elif transf_syntax == "Implicit VR Little Endian":
                cropped_frames_array = np.array(cropped_frames)
                ds.PixelData = cropped_frames_array.tobytes()#μετατροπή του πίνακα σε bytes
                ds.file_meta.TransferSyntaxUID = ds.file_meta.TransferSyntaxUID
                if ds.PhotometricInterpretation == "MONOCROME2":
                    pass
                else:
                    ds.PhotometricInterpretation = "RGB"
                ds.is_implicit_VR = True    

            elif transf_syntax != "Implicit VR Little Endian":#αν είναι δριαφορετικό του Implicit VR Little Endian
                #εφαρμόζει συμπίεση jpeg
                jpeg_data_list = []
                for cropped_frame in cropped_frames:
                    image = Image.fromarray(cropped_frame)
                    buffer = io.BytesIO()
                    image.save(buffer, format="JPEG", quality=85, subsampling=1, optimize=True)
                    jpeg_data_list.append(buffer.getvalue())
                ds.PixelData = encapsulate(jpeg_data_list)

        
        #ενημέρωση του dataset με τις νέες διαστάσεις
        ds.Rows, ds.Columns = cropped_frames[0].shape[:2]

        #Δημιουργία νέου MediaStorage SOP Instance UID
        new_MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        ds.file_meta.MediaStorageSOPInstanceUID = new_MediaStorageSOPInstanceUID
        #δημιουργει ίδιο με το SOPInstanceUID
        
        #Δημιουργία νέου SOP Instance UID
        new_sop_instance_uid = pydicom.uid.generate_uid()
        ds.SOPInstanceUID = new_sop_instance_uid

        #έλεγχος αν υπάρχει το tag (0002,0013)
        if (0x0002, 0x0013) in ds.file_meta:
            ds.file_meta[(0x0002, 0x0013)].value = f"PYDICOM {pydicom.__version__}"
        else:
            pass

        new_StudyInstanceUID = pydicom.uid.generate_uid()
        ds.StudyInstanceUID = new_StudyInstanceUID

        new_SeriesInstanceUID = pydicom.uid.generate_uid()
        ds.SeriesInstanceUID = new_SeriesInstanceUID

        #ds.remove_private_tags()
        try:
            #διαγραφή περιττών tags X0, Y0, X1, Y1
            sequence_element = ds[0x0018, 0x6011]
            sequence = sequence_element.value
            item = sequence[0]
            #del item[0x0018, 0x6018]
            #del item[0x0018, 0x601a]
            #del item[0x0018, 0x601c]
            #del item[0x0018, 0x601e]

            item[0x0018, 0x6018].value = 0
            item[0x0018, 0x601a].value = 0
            item[0x0018, 0x601c].value = crop_width
            item[0x0018, 0x601e].value = crop_height

        except Exception as e:
            console_message(f"sequence_element {e} not found",level="debug")
            
        #Λήψη των tags από την ενότητα tags_to_del του settings.ini
        tags_to_delete = []
        for key in config['tags_to_del']:
            tag = tuple(int(part.strip(), 16) for part in config['tags_to_del'][key].split(","))
            tags_to_delete.append(tag)

        #Διαγραφή των καθορισμένων tags
        for tag in tags_to_delete:
            if tag in ds:
                #print(ds[tag])#τα tags που διεγράφει
                del ds[tag]
                
        
        ds.remove_private_tags()
 
        global output_directory2
        #Αποθήκευση του νέου DICOM αρχείου
        output_filename = f"{output_directory}\\{files_folder}_{fileNo:04_}_{tag_value}.dcm"#με το :04 ορίζω 5 ψηφία και γεμίζω μπροστά με 0

        patient_s_ID = config['settings'].get('patient_s_ID', 'delete')
        if patient_s_ID == "delete":
            del ds[0x0010, 0x0020]
        else:
            ds.PatientID = f"{files_folder}_{fileNo:04_}_{tag_value}"
        
        ds.save_as(output_filename, enforce_file_format=True)
        #ds.save_as(output_filename, write_like_original=False)
        output_directory2 = output_directory

        #print(f"New cropped file saved as: {output_filename}")
        console_message(f"New cropped file saved as: {output_filename}",level="debug")
    except Exception as e:
        #print(f"Error anonymizing {file_path}: {str(e)}")
        console_message(f"anonymizing {file_path}: {str(e)}",level="error")
        
def zip_folder():
    #files_folder,το όνομα που θα πάρει τo zipped αρχείο
    #output_directory2, το πλήρες path του φακέλου που θα γίνει zip αρχείο
    global files_folder,output_directory2 
    save_zip_to = filedialog.askdirectory()
    if not save_zip_to:
        return
    
    try: 
        #το σημείο που θα αποθηκευθεί το αρχείο zip
        save_zip_to = os.path.normpath(save_zip_to)

        #prints for debug
        #print("Zip the folder:", files_folder)
        #print("Full path: ", output_directory2)
        #print("Save zip to", save_zip_to)
        
        zipped_file = os.path.join(save_zip_to, files_folder)
        zipped_file = os.path.normpath(zipped_file)
        #print("Folder to zip: ", folder_to_zip)
        
        shutil.make_archive(zipped_file, 'zip', output_directory2)
        
        console_message(f"created zip file: {zipped_file}.zip", level="debug")

        clear_anon_treeview()
        
        id_entry_entry.config(state="normal", text="")
        id_entry_entry.delete(0, "end")
        anonymize_button["state"] = "normal"
        
        #διαγραφή του temp file
        folder_pattern = files_folder
        for folder_name in os.listdir(output_path):
            if re.match(folder_pattern, folder_name):
                folder_to_del = os.path.join(output_path, folder_name)
                if os.path.isdir(folder_to_del):
                    shutil.rmtree(folder_to_del)
                    
        messagebox.showinfo("ZIP Export", "Export to ZIP completed.")
        
        #διαβάζω το σύνολο των αρχείων dicom που είναι στο output path
        file_count = sum(len(files) for _, _, files in os.walk(output_path))
        foot_label1.config(text=f"{file_count} files\nat temp folder")
        

    except Exception as e:
        console_message("failed to create zip file", level="error")
    
def del_forlders():
    clear_anon_treeview()
    for folder_name in os.listdir(output_path):
        folder_to_del = os.path.join(output_path, folder_name)
        # Ελέγχει αν είναι φάκελος
        if os.path.isdir(folder_to_del):
            # Διαγραφή του φακέλου και των περιεχομένων του
            shutil.rmtree(folder_to_del)

    id_entry_entry.config(state="normal", text="")
    id_entry_entry.delete(0, "end")
    anonymize_button["state"] = "normal"
    #διαβάζω το σύνολο των αρχείων dicom που είναι στο output path
    file_count = sum(len(files) for _, _, files in os.walk(output_path))
    foot_label1.config(text=f"{file_count} files\nat temp folder")
    messagebox.showinfo("Delete files", "Temp files deleted successfully")
  
def OnDoubleClick(event):
    treeview = event.widget#λαμβάνω όλο το treeview
    '''
    print("Widget info:", treeview)
    print("Widget ID:", str(treeview))
    print("Widget name:", treeview.winfo_name())
    '''
    
    if treeview == selected_files_treeview:
        source_stage_sel = "Selected files"
    elif treeview == ordered_files_treeview:
        source_stage_sel = "Ordered files"
    elif treeview == anonimyzed_files_treeview:
        source_stage_sel = "Anonymized files"
    else:
        source_stage_sel = ""#δε θα συμβεί ποτέ

    #print(source_stage_sel)
    #print(type(source_stage_sel))
    
    #selected_item = treeview.selection()
    selected_item = treeview.focus()   
    
    if selected_item:
        item_data = treeview.item(selected_item)
        #file_name = item_data['values'][0]
        #file_path = item_data['values'][1]
        preview_selected_file(treeview, source_stage_sel)

def open_manual():
    filename = "US-DICOMizer_manual.pdf"
    root_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(root_dir, filename)
    console_message(f"root_dir: {root_dir}", level="debug")
    console_message(f"pdf_path: {pdf_path}", level="debug")

    if not os.path.isfile(pdf_path):
        messagebox.showerror("Error", f"The file '{filename}' was not found.")
        return
    
    try:
        webbrowser.open_new(pdf_path)
    
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open the file '{filename}': {e}")
        console_message(f"Failed to open the file '{filename}': {e}", level="error")

def about():
    about_window = tk.Toplevel(root)
    about_window.title("About")
    about_window.iconbitmap(r'icon.ico')
    about_window.geometry("260x180")#Πλάτος x Ύψος

    about_frame = tk.Frame(about_window)# bg="#33A1C9"
    about_frame.grid(row=0, column=0, columnspan=4, sticky="nsew")

    about_label1 = ttk.Label(about_frame, text="This application was developed by\nPechlivanis Dimitrios", )
    about_label1.grid(padx=5, pady=0, column=0, row=0, sticky="w")

    email_label = tk.Label(about_frame, text="📧 pechlivanis.d@gmail.com",font=("Segoe UI", 10), fg="blue", cursor="hand2" )
    email_label.grid(padx=5, pady=0, column=0, row=1, sticky="w")
    email_label.bind("<Button-1>", lambda e: open_mail())

    about_label2 = ttk.Label(about_frame, text="\nIs open-source and available on GitHub at:", )
    about_label2.grid(padx=5, pady=0, column=0, row=2, sticky="w")
    

    link_github = tk.Label(about_frame, text="github.com/thrombusplus/US-DICOMizer\n",font=("Segoe UI", 10), fg="blue", cursor="hand2")
    link_github.grid(padx=5, pady=0, column=0, row=3, sticky="w")
    link_github.bind("<Button-1>", lambda e: open_web_link("https://github.com/thrombusplus/US-DICOMizer"))

    about_label3 = ttk.Label(about_frame, text="Is part of the ThrombUS+ project:", )
    about_label3.grid(padx=5, pady=0, column=0, row=4, sticky="w")

    link_thrombus = tk.Label(about_frame, text="thrombus.eu",font=("Segoe UI", 10), fg="blue", cursor="hand2")
    link_thrombus.grid(padx=5, pady=0, column=0, row=5, sticky="w")
    link_thrombus.bind("<Button-1>", lambda e: open_web_link("https://thrombus.eu/"))

def open_web_link(web_link_str):
    webbrowser.open_new_tab(web_link_str)

def open_mail():
    email = "pechlivanis.d@gmail.com"
    mailto_link = f"mailto:{email}"
    webbrowser.open(mailto_link)

           
windll.shcore.SetProcessDpiAwareness(0)
#Δημιουργία του βασικού παραθύρου της εφαρμογής
root = tk.Tk()
root.title("US-DICOMizer")
root.iconbitmap(r'icon.ico')
screen_width= root.winfo_screenwidth() 
screen_height= root.winfo_screenheight()
#setting tkinter window size
root.geometry("%dx%d" % (screen_width, screen_height - 50))

#Maximize the window using state property
root.state('zoomed')

# Εφαρμογή του στυλ στα κουμπιά
configure_style()

#διαγραφή των temp unzipped φακέλων σε κάθε εκκίνηση της εφαρμγής
del_unzipped_folders()

# Κατασκευή του menu bar
def menubar():
    root_menu = Menu()
    root.config(menu=root_menu)
    main_menu = Menu(root_menu, tearoff=False)
    root_menu.add_cascade(label="Menu", menu=main_menu)
    main_menu.add_command(label="Settings", command=settings)
    main_menu.add_command(label="App manual", command=open_manual)
    main_menu.add_command(label="About", command=about)
    main_menu.add_separator()
    main_menu.add_command(label="Exit", command=root.quit)

menubar()

#--- start --- Πλαίσιο για τον τίτλο του παραθύρου -----
frame_head = tk.Frame(root, bg="#33A1C9")
frame_head.grid(row=0, column=0, columnspan=4, sticky="nsew")

label_head = tk.Label(frame_head, text="US-DICOMizer (crop and anonymize ultrasound DICOM files)",
                      bg="#33A1C9",
                      font=("Segoe UI", 12))
label_head.pack()
#--- end --- Πλαίσιο για τον τίτλο του παραθύρου -----

#--- start --- Selected files Πλαίσιο για τη φόρτωση του αρχείου ή του φακέλου ---
frame_0 = tk.LabelFrame(root, text="Selected files")#, bg="#FEE5EE"
frame_0.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
# Ρύθμιση του row και column του frame_1 ώστε να μπορεί να επεκτείνεται δυναμικά
'''
frame_0.grid_rowconfigure(0, weight=0)  # Επιτρέπει στον πρώτο row να επεκταθεί
frame_0.grid_rowconfigure(1, weight=0)  # Ο δεύτερος row δεν επεκτείνεται
frame_0.grid_columnconfigure(0, weight=0)  # Επιτρέπει στον πρώτο column να επεκταθεί
frame_0.grid_columnconfigure(1, weight=0)  # Επιτρέπει στον δεύτερο column να επεκταθεί
'''
sub_frame_0_L = tk.Frame(frame_0)#, bg="#66CD00"
sub_frame_0_L.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
#sub_frame_0_L.grid_propagate(False)  # Απενεργοποιούμε την προσαρμογή μεγέθους βάσει περιεχομένου
'''
sub_frame_0_L.grid_rowconfigure(0, weight=0)  # Προσθέτουμε weight για να επεκτείνεται
sub_frame_0_L.grid_columnconfigure(0, weight=0)  # Προσαρμογή του minsize
'''

#Treeview για την εμφάνιση των ονομάτων των αρχείων
selected_files_treeview = ttk.Treeview(sub_frame_0_L, columns=("DICOM files","Path",), show="headings",
                                 selectmode="browse", height=18)
selected_files_treeview.heading("DICOM files", text="DICOM files")
selected_files_treeview.column("DICOM files", width=150)
selected_files_treeview.column("Path", width=0, stretch=tk.NO)
selected_files_treeview.bind("<Double-1>", OnDoubleClick)
selected_files_treeview.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
#selected_files_treeview.pack(padx=5, pady=5, side="left", fill="both")

# δημιουργία του scrollbar
tree1_scrollbar = tk.Scrollbar(sub_frame_0_L,
                                   orient="vertical", command=selected_files_treeview.yview)
tree1_scrollbar.grid(row=0, column=1, sticky="ns")
#tree1_scrollbar.pack(side="right", fill="y")
# σύνδεση του scrollbar με το Treeview
selected_files_treeview.configure(yscrollcommand=tree1_scrollbar.set)

sub_frame_0_R = tk.Frame(frame_0)#, bg="#8EE5EE"
sub_frame_0_R.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
#sub_frame_0_R.grid_rowconfigure(0, weight=1)  # Προσθέτουμε weight για να επεκτείνεται
#sub_frame_0_R.grid_columnconfigure(0, weight=1)  # Προσαρμογή του minsize
#sub_frame_0_R.grid_propagate(False)

button_load_file = ttk.Button(sub_frame_0_R, text="Load Single\nDICOM File", command=load_file, style='small.TButton')
button_load_file.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

button_load_folder = ttk.Button(sub_frame_0_R, text="Load DICOM\nFolder", command=load_folder, style='smal.TButton')
button_load_folder.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

button_load_zip = ttk.Button(sub_frame_0_R, text="Load\nDICOM .zip", command=load_zip_and_display, style='small.TButton')
button_load_zip.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

button_add = ttk.Button(sub_frame_0_R, text="Add ->", command=add_selected_file_to_ordered, width=10, style='small.TButton')
button_add.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")

source_stage_sel = "Selected files"
button_preview1 = ttk.Button(sub_frame_0_R, text="Preview",
                             command=lambda: preview_selected_file(selected_files_treeview,source_stage_sel),
                             width=10, style='preview.TButton')
button_preview1.grid(row=4, column=0, padx=5, pady=5, sticky="nsew")

button_clear = ttk.Button(sub_frame_0_R, text="Clear", command=clear_treeview, width=10, style='clear.TButton')
button_clear.grid(row=5, column=0, padx=5, pady=5, sticky="nsew")
#--- end --- Selected files Πλαίσιο για τη φόρτωση του αρχείου ή του φακέλου -----

#--- start --- Ordered files  Πλαίσιο με τα επιλεγμένα αρχεια προς ταξινόμηση ---
frame_1 = tk.LabelFrame(root, text="   Ordered files")#, bg="#FEE5EE"
frame_1.grid(row=1, column=1, padx=0, pady=0, sticky="nsew")
# Ρύθμιση του row και column του frame_1 ώστε να μπορεί να επεκτείνεται δυναμικά
'''
frame_1.grid_rowconfigure(0, weight=0)  # Επιτρέπει στον πρώτο row να επεκταθεί
frame_1.grid_rowconfigure(1, weight=0)  # Ο δεύτερος row δεν επεκτείνεται
frame_1.grid_columnconfigure(0, weight=0)  # Επιτρέπει στον πρώτο column να επεκταθεί
frame_1.grid_columnconfigure(1, weight=0)  # Επιτρέπει στον δεύτερο column να επεκταθεί
'''
sub_frame_1_L = tk.Frame(frame_1)#, bg="#66CD00"
sub_frame_1_L.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
#sub_frame_1_L.grid_propagate(False)  # Απενεργοποιούμε την προσαρμογή μεγέθους βάσει περιεχομένου

button_up = ttk.Button(sub_frame_1_L, text="Up", command=move_up,
                       style='small.TButton', width=5)
button_up.grid(row=0, column=0, padx=3, pady=45, sticky="nsew")

button_down = ttk.Button(sub_frame_1_L, text="Down", command=move_down,
                         style='small.TButton', width=5)
button_down.grid(row=1, column=0, padx=3, pady=10, sticky="nsew")

button_remove = ttk.Button(sub_frame_1_L, text="<-\nRemove",
                           command=from_ordered_to_selected_file,
                           style='small.TButton',
                           width=7)
button_remove.grid(row=2, column=0, padx=3, pady=5, sticky="s")#,sticky="nsew"

'''
button_delete = ttk.Button(sub_frame_1_L, text="Del",
                           command=None,
                           style='small.TButton',
                           width=5)
button_delete.grid(row=3, column=0, padx=3, pady=5, sticky="s")#,sticky="nsew"
'''
source_stage_ord = "Ordered files"
button_preview2 = ttk.Button(sub_frame_1_L, text="Preview",
                             command=lambda: preview_selected_file(ordered_files_treeview, source_stage_ord),
                             width=7, style='preview.TButton')
button_preview2.grid(row=4, column=0, padx=3, pady=5,sticky="nsew")

sub_frame_1_R = tk.Frame(frame_1)#, bg="#8EE5EE"
sub_frame_1_R.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
#sub_frame_1_R.grid_rowconfigure(0, weight=1)  # Προσθέτουμε weight για να επεκτείνεται
sub_frame_1_R.grid_columnconfigure(0, weight=0)  # Προσαρμογή του minsize

#Treeview για την εμφάνιση των ονομάτων των αρχείων
ordered_files_treeview = ttk.Treeview(sub_frame_1_R, columns=("DICOM files","path","tag", "x0", "y0", "x1", "y1", "num_of_frames", "applied"), show="headings",
                                  selectmode="browse", height=18)
ordered_files_treeview.heading("DICOM files", text="DICOM files")
ordered_files_treeview.column("DICOM files", width=115)
#ordered_files_treeview.heading("path", text="path")
ordered_files_treeview.column("path", width=0, stretch=tk.NO)
ordered_files_treeview.heading("tag", text="tag")
ordered_files_treeview.column("tag", width=45)
ordered_files_treeview.column("x0", width=0, stretch=tk.NO)
ordered_files_treeview.column("y0", width=0, stretch=tk.NO)
ordered_files_treeview.column("x1", width=0, stretch=tk.NO)
ordered_files_treeview.column("y1", width=0, stretch=tk.NO)
ordered_files_treeview.column("num_of_frames", width=0, stretch=tk.NO)
ordered_files_treeview.column("applied", width=0, stretch=tk.NO)

ordered_files_treeview.bind("<Double-1>", OnDoubleClick)
ordered_files_treeview.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
#--- end --- Ordered files Πλαίσιο με τα επιλεγμένα αρχεια προς ταξινόμηση -----

# δημιουργία του scrollbar
tree2_scrollbar = tk.Scrollbar(sub_frame_1_R,
                                   orient="vertical", command=ordered_files_treeview.yview)
tree2_scrollbar.grid(row=0, column=1, sticky="ns")
# σύνδεση του scrollbar με το Treeview
ordered_files_treeview.configure(yscrollcommand=tree2_scrollbar.set)

#--- start --- Πλαίσιο για την προβολή DICOM preview ---
frame_2 = tk.LabelFrame(root, text="Image preview")#, bg="#FFF5EE"
frame_2.grid(row=1, column=2, rowspan=3, padx=5, pady=0, sticky="nsew")
frame_2.grid_rowconfigure(0, weight=1)  #επεκτίνει το περιεχόμενο του frame_2 προς τα κάτω
frame_2.grid_columnconfigure(0, weight=1)
frame_2.grid_propagate(0)
#--- end --- Πλαίσιο για την DICOM preview ---

#--- start --- Πλαίσιο για τα attributes του DICOM ---
frame_3 = tk.LabelFrame(root, text="DICOM Attributes", labelanchor="n")#, bg="#F0F8FF"
frame_3.grid(row=1, column=3, rowspan=3, padx=5, pady=0, sticky="nsew")
frame_3.grid_rowconfigure(0, weight=1)
frame_3.grid_columnconfigure(0, weight=1)
frame_3.grid_propagate(0)
#--- end --- Πλαίσιο για τα attributes του DICOM ---

#--- start --- Πλαίσιο πριν την ανωνυμοποιηση ---
frame_0_1 = tk.LabelFrame(root, text="Actions")#, bg="#F0F8FF"
frame_0_1.grid(row=3, column=0, padx=5, pady=0, sticky="nsew")
#frame_0_1.grid_rowconfigure(0, weight=0)  #το πρώτο row δεν επεκτείνεται
#frame_0_1.grid_rowconfigure(1, weight=0)  #το δευτερο row δεν επεκτείνεται
#frame_0_1.grid_columnconfigure(0, weight=1)  #επιτρέπει στον πρώτο column να επεκταθεί
frame_0_1.grid_columnconfigure(1, weight=1)  #επιτρέπει στον δεύτερο column να επεκταθεί
#frame_0_1.grid_propagate(False)

'''
frame_0_1.grid_propagate(0 ή 1)

grid_propagate(0) το frame διατηρεί το μέγεθός του ανεξάρτητα από το μέγεθος των widgets που περιέχει,
δεν αλλάζει μέγεθος αυτόματα σύμφωνα με τα περιεχόμενα.

grid_propagate(1) το frame προσαρμόζεται στο μέγεθος των widgets που περιέχει,
αλλάζει μέγεθος αυτόματα ανάλογα με τα widgets μέσα στο frame.
αν δε το ορίσω απο default έχει τιμή 1, παίζει και με True-False
'''

id_entry_label = tk.Label(frame_0_1, text="Patient's ID")
id_entry_label.grid(row=0, column=0, padx=5, pady=0, sticky="nsew")
id_entry_entry = ttk.Entry(frame_0_1, text="ID")
id_entry_entry.grid(row=0, column=1, padx=5, pady=0, sticky="nsew")

save_path_text = ScrolledText(frame_0_1, height=2, width=28, wrap=tk.WORD)
save_path_text.grid(row=1, column=0, columnspan=2, padx=5, pady=5,  sticky="w")
save_path_text.insert(tk.END, output_path)
save_path_text.configure(state='disabled')

#save_path_label = tk.Label(frame_0_1, text=f"Save to: {output_path}")
#save_path_label.grid(row=1, column=0, padx=5, pady=5,  sticky="w")

anonymize_button = ttk.Button(frame_0_1, text="Anonymize Loaded images <F8>", style="anon.TButton",
                        command=anonymize_selected_files)
anonymize_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="sew")

#-----start-------------- frame_1_1 Anonymized Πλαίσιο ---------------------------
frame_1_1 = tk.LabelFrame(root, text="Anonymized DICOM files")#, bg="#F0F8FF"
frame_1_1.grid(row=3, column=1, padx=5, pady=0, sticky="nsew")
#frame_1_1.grid_propagate(False)
#frame_1_1.grid_rowconfigure(0, weight=0)
#frame_1_1.grid_rowconfigure(1, weight=0)
#frame_1_1.grid_columnconfigure(0, weight=0)
#frame_1_1.grid_columnconfigure(1, weight=0)

anonimyzed_files_treeview = ttk.Treeview(frame_1_1, columns=("DICOM files",), show="headings",
                                  selectmode="browse", height=14)
anonimyzed_files_treeview.heading("DICOM files", text="DICOM files")
anonimyzed_files_treeview.column("DICOM files", width=130)
anonimyzed_files_treeview.bind("<Double-1>", OnDoubleClick)
anonimyzed_files_treeview.grid(row=0, column=0,
                               rowspan=3,
                               padx=5, pady=5, sticky="nsew")

#κατασκευή των scrollbars
tree3_scrollbar_v = tk.Scrollbar(frame_1_1,
                                   orient="vertical", command=anonimyzed_files_treeview.yview)
tree3_scrollbar_v.grid(row=0, column=1,rowspan=3, sticky="ns")
# σύνδεση του scrollbar με το Treeview
anonimyzed_files_treeview.configure(yscrollcommand=tree3_scrollbar_v.set)

'''
tree3_scrollbar_h = tk.Scrollbar(frame_1_1, orient="horizontal",
                                         command=anonimyzed_files_treeview.xview)  
tree3_scrollbar_h.grid(row=3, column=0, columnspan=2, sticky="ew")

anonimyzed_files_treeview.configure(xscrollcommand=tree3_scrollbar_h.set)
'''

source_stage_anon = "Anonymized files"
button_preview = ttk.Button(frame_1_1, text="Preview",
                            command=lambda: preview_selected_file(anonimyzed_files_treeview,source_stage_anon),
                            width=8,style='preview.TButton')
button_preview.grid(row=0, column=2, padx=5, pady=5, sticky="sew")

zip_button = ttk.Button(frame_1_1, text="Export to\nZIP files", style="small.TButton",
                        command=lambda: zip_folder(), width=8)
zip_button.grid(row=1, column=2, padx=5, pady=5, sticky="sew")

button_clear2 = ttk.Button(frame_1_1, text="Clear", command=clear_anon_treeview2, width=10, style='clear.TButton')
button_clear2.grid(row=2, column=2, padx=5, pady=5, sticky="sew")
#-----end-------------- frame_1_1 Anonymized Πλαίσιο ---------------------------

#--- start --- Πλαίσιο για το footer ---
frame_footer = tk.Frame(root, padx=0, pady=0, bg="#00d0c0")
frame_footer.grid(row=4, column=0, columnspan=4, sticky="ew")

#διαβάζω το σύνολο των αρχείων dicom που είναι στο output path
file_count = sum(len(files) for _, _, files in os.walk(output_path))

foot_label1 = tk.Label(frame_footer, text=f"{file_count} files\nat temp folder", font=("Segoe UI", 8), bg="#00d0c0")
foot_label1.grid(padx=5, row=0, column=0, sticky="w")

delete_button1 = ttk.Button(frame_footer, text="Delete files", style="small.TButton", command=lambda: del_forlders())
delete_button1.grid(padx=5, row=0, column=2, sticky="w")

ver_label = tk.Label(frame_footer, text=f"ver: {version}", bg="#00d0c0")
ver_label.grid(padx=5, row=0, column=3, sticky="w")

log_label = tk.Label(frame_footer, text=f"Console\nlog", bg="#00d0c0")
log_label.grid(padx=5, row=0, column=4, sticky="e")

console = ScrolledText(frame_footer, font=("Segoe UI", 8), wrap="word", height=3)
console.grid(row=0, column=5, sticky="w")
#redirected = Consoleredirect(console)
#sys.stdout = redirected

free_label = tk.Label(frame_footer, text="Free\ntext", font=("Segoe UI", 8), bg="#00d0c0")
free_label.grid(padx=5, row=0, column=6, sticky="e")

freetext = ScrolledText(frame_footer, font=("Segoe UI", 8), wrap="word", height=3)
freetext.grid(row=0, column=7, sticky="w")

#--- end --- Πλαίσιο για το footer ---

'''
#--- start --- Πλαίσιο για το console log ---
console_log_frame = tk.LabelFrame(root, padx=5, pady=5, text="Console log")
console_log_frame.grid(row=5, column=0, columnspan=4, sticky="ew")
console_log_frame.grid_propagate(1)
console = tk.Text(console_log_frame, font=("Segoe UI", 10), wrap="word")
console.grid(row=0, column=0)#, sticky="w"
#redirected = Consoleredirect(console)
#sys.stdout = redirected
'''

# Ρύθμιση του grid για να προσαρμόζεται δυναμικά το παράθυρο
root.grid_columnconfigure(0, weight=0)#, minsize=50
root.grid_columnconfigure(1, weight=0)#, minsize=50
root.grid_columnconfigure(2, weight=1)
root.grid_columnconfigure(3, weight=1)
#root.grid_rowconfigure(1, weight=1)
#root.grid_rowconfigure(2, weight=1)
# Εμφάνιση του παραθύρου

#root.bind("<F12>",quit)
root.bind("<F9>",lambda event: zip_folder())
root.bind("<F8>",lambda event: anonymize_selected_files())
root.bind("<F6>",lambda event: add_all_from_selected_file_to_ordered())
root.bind("<Prior>",lambda event: move_up())
root.bind("<Next>",lambda event: move_down())

logger.info('loaded all functions successfully')
root.mainloop()
