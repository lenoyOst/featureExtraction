import decisionTree
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
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
# For nural network
import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import SGD
import matplotlib.pyplot as plt

def BoolToNumber(b):
    if(b):
        return 1
    else:
        return 0
arr=decisionTree.getArrayOfTrainsTestsData()
scores = {16: [], 17:[], 19:[], 21:[], 22:[]}
lables = [16, 17, 19, 21, 22]

for a in arr:
    x_train = (a[0][0])
    y_train = (a[0][1])
    x_test = (a[1][0])
    y_test = (a[1][1])

    #model = LogisticRegression(solver='liblinear', random_state=0)
    model1 = LinearDiscriminantAnalysis()
    #model = KNeighborsClassifier()
    model2 = DecisionTreeClassifier( random_state=0)
    model3 = GaussianNB()
    #model = SVC(gamma='auto', probability=True)
    model1.fit(x_train, y_train)
    model2.fit(x_train, y_train)
    model3.fit(x_train, y_train)

    match = []
    match.append(list(map(lambda subarr: subarr[lables.index(y_test[0])]*100, model1.predict_proba(x_test))))
    match.append(list(map(lambda subarr: subarr[lables.index(y_test[0])]*100, model2.predict_proba(x_test))))
    match.append(list(map(lambda subarr: subarr[lables.index(y_test[0])]*100, model3.predict_proba(x_test))))
    match = list(map(lambda row: list(map(lambda value: BoolToNumber(value>= 80), row)), match))
    results = []
    for i in range(len(match[0])):
        results.append((match[0][i] + match[1][i] +match[2][i]) >= 2)
    scores[y_test[0]].extend(results)

for key in scores:
    count = len(scores[key])
    good = len(list(filter(lambda value: value == True, scores[key])))
    print(key, (good/count)*100)