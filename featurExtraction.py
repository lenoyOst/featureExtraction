import features
import mysql
import sys
from time import sleep
import os
import shutil
import datetime
import csv


acA, acV, acM = [], [], []
def loopExtract(driveID , min):
    stop = False
    connection = mysql.connector.connect(
        #host = "84.229.65.93",
        #host = "84.94.84.90",
        host = "127.0.0.1",
        #user = "Omer",
        user = "root",
        password = "OMEome0707",
        database = "ottomate",
        auth_plugin='mysql_native_password'
    )
    cursor = connection.cursor()
    index = 1

    fs = []        
    while(True):
        if(not os.path.exists('cache/'+driveID+'_'+str(index)+'.csv')):
            max_id, f = features.extract(cursor , driveID, connection, index*min + 5)
            with open('cache/'+driveID+'_'+str(index)+'.csv', 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([max_id])
                for key in f:
                    writer.writerow(f[key])
        else:
            with open('cache/'+driveID+'_'+str(index)+'.csv', 'r') as f:
                lis = [line.split(',') for line in f]
                lis = list(map(lambda row: list(map(lambda x: float(''.join(list(filter(lambda c: c!= '\n', x)))), row)), lis))
                max_id = int(lis[0][0])
                f = {}
                i = 1
                for key in features.Feature:
                    f[key] = lis[i]
                    i+=1
        fs.append(f)

        cursor.execute("SELECT MAX(drive_characteristics_id) FROM drive_characteristics WHERE drive_id ="+driveID)
        result = cursor.fetchall()
        last_id = result[0][0]
        if(last_id == max_id):
            break

        index+=1
    
    return fs
def main(argv):
    #USE: [driveID] [time in minuets]
    loopExtract(argv[0] ,int(argv[1]))

if(__name__ == "__main__"):
    for drive in daniel:
        main([str(drive), 5])

    if(len(sys.argv) != 3):
        print("USE: [driveID] [time in minuets]")
    else:
        main(sys.argv[1:])