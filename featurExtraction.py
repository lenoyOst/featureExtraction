import features
import mysql
import sys
from time import sleep
import os
import shutil
import datetime

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
    path = driveID
    if not os.path.exists(path):
        os.mkdir(path)        
    while(True):
        file = open(path+'/'+str(index)+'.txt', mode = 'w')
        max_id, f = features.extract(cursor , driveID, connection, index*min)

        for key in f:
            file.write(str(f[key])+'\n')
        file.close()
       
        cursor.execute("SELECT MAX(drive_characteristics_id) FROM drive_characteristics WHERE drive_id ="+driveID)
        result = cursor.fetchall()
        last_id = result[0][0]
        if(last_id == max_id):
            break

        index+=1
def main(argv):
    #USE: [driveID] [time in minuets]
    loopExtract(argv[0] ,int(argv[1]))

if(__name__ == "__main__"):
    for i in [112, 113, 114, 115]:
        print(datetime.datetime.now())
        main([str(i), 5])
        print(datetime.datetime.now())
    if(len(sys.argv) != 3):
        print("USE: [driveID] [time in minuets]")
    else:
        main(sys.argv[1:])

    