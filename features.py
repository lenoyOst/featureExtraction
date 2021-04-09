from xlwt import Workbook
import mysql.connector
import datetime
import functools
import math
import operator
import statistics

class Segment:
    def __init__(self, startTime, endTime, startSpeed, endSpeed):
        self.startTime = startTime
        self.endTime = endTime
        self.startSpeed = startSpeed
        self.endSpeed = endSpeed
        self.incline = ((endSpeed - startSpeed) / 3.6) / (endTime - startTime).total_seconds()
        if(startSpeed == 0):
                self.driveType = 'a'
        else:
            precents = abs(endSpeed - startSpeed) / startSpeed
            if(precents > 0.2):
                if(self.incline>0):
                    self.driveType = 'a'
                else:
                    self.driveType = 'd'
            else:
                self.driveType = 'c'
    def isAcceleration(self):
        return self.driveType == 'a'
    def isDecceleration(self):
        return self.driveType == 'd'
    def isConstant(self):
        return self.driveType == 'c'
    def toString(self):
        return self.driveType+": " + str(self.incline) +", " + str(self.startSpeed) + " to " + str(self.endSpeed)

def connect(h, u, p, d):
    return mysql.connector.connect(
        host = h,
        user = u,
        password = p,
        database = d
    )
    
def getDriveSpeedData(db, id):
    mycursor = db.cursor()
    mycursor.execute("SELECT time, speed FROM drive_characteristics WHERE drive_id = "+id)
    result = mycursor.fetchall()
    return list(map(lambda couple: (datetime.datetime.strptime(couple[0], "%Y-%m-%d %H:%M:%S.%f"), couple[1]), result))

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
    
    points = list()

    count = 0
    for i in range(1, len(speedDriveData)):
        if(speedDriveData[i][1] - speedDriveData[i-1][1] == 0):
            points.append((speedDriveData[i][0], speedDriveData[i][1]))

    c = 1
    start = 0
    end = 1
    couples = list()
    
    while(end +1 < len(points)):
        segment1 = Segment(points[start][0], points[end][0], points[start][1], points[end][1])
        segment2 = Segment(points[end][0], points[end+1][0], points[end][1], points[end+1][1])
        diffrence = abs(segment1.incline - segment2.incline)
        if((diffrence < c and diffrence > 0 - c) and segment1.incline*segment2.incline >= 0):
             end += 1
        else:
            couples.append(segment1)
            start = end
            end = start + 1

    return couples    

def AccelerationFromZero(segments):
    return list(filter(lambda segment: segment.startSpeed < 10 and segment.isAcceleration(), segments))

def DeccelerationToZero(segments):
    return list(filter(lambda segment: segment.endSpeed < 10 and segment.isDecceleration(), segments))

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

while(True):
    choise = input("enter choise (graph/segments/a/d):   ")
    if(choise == "graph"):
        CreatespeedGraph(driveSpeedData)
    elif(choise == "segments"):
        for segment in segments:
            print(segment.toString())
    elif(choise == "a"):
        print(statistic(accelerations))
    elif(choise == "d"):
        print(statistic(deccelerations))
    else:
        print("done")
        break