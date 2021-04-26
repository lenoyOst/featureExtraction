import features
import featurExtraction
import statistics
import math
import mysql
from xlwt import Workbook
import os

def getDriveIDs(customer_car_id):
    connection = mysql.connector.connect(
            #host = "84.229.65.93",
            host = "84.94.84.90",
            #host = "127.0.0.1",
            user = "Omer",
            #user = "root",
            password = "OMEome0707",
            database = "ottomate",
            auth_plugin='mysql_native_password'
        )
    cursor = connection.cursor()

    cursor.execute("SELECT drive_id FROM drive WHERE customer_car_id = "+str(customer_car_id))
    result = cursor.fetchall()

    result = list(map(lambda  row: row[0], result))
    return result


def getVariances():
    if not os.path.exists('Variances'):
        os.mkdir('Variances')

    wb = Workbook()
        
        #21
        
    fs=[]
    customer_car_id=input("enter: " )
    for drive in getDriveIDs(customer_car_id):
        for feature in featurExtraction.loopExtract(str(drive) , 5):
            fs_sub=[]
            for name in features.Feature:
                for j in range(3):
                    fs_sub.append(feature[name][j])
            fs.append(fs_sub)
            
    vriances=[]
    for i in range(42):
        temp=[]
        for drive in fs:
            temp.append(drive[i]) 
        vriances.append((i+1,statistics.variance(temp)) )
    vriances.sort(key=(lambda touple: touple[1]))

    s = wb.add_sheet(str(customer_car_id))
    for i in range(42):
        s.write(i, 1, vriances[i][0])
        s.write(i, 0, vriances[i][1])

    wb.save('Variances/'+str(customer_car_id)+'.csv')

if(__name__ == "__main__"):
    getVariances()