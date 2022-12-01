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
import math
from PIL import Image, ImageTk, ImageGrab
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

# explicit state machine
currState = "selecting game"
loggedInUser = None
seenTips = []

# for any new button, pack when it should be there, and pack_forget in all others
def setState(newState):
    global titleText
    global currState
    currState = newState

    # despagghetified
    for button in buttons:
        button.pack_forget()
        button.place_forget()

    if newState == "selecting game":
        loginButton.pack()
        moreInfoButton.pack()
        confirmGameButton.pack()
        followUserButton.pack()
        createTipButton.pack()
        editExistingGameButton.pack()
        uploadGameButton.pack()
        if loggedInUser == None:
            followUserButton["state"] = DISABLED
            createTipButton["state"] = DISABLED
        if setGame.get() == "select game":
            confirmGameButton["state"] = DISABLED
            editExistingGameButton["state"] = DISABLED

        titleText.set("Welcome to Intuitive Intel!")
        dropGame.pack()

    elif newState == "waiting in menu":
        titleText.set(f"Good luck in {setGame.get()}")
        findingMatchButton.pack()
        moreInfoButton.pack()
        confirmPreferencesButton.pack()
        dropCharacter.pack()
        saveFavoritesButton.pack()
        selectGameButton.pack()
        confirmPreferencesButton["state"] = DISABLED
        saveFavoritesButton["state"] = DISABLED
        
    elif newState == "waiting in queue":
        matchMissedButton.pack()
        moreInfoButton.pack()
        startAutoDetectButton.pack()
        cancelSearchButton.pack()

    elif newState == "map missed":
        matchMissedButton.pack()
        moreInfoButton.pack()
        cancelSearchButton.pack()
        confirmMapButton.pack()
        if setMap.get() == "select map":
            confirmMapButton["state"] = DISABLED
        else:
            confirmMapButton["state"] = ACTIVE

        dropMap.pack()
        
    elif newState == "in a match":
        moreInfoButton.pack()
        nextTipButton.pack()
        confirmRatingButton.pack()
        dropRating.pack()
        matchOverButton.pack()
        ratingLabel.pack()
        confirmRatingButton["state"] = DISABLED

        canvas.pack()

    elif newState == "creating tip": # for now you have to select game first
        inputTitle.pack()
        tipTextLabel.place(x=250, y=95)
        tipTitleLabel.place(x=250, y=75)
        inputTipText.pack()
        postTipButton.pack()
        quitMakingTipsButton.pack()
        titleText.set(f"What cool tip have you got for us?")
        dropMap.pack()
        dropCharacter.pack()
        
    elif newState == "browsing users":
        inputUser.pack()
        searchForUserButton.pack()
        confirmUserButton.pack()
        confirmUserButton["state"] = DISABLED
        selectGameButton.pack()
        titleText.set(f"Please type the username exactly")

    elif newState == "uploading game":
        inputGameText.pack()
        uploadToDBButton.pack()
        inputCharText.pack()
        addCharacterToGameButton.pack()
        inputMapText.pack()
        addMapToGameButton.pack()
        selectGameButton.pack()
        titleText.set(f"What game should we add to the database?")

    elif newState == "editing existing game":
        inputCharText.pack()
        addCharacterToGameButton.pack()
        inputMapText.pack()
        addMapToGameButton.pack()
        selectGameButton.pack()
        titleText.set(f"What is missing from {setGame.get()}?")

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
    potentialGame = "not a game"
    while potentialGame != game:
        nextLine = favorites.readline()
        if nextLine != "":
            currLine = json.loads(nextLine)
            potentialGame = currLine["Game"]
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
    loginButton["text"] = "switch account"
    if possibleUser != None and len(possibleUser) > 0:
        global loggedInUser
        print(possibleUser)
        loggedInUser = {
           "userid" :  possibleUser[0][0],
           "username" : possibleUser[0][1],
           "email" : possibleUser[0][2],
           "imgurl" : possibleUser[0][3]
        }
        followUserButton["state"] = ACTIVE
        checkGameSelected()
    else: 
        global currTipText
        global canvas
        canvas.itemconfig(currTipText, text="No account found with that email.")
        print("No account found with that email.")
    retrieveSeenTips()

