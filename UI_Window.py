from tkinter import *
import easyocr
import webbrowser
import threading
import psycopg2

#Create an instance of tkinter window or frame
win = Tk()

#Setting the geometry of window
win.geometry("600x350")

#Create a Label
titleText = StringVar() # this datatype is from tkinter
titleText.set("Welcome to Intuitive Intel!")
Label(win, textvariable = titleText,font=('Helvetica bold', 15)).pack(pady=20)

#Create our website
webSiteLink = StringVar()
webSiteLink.set("https://utah.instructure.com/groups/425595")

#Make the window jump above all
win.attributes('-topmost',True)

#TODO: don't hardcode, read in as option from game database
try:
    connection = psycopg2.connect(user="misago", password="misago", host="127.0.0.1", port="5432", database="misago")
    cursor = connection.cursor()
    cursor.execute("select * from Valorant_Map_Table")
    maps = []
    for value in cursor.fetchall():
        maps.append(value[0])
    cursor.close()
    connection.close()
except:
    print("Failed to connect to Database.")


def ocrStuff():
    #Initialize stuff
    print("waiting for match...")
    reader = easyocr.Reader(['en'])

    #Search until we find a map
    foundMap = False 
    while not foundMap:
        result = reader.readtext('bind.jpg', detail = 0)
        for res in result:
            for map in maps:
                if res == map:
                    foundMap = True
                    result = map
                    break
        if thread._is_stopped:
            print("thread successfully cancelled")
            return
    print(result)
    cancelSearchButton["state"] = "disabled"
    findingMatchButton["state"] = "active"
    titleText.set("Map found: " + result)
    try:
        connection = psycopg2.connect(user="misago", password="misago", host="127.0.0.1", port="5432", database="misago")
        cursor = connection.cursor()
        cursor.execute("select tipID, content from Tip_Table where mapName = \'" + result + "\'")
        print(cursor.fetchall())
        cursor.close()
        connection.close()
    except:
        print("Failed to connect to database.")
    return result


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

thread = threading.Thread(target = ocrStuff, args = ())
thread._stop = threading.Event()

win.mainloop()
