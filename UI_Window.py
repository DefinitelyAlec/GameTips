
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

currState = "selecting game"

# for any new button, pack when it should be there, and pack_forget in all others
def setState(newState):
    global currState
    currState = newState
    if newState == "selecting game":
        findingMatchButton.pack_forget()
        matchMissedButton.pack_forget()
        moreInfoButton.pack()
        moreInfoButton["state"] = ACTIVE
        cancelSearchButton.pack_forget()
        confirmMapButton.pack_forget()
        confirmGameButton.pack()
        confirmGameButton["state"] = DISABLED # starts disabled in this state, wait until an option is selected in dropgame via trace
        selectGameButton.pack_forget()
        matchOverButton.pack_forget()
        confirmSkillLevelButton.pack_forget()
        confirmCharButton.pack_forget()
        createTipButton.pack()
        createTipButton["state"] = DISABLED
        inputTitle.pack_forget()
        inputTipText.pack_forget()
        postTipButton.pack_forget()
        quitMakingTipsButton.pack_forget()

        dropGame.pack()
        dropMap.pack_forget()
        dropSkill.pack_forget()
        dropCharacter.pack_forget()
        canvas.pack_forget()

    elif newState == "waiting in menu":
        findingMatchButton.pack()
        findingMatchButton["state"] = ACTIVE
        matchMissedButton.pack_forget()
        moreInfoButton.pack()
        moreInfoButton["state"] = ACTIVE
        cancelSearchButton.pack_forget()
        confirmMapButton.pack_forget()
        confirmGameButton.pack_forget()
        selectGameButton.pack()
        selectGameButton["state"] = ACTIVE
        matchOverButton.pack_forget()
        confirmSkillLevelButton.pack()
        confirmSkillLevelButton["state"] = DISABLED
        confirmCharButton.pack()
        confirmCharButton["state"] = DISABLED
        createTipButton.pack()
        inputTitle.pack_forget()
        inputTipText.pack_forget()
        postTipButton.pack_forget()
        quitMakingTipsButton.pack_forget()

        dropGame.pack_forget()
        dropMap.pack_forget()
        dropSkill.pack()
        dropCharacter.pack()
        canvas.pack_forget()

    elif newState == "waiting in queue":
        findingMatchButton.pack()
        findingMatchButton["state"] = DISABLED
        matchMissedButton.pack()
        matchMissedButton["state"] = ACTIVE
        moreInfoButton.pack()
        moreInfoButton["state"] = ACTIVE
        cancelSearchButton.pack()
        cancelSearchButton["state"] = ACTIVE
        confirmMapButton.pack_forget()
        confirmGameButton.pack_forget()
        selectGameButton.pack_forget()
        matchOverButton.pack_forget()
        confirmSkillLevelButton.pack()
        confirmSkillLevelButton["state"] = DISABLED
        confirmCharButton.pack()
        createTipButton.pack_forget()
        inputTitle.pack_forget()
        inputTipText.pack_forget()
        postTipButton.pack_forget()
        quitMakingTipsButton.pack_forget()

        dropGame.pack_forget()
        dropMap.pack_forget()
        dropSkill.pack()
        dropCharacter.pack_forget()
        canvas.pack_forget()

    elif newState == "map missed":        
        findingMatchButton.pack()
        findingMatchButton["state"] = DISABLED
        matchMissedButton.pack()
        matchMissedButton["state"] = ACTIVE
        moreInfoButton.pack()
        moreInfoButton["state"] = ACTIVE
        cancelSearchButton.pack()
        cancelSearchButton["state"] = DISABLED
        confirmMapButton.pack()
        confirmMapButton["state"] = DISABLED # same deal as confirm game button
        confirmGameButton.pack_forget()
        selectGameButton.pack_forget()
        matchOverButton.pack_forget()
        confirmSkillLevelButton.pack()
        confirmSkillLevelButton["state"] = DISABLED
        confirmCharButton.pack()
        createTipButton.pack_forget()
        inputTitle.pack_forget()
        inputTipText.pack_forget()
        postTipButton.pack_forget()
        quitMakingTipsButton.pack_forget()
        
        dropGame.pack_forget()
        dropMap.pack()
        dropSkill.pack()
        dropCharacter.pack()
        canvas.pack_forget()

    elif newState == "in a match":
        findingMatchButton.pack_forget()
        matchMissedButton.pack_forget()
        moreInfoButton.pack()
        moreInfoButton["state"] = ACTIVE
        cancelSearchButton.pack_forget()
        confirmMapButton.pack_forget()
        confirmGameButton.pack_forget()
        selectGameButton.pack_forget()
        matchOverButton.pack()
        matchOverButton["state"] = ACTIVE
        confirmSkillLevelButton.pack_forget()
        confirmCharButton.pack()
        createTipButton.pack_forget()
        inputTitle.pack_forget()
        inputTipText.pack_forget()
        postTipButton.pack_forget()
        quitMakingTipsButton.pack_forget()
        
        dropGame.pack_forget()
        dropMap.pack_forget()
        dropSkill.pack_forget()
        dropCharacter.pack()
        canvas.pack()

    elif newState == "creating tip": # for now you have to select game first
        findingMatchButton.pack_forget()
        matchMissedButton.pack_forget()
        moreInfoButton.pack_forget()
        cancelSearchButton.pack_forget()
        confirmMapButton.pack_forget()
        confirmGameButton.pack()
        selectGameButton.pack_forget()
        matchOverButton.pack_forget()
        confirmSkillLevelButton.pack_forget()
        confirmCharButton.pack_forget()
        createTipButton.pack_forget()
        inputTitle.pack()
        inputTipText.pack()
        postTipButton.pack()
        quitMakingTipsButton.pack()
        
        dropGame.pack()
        dropMap.pack()
        dropSkill.pack()
        dropCharacter.pack()
        canvas.pack_forget()