def login():
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
global canvas
global following
global ratingAverage
following = None
ratingAverage = 0.0
canvas = Canvas(win, width = 1000, height = 100)
buttons.append(canvas)
currTipText = canvas.create_text(333, 50, text="", fill="black", font=('Helvetica 12'), width = 333)

games = [] 
games.append("select game")
for value in connectAndQuery("SELECT name, gameid FROM games"):
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

tipTitleLabel = Label(win, text = "Tip Title:")
tipTitleLabel.place(x=250, y=75)
buttons.append(tipTitleLabel)
inputTitleStr = StringVar()
inputTitle = Entry(win, textvariable= inputTitleStr)
inputTitle.insert(0, "Default Tip Title")
buttons.append(inputTitle)

tipTextLabel = Label(win, text = "Tip Text:")
tipTextLabel.place(x=250, y=95)
buttons.append(tipTextLabel)
inputTipTextStr = StringVar()
inputTipText = Entry(win, textvariable= inputTipTextStr)
inputTipText.insert(0, "Default Tip Info")
buttons.append(inputTipText)

ratingLabel = Label(win, text = "rating: " + str(ratingAverage))
ratingLabel.place(x=400, y=300)
buttons.append(ratingLabel)

inputUserStr = StringVar()
inputUser = Entry(win, textvariable= inputUserStr)
inputUser.insert(0, "Type username EXACTLY")
buttons.append(inputUser)

inputGameStr = StringVar()
inputGameText = Entry(win, textvariable= inputGameStr)
inputGameText.insert(0, "Type game name")
buttons.append(inputGameText)

inputCharStr = StringVar()
inputCharText = Entry(win, textvariable= inputCharStr)
inputCharText.insert(0, "Type character name")
buttons.append(inputCharText)

inputMapStr = StringVar()
inputMapText = Entry(win, textvariable= inputMapStr)
inputMapText.insert(0, "Type map name")
buttons.append(inputMapText)

def getTips(mapName):
    global listOfTips
    global following
    charSelected = setCharacter.get() != "select character"

    query = f"SELECT * FROM tips LEFT JOIN maps ON map = mapid LEFT JOIN characters ON charid = character WHERE (name(maps) = \'{mapName}\' OR name(maps) IS NULL) "
    if(charSelected):
        query += f"AND (name(characters) = \'{setCharacter.get()}\' OR name(characters) IS NULL) "
    query += " ORDER BY map NULLS FIRST, character NULLS FIRST"
    if(following != None):
        print("following is not null")
        query += ", CASE "
        for creator in following:
            print(f"creator is not null, it's {creator}" )
            print(f"and this creator[0] is {creator[0]}")
            query += f" WHEN CREATOR = {creator[0]} THEN 0 "
        query += " ELSE 3 END"
        
    print(query)
    listOfTips = connectAndQuery(query)

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
                if text.lower() == map.lower():
                    foundMap = True
                    resultMap = map
                    break
        if thread._is_stopped:
            print("thread successfully cancelled")
            return
    print(resultMap)
    getTips(setMap.get())
    currTip = listOfTips.pop()
    titleText.set("Map found: " + resultMap + "\nTip: " + currTip[0])
    setState("in a match")
    nextTip()

    return resultMap

# when user starts searching for a game
def findMatch():
    setState("waiting in queue")

# user has found a match and did not get a tip
def matchFound():
    print("Which map was it?")
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
    nextTip()

    setState("in a match")

def getFollowing():
    global following
    if(loggedInUser == None):
        return
    uid = loggedInUser["userid"]
    query = f"SELECT creator from followers where follower = {uid}"
    following = connectAndQuery(query)

