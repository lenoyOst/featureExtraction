from xlwt import Workbook
import mysql.connector
import datetime
import functools
import math
import operator
import statistics
import scipy.stats

def connect(h, u, p, d):
    return mysql.connector.connect(
        host = h,
        user = u,
        password = p,
        database = d
    )

def getLastUpdate(db, id):
    mycursor = db.cursor()
    mycursor.execute("SELECT MAX(time) FROM drive_characteristics WHERE drive_id = "+id)
    result = mycursor.fetchall()
    return result

driveID = input("enter driveID:   ")
while(True):
    if(input() == 'done'):
        break
    connection = connect ("84.229.64.49", "Omer", "OMEome0707", "ottomate")
    print(getLastUpdate(connection, driveID))