# Wrapper for any query to db
def connectAndQuery(query):
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
            connection.commit()
            cursor.close()
            connection.close()
    except Exception as error:
        print ("Oops! An exception has occured:", error)
        print ("Exception TYPE:", type(error))
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
webSiteLink.set("https://intuitiveintel.netlify.app/")

#Make the window jump above all
win.attributes('-topmost',True)

global img
global canvas
canvas = Canvas(win, width = 1000, height = 100)

games = [] 
games.append("invalid game option")
for value in connectAndQuery("SELECT name FROM games"):
    games.append(value[0])
    
maps = []
maps.append("invalid map option")
def getMaps():
    setMap.trace('w', checkMapSelected)
    maps.clear()
    for value in connectAndQuery("SELECT * FROM maps JOIN games ON gameid = game WHERE name(games) = \'" + setGame.get() + "\'"):
        maps.append(value[0])
    
skillLevels = []
skillLevels.append("invalid skill option")
def getSkills():
    skillLevels.clear()
    for value in connectAndQuery("SELECT * FROM skillLevels JOIN games ON gameid = game WHERE name = \'" + setGame.get() + "\'"):
        skillLevels.append(value[1])

characters = []
characters.append("invalid character option")
def getChars():
    characters.clear()
    for value in connectAndQuery("SELECT * FROM characters JOIN games ON gameid = game WHERE name(games) = \'" + setGame.get() + "\'"):
        characters.append(value[0])


inputTitleStr = StringVar()
inputTitle = Entry(win, textvariable= inputTitleStr)

inputTipTextStr = StringVar()
inputTipText = Entry(win, textvariable= inputTipTextStr)

def displayImage():
    global canvas
    global img
    #display code, not screenshot
    # display image(s)
    #canvas.pack_forget() # it stacks and falls lower and lower without this
    canvas = Canvas(win, width = 1920, height = 1080)
    canvas.pack()
    urllib.request.urlretrieve(
      'https://media.geeksforgeeks.org/wp-content/uploads/20210318103632/gfg-300x300.png',
       "gfg.png")
  
    img = Image.open("gfg.png")
    img = ImageTk.PhotoImage(img)
    canvas.create_image(10,10,anchor = NW, image = img)


def getTip(mapName):
    listOfTips = connectAndQuery("SELECT * FROM tips JOIN maps ON map = mapid JOIN characters ON charid = character WHERE name(maps) = \'" + mapName + "\'")
    # TODO: Change up how we are selecting a tip.
    return listOfTips.pop()


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
    result = getTip(resultMap)
    cancelSearchButton["state"] = "disabled"
    findingMatchButton["state"] = "active"
    result = getTip(setMap.get())
    titleText.set("Map found: " + resultMap + "\nTip: " + result[0])
    canvas.create_text(300, 50, text=result[1], fill="black", font=('Helvetica 12'), width = 300)

    setState("in a match")

    return resultMap

# when user starts searching for a game
def findMatch():
    setState("waiting in queue")
    global thread
    if thread._started:
        thread = threading.Thread(target = ocrStuff, args = ())
        thread.start()

# user has found a match and did not get a tip
def matchFound():
    print("oops, which map was it?")
    setState("map missed")

# when user goes to the site (home page by default, tip page if a tip is active)
def goToSite():
    print("redirecting to site...")
    webbrowser.open(webSiteLink.get(), new=1)

# user was searching for a match, and changed their mind
def cancelMatch():
    global thread
    print("cancelling match")
    thread._is_stopped = True
    setState("waiting in menu")

    
# helper for above
def confirmMap():
    global thread
    print("map confirmed")
    thread._is_stopped = True
    result = getTip(setMap.get())
    #TODO: make new method to handle all logic when finding a match
    titleText.set("Map found: " + setMap.get() + "\nTip: " + result[0])
    canvas.create_text(300, 50, text=result[1], fill="black", font=('Helvetica 12'), width = 300)
    setState("in a match")

