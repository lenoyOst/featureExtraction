import random
from numpy.lib.type_check import isreal
import features
import featurExtraction
import mysql
import csv
import pandas as pd
from sklearn.model_selection import train_test_split
import numpy as np
from random import randint

from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import BaggingClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import LogisticRegressionCV
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier

import concurrent.futures
import time
import datetime

Guess = tuple[int, int]

#SQL connection

connection = mysql.connector.connect(
            host = "127.0.0.1",
            user = "root",
            password = "OMEome0707",
            database = "ottomate",
            auth_plugin='mysql_native_password'
        )
cursor = connection.cursor()

def reconnect() -> None:
    connection.close()
    connection = mysql.connector.connect(
            host = "127.0.0.1",
            user = "root",
            password = "OMEome0707",
            database = "ottomate",
            auth_plugin='mysql_native_password'
        )
    cursor = connection.cursor()

#SQL queries
def getDriveIDs(customer_car_id = None) -> list[int]:
    #get drive id's
    if(customer_car_id is None):
        #all drive id's (except the trashed one's)
        cursor.execute('SELECT drive_id FROM drive WHERE customer_car_id != 15')
    else:
        #drive id's of customer_car_id
        cursor.execute('SELECT drive_id FROM drive WHERE customer_car_id = '+str(customer_car_id))
    
    result = cursor.fetchall()
    result = list(map(lambda  row: row[0], result))
    return result

def getCustomerCarIds(car_id = None, customer_id = None) -> list[int]:
    #get customer_car id's
    if(car_id is None and customer_id is None):
        #all customer_car id's
        cursor.execute('select customer_car_id from customer_car WHERE customer_id != 0 or car_id != 0')
    elif(customer_id is not None):
        #customer_car id's of customer_id
        cursor.execute('select customer_car_id from customer_car WHERE customer_id = '+str(customer_id))
    elif(car_id is not None):
        #customer_car id's of car_id
        cursor.execute('select customer_car_id from customer_car WHERE car_id = '+str(car_id))
    else:
        #customer_car id's of customer_id and car_id
        cursor.execute('select customer_car_id from customer_car WHERE customer_id = '+str(customer_id)+'and car_id == '+str(car_id))
    
    result = cursor.fetchall()
    result = list(map(lambda  row: row[0], result))
    return result

def getRealCustomerCarIds() -> list[int]:
    #get real customer_car id's
    cursor.execute("select customer_car_id from customer_car where customer_id != 0")
    result = cursor.fetchall()

    result = list(map(lambda  row: row[0], result))
    return result

def getThiefCustomerCarIds() -> list[int]:
    #get thief customer_car id's
    cursor.execute("select customer_car_id from customer_car where customer_id = 0 and car_id != 0")
    result = cursor.fetchall()

    result = list(map(lambda  row: row[0], result))
    return result

def getCarIDs(customer_car_id = None) -> list[str]:
    if(customer_car_id is None):
        cursor.execute("select distinct car_id from customer_car where car_id != 0")
    else:
        cursor.execute("select distinct car_id from customer_car where customer_car_id = "+str(customer_car_id))
    
    result = cursor.fetchall()
    result = list(map(lambda  row: row[0], result))
    return result 

def getDriveIDsByOpen(open) -> list[int]:
    #get drive id's
    if(open):
        #all opened drive id's
        cursor.execute('SELECT drive_id FROM drive WHERE end_time is null')
    else:
        #drive closed id's
        cursor.execute('SELECT drive_id FROM drive WHERE end_time is not null')

    result = cursor.fetchall()
    result = list(map(lambda  row: row[0], result))
    return result

def getDriveIDsCustomerCarIDs(open):
    #get drive id's, customer car id's
    if(open):
        #all opened
        cursor.execute('SELECT drive_id, customer_car_id FROM drive WHERE end_time is null')
    else:
        #all closed
        cursor.execute('SELECT drive_id, customer_car_id FROM drive WHERE end_time is not null')

    result = cursor.fetchall()
    return result

def tryCloseDrive(driveID) -> bool:
    cursor.execute('SELECT max(time) FROM drive_characteristics WHERE drive_id = '+str(driveID))
    result = cursor.fetchall()
    first_time = result[0][0]

    reconnect()
    time.sleep(1)

    cursor.execute('SELECT max(time) FROM drive_characteristics WHERE drive_id = '+str(driveID))
    result = cursor.fetchall()
    second_time = result[0][0]
    
    if(first_time == second_time):
        cursor.execute("UPDATE drive SET end_time = '"+first_time+"' WHERE drive_id = "+str(driveID))
        connection.commit()
        return True

    return False