# use game selected in dropdown
def confirmGame():
    global dropMap
    global dropCharacter

    setCharacter.set("select character")

    getMaps()
    getChars()
    getFollowing()
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
    currGame = connectAndQuery(f"SELECT * FROM games WHERE name = \'{setGame.get()}\'")[0]

    print("This tip will help many other gamers now :)")
    query = "INSERT INTO tips(title, explanation, creator"
    if charSelected:
        query += ", character"
    if mapSelected:
        query += ", map"
    query += f", game) SELECT \'{inputTitleStr.get()}\', \'{inputTipTextStr.get()}\', {loggedInUser['userid']}"
    if charSelected:
        query += ", charid"
    if mapSelected:
        query += ", mapid"
    query += f", gameid FROM games g "

    if charSelected or mapSelected:
        query += "JOIN "
        if charSelected:
            query += "characters c ON game(c) = gameid(g) "
            if mapSelected:
                query += "JOIN "
        if mapSelected:
            query += "maps m ON gameid(g) = game(m) "
    query += f"WHERE name(g) = \'{setGame.get()}\' "
    if charSelected or mapSelected:
        query += "AND "
        if charSelected:
            query += f"name(c) = \'{setCharacter.get()}\' "
            if mapSelected:
                query += "AND "
        if mapSelected:
            query += f"name(m) = \'{setMap.get()}\' "
    query += "RETURNING *"
    print(query)
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
        newFavorite = "{\"Game\":\"" + setGame.get() + "\", \"Favorite Character\":\"" + setCharacter.get() +"\"}\n"
        f.write(newFavorite)
        for line in lines:
            if json.loads(line)["Game"] != setGame.get():
                f.write(line)
    saveFavoritesButton["state"] = DISABLED

def saveSeenTips():
    global seenTips
    global loggedInUser
    if loggedInUser is None:
        return
    lines = open('userInfo.txt','r').readlines()
    oldUserLog = {}
    with open('userInfo.txt','w') as jsonFile:
        for line in lines:
            jsonLine = json.loads(line)
            if jsonLine["userid"] != loggedInUser["userid"]:
                jsonFile.write(line)
            else:
                oldUserLog = jsonLine
        if oldUserLog == {}:
            oldUserLog = loggedInUser
        newUserLog = oldUserLog
        tipids = newUserLog.get("tipids", [])
        for tipid in seenTips:
            if tipid not in tipids:
                tipids.append(tipid)
        newUserLog["tipids"] = tipids
        print(newUserLog)
        jsonFile.write(json.dumps(newUserLog))

def retrieveSeenTips():
    global loggedInUser
    global seenTips
    if loggedInUser is None:
        return
    for line in open('userInfo.txt','r').readlines():
        jsonLine = json.loads(line)
        if jsonLine["userid"] == loggedInUser["userid"]:
            seenTips = jsonLine["tipids"]
            return
    
def confirmRating():
    print("Thank you for rating this tip!")
    confirmRatingButton["state"] = DISABLED
    uid = loggedInUser["userid"]
    query = f"INSERT INTO ratings VALUES({uid}, {setRating.get()}, {currTip[6]}) ON CONFLICT(rater, tip) DO UPDATE SET rating = {setRating.get()} RETURNING *"
    connectAndQuery(query)

def followUser():
    print("select a user to follow!")
    setState("browsing users")

def searchForUser():
    print("searching for that user...")
    query = f"SELECT * FROM users where username = \'{inputUserStr.get()}\'" 
    result = connectAndQuery(query) # one user if this userrname exists
    try:
        uid = loggedInUser["userid"]
        query = f"SELECT * FROM followers where follower = {uid} AND creator = {result[0][0]}"
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
    uid = loggedInUser["userid"]
    query = f"INSERT INTO followers SELECT {uid}, u.user_id from users as u where u.username = \'{inputUserStr.get()}\' returning *"
    connectAndQuery(query)
    confirmUserButton["state"] = DISABLED

def startAutoDetect():
    global thread
    if thread._started:
        thread = threading.Thread(target = ocrStuff, args = ())
        thread.start()
listOfSeenTips = []

