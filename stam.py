from xlwt import Workbook
import mysql.connector
import datetime
import functools
import math
import operator
import statistics
import scipy.stats
import numpy

id = input("enter something you bitch:   ")
connection = mysql.connector.connect(
    host = "84.229.64.49",
    user = "Omer",
    password = "OMEome0707",
    database = "ottomate"
)
cursor = connection.cursor()
cursor.execute("SELECT start_time FROM drive WHERE drive_id = "+id)
result = cursor.fetchall()
startTime = result[0][0]
cursor.execute("SELECT time, throtle_precentage FROM drive_characteristics WHERE drive_id = "+id)
result = cursor.fetchall()
pedalData = list(map(lambda couple: (((datetime.datetime.strptime(couple[0], "%Y-%m-%d %H:%M:%S.%f") - startTime).total_seconds(), couple[1])), result))

wb = Workbook()
s = wb.add_sheet(id+" pedal")
for i in range(len(pedalData)):
    s.write(i, 1, pedalData[i][1])
    s.write(i, 0, pedalData[i][0])
wb.save(id+ "pedal"+'.xls')