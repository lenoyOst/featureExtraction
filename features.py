from xlwt import Workbook
import mysql.connector
import datetime
import functools
import math
import operator
import statistics
import scipy.stats
import numpy
import requests
from enum import Enum
import os

def convertGpsDateTo_latlon(latGPS, latDirection, lonGPS, lonDirection):
    if((latGPS is None) or (latDirection is None) or (lonGPS is None) or (lonDirection is None)):
        return (None,None)
    latGps, lonGps = float(latGPS), float(lonGPS)

    if(latDirection == 'S'):
        latGps = -latGps
    if(lonDirection == 'W'):
        lonGps = -lonGps

    latDeg, lonDeg = int(latGps/100), int(lonGps/100)
    latMin, lonMin = latGps-latDeg * 100, lonGps-lonDeg * 100
    lat, lon = latDeg + (latMin/60), lonDeg + (lonMin/60)
    return lat, lon
def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False
def getSpeedLimit(latlon):
    lat = latlon[0]
    lon = latlon[1]
    if((lat is None) or (lon is None)):
        return None
    x = requests.get(url = 'http://dev.virtualearth.net/REST/v1/Routes/SnapToRoad', params = {"points": str(lat)+","+str(lon), "includeTruckSpeedLimit" : "true", "IncludeSpeedLimit" : "true", "speedUnit" : "kph", "&travelMode" : "driving", "key":"AtRSuwR9wPyTyx2eIa8vOBGprp03EI9QXG_fqHQxpvXPULuqPrBADXLHIjNbJ49D"})
    data = x.text

    speed = ""
    index = 0
    while(index >=0 and index+12 < len(data)):
        index = data.find("speedLimit", index+1)
        if(index == -1):
            break
        while(RepresentsInt(data[index+12])):
            speed+=data[index+12]
            index+=1
        if(len(speed) != 0):
            break
    if(speed!=''):
        return float(speed)
    else:
        return None

def mostCommonSpeedLimit(l):
    counter = {}
    for value in l:
        if(value[1] in counter):
            counter[value[1]] += 1
        else:
            counter[value[1]] = 1
    return sorted(counter, key = counter.get, reverse=True)[0]

class Feature(Enum):
    AccelerationsFromZero = 1
    DeccelerationsToZero = 2
    VarianceConstantSpeed = 3
    DistancesFromRegressionAcceleration = 4
    DistancesFromRegressionDecceleration = 5
    PearsonsAcceleration = 6
    PearsonsDecceleration = 7
    ConstantExtremePedal = 8
    ConstantPressPedalInclines = 9
    ConstantReleasePedalInclines = 10
    ConstantPressPedalTime = 11
    ConstantAboveSpeedLimitTime = 12
    ConstantAboveSpeedLimitSpeeed = 13
    ConstantBelowSpeedLimitSpeeed = 14

class Line:
    def __init__(self, points):
        xs = list(map(lambda point: point[0], points))
        ys = list(map(lambda point: point[1], points))
        self.a = numpy.cov(points)[0][1]/statistics.variance(xs)
        self.b = (sum(ys) / len(ys)) - self.a * (sum(xs) / len(xs))
        self.middleSpeed = (self.f(points[len(points) - 1][0]) - self.f(points[0][0]))/2
    def f(self, x):
        return self.a * x + self.b
    def toString(self):
        return "y="+str(self.a)+"x+"+str(self.b)
    def distance(self, point):
        return abs(point[1] - (self.a * point[0]) - self.b) / math.sqrt(self.a ** 2 + 1)

