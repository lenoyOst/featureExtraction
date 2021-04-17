import features
import mysql
import sys
from time import sleep

def loopExtract(driveID , min):
    stop = False
    connection = mysql.connector.connect(
        host = "84.229.64.49",
        user = "Omer",
        password = "OMEome0707",
        database = "ottomate",
        auth_plugin='mysql_native_password'
    )
    cursor = connection.cursor()
    while(not stop):
        features.extract(cursor , driveID)
        sleep(min*60)
       
        cursor.execute("SELECT end_time FROM drive WHERE drive_id = "+driveID)
        result = cursor.fetchall()
        stop = result[0][0] is not None
def main(argv):
    #argv : [driveID][time in minuets]
    loopExtract(argv[0] ,int(argv[1]))

if(__name__ == "__main__"):
    if(len(sys.argv) != 3):
        print("accpected argv : [driveID][time in minuets]")
    else:
        main(sys.argv[1:])

    