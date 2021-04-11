from xlwt import Workbook
import mysql.connector
import datetime
import functools
import math
import operator
import statistics
import scipy.stats
import numpy

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
    def __init__(self, startTime, endTime, startSpeed, endSpeed, driveType = 'n'):
        self.startTime = startTime
        self.endTime = endTime
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
    def __init__(self, driveID):
        self.id = driveID

        connection = mysql.connector.connect(
            host = "84.229.64.49",
            user = "Omer",
            password = "OMEome0707",
            database = "ottomate"
        )
        cursor = connection.cursor()
        cursor.execute("SELECT start_time FROM drive WHERE drive_id = "+self.id)
        result = cursor.fetchall()
        startTime = result[0][0]
        cursor.execute("SELECT time, speed FROM drive_characteristics WHERE drive_id = "+self.id)
        result = cursor.fetchall()
        self.speedData = list(map(lambda couple: (((datetime.datetime.strptime(couple[0], "%Y-%m-%d %H:%M:%S.%f") - startTime).total_seconds(), couple[1])), result))

        points = []
        for i in range(1, len(self.speedData) -1):
            if((self.speedData[i][1] - self.speedData[i-1][1]) * (self.speedData[i+1][1] - self.speedData[i][1]) <= 0):
                points.append((self.speedData[i][0], self.speedData[i][1]))

        c = 0.8
        start = 0
        end = 1
        segments = []
        while(end +1 < len(points)):
            segment1 = Segment(points[start][0], points[end][0], points[start][1], points[end][1])
            segment2 = Segment(points[end][0], points[end+1][0], points[end][1], points[end+1][1])
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
                cSegment = Segment(cSegment.startTime, segment.endTime, cSegment.startSpeed, segment.endSpeed, 'c')
            else:
                cSegment = segment
                isThereConstant = True
        if(isThereConstant):
            self.speedSegments.append(cSegment) 

        cursor.execute("SELECT MIN(throtle_precentage) FROM drive_characteristics WHERE drive_id = "+self.id)
        result = cursor.fetchall()
        minPedal = result[0][0]

        cursor.execute("SELECT time, throtle_precentage FROM drive_characteristics WHERE drive_id = "+self.id)
        result = cursor.fetchall()
        self.pedalData = list(map(lambda couple: (((datetime.datetime.strptime(couple[0], "%Y-%m-%d %H:%M:%S.%f") - startTime).total_seconds(), couple[1] - minPedal)), result))
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
    def SpeedAccelerationsFromZero(self):        
        accelerations = list(filter(lambda segment: segment.startSpeed < 10 and segment.isAcceleration(), self.speedSegments))
        return list(map(lambda segment: segment.incline, accelerations))
    def SpeedDeccelerationsToZero(self):
        deccelerations = list(filter(lambda segment: segment.endSpeed < 10 and segment.isDecceleration(), self.speedSegments))
        return list(map(lambda segment: segment.incline, deccelerations))
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

def statistic(arr):
    count = len(arr)
    if(count == 0):
        return None
    avg = sum(arr)/count
    return [avg, statistics.variance(arr), statistics.median(arr)]

drive = Drive(input("enter driveID:   "))


file = open(drive.id+".txt", 'w')
lines = []
lines.append("1) "+str(statistic(drive.SpeedAccelerationsFromZero()))+'\n')
lines.append("2) "+str(statistic(drive.SpeedDeccelerationsToZero()))+'\n')
lines.append("3) "+str(statistic(drive.diffrencesFromAvgConstantSpeed()))+'\n')
lines.append("4) "+str(statistic(drive.distancesFromRegressionSpeedAcceleration()))+'\n')
lines.append("5) "+str(statistic(drive.distancesFromRegressionSpeedDecceleration()))+'\n')
lines.append("6) "+str(statistic(drive.distancesFromRegressionConstantSpeed()))+'\n')
lines.append("7) "+str(statistic(drive.PedalAccelerationFromZero()))+'\n')
lines.append("8) "+str(statistic(drive.pearsons()))+'\n')

file.writelines(lines)
file.close()

if (input("create excel files? (y/n)   ") == 'y'):
    drive.createSpeedGraph(drive+"speeds")
    drive.createSpeedSegmentGraph(drive+"segments")
    drive.createPedalGraph(drive +"pedals")