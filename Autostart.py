import runpy
import psutil
import time
import psycopg2
from tkinter import messagebox

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


games = []
for value in connectAndQuery("SELECT name FROM games"):
    games.append(value[0])
print(games)
gameNotFound = True
while gameNotFound:
    time.sleep(1)
    for p in psutil.process_iter(attrs=['name']):
        process = p.info['name'].lower().split('.')[0]
        for game in games:
            if process in game.lower() and process != '':
                print(f"Found process: {process} that matches game: {game}")
                gameNotFound = False
                break
        if not gameNotFound: break

answer = messagebox.askyesno("Question","Do you want to run Intuitive Intel?")

if answer:
    runpy.run_path(path_name='.\\UI_Window.py')