#split train test
def oneTestRestTrain(customerCarIDs):
    col_names = []
    feature_cols=[]
    
    for i in range(1,43):
        col_names.append(str(i))
        feature_cols.append(str(i))
    col_names.append('label')

    result=[]
    driveIDs=[]

    for customerCarID in customerCarIDs:
        for driveID in getDriveIDs(customerCarID):
            driveIDs.append((driveID,customerCarID))

    for testNum in range(len(driveIDs)):
        test=[]
        with open('dataTrain.csv', 'w', newline='') as file:
            index = 0
            writer = csv.writer(file)
            fs=[]
            for drive in driveIDs:
                for feature in featurExtraction.loopExtract(str(drive[0]) , 5):
                    fs_sub=[]
                    for name in features.Feature:
                        for j in range(3):
                            fs_sub.append(feature[name][j])
                    fs_sub.append(drive[1])
                    if(testNum == index):
                        test.append(fs_sub)
                    else:            
                        fs.append(fs_sub)
                index+=1
            for drivef in fs:
                writer.writerow(drivef)
        with open('dataTest.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            for drivef in test:
                writer.writerow(drivef)
        pima = pd.read_csv("dataTrain.csv", header=None, names=col_names)
        X_train = pima[feature_cols]
        y_train = pima.label
        pima = pd.read_csv("dataTest.csv", header=None, names=col_names)
        X_test = pima[feature_cols]
        y_test = pima.label
        result.append(((X_train,y_train),(X_test,y_test)))
    print(type(result[0][0][0]), type(result[0][0][1]), type(result[0][1][0]), type(result[0][1][1]))
    return result

def precentTestRestTrain(customerCarIDs, precent):   
    col_names = []
    feature_cols=[]
    
    for i in range(1,43):
        col_names.append(str(i))
        feature_cols.append(str(i))
    col_names.append('label')

    if(precent>0 and precent<100):
        with open('dataTrain.csv', 'w', newline='') as file:
            testNum = []
            test=[]
            driveIDs=[]
            writer = csv.writer(file)
            i=0
            for customerCarID in customerCarIDs:
                for drive in getDriveIDs(customerCarID):
                    driveIDs.append((i,customerCarID,drive))
                    i+1
            
           
            sumOfTestDrive=(precent*len(driveIDs))/100
            for i in range(0,sumOfTestDrive):
                rand=randint(0, len(driveIDs))
                if(rand in testNum):
                    i-1
                else:
                    testNum.append(rand)

            index = 0
            fs=[]
            for drive in driveIDs:
                for feature in featurExtraction.loopExtract(str(drive[2]) , 5):
                    fs_sub=[]
                    for name in features.Feature:
                        if(name == features.Feature.driveTime):
                            fs_sub.append(feature[name][0])
                        else:
                            for j in range(3):
                                fs_sub.append(feature[name][j])
                    fs_sub.append(drive[1])
                    if(index in testNum):
                        test.append(fs_sub)
                    else:            
                        fs.append(fs_sub)
                index+=1
            for drivef in fs:
                writer.writerow(drivef)
        with open('dataTest.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            for drivef in test:
                writer.writerow(drivef)
        pima = pd.read_csv("dataTrain.csv", header=None, names=col_names)
        X_train = pima[feature_cols] # Features
        y_train = pima.label # Target variable
        pima = pd.read_csv("dataTest.csv", header=None, names=col_names)
        X_test = pima[feature_cols] # Features
        y_test = pima.label # Target variable
    
    else:
        with open('data.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            for customerCarID in customerCarIDs:
                fs=[]
                for drive in getDriveIDs(customerCarID):
                    for feature in featurExtraction.loopExtract(str(drive) , 5):
                        fs_sub=[]
                        for name in features.Feature:
                            for j in range(3):
                                fs_sub.append(feature[name][j])
                        fs.append(fs_sub)
                for drivef in fs:
                    drivef.append(customerCarID)
                    writer.writerow(drivef)

        pima = pd.read_csv("data.csv", header=None, names=col_names)

        if(precent==0):
            x_train = pima[feature_cols] # Features
            y_train = pima.label # Target variable
            x_test =None
            y_test =None
        else:
            x_test = pima[feature_cols] # Features
            y_test = pima.label # Target variable
            x_train =None
            y_train =None
        
    return ((x_train, y_train),(x_test, y_test))

def allTrain(drives): #list[(driveID,customer_car_id)]
    col_names = []
    feature_cols=[]

    for i in range(1,43):
        col_names.append(str(i))
        feature_cols.append(str(i))
    col_names.append('label')

    with open('data.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            fs=[]
            for drive in drives:
                for feature in featurExtraction.loopExtract(str(drive[0]) , 5):
                    fs_sub=[]
                    for name in features.Feature:
                        for j in range(3):
                            fs_sub.append(feature[name][j])
                    fs_sub.append(drive[1])
                    fs.append(fs_sub)
            for drivef in fs:
                writer.writerow(drivef)

    pima = pd.read_csv("data.csv", header=None, names=col_names)
    return (pima[feature_cols],pima.label)

#guesses
def guesses(model, x_train, y_train, x_test, y_test) -> list[Guess]:
    result = []
    model.fit(x_train, y_train)
    probs = model.predict_proba(x_test)
    for i in range(len(probs)):
        match_value = 0
        match_id = 0
        for j in range(len(probs[i])):
            if(probs[i][j] > match_value):
                match_value = probs[i][j]
                match_id = model.classes_[j]
        if(match_value >= 0.8):
            result.append((y_test[i], match_id))
        else:
            result.append((y_test[i], None))
    return result

def guessToBool(guess) -> bool:
    if(guess[1] is None):
        ans = True
    elif(getCarIDs(guess[0])[0] == getCarIDs(guess[1])[0]):
        ans = False
    else:
        ans = True

    return ans

#tables
def calculateTable(result) -> None:
    tp, tn,fp, fn = 0,0,0,0
    for a, b, _ in result:
        if(a and b):
            tp+=1
        elif(a and not b):
            fp+=1
        elif(not a and b):
            fn+=1
        else:
            tn+=1

    total = tp+tn+fp+fn
    tp = float('{:0.2f}'.format(tp/total*100))
    fp = float('{:0.2f}'.format(fp/total*100))
    tn = float('{:0.2f}'.format(tn/total*100))
    fn = float('{:0.2f}'.format(fn/total*100))
    p = float('{:0.2f}'.format(tp + fp))
    n = float('{:0.2f}'.format(tn + fn))
    t = float('{:0.2f}'.format(tp + tn))
    f = float('{:0.2f}'.format(fp + fn))
    total = float('{:0.2f}'.format(t+f))

    rows = ['True', 'False', 'Total']
    cols = ['Positive', 'Negative', 'Total']
    data = np.array([[tp, fp, p],
                    [tn, fn, n],
                    [t, f, total]])

    row_format ="{:>10}" * (len(rows) + 1)
    print(row_format.format("", *rows))
    for team, col in zip(cols, data):
        print(row_format.format(team, *col))
        
def calculateCarSeperateTable(result) -> None:
    cars = getCarIDs()
    for car in cars:
        tp, tn,fp, fn = 0,0,0,0
        for a, b, c in result:
            if(c == car):
                if(a and b):
                    tp+=1
                elif(a and not b):
                    fp+=1
                elif(not a and b):
                    fn+=1
                else:
                    tn+=1

        total = tp+tn+fp+fn
        tp = float('{:0.2f}'.format(tp/total*100))
        fp = float('{:0.2f}'.format(fp/total*100))
        tn = float('{:0.2f}'.format(tn/total*100))
        fn = float('{:0.2f}'.format(fn/total*100))
        p = float('{:0.2f}'.format(tp + fp))
        n = float('{:0.2f}'.format(tn + fn))
        t = float('{:0.2f}'.format(tp + tn))
        f = float('{:0.2f}'.format(fp + fn))
        total = float('{:0.2f}'.format(t+f))

        rows = ['True', 'False', 'Total']
        cols = ['Positive', 'Negative', 'Total']
        data = np.array([[tp, fp, p],
                        [tn, fn, n],
                        [t, f, total]])

        row_format ="{:>10}" * (len(rows) + 1)
        print('car: ', car)
        print(row_format.format("", *rows))
        for team, col in zip(cols, data):
            print(row_format.format(team, *col))
        print()

#models
def oneModel(model) -> list[tuple[bool, bool, str]]:
    result = []

    #real_drivers
    train_test_arr = oneTestRestTrain(getRealCustomerCarIds())
    for ((x_train, y_train),(x_test, y_test)) in train_test_arr:
        result.extend(list(map(lambda g: (guessToBool(g), False, getCarIDs(g[0])[0]), guesses(model, x_train, y_train, x_test, y_test))))
        
    #theif_drivers
    ((_, _),(x_test, y_test)) = precentTestRestTrain(getThiefCustomerCarIds(), 100)
    ((x_train, y_train),(_,_)) = precentTestRestTrain(getRealCustomerCarIds(), 0)
    result.extend(list(map(lambda g: (guessToBool(g), True, getCarIDs(g[0])[0]), guesses(model, x_train, y_train, x_test, y_test))))
    
    return result

def multyModel(models, min) -> list[tuple[bool, bool, str]]:
    train_test_arr = oneTestRestTrain(getRealCustomerCarIds())
    test_arr = precentTestRestTrain(getThiefCustomerCarIds(), 100)
    train_arr = precentTestRestTrain(getRealCustomerCarIds(), 0)

    results = []
    for model in models:
        result = []

        #real_drivers
        for ((x_train, y_train),(x_test, y_test)) in train_test_arr:
            result.extend(list(map(lambda g: (guessToBool(g), False, getCarIDs(g[0])[0]), guesses(model, x_train, y_train, x_test, y_test))))
            
        #theif_drivers
        ((_, _),(x_test, y_test)) = test_arr
        ((x_train, y_train),(_,_)) = train_arr
        result.extend(list(map(lambda g: (guessToBool(g), True, getCarIDs(g[0])[0]), guesses(model, x_train, y_train, x_test, y_test))))
        
        results.append(result)
    
    result2 = []
    for j in range(len(results[0])):
        count = 0
        for i in range(len(results)):
            if(results[i][j][0]):
                count+=1
        if(count>=min):
            result2.append((True, results[0][j][1], results[0][j][2]))
        else:
            result2.append((False, results[0][j][1], results[0][j][2]))

    return result2

#for finding algorithms
def calculateTrueCol(result) -> float:
    tp, tn,fp, fn = 0,0,0,0
    for a, b, _ in result:
        if(a and b):
            tp+=1
        elif(a and not b):
            fp+=1
        elif(not a and b):
            fn+=1
        else:
            tn+=1

    total = tp+tn+fp+fn
    tp = float('{:0.2f}'.format(tp/total*100))
    tn = float('{:0.2f}'.format(tn/total*100))
    t = float('{:0.2f}'.format(tp + tn))
    return t
        
def mulyModelForTrueCols(models) -> list[float]:
    train_test_arr = oneTestRestTrain(getRealCustomerCarIds())
    test_arr = precentTestRestTrain(getThiefCustomerCarIds(), 100)
    train_arr = precentTestRestTrain(getRealCustomerCarIds(), 0)

    results = []
    for model in models:
        result = []

        #real_drivers
        for ((x_train, y_train),(x_test, y_test)) in train_test_arr:
            result.extend(list(map(lambda g: (guessToBool(g), False, getCarIDs(g[0])[0]), guesses(model, x_train, y_train, x_test, y_test))))
            
        #theif_drivers
        ((_, _),(x_test, y_test)) = test_arr
        ((x_train, y_train),(_,_)) = train_arr
        result.extend(list(map(lambda g: (guessToBool(g), True, getCarIDs(g[0])[0]), guesses(model, x_train, y_train, x_test, y_test))))
        
        results.append(result)
    
    trueColsResults=[]
    for result in results:
        trueColsResults.append(calculateTrueCol(result))
    
    return trueColsResults

#closing drives
def closeDrives() -> None:
    for drive_id in getDriveIDsByOpen(True):
        tryCloseDrive(drive_id)

#main
def checkAccurency() -> None:
    result = multyModel([LogisticRegressionCV(random_state=0), LogisticRegression(random_state=0), MLPClassifier(random_state=0, max_iter=1000), GradientBoostingClassifier(random_state=0), LinearDiscriminantAnalysis()], 4)
    #result = oneModel(LogisticRegressionCV(random_state=0))
    calculateTable(result)
    calculateCarSeperateTable(result)

#closeDrives()

def realTimeCheck(driveID):
    minute = 5
    sectionNum = 4
    
    #learn
    pass
    #end learn
    
    #test
    time.sleep(sectionNum*minute*60)

    ended =False

    while(not ended):
        ended = tryCloseDrive(driveID)
        if(ended):
            f = featurExtraction.sectionExtract(driveID, minute, sectionNum)
            #calc
            pass
            #end calc

        else:
            beforeExtracting = datetime.now()
            f = featurExtraction.sectionExtract(driveID, minute, sectionNum)
            afterExtracting = datetime.now()

            #calc
            pass
            #end calc

            delta = (afterExtracting - beforeExtracting).total_seconds()
            if(delta <minute*60):
                time.sleep(delta - minute*60)
            sectionNum+=1

checkAccurency()