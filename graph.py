import features
import mysql
import sys

def main(argv):
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

    features.createGraph(cursor, argv[0], connection)

if(__name__ == "__main__"):
    if(len(sys.argv) != 2):
        print("USE: [driveID]")
    else:
        main(sys.argv[1:])