class Segment:
    def __init__(self, startTime, endTime, startSpeed, endSpeed,startIndex , endIndex, driveType = 'n' ):
        self.startTime = startTime
        self.endTime = endTime
        self.startIndex = startIndex
        self.endIndex = endIndex
        self.startSpeed = startSpeed
        self.endSpeed = endSpeed
        self.incline = ((endSpeed - startSpeed) / 3.6) / (endTime - startTime)
        if(driveType == 'n'):
            if(startSpeed == 0):
                if(endSpeed < 10):
                    self.driveType = 'c'
                else:
                    self.driveType = 'a'
            else:
                precents = abs(endSpeed - startSpeed) / startSpeed
                if(precents > 0.15 and not (startSpeed <10 and endSpeed <10)):
                    if(self.incline>0):
                        self.driveType = 'a'
                    else:
                        self.driveType = 'd'
                else:
                    self.driveType = 'c'
        else:
            self.driveType = driveType
    def isAcceleration(self):
        return self.driveType == 'a'
    def isDecceleration(self):
        return self.driveType == 'd'
    def isConstant(self):
        return self.driveType == 'c'
    def toString(self):
        return self.driveType+": " + str(self.incline) +", " + str(self.startSpeed) + " to " + str(self.endSpeed) +" , " + str(self.startTime)+" to "+str(self.endTime)
    def startPoint(self):
        return (self.startTime, self.startSpeed)
    def endPoint(self):
        return (self.endTime, self.endSpeed)

