from xlwt import Workbook
import mysql.connector
import datetime
import functools
import math
import operator
import statistics
import scipy.stats

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
        return self.driveType+": " + str(self.incline) +", " + str(self.startSpeed) + " to " + str(self.endSpeed)
    def startPoint(self):
        return (self.startTime, self.startSpeed)
    def endPoint(self):
        return (self.endTime, self.endSpeed)

def connect(h, u, p, d):
    return mysql.connector.connect(
        host = h,
        user = u,
        password = p,
        database = d
    )
    
def getDriveSpeedData(db, id):
    mycursor = db.cursor()
    mycursor.execute("SELECT start_time FROM drive WHERE drive_id = "+id)
    result = mycursor.fetchall()
    startTime = result[0][0]
    mycursor.execute("SELECT time, speed FROM drive_characteristics WHERE drive_id = "+id)
    result = mycursor.fetchall()
    return list(map(lambda couple: (((datetime.datetime.strptime(couple[0], "%Y-%m-%d %H:%M:%S.%f") - startTime).total_seconds(), couple[1])), result))

def CreatespeedGraph(speedDriveData):  
    name = input("enter name:   ")

    wb = Workbook()
    s = wb.add_sheet(name)
    
    points = list()

    count = 0
    for i in range(0, len(speedDriveData)):
        s.write(i, 1, speedDriveData[i][1])
        s.write(i, 0, speedDriveData[i][0])

    wb.save(name+'.xls')

def driveSpeedSegments(speedDriveData):  
    
    points = []

    for i in range(1, len(speedDriveData)):
        if(speedDriveData[i][1] - speedDriveData[i-1][1] == 0):
            points.append((speedDriveData[i][0], speedDriveData[i][1]))

    c = 1
    start = 0
    end = 1
    segments = []
    
    while(end +1 < len(points)):
        segment1 = Segment(points[start][0], points[end][0], points[start][1], points[end][1])
        segment2 = Segment(points[end][0], points[end+1][0], points[end][1], points[end+1][1])
        diffrence = abs(segment1.incline - segment2.incline)
        if((diffrence < c and diffrence > 0 - c) and segment1.incline*segment2.incline >= 0):
             end += 1
        else:
            segments.append(segment1)
            start = end
            end = start + 1

    newSegments = []
    isThereConstant = False
    for segment in segments:
        if(not segment.isConstant()):
            if(isThereConstant):
                newSegments.append(cSegment)
                isThereConstant = False
            newSegments.append(segment)
        elif(isThereConstant):
            cSegment = Segment(cSegment.startTime, cSegment.endTime, cSegment.startSpeed, cSegment.endSpeed, 'c')
        else:
            cSegment = segment
            isThereConstant = True
    if(isThereConstant):
        newSegments.append(cSegment)

            
    return newSegments    

def AccelerationFromZero(segments):
    return list(filter(lambda segment: segment.startSpeed < 10 and segment.isAcceleration(), segments))

def DeccelerationToZero(segments):
    return list(filter(lambda segment: segment.endSpeed < 10 and segment.isDecceleration(), segments))

def Constant(segments):
    return list(filter(lambda segment: segment.isConstant(), segments))

def pearsons(segments, driveSpeedData):
    pearson = []
    for segment in segments:
        points = driveSpeedData[driveSpeedData.index(segment.startPoint()): driveSpeedData.index(segment.endPoint())+1]
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

driveID = input("enter driveID:   ")
connection = connect ("84.229.64.27", "Omer", "OMEome0707", "ottomate")
driveSpeedData = getDriveSpeedData(connection, driveID)
segments = driveSpeedSegments(driveSpeedData)
accelerations = list(map(lambda segment: segment.incline, AccelerationFromZero(segments)))
deccelerations = list(map(lambda segment: segment.incline, DeccelerationToZero(segments)))
pearson = pearsons(segments, driveSpeedData)

while(True):
    choise = input("enter choise (graph/segments/a/d/p):   ")
    if(choise == "graph"):
        CreatespeedGraph(driveSpeedData)
    elif(choise == "segments"):
        for segment in segments:
            print(segment.toString())
    elif(choise == "a"):
        print(statistic(accelerations))
    elif(choise == "d"):
        print(statistic(deccelerations))
    elif(choise == 'p'):
        print(statistic(pearson))
    else:
        print("done")
        break

#     calculate the "real" speed in constant segment (קו מגמה/ממוצע)
#     calculate how much the speeds are far from the "real" speed