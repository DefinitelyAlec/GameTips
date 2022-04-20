from tkinter import *
import easyocr
import webbrowser
import threading
import psycopg2
import pyautogui
import numpy as np
from PIL import Image, ImageTk, ImageGrab

def connectAndQuery(query):
    #Database stuff
    listToReturn = None
    try:
        print("Connected.")
        connection = psycopg2.connect(user="anyone", password="teamgametips",\
             host = "database-1.cgpwhtgqxogz.us-west-1.rds.amazonaws.com", port = 5432, database = "teamgametipsdb")
        cursor = connection.cursor()

        cursor.execute(query)
        listToReturn = cursor.fetchall()
        if connection:
            print("Closing connection.")
            cursor.close()
            connection.close()
    except:
        print("Database failure.")
    return listToReturn

#Create an instance of tkinter window or frame
win = Tk()

#Setting the geometry of window
win.geometry("600x350")

#Create a Label
titleText = StringVar() # this datatype is from tkinter
titleText.set("Welcome to Intuitive Intel!")
tipText = StringVar()
tipText.set("")
Label(win, textvariable = titleText,font=('Helvetica bold', 15)).pack(pady=20)

#Create our website
webSiteLink = StringVar()
webSiteLink.set("https://utah.instructure.com/groups/425595")

#Make the window jump above all
win.attributes('-topmost',True)

global img
global canvas
canvas = Canvas(win, width = 1000, height = 100)

#TODO: don't hardcode, read in as option from game database
maps = []
for value in connectAndQuery("SELECT * FROM Valorant_Map_Table"):
    maps.append(value[0])

def screenshot():
    global img
    global canvas
    #display code, not screenshot
    # display image(s)
    canvas.pack_forget() # it stacks and falls lower and lower without this
    canvas = Canvas(win, width = 1920, height = 1080)
    canvas.pack()
    img = pyautogui.screenshot()
    img = ImageTk.PhotoImage(img)
    canvas.create_image(10,10,anchor = NW, image = img)


def getTip(mapName):
    listOfTips = connectAndQuery("SELECT content, userid FROM tip_table WHERE mapname = '" + mapName + "'")
    # TODO: Change up how we are selecting a tip.
    return listOfTips.pop()[0]


def ocrStuff():
    global img
    #Initialize stuff
    print("waiting for match...")
    reader = easyocr.Reader(['en'])

    #Search until we find a map
    foundMap = False 
    resultMap = None
    
    while not foundMap:
        print("map not found, looping")
        img = pyautogui.screenshot()
        numpyVersion = np.array(img)
        readerResult = reader.readtext(numpyVersion, detail = 0)
        for text in readerResult:
            for map in maps:
                if text == map:
                    foundMap = True
                    resultMap = map
                    break
        if thread._is_stopped:
            print("thread successfully cancelled")
            return
    print(resultMap)
    cancelSearchButton["state"] = "disabled"
    findingMatchButton["state"] = "active"
    titleText.set("Map found: " + resultMap + "\nTip: " + getTip(resultMap))
    
    return resultMap


def findMatch():
    global thread
    cancelSearchButton["state"] = "active"
    findingMatchButton["state"] = "disabled"
    if thread._started:
        thread = threading.Thread(target = ocrStuff, args = ())
        thread.start()

def goToSite():
    print("redirecting to site...")
    webbrowser.open(webSiteLink.get(), new=1)

def cancelMatch():
    global thread
    print("cancelling match")
    thread._is_stopped = True
    cancelSearchButton["state"] = "disabled" 
    findingMatchButton["state"] = "active"

# add buttons
findingMatchButton = Button(win, text = "finding a match!", fg = "green",
                        command = findMatch)
findingMatchButton.pack()

moreInfoButton = Button(win, text = "click for our website", fg = "black",
                        command = goToSite)
moreInfoButton.pack()

cancelSearchButton = Button(win, text = "cancel search", fg = "red",
                        command = cancelMatch)
cancelSearchButton.pack()
cancelSearchButton["state"] = "disabled"

# for testing, will put this in a loop after pressing findingMatchButton
screenshotButton = Button(win, text = "take a screenshot", fg = "black",
                        command = screenshot)
screenshotButton.pack()

thread = threading.Thread(target = ocrStuff, args = ())
thread._stop = threading.Event()

win.mainloop()
exit(0)
