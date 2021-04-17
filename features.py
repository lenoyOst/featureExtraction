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
                if(endSpeed < 5):
                    self.driveType = 'c'
                else:
                    self.driveType = 'a'
            else:
                precents = abs(endSpeed - startSpeed) / startSpeed
                if(precents > 0.2 and not (startSpeed <10 and endSpeed <10)):
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
    def __init__(self, cursor , driveId):
        self.id = driveId
        #getting the speedData array from the DB (setting the correct time stemps)
        cursor.execute("SELECT start_time FROM drive WHERE drive_id = "+self.id)
        result = cursor.fetchall()
        startTime = result[0][0]
        cursor.execute("SELECT time, speed FROM drive_characteristics WHERE drive_id = "+self.id)
        result = cursor.fetchall()
        self.speedData = list(map(lambda couple: (((datetime.datetime.strptime(couple[0], "%Y-%m-%d %H:%M:%S.%f") - startTime).total_seconds(), couple[1])), result))
        #calculating the constant/acceleration/decceleration segments 
        points = []
        for i in range(1, len(self.speedData) -1):
            if((self.speedData[i][1] - self.speedData[i-1][1]) * (self.speedData[i+1][1] - self.speedData[i][1]) <= 0):
                points.append((self.speedData[i][0], self.speedData[i][1]))
        c = 0.8
        start = 0
        end = 1
        segments = []
        while(end +1 < len(points)):
            segment1 = Segment(points[start][0], points[end][0], points[start][1], points[end][1] ,  start , end)
            segment2 = Segment(points[end][0], points[end+1][0], points[end][1] , points[end+1][1] , start , end)
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
        cursor.execute("SELECT MIN(pedal_degree) FROM drive_characteristics WHERE drive_id = "+self.id)
        result = cursor.fetchall()
        minPedal = result[0][0]

        cursor.execute("SELECT time, pedal_degree FROM drive_characteristics WHERE drive_id = "+self.id)
        result = cursor.fetchall()
        self.pedalData = list(map(lambda couple: (((datetime.datetime.strptime(couple[0], "%Y-%m-%d %H:%M:%S.%f") - startTime).total_seconds(), couple[1] - minPedal)), result))
        #speedLimit
        cursor.execute("SELECT time, lat , latD , lon , lonD FROM drive_characteristics WHERE drive_id = "+self.id) 
        result = cursor.fetchall()
        self.speedLimitData = list(map(lambda row : ((datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S.%f") - startTime).total_seconds(), getSpeedLimit(convertGpsDateTo_latlon(row[1],row[2],row[3],row[4]))) , result))
    def createSpeedGraph(self, name):
        wb = Workbook()
        s = wb.add_sheet(name)
        for i in range(len(self.speedData)):
            s.write(i, 1, self.speedData[i][1])
            s.write(i, 0, self.speedData[i][0])
        wb.save(name+'.xls')
    def createSpeedSegmentGraph(self, name):
        wb = Workbook()
        s = wb.add_sheet(name)
        for i in range(len(self.speedSegments)):
            s.write(i, 1, self.speedSegments[i].startSpeed)
            s.write(i, 0, self.speedSegments[i].startTime)
        wb.save(name+'.xls')
    def createPedalGraph(self, name):
        wb = Workbook()
        s = wb.add_sheet(name)
        for i in range(len(self.pedalData)):
            s.write(i, 1, self.pedalData[i][1])
            s.write(i, 0, self.pedalData[i][0])
        wb.save(name+'.xls')
        #lenoy test
    def createMaxPedalGraph(self, name):
        wb = Workbook()
        s = wb.add_sheet(name)
        points = [] 
        for i in range(1, len(self.pedalData) -1):
            if((self.pedalData[i][1] - self.pedalData[i-1][1]) * (self.pedalData[i+1][1] - self.pedalData[i][1]) <= 0):
                points.append((self.speedData[i][0], self.speedData[i][1]))
        for i in range(len(points)):
            s.write(i, 1, self.pedalData[i][1])
            s.write(i, 0, self.pedalData[i][0])
        wb.save(name+'.xls')
    def SpeedAccelerationsFromZero(self):        
        accelerations = list(filter(lambda segment: segment.startSpeed < 10 and segment.isAcceleration(), self.speedSegments))
        return list(map(lambda segment: segment.incline, accelerations))
    def SpeedDeccelerationsToZero(self):
        deccelerations = list(filter(lambda segment: segment.endSpeed < 10 and segment.isDecceleration(), self.speedSegments))
        return list(map(lambda segment: segment.incline, deccelerations))
    #pedal 
    def extreme_points_in_constant(self):
        constants = list(filter(lambda segment: segment.isConstant(), self.speedSegments))
        extremePointsInSegment = []
        for segment in constants:
            for i in range(segment.startIndex + 1 ,segment.endIndex - 1):
                count = 0
                if((self.pedalData[i][1] - self.pedalData[i-1][1]) * (self.pedalData[i+1][1] - self.pedalData[i][1]) <= 0):
                    count+=1
            extremePointsInSegment.append(count / (segment.endTime - segment.startTime))
        return extremePointsInSegment

    def inclines_of_pedal_press_in_constant(self):
        constants = list(filter(lambda segment: segment.isConstant(), self.speedSegments))
        inclines = []
        for segment in constants:
            for i in range(segment.startIndex + 1 , segment.endIndex):
                if((self.pedalData[i][1] - self.pedalData[i-1][1]) * (self.pedalData[i+1][1] - self.pedalData[i][1]) <= 0): 
                    num = self.pedalData[i][1] - self.pedalData[i-1][1] / (self.pedalData[i][0] - self.pedalData[i-1][0])
                    if(num >= 0):   
                        inclines.append(num)
        return inclines
    
    def inclines_of_pedal_release_in_constant(self):
        constants = list(filter(lambda segment: segment.isConstant(), self.speedSegments))
        inclines = []
        for segment in constants:
            for i in range(segment.startIndex + 1 , segment.endIndex+1):
                if((self.pedalData[i][1] - self.pedalData[i-1][1]) * (self.pedalData[i+1][1] - self.pedalData[i][1]) <= 0): 
                    num = self.pedalData[i][1] - self.pedalData[i-1][1] / (self.pedalData[i][0] - self.pedalData[i-1][0])
                    if(num <= 0):   
                        inclines.append(num)
        return inclines
    def constant_time_press_constant(self):
        constants = list(filter(lambda segment: segment.isConstant(), self.speedSegments))
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

    def constant_time_release_constant(self):
        constants = list(filter(lambda segment: segment.isConstant(), self.speedSegments))
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
    #end pedal related manipulation
    def diffrencesFromAvgConstantSpeed(self):
        constant = list(filter(lambda segment: segment.isConstant(), self.speedSegments))
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
        return list(map(lambda middleDistances: (sum(middleDistances[1])/len(middleDistances[1]))/middleDistances[0], middlesDistancess))
    
    def distancesFromRegressionSpeedDecceleration(self):
        constant = list(filter(lambda segment: segment.isDecceleration(), self.speedSegments))
        segments = list(map(lambda segment: self.speedData[self.speedData.index(segment.startPoint()): self.speedData.index(segment.endPoint())+1], constant))
        lines = list(map(lambda pointList: (pointList ,Line(pointList)), segments))
        middlesDistancess = list(map(lambda pointsLine : (pointsLine[1].middleSpeed, list(map(lambda point: pointsLine[1].distance(point), pointsLine[0]))), lines))
        return list(map(lambda middleDistances: (sum(middleDistances[1])/len(middleDistances[1]))/middleDistances[0], middlesDistancess))
    
    def distancesFromRegressionConstantSpeed(self):
        constant = list(filter(lambda segment: segment.isConstant(), self.speedSegments))
        segments = list(map(lambda segment: self.speedData[self.speedData.index(segment.startPoint()): self.speedData.index(segment.endPoint())+1], constant))
        segments = list(filter(lambda pointsList: not all(point[1] == 0 for point in pointsList), segments))
        lines = list(map(lambda pointList: (pointList ,Line(pointList)), segments))
        middlesDistancess = list(map(lambda pointsLine : (pointsLine[1].middleSpeed, list(map(lambda point: pointsLine[1].distance(point), pointsLine[0]))), lines))
        return list(map(lambda middleDistances: (sum(middleDistances[1])/len(middleDistances[1]))/middleDistances[0], middlesDistancess))
    
    def PedalAccelerationFromZero(self):
        accelerations = []
        for i in range(len(self.pedalData) - 1):
            if(self.pedalData[i][1] == 0 and self.pedalData[i+1][1] != 0):
                start = self.pedalData[i]
            elif(self.pedalData[i][1] > self.pedalData[i+1][1]):
                accelerations.append((self.pedalData[i][1] - start[1]) / self.pedalData[i][0] - start[0])
        return accelerations
    def pearsons(self):
        pearson = []
        for segment in self.speedSegments:
            points = self.speedData[self.speedData.index(segment.startPoint()): self.speedData.index(segment.endPoint())+1]
            x = list(map(lambda point: point[0], points))
            y = list(map(lambda point: point[1], points))
            if(all(speed == y[0] for speed in y)):
                pearson.append(1)
            else:
                pearson.append(abs(scipy.stats.pearsonr(x, y)[0]))
        return pearson
    #speed limit statiscs
    def time_above_speedLimit(self):
        constant = list(filter(lambda segment : segment.isConstant(),self.speedSegments))
        timeAboveSpeedLimit = []
        for segment in constant:
            time = 0
            for i in range(segment.startIndex , segment.endIndex):
                if((self.speedLimitData[i][1] is not None) and self.speedLimitData[i][1] < self.speedData[i][1]):
                    time+=self.speedLimitData[i+1][0] - self.speedLimitData[i][0]
            timeAboveSpeedLimit.append(time/(self.speedLimitData[segment.endIndex][0] - self.speedLimitData[segment.startIndex][0]))
        return timeAboveSpeedLimit 
    def speed_above_speedLimit(self):
        constant = list(filter(lambda segment : segment.isConstant(),self.speedSegments))
        speedAboveSpeedLimit = []
        for segment in constant:
            for i in range(segment.startIndex , segment.endIndex):
                if((self.speedLimitData[i][1] is not None) and self.speedLimitData[i][1] < self.speedData[i][1]):
                    speedAboveSpeedLimit.append(self.speedData[i][1] / self.speedLimitData[i][1])
        return speedAboveSpeedLimit   
    def speed_below_speedLimit(self):
        constant = list(filter(lambda segment : segment.isConstant(),self.speedSegments))
        speedBelowSpeedLimit = []
        for segment in constant:
            for i in range(segment.startIndex , segment.endIndex):
                if((self.speedLimitData[i][1] is not None) and self.speedLimitData[i][1] > self.speedData[i][1]):
                    speedBelowSpeedLimit.append(self.speedData[i][1] / self.speedLimitData[i][1])
        return speedBelowSpeedLimit 
    #end speed limit
def statistic(arr):
    count = len(arr)
    if(count == 0):
        return None
    avg = sum(arr)/count
    return [avg, statistics.variance(arr), statistics.median(arr)]

def extract(cursor , driveId):
    drive = Drive(cursor , driveId )

    file = open(drive.id+".txt", 'w')
    lines = []
    lines.append("1) "+str(statistic(drive.SpeedAccelerationsFromZero()))+'\n')
    lines.append("2) "+str(statistic(drive.SpeedDeccelerationsToZero()))+'\n')
    lines.append("3) "+str(statistic(drive.diffrencesFromAvgConstantSpeed()))+'\n')
    lines.append("4) "+str(statistic(drive.distancesFromRegressionSpeedAcceleration()))+'\n')
    lines.append("5) "+str(statistic(drive.distancesFromRegressionSpeedDecceleration()))+'\n')
    lines.append("6) "+str(statistic(drive.distancesFromRegressionConstantSpeed()))+'\n')
    lines.append("7) "+str(statistic(drive.PedalAccelerationFromZero()))+'\n')
    lines.append("8) "+str(statistic(drive.inclines_of_pedal_press_in_constant()))+'\n')
    lines.append("9) "+str(statistic(drive.inclines_of_pedal_release_in_constant()))+'\n')
    lines.append("10) "+str(statistic(drive.constant_time_press_constant()))+'\n')
    lines.append("11) "+str(statistic(drive.constant_time_release_constant()))+'\n')
    lines.append("12) "+str(statistic(drive.extreme_points_in_constant()))+'\n')
    lines.append("13) "+str(statistic(drive.time_above_speedLimit()))+'\n')
    lines.append("14) "+str(statistic(drive.speed_above_speedLimit()))+'\n')
    lines.append("15) "+str(statistic(drive.speed_below_speedLimit()))+'\n')

    file.writelines(lines)
    file.close()
def createGrafe(cursor , driveId):
    drive = Drive(cursor , driveId )
    drive.createSpeedGraph(drive.id+"speeds")
    drive.createSpeedSegmentGraph(drive.id+"segments")
    drive.createPedalGraph(drive.id +"pedals")
    drive.createMaxPedalGraph(drive.id +"Maxpedals")
