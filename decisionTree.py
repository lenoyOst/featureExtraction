import features
import featurExtraction
import statistics
import math
import mysql
from xlwt import Workbook
import os
import csv
from random import randint
# Load libraries
import pandas as pd
from sklearn.tree import DecisionTreeClassifier # Import Decision Tree Classifier
from sklearn.model_selection import train_test_split # Import train_test_split function
from sklearn import metrics #Import scikit-learn metrics module for accuracy calculation

def getDriveIDs(customer_car_id):
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

def getData(IDs):   
    with open('data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        for ID in IDs:
            fs=[]
            for drive in getDriveIDs(ID):
                for feature in featurExtraction.loopExtract(str(drive) , 5):
                    fs_sub=[]
                    for name in features.Feature:
                        for j in range(3):
                            fs_sub.append(feature[name][j])
                    fs.append(fs_sub)
            for drivef in fs:
                drivef.append(ID)
                writer.writerow(drivef)

def getDataRandomTest(IDs):   
    with open('dataTrain.csv', 'w', newline='') as file:
        testNum = -1
        test=[]
        writer = csv.writer(file)
        for ID in IDs:
            index = 0
            leng = len(getDriveIDs(ID))
            testNum = randint(0,leng-1)
            fs=[]
            for drive in getDriveIDs(ID):
                for feature in featurExtraction.loopExtract(str(drive) , 5):
                    fs_sub=[]
                    for name in features.Feature:
                        if(name == features.Feature.driveTime):
                            fs_sub.append(feature[name][0])
                        else:
                            for j in range(3):
                                fs_sub.append(feature[name][j])
                    if(testNum == index):
                        fs_sub.append(ID)
                        test.append(fs_sub)
                    else:            
                        fs.append(fs_sub)
                index+=1
            for drivef in fs:
                drivef.append(ID)
                writer.writerow(drivef)
    with open('dataTest.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        for drivef in test:
            #drivef.append(ID)
            writer.writerow(drivef)

if(__name__ == "__main__"):
    col_names = []
    feature_cols=[]
    for i in range(1,38):
        col_names.append(str(i))
        feature_cols.append(str(i))
    col_names.append('label')
    # load dataset
    getDataRandomTest([16,17,22,21])
    pima = pd.read_csv("dataTrain.csv", header=None, names=col_names)
    X_train = pima[feature_cols] # Features
    y_train = pima.label # Target variable
    #X_train, a, y_train, b = train_test_split(X, y, test_size=0, random_state=1) 
    pima = pd.read_csv("dataTest.csv", header=None, names=col_names)
    X_test = pima[feature_cols] # Features
    y_test = pima.label # Target variable
    #c, X_test, d, y_test = train_test_split(X, y, test_size=100, random_state=1) 

    clf = DecisionTreeClassifier(criterion="entropy", max_depth=3)

    # Train Decision Tree Classifer
    clf = clf.fit(X_train,y_train)

    #Predict the response for test dataset
    y_pred = clf.predict(X_test)
    print("predict" , y_pred)