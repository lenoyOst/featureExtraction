import features
import mysql
import sys
import math
import datetime

def main(argv):
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

    cursor.execute('SELECT start_time FROM drive WHERE drive_id = '+argv[0])
    startTime = cursor.fetchall()[0][0]
    cursor.execute('SELECT MAX(time) FROM drive_characteristics WHERE drive_id = '+argv[0])
    endTime = cursor.fetchall()[0][0]
    endTime = datetime.datetime.strptime(endTime, "%Y-%m-%d %H:%M:%S.%f")

    delta = math.ceil((endTime-startTime).total_seconds() / 60)
    features.createGraph(cursor, argv[0], connection, delta)

if(__name__ == "__main__"):
    if(len(sys.argv) != 2):
        print("USE: [driveID]")
    else:
        main(sys.argv[1:])