def nextTip():
    global currTipText
    global seenTips
    global ratingAverage
    currTip = None
    while len(listOfTips) > 0:
        currTip = listOfTips.pop()
        if not currTip[7] in seenTips:
            seenTips.append(currTip[7])
            break
        else:
            listOfSeenTips.append(currTip)
            currTip = None
    
    if currTip is None and len(listOfSeenTips) > 0:
        currTip = listOfSeenTips.pop()
    elif currTip is None: 
        currTip = ["There are no more tips!!!"] + [None]*10
        canvas.itemconfig(currTipText, text="")
        titleText.set("Map found: " + setMap.get() + "\nTip: " + currTip[0])
        return

    print(currTip)
    ratingQuery = f"SELECT avg(rating) FROM ratings WHERE tip = {currTip[6]}"
    ratingAverage = connectAndQuery(ratingQuery)
    if ratingAverage[0][0] is not None:
        ratingLabel.config(text = "overall rating: " + str(round(ratingAverage[0][0], 2)))
    else:
        ratingLabel.config(text = "overall rating: No rating yet")
    #TODO: reset the link once alec is done
    webSiteLink.set(f"")
    titleText.set("Map found: " + setMap.get() + "\nTip: " + currTip[0])
    canvas.itemconfig(currTipText, text=currTip[1])

def uploadGame():
    print("what game would you like people to make tips for?")
    setState("uploading game")

global currGame

def uploadToDB():
    global currGame
    query = f"INSERT INTO games VALUES(\'{inputGameStr.get()}\') RETURNING *"
    currGame = connectAndQuery(query)[0]

def addCharacterToGame():
    global currGame
    query = f"INSERT INTO characters VALUES(\'{inputCharStr.get()}\', {currGame[0][1]}) RETURNING *"
    connectAndQuery(query)

def addMapToGame():
    global currGame
    query = f"INSERT INTO maps VALUES(\'{inputMapStr.get()}\', {currGame[0][1]}) RETURNING *"
    connectAndQuery(query)

def editExistingGame():
    global currGame
    query = f"SELECT * FROM games WHERE name = \'{setGame.get()}\'"
    currGame = connectAndQuery(query)
    setState("editing existing game")

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

matchOverButton = Button(win, text = "match over", fg = "black",
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
buttons.append(nextTipButton)

uploadGameButton = Button(win, text= "upload a new game", fg = "black",
                            command=uploadGame)
buttons.append(uploadGameButton)

uploadToDBButton = Button(win, text= "upload a new game", fg = "black",
                            command=uploadToDB)
buttons.append(uploadToDBButton)

addCharacterToGameButton = Button(win, text = "add character", fg = "black",
                            command = addCharacterToGame)
buttons.append(addCharacterToGameButton)

addMapToGameButton = Button(win, text = "add map", fg = "black",
                            command= addMapToGame)
buttons.append(addMapToGameButton)

editExistingGameButton = Button(win, text = "edit this game?", fg = "black",
                            command= editExistingGame)
buttons.append(editExistingGameButton)

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
    if setGame.get() != "select game":
        confirmGameButton["state"] = ACTIVE
        editExistingGameButton["state"] = ACTIVE
        if loggedInUser != None:
            createTipButton["state"] = ACTIVE
    else:
        confirmGameButton["state"] = DISABLED
        editExistingGameButton["state"] = DISABLED

setGame.trace('w', checkGameSelected)

def checkMapSelected(*args):
    if setMap.get() != "select map":
        confirmMapButton["state"] = ACTIVE
    else:
        confirmMapButton["state"] = DISABLED

setMap.trace('w', checkMapSelected)

def checkCharSelected(*args):
    if setCharacter.get() != "select character":
        confirmPreferencesButton["state"] = ACTIVE
        saveFavoritesButton["state"] = ACTIVE
    else:
        confirmPreferencesButton["state"] = DISABLED
        saveFavoritesButton["state"] = DISABLED

setCharacter.trace('w', checkCharSelected)

def checkRatingSelected(*args):
    if loggedInUser != None:
        confirmRatingButton["state"] = ACTIVE
    else:
        confirmRatingButton["text"] = "Please login to rate"

setRating.trace('w', checkRatingSelected)

# allow window to accept inputs while running ocr
thread = threading.Thread(target = ocrStuff, args = ())
thread._stop = threading.Event()

#displayImage()

setState("selecting game")
confirmGameButton["state"] = DISABLED
retrieveSeenTips()

win.mainloop()
saveSeenTips()
exit(0)
