from argparse import Action
from msilib.schema import File
from tkinter import *
import easyocr
import webbrowser
import threading
import psycopg2
import pyautogui
import numpy as np
import urllib.request
from PIL import Image, ImageTk, ImageGrab
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

# explicit state machine
currState = "selecting game"
loggedInUser = None

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
        loginButton.pack()
        loginButton["state"] = ACTIVE
        followUserButton.pack()
        followUserButton["state"] = DISABLED
        titleText.set("Welcome to Intuitive Intel!")

        dropGame.pack()

    elif newState == "waiting in menu":
        titleText.set(f"Good luck in {setGame.get()}")
        findingMatchButton.pack()
        findingMatchButton["state"] = ACTIVE
        moreInfoButton.pack()
        moreInfoButton["state"] = ACTIVE
        selectGameButton.pack()
        selectGameButton["state"] = ACTIVE
        confirmPreferencesButton.pack()
        confirmPreferencesButton["state"] = DISABLED
        dropCharacter.pack()

        saveFavoritesButton.pack()
        
    elif newState == "waiting in queue":
        matchMissedButton.pack()
        matchMissedButton["state"] = ACTIVE
        moreInfoButton.pack()
        moreInfoButton["state"] = ACTIVE
        cancelSearchButton.pack()
        cancelSearchButton["state"] = ACTIVE
        startAutoDetectButton.pack()

    elif newState == "map missed":
        matchMissedButton.pack()
        matchMissedButton["state"] = ACTIVE
        moreInfoButton.pack()
        moreInfoButton["state"] = ACTIVE
        cancelSearchButton.pack()
        cancelSearchButton["state"] = DISABLED
        confirmMapButton.pack()
        confirmMapButton["state"] = DISABLED

        dropMap.pack()
        
    elif newState == "in a match":
        moreInfoButton.pack()
        moreInfoButton["state"] = ACTIVE
        nextTipButton.pack()
        confirmRatingButton.pack()
        dropRating.pack()
        matchOverButton.pack()
        matchOverButton["state"] = ACTIVE
        
        canvas.pack()

    elif newState == "creating tip": # for now you have to select game first
        inputTitle.pack()
        inputTipText.pack()
        postTipButton.pack()
        quitMakingTipsButton.pack()
        
        dropMap.pack()
        dropCharacter.pack()
        
    elif newState == "browsing users":
        inputUser.pack()
        searchForUserButton.pack()
        confirmUserButton.pack()
        confirmUserButton["state"] = DISABLED
        selectGameButton.pack()
        

# Wrapper for any query to db
def connectAndQuery(query):
    listToReturn = None
    try:
        print("Connected.")
        connection = psycopg2.connect(user="anyone", password="teamgametips",\
             host = "database-1.cgpwhtgqxogz.us-west-1.rds.amazonaws.com", port = 5432, database = "teamgametipsdb")
        cursor = connection.cursor()

        cursor.execute(query)
        try:
            listToReturn = cursor.fetchall()
        except:
            listToReturn = None
        if connection:
            print("Closing connection.")
            connection.commit()
            cursor.close()
            connection.close()
    except Exception as error:
        print ("Oops! An exception has occured:", error)
        print ("Exception TYPE:", type(error))
    return listToReturn

def loadFavorites(game):
    favorites = open("localFavorites.txt")
    currGame = "not a game"
    while currGame != game:
        nextLine = favorites.readline()
        if nextLine != "":
            currLine = json.loads(nextLine)
            currGame = currLine["Game"]
        else:
            return
    setCharacter.set(currLine["Favorite Character"])

def get_authenticated_login_service():
    CLIENT_SECRETS_FILE = 'client_secret.json'
    SCOPES = ['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email', 'openid']
    API_SERVICE_NAME = 'oauth2'
    API_VERSION = 'v2'
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(host='localhost',
        port=8080, 
        authorization_prompt_message='Please visit this URL: {url}', 
        success_message='The auth flow is complete; you may close this window.',
        open_browser=True)
    return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

