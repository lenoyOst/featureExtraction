import features
import mysql

connection = mysql.connector.connect(
        host = "84.229.64.49",
        user = "Omer",
        password = "OMEome0707",
        database = "ottomate",
        auth_plugin='mysql_native_password'
    )
cursor = connection.cursor()

features.createGraph(cursor, '70')