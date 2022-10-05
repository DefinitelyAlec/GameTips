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

# explicit state machine
currState = "selecting game"

# for any new button, pack when it should be there, and pack_forget in all others
def setState(newState):
    global titleText
    global currState
    currState = newState
    
    # despagghetified
    for button in buttons:
        button.pack_forget()

    if newState == "selecting game":
        moreInfoButton.pack()
        moreInfoButton["state"] = ACTIVE
        confirmGameButton.pack()
        confirmGameButton["state"] = DISABLED # starts disabled in this state, wait until an option is selected in dropgame via trace
        createTipButton.pack()
        createTipButton["state"] = DISABLED

        dropGame.pack()

    elif newState == "waiting in menu":
        titleText.set(f"Good luck in {setGame.get()}")
        findingMatchButton.pack()
        findingMatchButton["state"] = ACTIVE
        moreInfoButton.pack()
        moreInfoButton["state"] = ACTIVE
        selectGameButton.pack()
        selectGameButton["state"] = ACTIVE
        confirmSkillLevelButton.pack()
        confirmSkillLevelButton["state"] = DISABLED
        confirmCharButton.pack()
        confirmCharButton["state"] = DISABLED

        dropSkill.pack()
        dropCharacter.pack()
        dropSkill.pack()
        
    elif newState == "waiting in queue":
        findingMatchButton.pack()
        findingMatchButton["state"] = DISABLED
        matchMissedButton.pack()
        matchMissedButton["state"] = ACTIVE
        moreInfoButton.pack()
        moreInfoButton["state"] = ACTIVE
        cancelSearchButton.pack()
        cancelSearchButton["state"] = ACTIVE

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

        dropMap.pack()
        
    elif newState == "in a match":
        moreInfoButton.pack()
        moreInfoButton["state"] = ACTIVE
        matchOverButton.pack()
        matchOverButton["state"] = ACTIVE
        
        canvas.pack()

    elif newState == "creating tip": # for now you have to select game first
        inputTitle.pack()
        inputTipText.pack()
        postTipButton.pack()
        quitMakingTipsButton.pack()
        
        dropMap.pack()
        dropSkill.pack()
        dropCharacter.pack()
        
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
win.geometry("800x450")

buttons = []

#Create a Label
titleText = StringVar() # this datatype is from tkinter
titleText.set("Welcome to Intuitive Intel!")
Label(win, textvariable = titleText,font=('Helvetica bold', 15)).pack(pady=20)

#Create our website
webSiteLink = StringVar()
webSiteLink.set("https://intuitiveintel.netlify.app/")

#Make the window jump above all
win.attributes('-topmost',True)

global img
global canvas
canvas = Canvas(win, width = 1000, height = 100)
buttons.append(canvas)

games = [] 
games.append("select game")
for value in connectAndQuery("SELECT name FROM games"):
    games.append(value[0])
    
maps = []
maps.append("invalid map option")
def getMaps():
    setMap.trace('w', checkMapSelected)
    maps.clear()
    maps.append("select map")
    for value in connectAndQuery("SELECT * FROM maps JOIN games ON gameid = game WHERE name(games) = \'" + setGame.get() + "\'"):
        maps.append(value[0])
    
skillLevels = []
skillLevels.append("invalid skill option")
def getSkills():
    skillLevels.clear()
    skillLevels.append("select skill level")
    for value in connectAndQuery("SELECT * FROM skillLevels JOIN games ON gameid = game WHERE name = \'" + setGame.get() + "\'"):
        skillLevels.append(value[1])

characters = []
characters.append("invalid character option")
def getChars():
    characters.clear()
    characters.append("select character")
    for value in connectAndQuery("SELECT * FROM characters JOIN games ON gameid = game WHERE name(games) = \'" + setGame.get() + "\'"):
        characters.append(value[0])


inputTitleStr = StringVar()
inputTitle = Entry(win, textvariable= inputTitleStr)
buttons.append(inputTitle)

inputTipTextStr = StringVar()
inputTipText = Entry(win, textvariable= inputTipTextStr)
buttons.append(inputTipText)

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
    charSelected = setCharacter.get() != "select character"
    skillLevelSelected = setSkillLevel.get() != "select skill level"

    query = "SELECT * FROM tips JOIN maps ON map = mapid "
    if(charSelected):
        query += "JOIN characters ON charid = character "
    if(skillLevelSelected):
        query+= "JOIN skilllevels ON id = skilllevel "
    query += f"WHERE name(maps) = \'{mapName}\' "
    if(charSelected):
        query += f"AND name(characters) = \'{setCharacter.get()}\' "
    if(skillLevelSelected):
        query += f"AND level = \'{setSkillLevel.get()}\' "
    listOfTips = connectAndQuery(query)
    # TODO: Change up how we are selecting a tip.
    # TODO: Have fail state for if character/skill combo DNE
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
    buttons.remove(dropMap)
    buttons.remove(dropSkill)
    buttons.remove(dropCharacter)
    dropMap = OptionMenu(win, setMap, *maps)
    dropSkill = OptionMenu(win, setSkillLevel, *skillLevels)
    dropCharacter = OptionMenu(win, setCharacter, *characters)
    buttons.append(dropMap)
    buttons.append(dropSkill)
    buttons.append(dropCharacter)
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
    buttons.remove(dropMap)
    buttons.remove(dropSkill)
    buttons.remove(dropCharacter)
    dropMap = OptionMenu(win, setMap, *maps)
    dropSkill = OptionMenu(win, setSkillLevel, *skillLevels)
    dropCharacter = OptionMenu(win, setCharacter, *characters)
    buttons.append(dropMap)
    buttons.append(dropSkill)
    buttons.append(dropCharacter)
    setState("creating tip")
    
