from argparse import Action
from tkinter import *
import easyocr
import webbrowser
import threading
import psycopg2
import pyautogui
import numpy as np
import urllib.request
from PIL import Image, ImageTk, ImageGrab

win = Tk()

#Setting the geometry of window
win.geometry("800x450")

def buttonMethod():
    print("button pressed!")
    for button in buttons:
        button.pack_forget()

buttons = []

myButton = Button(win, text = "button", fg = "green",
                        command = buttonMethod)
buttons.append(myButton)

setStr = StringVar()
strs = ["1", "2", "3"]

dropMenu = OptionMenu(win, setStr, *strs)
buttons.append(dropMenu)

setStr2 = StringVar()
strs2 = ["1", "2", "3"]

dropMenu2 = OptionMenu(win, setStr2, *strs2)
buttons.append(dropMenu2)

for button in buttons:
    print(button)
    button.pack()

win.mainloop()
exit(0)