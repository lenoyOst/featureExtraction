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
# For nural network
import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import SGD
import matplotlib.pyplot as plt

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

def getCustomerCarIds():
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

    cursor.execute("select customer_car_id from customer_car")
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
            writer.writerow(drivef)

def defineNuralNetwork(X_train,X_test,y_train,y_test):
    # Initialize the constructor
    model = Sequential()

    # Add an input layer 
    model.add(Dense(12, activation='sigmoid', input_shape=(37,), use_bias=True))

    # Add one hidden layer 
    model.add(Dense(8, activation='sigmoid'))

    # Add an output layer 
    model.add(Dense(1, activation='sigmoid'))

    # Model output shape
    model.output_shape

    # Model summary
    model.summary()

    # Model config
    model.get_config()

    # List all weight tensors 
    #model.get_weights()

    opt = SGD(learning_rate=0.01)

    model.compile(loss='binary_crossentropy',
                optimizer=opt,
                metrics=['accuracy'])
                    
    history = model.fit(X_train, y_train,epochs=500, batch_size=1024, verbose=1, validation_data=(X_test, y_test))

    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('Loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'validation'], loc='upper left')
    plt.show()
    
def startDecisionTree( X_train, y_train,X_test,y_test):
    clf = DecisionTreeClassifier(criterion="entropy", max_depth=3)
    # Train Decision Tree Classifer
    clf = clf.fit(X_train,y_train)
    #Predict the response for test dataset
    y_pred = clf.predict(X_test)
    print("predict" , y_pred)

def getArrayOfTrainsTestsData(col_names,feature_cols):
    arr=[]
    driveIDs=[]
    numberOfDrives=0
    for id in getCustomerCarIds():
        for drive in getDriveIDs(id):
            driveIDs.append(drive)
            numberOfDrives=numberOfDrives+1
    for testNum in range(numberOfDrives):
        with open('dataTrain.csv', 'w', newline='') as file:
            index = 0
            test=[]
            writer = csv.writer(file)
            fs=[]
            for drive in driveIDs:
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
                writer.writerow(drivef)
        pima = pd.read_csv("dataTrain.csv", header=None, names=col_names)
        X_train = pima[feature_cols] # Features
        y_train = pima.label # Target variable
        pima = pd.read_csv("dataTest.csv", header=None, names=col_names)
        X_test = pima[feature_cols] # Features
        y_test = pima.label # Target variable
        arr.append((x_train,y_train,x_test,y_test))
    return arr
    




if(__name__ == "__main__"):
    col_names = []
    feature_cols=[]
    for i in range(1,38):
        col_names.append(str(i))
        feature_cols.append(str(i))
    col_names.append('label')
    for touple in getArrayOfTrainsTestsData(col_names, feature_cols):
        
    # load dataset
    getDataRandomTest([16,17,22,21])
    pima = pd.read_csv("dataTrain.csv", header=None, names=col_names)
    X_train = pima[feature_cols] # Features
    y_train = pima.label # Target variable
    y_train_nural=np.ravel(y_train)
    pima = pd.read_csv("dataTest.csv", header=None, names=col_names)
    X_test = pima[feature_cols] # Features
    y_test = pima.label # Target variable
    y_test_nural=np.ravel(y_test)
    #nural network
    ##defineNuralNetwork(X_train, X_test, y_train_nural, y_test_nural)
    #decision tree
    ##startDecisionTree(X_train, y_train, X_test, y_test)