def loginHelper():
    service = get_authenticated_login_service()
    googleUser = service.userinfo().get().execute()
    possibleUser = connectAndQuery(f"SELECT * FROM users WHERE email = \'" + googleUser["email"] + "\'")
    if possibleUser != None and len(possibleUser) > 0:
        global loggedInUser
        loggedInUser = possibleUser[0]
        followUserButton["state"] = ACTIVE

    else: 
        print("No account found with that email.")

def login():
    loginButton["state"] = DISABLED
    global thread
    if thread._started:
        thread = threading.Thread(target = loginHelper, args = (), )
        thread.start()


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

global currTip
global listOfTips
global currTipText
global img
global canvas
global following
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

characters = []
characters.append("invalid character option")
def getChars():
    characters.clear()
    characters.append("select character")
    for value in connectAndQuery("SELECT * FROM characters JOIN games ON gameid = game WHERE name(games) = \'" + setGame.get() + "\'"):
        characters.append(value[0])

# setup the inputs to prompt the user
inputTitleStr = StringVar()
inputTitle = Entry(win, textvariable= inputTitleStr)
inputTitle.insert(0, "Default Tip Title")
buttons.append(inputTitle)

inputTipTextStr = StringVar()
inputTipText = Entry(win, textvariable= inputTipTextStr)
inputTipText.insert(0, "Default Tip Info")
buttons.append(inputTipText)

inputUserStr = StringVar()
inputUser = Entry(win, textvariable= inputUserStr)
inputUser.insert(0, "Type username EXACTLY")
buttons.append(inputUser)

def getTips(mapName):
    global listOfTips
    charSelected = setCharacter.get() != "select character"

    query = f"SELECT * FROM tips LEFT JOIN maps ON map = mapid LEFT JOIN characters ON charid = character WHERE (name(maps) = \'{mapName}\' OR name(maps) IS NULL) "
    if(charSelected):
        query += f"AND (name(characters) = \'{setCharacter.get()}\' OR name(characters) IS NULL) "
    query += "ORDER BY map NULLS FIRST, character NULLS FIRST, level NULLS FIRST"
    listOfTips = connectAndQuery(query)
    for tip in listOfTips:
        print(tip)

def ocrStuff():
    global img
    global currTip
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
    getTips(setMap.get())
    currTip = listOfTips.pop()
    titleText.set("Map found: " + resultMap + "\nTip: " + currTip[0])
    global currTipText
    currTipText = canvas.create_text(300, 50, text=currTip[1], fill="black", font=('Helvetica 12'), width = 300)

    setState("in a match")

    return resultMap

# when user starts searching for a game
def findMatch():
    setState("waiting in queue")

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

    
# confirm map when selecting
def confirmMap():
    global thread
    global currTip
    print("map confirmed")
    thread._is_stopped = True
    getTips(setMap.get())
    currTip = listOfTips.pop()
    webSiteLink.set(currTip[6])
    titleText.set("Map found: " + setMap.get() + "\nTip: " + currTip[0])
    global currTipText
    currTipText =  canvas.create_text(300, 50, text=currTip[1], fill="black", font=('Helvetica 12'), width = 300)

    setState("in a match")

def getFollowing():
    global following
    if(loggedInUser == None):
        return
    query = f"SELECT creator from followers where follower = {loggedInUser[0]}"
    following = connectAndQuery(query)

def queryForGetGame():
    global dropMap
    global dropCharacter
    global following

    getMaps()
    getChars()
    getFollowing()



# use game selected in dropdown
def confirmGame():
    global thread
    global dropMap
    global dropCharacter

    setCharacter.set("select character")

    if thread._started:
        thread = threading.Thread(target = queryForGetGame, args = ())
        thread.start()

    queryForGetGame()
    loadFavorites(setGame.get())

    buttons.remove(dropMap)
    buttons.remove(dropCharacter)
    dropMap = OptionMenu(win, setMap, *maps)
    dropCharacter = OptionMenu(win, setCharacter, *characters)
    buttons.append(dropMap)
    buttons.append(dropCharacter)

    setState("waiting in menu")
    
# switch game to a different game
def selectGame():
    print("swapping game")
    setState("selecting game")

# do all logic when match is over
def matchOver():
    print("GG")
    setState("waiting in menu")

