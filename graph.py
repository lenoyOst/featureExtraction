import features
import mysql

connection = mysql.connector.connect(
        #host = "84.229.65.93",
        host = "84.94.84.90",
        user = "Omer",
        password = "OMEome0707",
        database = "ottomate",
        auth_plugin='mysql_native_password'
    )
cursor = connection.cursor()

features.createGraph(cursor, '96')