# post the tip to the database
def postTip():
    charSelected = setCharacter.get() != "select character"
    mapSelected = setMap.get() != "select map"
    skillLevelSelected = setSkillLevel.get() != "select skill level"

    print("This tip will help many other gamers now :)")
    query = "INSERT INTO tips(title, explanation"
    if charSelected:
        query += ", character"
    if mapSelected:
        query += ", map"
    if skillLevelSelected:
        query += ", skilllevel"
    query += f") SELECT \'{inputTitleStr.get()}\', \'{inputTipTextStr.get()}\'"
    if charSelected:
        query += ", charid"
    if mapSelected:
        query += ", mapid"
    if skillLevelSelected:
        query += ", id"

    if charSelected or mapSelected or skillLevelSelected:
        query += " FROM "

        if charSelected:
            query += "characters c "
            if mapSelected or skillLevelSelected:
                query += "JOIN "
        if mapSelected:
            query += "maps m "
            if charSelected:
                query += "ON game(c) = game(m) "
            if skillLevelSelected:
                query += "JOIN "
        if skillLevelSelected:
            query += "skilllevels s "
            if charSelected or mapSelected:
                if charSelected:
                    query += "ON game(c) = game(s) "
                else:
                    query += "ON game(m) = game(s) "
        query += "WHERE "
        if charSelected:
            query += f"name(c) = \'{setCharacter.get()}\' "
            if mapSelected or skillLevelSelected:
                query += "AND "
        if mapSelected:
            query += f"name(m) = \'{setMap.get()}\' "
            if skillLevelSelected:
                query += "AND "
        if skillLevelSelected:
            query += f"level = \'{setSkillLevel.get()}\' "
    query += "RETURNING *"
    connectAndQuery(query)

def quitMakingTips():
    print("go get those w's")
    setState("selecting game")
    
# add buttons
findingMatchButton = Button(win, text = "finding a match!", fg = "green",
                        command = findMatch)
buttons.append(findingMatchButton)

matchMissedButton = Button(win, text = "match found!", fg = "red",
                        command = matchFound)
buttons.append(matchMissedButton)

moreInfoButton = Button(win, text = "click for our website", fg = "black",
                        command = goToSite)
buttons.append(moreInfoButton)

cancelSearchButton = Button(win, text = "cancel search", fg = "red",
                        command = cancelMatch)
buttons.append(cancelSearchButton)

confirmMapButton = Button(win, text = "confirm map", fg = "black",
                          command = confirmMap)
buttons.append(confirmMapButton)

confirmGameButton = Button(win, text = "confirm game", fg = "black",
                           command = confirmGame)
buttons.append(confirmGameButton)

selectGameButton = Button(win, text = "switch game", fg = "green",
                          command = selectGame)
buttons.append(selectGameButton)

matchOverButton = Button(win, text = "match over, clear tip", fg = "black",
                         command = matchOver)
buttons.append(matchOverButton)

confirmSkillLevelButton = Button(win, text = "confirm skill level", fg = "black",
                                 command = confirmSkillLevel)
buttons.append(confirmSkillLevelButton)

confirmCharButton = Button(win, text = "confirm character", fg = "black",
                                command = confirmChar)
buttons.append(confirmCharButton)

createTipButton = Button(win, text = "create your own tip!", fg = "black",
                         command = createTip)
buttons.append(createTipButton)

postTipButton = Button(win, text = "post tip to database!", fg = "red",
                       command = postTip)
buttons.append(postTipButton)

quitMakingTipsButton = Button(win, text = "finish making tips", fg = "black",
                             command = quitMakingTips)
buttons.append(quitMakingTipsButton)

# allow user to select game when app launches
setGame = StringVar()
setGame.set("select game")

dropGame = OptionMenu(win, setGame, *games)
buttons.append(dropGame)

# allow user to select map from a dropdown if ocr failed
setMap = StringVar()
setMap.set("select map")

dropMap = OptionMenu(win, setMap, *maps)
buttons.append(dropMap)

# allow user to select skill level from a dropdown
setSkillLevel = StringVar()
setSkillLevel.set("select skill level")

dropSkill = OptionMenu(win, setSkillLevel, *skillLevels)
buttons.append(dropSkill)

setCharacter = StringVar()
setCharacter.set("select character")

dropCharacter = OptionMenu(win, setCharacter, *characters)
buttons.append(dropCharacter)

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
