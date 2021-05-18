import features
import mysql
import sys
from time import sleep
import os
import shutil
import datetime
import csv

def sectionExtract(driveID, minute, sectionNum):
    connection = mysql.connector.connect(
        host = "127.0.0.1",
        user = "root",
        password = "OMEome0707",
        database = "ottomate",
        auth_plugin='mysql_native_password'
    )
    cursor = connection.cursor()
    if(not os.path.exists('new_cache/'+driveID+'_'+str(minute*sectionNum)+'.csv')):
        max_id, f = features.extract(cursor , driveID, connection, sectionNum*minute)
        with open('new_cache/'+driveID+'_'+str(minute*sectionNum)+'.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([max_id])
            for key in f:
                writer.writerow(f[key])
        return f
    else:
        with open('new_cache/'+driveID+'_'+str(minute*sectionNum)+'.csv', 'r') as f:
            lis = [line.split(',') for line in f]
            lis = list(map(lambda row: list(map(lambda x: float(''.join(list(filter(lambda c: c!= '\n', x)))), row)), lis))
            max_id = int(lis[0][0])
            f = {}
            i = 1
            for key in features.Feature:
                f[key] = lis[i]
                i+=1
            return f
            
def loopExtract(driveID , minute):
    stop = False
    connection = mysql.connector.connect(
        host = "127.0.0.1",
        user = "root",
        password = "OMEome0707",
        database = "ottomate",
        auth_plugin='mysql_native_password'
    )
    cursor = connection.cursor()
    index = 1

    fs = []        
    while(True):
        if(not os.path.exists('new_cache/'+driveID+'_'+str(minute*index+minute)+'.csv')):
            max_id, f = features.extract(cursor , driveID, connection, index*minute + 5)
            with open('new_cache/'+driveID+'_'+str(minute*index+minute)+'.csv', 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([max_id])
                for key in f:
                    writer.writerow(f[key])
        else:
            with open('new_cache/'+driveID+'_'+str(minute*index+minute)+'.csv', 'r') as f:
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
