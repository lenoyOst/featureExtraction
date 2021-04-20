import features
import mysql
import sys
from time import sleep

def loopExtract(driveID , min):
    stop = False
    connection = mysql.connector.connect(
        host = "84.229.65.93",
        #host = "84.94.84.90",
        #host = "127.0.0.1",
        user = "Omer",
        #user = "root",
        password = "OMEome0707",
        database = "ottomate",
        auth_plugin='mysql_native_password'
    )
    cursor = connection.cursor()
    index = 1
    while(not stop):
        file = open(driveID, mode = 'w')
        f = features.extract(cursor , driveID, connection)

        for key in f:
            file.write(str(f[key])+'\n')
        sleep(min*60)
        file.close()
       
        cursor.execute("SELECT end_time FROM drive WHERE drive_id = "+driveID)
        result = cursor.fetchall()
        stop = result[0][0] is not None
        index+=1
def main(argv):
    #USE: [driveID] [time in minuets]
    loopExtract(argv[0] ,int(argv[1]))

if(__name__ == "__main__"):
    if(len(sys.argv) != 3):
        print("USE: [driveID] [time in minuets]")
    else:
        main(sys.argv[1:])

    