# confirmation button to set preferences
def confirmPreferences():
    print(f"we will try to give you tips for {setCharacter.get()}")
    confirmPreferencesButton["state"] = DISABLED

# launch user to creating a tip UI
def createTip():
    print("we're excited to see what you make!")    
    global dropMap
    global dropCharacter
    getMaps()
    getChars()
    buttons.remove(dropMap)
    buttons.remove(dropCharacter)
    dropMap = OptionMenu(win, setMap, *maps)
    dropCharacter = OptionMenu(win, setCharacter, *characters)
    buttons.append(dropMap)
    buttons.append(dropCharacter)
    setState("creating tip")
    
# post the tip to the database
def postTip():
    charSelected = setCharacter.get() != "select character"
    mapSelected = setMap.get() != "select map"

    print("This tip will help many other gamers now :)")
    query = "INSERT INTO tips(title, explanation, creator"
    if charSelected:
        query += ", character"
    if mapSelected:
        query += ", map"
    query += f") SELECT \'{inputTitleStr.get()}\', \'{inputTipTextStr.get()}\', {loggedInUser[0]}"
    if charSelected:
        query += ", charid"
    if mapSelected:
        query += ", mapid"

    if charSelected or mapSelected:
        query += " FROM "

        if charSelected:
            query += "characters c "
            if mapSelected:
                query += "JOIN "
        if mapSelected:
            query += "maps m "
            if charSelected:
                query += "ON game(c) = game(m) "
        query += "WHERE "
        if charSelected:
            query += f"name(c) = \'{setCharacter.get()}\' "
            if mapSelected:
                query += "AND "
        if mapSelected:
            query += f"name(m) = \'{setMap.get()}\' "
    query += "RETURNING *"
    connectAndQuery(query)

def quitMakingTips():
    print("go get those w's")
    setState("selecting game")

def saveFavorites():
    print(f"saving {setCharacter.get()} as favorite")
    
    # https://stackoverflow.com/questions/4710067/how-to-delete-a-specific-line-in-a-file
    with open("localFavorites.txt", "r") as f:
        lines = f.readlines()
    with open("localFavorites.txt", "w") as f:
        for line in lines:
            if json.loads(line)["Game"] != setGame.get():
                f.write(line)
        newFavorite = "{\"Game\":\"" + setGame.get() + "\", Favorite Character\":\"" + setCharacter.get() +"\"}\n"
        f.write(newFavorite)

    
def confirmRating():
    print("Thank you for rating this tip!")
    confirmRatingButton["state"] = DISABLED
    query = f"INSERT INTO ratings VALUES({loggedInUser[0]}, {setRating.get()}, {currTip[7]}) ON CONFLICT(rater, tip) DO UPDATE SET rating = {setRating.get()} RETURNING *"
    connectAndQuery(query)

def followUser():
    print("select a user to follow!")
    setState("browsing users")

def searchForUser():
    print("searching for that user...")
    query = f"SELECT * FROM users where username = \'{inputUserStr.get()}\'" 
    result = connectAndQuery(query) # one user if this userrname exists
    try:
        query = f"SELECT * FROM followers where follower = {loggedInUser[0]} AND creator = {result[0][0]}"
        result = connectAndQuery(query) # one result if user is following, zero if user is not following
        try:
            # user is already following
            print(result[0])
            print(f"you are already following this creator, unfollow them?")
            confirmUserButton["text"] = "Unfollow"
            confirmUserButton["state"] = ACTIVE
            confirmUserButton.configure(command= confirmUnfollowUser)
        except:
            # user is not currently following
            print(f"you are not following this creator yet, follow them?")
            confirmUserButton["text"] = "Follow"
            confirmUserButton["state"] = ACTIVE
            confirmUserButton.configure(command= confirmFollowUser)
            
    except:
        print("there are no users with that name, please type it exactly.")

def confirmUnfollowUser():
    query = f"WITH id AS (SELECT user_id FROM users where username = \'{inputUserStr.get()}\') DELETE FROM followers WHERE follower = {loggedInUser[0]} AND creator IN (SELECT user_id FROM id) returning *"
    connectAndQuery(query)
    confirmUserButton["state"] = DISABLED
    