# helper for above
def confirmGame():
    global dropMap
    global dropSkill
    global dropCharacter
    getMaps()
    getSkills()
    getChars()
    dropMap = OptionMenu(win, setMap, *maps)
    dropSkill = OptionMenu(win, setSkillLevel, *skillLevels)
    dropCharacter = OptionMenu(win, setCharacter, *characters)
    setState("waiting in menu")
    
# only button on launch? User selects which game they are playing
def selectGame():
    print("swapping game")
    setState("selecting game")

# to limit buttons available during match
def matchOver():
    print("GG")
    setState("waiting in menu")

# confirmation button to limit tips based on preferred skill level
def confirmSkillLevel():
    print("we will try to give you " + setSkillLevel.get() + " level tips")
    confirmSkillLevelButton["state"] = DISABLED

# confirmation button to limit tips based on preferred character
def confirmChar():
    print("we will try to give you tips for " + setCharacter.get())
    confirmCharButton["state"] = DISABLED

# launch user to creating a tip UI
def createTip():
    print("we're excited to see what you make!")    
    global dropMap
    global dropSkill
    global dropCharacter
    getMaps()
    getSkills()
    getChars()
    dropMap = OptionMenu(win, setMap, *maps)
    dropSkill = OptionMenu(win, setSkillLevel, *skillLevels)
    dropCharacter = OptionMenu(win, setCharacter, *characters)
    setState("creating tip")
    
# post the tip to the database
def postTip():
    print("This tip will help many other gamers now :)")
    print(inputTitleStr.get())
    print(connectAndQuery(f"INSERT INTO tips(title, explanation, character, map, skilllevel) SELECT \'{inputTitleStr.get()}\', \'{inputTipTextStr.get()}\', charid, mapid, id FROM characters c JOIN maps m ON game(c) = game(m) JOIN skilllevels s ON game(c) = game(s) WHERE name(c) = \'{setCharacter.get()}\' AND name(m) = \'{setMap.get()}\' AND level = \'{setSkillLevel.get()}\' RETURNING *"))
    #database stuff here

def quitMakingTips():
    print("go get those w's")
    setState("selecting game")

# add buttons
findingMatchButton = Button(win, text = "finding a match!", fg = "green",
                        command = findMatch)

matchMissedButton = Button(win, text = "match found!", fg = "red",
                        command = matchFound)

moreInfoButton = Button(win, text = "click for our website", fg = "black",
                        command = goToSite)

cancelSearchButton = Button(win, text = "cancel search", fg = "red",
                        command = cancelMatch)

confirmMapButton = Button(win, text = "confirm map", fg = "black",
                          command = confirmMap)

confirmGameButton = Button(win, text = "confirm game", fg = "black",
                           command = confirmGame)

selectGameButton = Button(win, text = "switch game", fg = "green",
                          command = selectGame)

matchOverButton = Button(win, text = "match over, clear tip", fg = "black",
                         command = matchOver)

confirmSkillLevelButton = Button(win, text = "confirm skill level", fg = "black",
                                 command = confirmSkillLevel)

confirmCharButton = Button(win, text = "confirm character level", fg = "black",
                                command = confirmChar)

createTipButton = Button(win, text = "create your own tip!", fg = "black",
                         command = createTip)

postTipButton = Button(win, text = "post tip to database!", fg = "red",
                       command = postTip)

quitMakingTipsButton = Button(win, text = "finish making tips", fg = "black",
                             command = quitMakingTips)

# allow user to select game when app launches
setGame = StringVar()
setGame.set("select game")

dropGame = OptionMenu(win, setGame, *games)

# allow user to select map from a dropdown if ocr failed
setMap = StringVar()
setMap.set("select map")

dropMap = OptionMenu(win, setMap, *maps)

# allow user to select skill level from a dropdown
setSkillLevel = StringVar()
setSkillLevel.set("select skill level")

dropSkill = OptionMenu(win, setSkillLevel, *skillLevels)

setCharacter = StringVar()
setCharacter.set("select character")

dropCharacter = OptionMenu(win, setCharacter, *characters)

# confirm game button inactive until a game is selected
def checkGameSelected(*args):
    confirmGameButton["state"] = ACTIVE
    createTipButton["state"] = ACTIVE

setGame.trace('w', checkGameSelected)

# TODO: make some more robust logic here
def checkMapSelected(*args):
    confirmMapButton["state"] = ACTIVE

setMap.trace('w', checkMapSelected)

def checkSkillSelected(*args):
    confirmSkillLevelButton["state"] = ACTIVE

setSkillLevel.trace('w', checkSkillSelected)

def checkCharSelected(*args):
    confirmCharButton["state"] = ACTIVE

setCharacter.trace('w', checkCharSelected)

# allow window to accept inputs while running ocr
thread = threading.Thread(target = ocrStuff, args = ())
thread._stop = threading.Event()

#displayImage()

setState("selecting game")

win.mainloop()
exit(0)
