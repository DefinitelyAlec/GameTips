from runpy import run_path
from psutil import process_iter
from time import sleep
from psycopg2 import connect
from tkinter import messagebox
from os import getcwd
from sys import argv

def connectAndQuery(query):
    listToReturn = None
    try:
        print("Connected.")
        connection = connect(user="anyone", password="teamgametips",\
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

if not len(argv) > 1:
    print("No path provided. Exiting.")
    exit()
games = []
for value in connectAndQuery("SELECT name FROM games"):
    games.append(value[0].replace(" ", "").strip())
gameNotFound = True
games.append("GenshinImpact")
while gameNotFound:
    sleep(1)
    for p in process_iter(attrs=['name']):
        process = p.info['name'].lower().split('.')[0]
        for game in games:
            if process in game.lower() and process != '':
                print(f"Found process: {process} that matches game: {game}")
                gameNotFound = False
                break
        if not gameNotFound: break

path = argv[1]
print(f"running: {path}")
answer = messagebox.askyesno("Question","Do you want to run Intuitive Intel?")

if answer:
    
    run_path(path_name=path)