def confirmFollowUser():
    query = f"INSERT INTO followers SELECT {loggedInUser[0]}, u.user_id from users as u where u.username = \'{inputUserStr.get()}\' returning *"
    connectAndQuery(query)
    confirmUserButton["state"] = DISABLED

def startAutoDetect():
    global thread
    if thread._started:
        thread = threading.Thread(target = ocrStuff, args = ())
        thread.start()

def nextTip():
    global currTipText
    currTip = listOfTips.pop()
    webSiteLink.set(currTip[6])
    titleText.set("Map found: " + setMap.get() + "\nTip: " + currTip[0])
    canvas.itemconfig(currTipText, text=currTip[1])

# add buttons
findingMatchButton = Button(win, text = "finding a match!", fg = "green",
                        command = findMatch)
buttons.append(findingMatchButton)

matchMissedButton = Button(win, text = "MATCH FOUND!", fg = "red",
                        command = matchFound)
buttons.append(matchMissedButton)

loginButton = Button(win, text = "click to login", fg = "blue",
                        command = login)
buttons.append(loginButton)

moreInfoButton = Button(win, text = "click for our website", fg = "black",
                        command = goToSite)
buttons.append(moreInfoButton)

cancelSearchButton = Button(win, text = "cancel search", fg = "red",
                        command = cancelMatch)
buttons.append(cancelSearchButton)

confirmMapButton = Button(win, text = "confirm map", fg = "black",
                          command = confirmMap)
buttons.append(confirmMapButton)

confirmGameButton = Button(win, text = "Play game", fg = "green",
                           command = confirmGame)
buttons.append(confirmGameButton)

selectGameButton = Button(win, text = "switch game", fg = "green",
                          command = selectGame)
buttons.append(selectGameButton)

matchOverButton = Button(win, text = "match over, clear tip", fg = "black",
                             command = matchOver)
buttons.append(matchOverButton)

confirmPreferencesButton = Button(win, text = "confirm preferences", fg = "green",
                            command = confirmPreferences)
buttons.append(confirmPreferencesButton)

createTipButton = Button(win, text = "create your own tip!", fg = "black",
                         command = createTip)
buttons.append(createTipButton)

postTipButton = Button(win, text = "post tip to database!", fg = "red",
                       command = postTip)
buttons.append(postTipButton)

quitMakingTipsButton = Button(win, text = "finish making tips", fg = "black",
                             command = quitMakingTips)
buttons.append(quitMakingTipsButton)

saveFavoritesButton = Button(win, text = "save as favorite", fg = "black",
                             command = saveFavorites)
buttons.append(saveFavoritesButton)

confirmRatingButton = Button(win, text = "confirm rating", fg = "black",
                             command = confirmRating)                            
buttons.append(confirmRatingButton)

followUserButton = Button(win, text = "manage followings", fg = "black",
                             command = followUser)
buttons.append(followUserButton)

searchForUserButton = Button(win, text = "search!", fg = "green",
                            command = searchForUser)
buttons.append(searchForUserButton)

confirmUserButton = Button(win, text = "follow this user", fg = "black",
                             command = confirmFollowUser)
buttons.append(confirmUserButton)

startAutoDetectButton = Button(win, text = "start OCR auto-detect", fg = "black",
                            command = startAutoDetect)
buttons.append(startAutoDetectButton)

nextTipButton = Button(win, text = "get a different tip", fg = "red",
                            command = nextTip)

ratings = [1,2,3,4,5]
setRating = StringVar()
setRating.set("select rating")

dropRating = OptionMenu(win, setRating, *ratings)
buttons.append(dropRating)

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

def checkCharSelected(*args):
    confirmPreferencesButton["state"] = ACTIVE

setCharacter.trace('w', checkCharSelected)

def checkRatingSelected(*args):
    confirmRatingButton["state"] = ACTIVE

setRating.trace('w', checkRatingSelected)

# allow window to accept inputs while running ocr
thread = threading.Thread(target = ocrStuff, args = ())
thread._stop = threading.Event()

#displayImage()

setState("selecting game")

win.mainloop()
exit(0)