class Drive:
    def __init__(self, cursor , driveId, connection, time):
        self.id = driveId
        cursor.execute("SELECT start_time FROM drive WHERE drive_id = "+self.id)
        result = cursor.fetchall()
        startTime = result[0][0]
        endTime = startTime +datetime.timedelta(minutes=time)
        cursor.execute("SELECT MAX(drive_characteristics_id) FROM drive_characteristics WHERE drive_id = "+self.id+" and time < '"+datetime.datetime.strftime(endTime, "%Y-%m-%d %H:%M:%S")+"'")
        result = cursor.fetchall()
        self.max_id = str(result[0][0])
        #getting the speedData array from the DB (setting the correct time stemps)
        cursor.execute("SELECT time, speed FROM drive_characteristics WHERE drive_id = "+self.id+" and drive_characteristics_id < "+self.max_id)
        result = cursor.fetchall()
        self.speedData = list(map(lambda couple: (((datetime.datetime.strptime(couple[0], "%Y-%m-%d %H:%M:%S.%f") - startTime).total_seconds(), couple[1])), result))
        for i in range(1, len(self.speedData) -1):
            if(self.speedData[i][1] == 0 and self.speedData[i+1][1] >7 and self.speedData[i-1][1] >7):
                self.speedData[i] = (self.speedData[i][0], self.speedData[i-1][1])
        timeDifference = 0.0
        for i in range (len(self.speedData)-1):
            timeDifference+=(self.speedData[i+1][0] - self.speedData[i][0])
        timeDifference/=(len(self.speedData)-1)
        self.skip = round(0.45/timeDifference)

        #calculating the constant/acceleration/decceleration segments 
        points = []
        for i in range(self.skip, len(self.speedData) - self.skip , self.skip):
            if((self.speedData[i][1] - self.speedData[i-self.skip][1]) * (self.speedData[i+self.skip][1] - self.speedData[i][1]) <= 0):
                points.append((self.speedData[i][0], self.speedData[i][1]))
        
        c = 0.8
        start = 0
        end = 1
        segments = []
        while(end +1 < len(points)):
            segment1 = Segment(points[start][0], points[end][0], points[start][1], points[end][1] ,  self.speedData.index(points[start]) , self.speedData.index(points[end]))
            segment2 = Segment(points[end][0], points[end+1][0], points[end][1] , points[end+1][1] , self.speedData.index(points[end]) , self.speedData.index(points[end+1]))
            diffrence = abs(segment1.incline - segment2.incline)
            if((diffrence < c) and segment1.incline*segment2.incline >= 0):
                end += 1
            else:
                segments.append(segment1)
                start = end
                end = start + 1
        self.speedSegments = []
        isThereConstant = False
        for segment in segments:
            if(not segment.isConstant()):
                if(isThereConstant):
                    self.speedSegments.append(cSegment)
                    isThereConstant = False
                self.speedSegments.append(segment)
            elif(isThereConstant):
                cSegment = Segment(cSegment.startTime, segment.endTime, cSegment.startSpeed, segment.endSpeed,cSegment.startIndex , segment.endIndex, 'c')
            else:
                cSegment = segment
                isThereConstant = True
        if(isThereConstant):
            self.speedSegments.append(cSegment) 

        #getting the pedalData array from the DB (setting the correct time stemps)
        cursor.execute("SELECT MIN(pedal_degree) FROM drive_characteristics WHERE drive_id = "+self.id+" and drive_characteristics_id < "+self.max_id)
        result = cursor.fetchall()
        minPedal = result[0][0]

        cursor.execute("SELECT time, pedal_degree FROM drive_characteristics WHERE drive_id = "+self.id+" and drive_characteristics_id < "+self.max_id)
        result = cursor.fetchall()
        self.pedalData = list(map(lambda couple: (((datetime.datetime.strptime(couple[0], "%Y-%m-%d %H:%M:%S.%f") - startTime).total_seconds(), couple[1] - minPedal)), result))
        
        #speedLimit
        cursor.execute("SELECT time, lat , latD , lon , lonD, speed_limit, drive_characteristics_id FROM drive_characteristics WHERE drive_id = "+self.id+" and drive_characteristics_id < "+self.max_id) 
        result = cursor.fetchall()
        result = list(map(lambda row : ((datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S.%f") - startTime).total_seconds(), row[1],row[2],row[3],row[4], row[5], row[6]) , result))
        constant = list(filter(lambda segment: segment.isConstant() and segment.startSpeed > 10 and segment.endSpeed > 10, self.speedSegments))
        def f(row):
            if (any(row[0] >= segment.startTime and row[0] <= segment.endTime for segment in constant)):
                if(row[5] is None):
                    ans = (row[0], getSpeedLimit(convertGpsDateTo_latlon(row[1],row[2],row[3],row[4])))
                    if(ans[1] is None):
                        ans = (ans[0], -1)
                    cursor.execute("UPDATE drive_characteristics SET speed_limit = "+ str(ans[1])+" WHERE drive_characteristics_id = "+str(row[6]))
                else:
                    ans = (row[0], row[5])
            else:
                ans = (row[0], 0)
                cursor.execute("UPDATE drive_characteristics SET speed_limit = "+ str(ans[1])+" WHERE drive_characteristics_id = "+str(row[6]))
            connection.commit()
            return ans
        self.speedLimitData = list(map(lambda row : f(row) , result))

    #graphs
    def createGraph(self):
        if not os.path.exists('graphs'):
            os.mkdir('graphs')

        wb = Workbook()
        
        #speed
        s = wb.add_sheet("speeds")
        for i in range(len(self.speedData)):
            s.write(i, 1, self.speedData[i][1])
            s.write(i, 0, self.speedData[i][0])
        
        #segments
        s = wb.add_sheet("segments")
        for i in range(len(self.speedSegments)):
            s.write(i, 1, self.speedSegments[i].startSpeed)
            s.write(i, 0, self.speedSegments[i].startTime)

        #pedals
        s = wb.add_sheet("pedals")
        for i in range(len(self.pedalData)):
            s.write(i, 1, self.pedalData[i][1])
            s.write(i, 0, self.pedalData[i][0])
        
        #limits
        s = wb.add_sheet("limits")
        for i in range(len(self.speedLimitData)):
            s.write(i, 1, self.speedLimitData[i][1])
            s.write(i, 0, self.speedLimitData[i][0])
        
        wb.save('graphs/'+self.id+'.xls')
    
    #speed
    def speedAccelerationsFromZero(self):        
        accelerations = list(filter(lambda segment: segment.startSpeed < 10 and segment.isAcceleration(), self.speedSegments))
        return list(map(lambda segment: segment.incline, accelerations))
    def speedDeccelerationsToZero(self):
        deccelerations = list(filter(lambda segment: segment.endSpeed < 10 and segment.isDecceleration(), self.speedSegments))
        return list(map(lambda segment: segment.incline, deccelerations))
    def distancesFromAvgConstantSpeed(self):
        constant = list(filter(lambda segment: segment.isConstant() and segment.startSpeed > 10 and segment.endSpeed > 10, self.speedSegments))
        segments = list(map(lambda segment: self.speedData[self.speedData.index(segment.startPoint()): self.speedData.index(segment.endPoint())+1], constant))
        speedss = list(map(lambda segment: list(map(lambda point: point[1], segment)), segments))
        speedss = list(filter(lambda speeds: not all(speed == 0 for speed in speeds), speedss))
        diffrences = list(map(lambda speeds: statistics.variance(speeds)/(sum(speeds)/len(speeds)), speedss))
        return diffrences
    def distancesFromRegressionSpeedAcceleration(self):
        constant = list(filter(lambda segment: segment.isAcceleration(), self.speedSegments))
        segments = list(map(lambda segment: self.speedData[self.speedData.index(segment.startPoint()): self.speedData.index(segment.endPoint())+1], constant))
        lines = list(map(lambda pointList: (pointList ,Line(pointList)), segments))
        middlesDistancess = list(map(lambda pointsLine : (pointsLine[1].middleSpeed, list(map(lambda point: pointsLine[1].distance(point), pointsLine[0]))), lines))
        return list(map(lambda middleDistances: (sum(middleDistances[1])/len(middleDistances[1])), middlesDistancess))  
    def distancesFromRegressionSpeedDecceleration(self):
        constant = list(filter(lambda segment: segment.isDecceleration(), self.speedSegments))
        segments = list(map(lambda segment: self.speedData[self.speedData.index(segment.startPoint()): self.speedData.index(segment.endPoint())+1], constant))
        lines = list(map(lambda pointList: (pointList ,Line(pointList)), segments))
        middlesDistancess = list(map(lambda pointsLine : (pointsLine[1].middleSpeed, list(map(lambda point: pointsLine[1].distance(point), pointsLine[0]))), lines))
        return list(map(lambda middleDistances: (sum(middleDistances[1])/len(middleDistances[1])), middlesDistancess))   
    def distancesFromRegressionConstantSpeed(self):
        constant = list(filter(lambda segment: segment.isConstant() and segment.startSpeed > 10 and segment.endSpeed > 10, self.speedSegments))
        segments = list(map(lambda segment: self.speedData[self.speedData.index(segment.startPoint()): self.speedData.index(segment.endPoint())+1], constant))
        segments = list(filter(lambda pointsList: not all(point[1] == 0 for point in pointsList), segments))
        lines = list(map(lambda pointList: (pointList ,Line(pointList)), segments))
        middlesDistancess = list(map(lambda pointsLine : (pointsLine[1].middleSpeed, list(map(lambda point: pointsLine[1].distance(point), pointsLine[0]))), lines))
        return list(map(lambda middleDistances: (sum(middleDistances[1])/len(middleDistances[1]))/middleDistances[0], middlesDistancess))   
    def pearsonsAcceleration(self):
        pearson = []
        segments = list(filter(lambda segment: segment.isAcceleration(), self.speedSegments))
        for segment in segments:
            points = self.speedData[self.speedData.index(segment.startPoint()): self.speedData.index(segment.endPoint())+1]
            x = list(map(lambda point: point[0], points))
            y = list(map(lambda point: point[1], points))
            if(all(speed == y[0] for speed in y)):
                pearson.append(1)
            else:
                pearson.append(abs(scipy.stats.pearsonr(x, y)[0]))
        return pearson
    def pearsonsDecceleration(self):
        pearson = []
        segments = list(filter(lambda segment: segment.isDecceleration(), self.speedSegments))
        for segment in segments:
            points = self.speedData[self.speedData.index(segment.startPoint()): self.speedData.index(segment.endPoint())+1]
            x = list(map(lambda point: point[0], points))
            y = list(map(lambda point: point[1], points))
            if(all(speed == y[0] for speed in y)):
                pearson.append(1)
            else:
                pearson.append(abs(scipy.stats.pearsonr(x, y)[0]))
        return pearson    
    
    #pedal 
    def constantExtremePedal(self):
        constants = list(filter(lambda segment: segment.isConstant() and segment.startSpeed > 10 and segment.endSpeed > 10, self.speedSegments))
        extremePointsInSegment = []
        for segment in constants:
            for i in range(segment.startIndex + 1 ,segment.endIndex - 1):
                count = 0
                if((self.pedalData[i][1] - self.pedalData[i-1][1]) * (self.pedalData[i+1][1] - self.pedalData[i][1]) <= 0):
                    count+=1
            extremePointsInSegment.append(count / (segment.endTime - segment.startTime))
        return extremePointsInSegment
    def constantPressPedalInclines(self):
        constants = list(filter(lambda segment: segment.isConstant() and segment.startSpeed > 10 and segment.endSpeed > 10, self.speedSegments))
        inclines = []
        for segment in constants:
            for i in range(segment.startIndex + 1 , segment.endIndex):
                if((self.pedalData[i][1] - self.pedalData[i-1][1]) * (self.pedalData[i+1][1] - self.pedalData[i][1]) <= 0 and (self.pedalData[i][1] - self.pedalData[i-1][1] != 0 or self.pedalData[i+1][1] - self.pedalData[i][1] != 0)): 
                    num = self.pedalData[i][1] - self.pedalData[i-1][1] / (self.pedalData[i][0] - self.pedalData[i-1][0])
                    if(num > 0 or (len(inclines) != 0 and num == 0 and i > inclines[len(inclines) - 1][1] + 2)):   
                        inclines.append((num, i))
        return list(map(lambda pair: pair[0], inclines))   
    def constantReleasePedalInclines(self):
        constants = list(filter(lambda segment: segment.isConstant() and segment.startSpeed > 10 and segment.endSpeed > 10, self.speedSegments))
        inclines = []
        for segment in constants:
            for i in range(segment.startIndex + 1 , segment.endIndex+1):
                if((self.pedalData[i][1] - self.pedalData[i-1][1]) * (self.pedalData[i+1][1] - self.pedalData[i][1]) <= 0 and (self.pedalData[i][1] - self.pedalData[i-1][1] != 0 or self.pedalData[i+1][1] - self.pedalData[i][1] != 0)): 
                    num = self.pedalData[i][1] - self.pedalData[i-1][1] / (self.pedalData[i][0] - self.pedalData[i-1][0])
                    if(num < 0 or (len(inclines) != 0 and num == 0 and i > inclines[len(inclines) - 1][1] + 1)):   
                        inclines.append((num, i))
        return list(map(lambda pair: pair[0], inclines))   
    def constantPressPedalTime(self):
        constants = list(filter(lambda segment: segment.isConstant() and segment.startSpeed > 10 and segment.endSpeed > 10, self.speedSegments))
        extremePoints = []
        timeConstant = []
        j = 0
        for segment in constants:
            for i in range(self.speedData.index(segment.startPoint()) ,self.speedData.index(segment.endPoint()) - 1):
                if((self.pedalData[i][1] - self.pedalData[i-1][1]) * (self.pedalData[i+1][1] - self.pedalData[i][1]) <= 0):
                    extremePoints.append(self.pedalData[i])
                    num = extremePoints[j][1] - extremePoints[j-1][1] * (extremePoints[j][0] - extremePoints[j-1][0])
                    if(num >= 0):
                        timeConstant.append(extremePoints[j][0] - extremePoints[j-1][0])
                    j+=1
        return timeConstant
    def constantReleasePedalTime(self):
        constants = list(filter(lambda segment: segment.isConstant() and segment.startSpeed > 10 and segment.endSpeed > 10, self.speedSegments))
        extremePoints = []
        timeConstant = []
        j = 0
        for segment in constants:
            for i in range(self.speedData.index(segment.startPoint()) ,self.speedData.index(segment.endPoint()) - 1):
                if((self.pedalData[i][1] - self.pedalData[i-1][1]) * (self.pedalData[i+1][1] - self.pedalData[i][1]) <= 0):
                    extremePoints.append(self.pedalData[i])
                    num = extremePoints[j][1] - extremePoints[j-1][1] * (extremePoints[j][0] - extremePoints[j-1][0])
                    if(num <= 0):
                        timeConstant.append(extremePoints[j][0] - extremePoints[j-1][0])
                    j+=1
        return timeConstant
    
    #speedLimit
    def constantAboveSpeedLimitTime(self):
        constant = list(filter(lambda segment : segment.isConstant() and segment.startSpeed > 10 and segment.endSpeed > 10,self.speedSegments))
        timeAboveSpeedLimit = []
        for segment in constant:
            speeds = list(filter(lambda point: point[1] > 0, self.speedLimitData[segment.startIndex:segment.endIndex]))
            if(len(speeds) == 0):
                continue
            speedLimit = mostCommonSpeedLimit(speeds)
            
            time = 0
            for i in range(segment.startIndex , segment.endIndex):
                if( speedLimit < self.speedData[i][1]):
                    time+=self.speedLimitData[i+1][0] - self.speedLimitData[i][0]
            timeAboveSpeedLimit.append(time/(self.speedLimitData[segment.endIndex][0] - self.speedLimitData[segment.startIndex][0]))
        return timeAboveSpeedLimit 
    def constantAboveSpeedLimitSpeeed(self):
        constant = list(filter(lambda segment : segment.isConstant()  and segment.startSpeed > 10 and segment.endSpeed > 10,self.speedSegments))
        speedAboveSpeedLimit = []
        for segment in constant:
            speeds = list(filter(lambda point:  point[1] > 0, self.speedLimitData[segment.startIndex:segment.endIndex]))
            if(len(speeds) == 0):
                continue
            speedLimit = mostCommonSpeedLimit(speeds)
            arr = []
            for i in range(segment.startIndex , segment.endIndex):
                if(speedLimit < self.speedData[i][1]):
                    arr.append(self.speedData[i][1] / speedLimit * 100 - 100)
            if(len(arr) != 0):
                speedAboveSpeedLimit.append(sum(arr)/len(arr))
        return speedAboveSpeedLimit   
    def constantBelowSpeedLimitSpeeed(self):
        constant = list(filter(lambda segment : segment.isConstant() and segment.startSpeed > 10 and segment.endSpeed > 10,self.speedSegments))
        speedBelowSpeedLimit = []
        for segment in constant:
            speeds = list(filter(lambda point: point[1] > 0, self.speedLimitData[segment.startIndex:segment.endIndex]))
            if(len(speeds) == 0):
                continue
            speedLimit = mostCommonSpeedLimit(speeds)
            arr = []
            for i in range(segment.startIndex , segment.endIndex):
                if(speedLimit > self.speedData[i][1]):
                    arr.append(self.speedData[i][1] / speedLimit*100)
            if(len(arr) != 0):
                speedBelowSpeedLimit.append(sum(arr)/len(arr))
            return speedBelowSpeedLimit 

def statistic(arr):
    try:
        count = len(arr)
        avg = sum(arr)/count
        if(len(arr) == 1):
            variance = 0
        else:
            variance = statistics.variance(arr)
        return [avg, variance, statistics.median(arr)]
    except:
        return [0.0,0.0,0.0]

def extract(cursor , driveId, connection, time):
    drive = Drive(cursor , driveId, connection, time)

    features = {}
    features[Feature.AccelerationsFromZero] = statistic(drive.speedAccelerationsFromZero())
    features[Feature.DeccelerationsToZero] = statistic(drive.speedDeccelerationsToZero())
    features[Feature.VarianceConstantSpeed] = statistic(drive.distancesFromAvgConstantSpeed())
    features[Feature.DistancesFromRegressionAcceleration] = statistic(drive.distancesFromRegressionSpeedAcceleration())
    features[Feature.DistancesFromRegressionDecceleration] = statistic(drive.distancesFromRegressionSpeedDecceleration())
    features[Feature.PearsonsAcceleration] = statistic(drive.pearsonsAcceleration())
    features[Feature.PearsonsDecceleration] = statistic(drive.pearsonsDecceleration())
    features[Feature.ConstantExtremePedal] = statistic(drive.constantExtremePedal())
    features[Feature.ConstantPressPedalInclines] = statistic(drive.constantPressPedalInclines())
    features[Feature.ConstantReleasePedalInclines] = statistic(drive.constantReleasePedalInclines())
    features[Feature.ConstantPressPedalTime] = statistic(drive.constantPressPedalTime())
    features[Feature.ConstantAboveSpeedLimitTime] = statistic(drive.constantAboveSpeedLimitTime())
    features[Feature.ConstantAboveSpeedLimitSpeeed] = statistic(drive.constantAboveSpeedLimitSpeeed())
    features[Feature.ConstantBelowSpeedLimitSpeeed] = statistic(drive.constantBelowSpeedLimitSpeeed())

    return int(drive.max_id), features

def createGraph(cursor , driveId, connection, time):
    drive = Drive(cursor , driveId, connection, time)
    drive.createGraph()