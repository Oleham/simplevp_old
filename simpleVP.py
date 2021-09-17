from tkinter import *
from tkcalendar import Calendar,DateEntry
from PIL import ImageTk, Image
import filehandling, sQLiteClass
import os, datetime

class Checkkolonne(Frame):
   #The IntVar objects contains the on/off states of the checklist.
   #The picks list contains the text of the checkbox at index [0].
   def __init__(self, parent=None, picks=[], side=TOP, anchor=W):
      Frame.__init__(self, parent)
      self.vars = []
      self.chk_list = []
      self.icon_list = []
      for i, pick in enumerate(picks):
         
         #Variable elements (saved in self.vars)
         #Checkbutton elements (saved in self.chk.list)
         var = IntVar()
         if pick[2] == "DISABLED":
            chk = Checkbutton(self, text=pick[0], variable=var, state=DISABLED)
         else:
            chk = Checkbutton(self, text=pick[0], variable=var)
         chk.grid(row=i, column=1, sticky="W")
         self.chk_list.append(chk)
         self.vars.append(var)
         
         #Icons on the left column (saved in self.icon_list)
         if pick[2] == "DELIEVERED":
            left_icon = ImageTk.PhotoImage(Image.open(os.path.join(PATH, "img", "delievered-icon.gif")))
            icon_label = Label(self, image=left_icon)
            icon_label.image = left_icon
            icon_label.grid(row=i, column=0)
         elif pick[2] == "DOWN":
            left_icon = ImageTk.PhotoImage(Image.open(os.path.join(PATH, "img", "down-icon.gif")))
            icon_label = Label(self, image=left_icon)
            icon_label.image = left_icon
            icon_label.grid(row=i, column=0)
         elif pick[2] == "UP":
            left_icon = ImageTk.PhotoImage(Image.open(os.path.join(PATH, "img", "up-icon.gif")))
            icon_label = Label(self, image=left_icon)
            icon_label.image = left_icon
            icon_label.grid(row=i, column=0)
         else:
            icon_label = Label(self)
            icon_label.grid(row=i, column=0)
         self.icon_list.append(icon_label)
   
   def update_table(self, flag):     
      if flag == "DOWN":
         for i, var in enumerate(self.vars):
            if var.get() == 1:
               new_icon = ImageTk.PhotoImage(Image.open(os.path.join(PATH, "img", "down-icon.gif")))
               self.icon_list[i].config(image=new_icon)
               self.icon_list[i].image= new_icon
      
      if flag == "UP":
         for i, var in enumerate(self.vars):
            if var.get() == 1:
               new_icon = ImageTk.PhotoImage(Image.open(os.path.join(PATH, "img", "up-icon.gif")))
               self.icon_list[i].config(image=new_icon)
               self.icon_list[i].image = new_icon

   def checkJobs(self):
      tbDownloaded = []
      for i, var in enumerate(self.vars):
         if var.get() == 1:
            tbDownloaded.append(jobStrList[i][1])
      return tbDownloaded

def update_database():     
   resp = simpleVPDB.update(e1.get(), e2.get(), e3.get())
   if resp != None:
      nyttVindu = Toplevel()
      prompt = Label(nyttVindu, text=(resp + "\n\nTips: Har du husket å skrive inn riktig passord?")).pack(padx=5, pady=5)

def makeCheckList():
   global lng
   global jobStrList 

   jobStrList = simpleVPDB.show_todays_jobs(str(calendarEntry.get_date())) 
   try:
      lng.grid_forget()
   except NameError:
      pass

   lng = Checkkolonne(root, picks=jobStrList)
   lng.grid(row=1, columnspan=3, sticky=W)
   lng.config(bd=3)

def makeCheckListAllJobs():
   global lng
   global jobStrList 

   jobStrList = simpleVPDB.show_todays_jobs(str(calendarEntry.get_date()), show_all_jobs=True) 
   try:
      lng.grid_forget()
   except NameError:
      pass

   lng = Checkkolonne(root, picks=jobStrList)
   lng.grid(row=1, columnspan=3, sticky=W)
   lng.config(bd=3)

def download():
   tbDownloaded = lng.checkJobs()
   lng.update_table("DOWN")
   filehandling.downloadJobs(tbDownloaded, e1.get(), e2.get(), e3.get(), e4.get().encode('unicode-escape').decode())
   simpleVPDB.add_to_Nedlastinger(tbDownloaded)

def upload():
   tbDownloaded = lng.checkJobs()
   lng.update_table("UP")
   filehandling.uploadJobs(tbDownloaded, e1.get(), e2.get(), e3.get(), e4.get().encode('unicode-escape').decode())
   simpleVPDB.update_Nedlastinger_with_ultime(tbDownloaded)

if __name__ == '__main__':

   #Database-object for å kommunisere med database
   simpleVPDB = sQLiteClass.Database()

   PATH = os.path.dirname(__file__)

   #Root
   root = Tk()
   root.title("simpleVP 2.0")
   windowIcon = PhotoImage(file=os.path.join(PATH, "img", "bob-omb.gif"))
   root.iconphoto(False, windowIcon)

   #Logo
   img = ImageTk.PhotoImage(Image.open(os.path.join(PATH, "img", "logo.gif")))
   canvas = Label(root, image = img)
   canvas.grid(row=0, columnspan=3)

   #Inntastingsfelt
   Label(root, text="XTRF").grid(row=2, column=0)
   Label(root, text="E-mail").grid(row=3, column=0)
   Label(root, text="Password").grid(row=4, column=0) #<-- Bruk .get metode for å hente ut teksten.
   Label(root, text="PPF Directory").grid(row=5, column=0)
   Label(root, text="TPF Directory").grid(row=6, column=0)
   e1 = Entry(root, width=70)
   e2 = Entry(root, width=70)
   e3 = Entry(root, show="*", width=70)
   e4 = Entry(root, width=70)
   e5 = Entry(root, width=70)
   e1.insert(END, os.environ.get("VENDOR_XTRF", "End point"))
   e2.insert(END, os.environ.get("VENDOR_EMAIL", "Email"))
   e3.insert(END, os.environ.get("VENDOR_PW", "Password"))
   e4.insert(END, os.environ.get("VENDOR_PPF", "PPF Directory"))
   e5.insert(END, os.environ.get("VENDOR_TPF", "TPF Directory"))
   e1.grid(row=2, column=1, columnspan=2)
   e2.grid(row=3, column=1, columnspan=2)
   e3.grid(row=4, column=1, columnspan=2)
   e4.grid(row=5, column=1, columnspan=2)
   e5.grid(row=6, column=1, columnspan=2)
   
   #CalendarEntry
   TODAY = datetime.date.today()
   calendarEntry = DateEntry(root,width=30,bg="white",fg="white",year=int(TODAY.strftime("%Y")), day=int(TODAY.strftime(r"%d")), month=int(TODAY.strftime("%m")))
   calendarEntry.grid(row=7, column=0)

   #Buttons
   Button(root, text="See PPF jobs", command=makeCheckList).grid(row=7, column=1)
   Button(root, text='Download', command=download).grid(row=8, column=1)
   Button(root, text='Quit', command=root.quit).grid(row=9, column=1)
   Button(root, text='See all jobs', command=makeCheckListAllJobs).grid(row=7, column=2)
   Button(root, text='Upload', command=upload).grid(row=8, column=2)
   updateBtnImg = ImageTk.PhotoImage(Image.open(os.path.join(PATH, "img" ,"update.gif")))
   Button(root, image=updateBtnImg, command=update_database).grid(row=9, column=2)
   

   root.mainloop()

   simpleVPDB.close()
