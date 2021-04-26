import features
import featurExtraction
import statistics
import math
import mysql

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

class Machine2():
    def __init__(self, lst):
        
        self.median = sum(lst)/len(lst)
        #self.median = statistics.median(lst)
        #self.variance = math.sqrt(statistics.variance(lst))
        
        self.varianceL = 0
        self.varianceR = 0
        nR = 0
        nL = 0
        for value in lst:
            if(value >= self.median):
                nR += 1
                self.varianceR += ((value - self.median)**2)
            if(value <= self.median):
                nL += 1
                self.varianceL += ((self.median - value)**2)
        if(nR == 0):
            self.varianceR = 0
        else:
            self.varianceR = math.sqrt(self.varianceR/nR)

        if(nL == 0):
            self.varianceL = 0
        else:
            self.varianceL = math.sqrt(self.varianceL/nL)

        minV = min(lst)
        maxV = max(lst)

        self.maxL = self.median - self.varianceL
        self.minR = self.median + self.varianceR      
        self.minL = minV - (self.maxL - minV)
        self.maxR = maxV + (maxV - self.minR)

    def detect(self, value):
        if(value >= self.maxL and value <= self.minR):
            return 100  

        if(value < self.maxL):
            if(self.minL == self.maxL):
                return -1 
            return max(100*(value-self.minL)/(self.maxL-self.minL), 0)
        elif(value > self.minR):
            if(self.minR == self.maxR):
                return -1  
            return max(100 - 100*(value - self.minR)/(self.maxR-self.minR), 0)
        else:
            return -1
class Machine():
    def __init__(self, lst):
        self.median = sum(lst)/len(lst)
        #self.median = statistics.median(lst)
        minV = min(lst)
        maxV = max(lst)
        self.minV = minV - (self.median - minV)
        self.maxV = maxV + (maxV - self.median)
    def detect(self, value):
        if(self.median == self.maxV or self.median == self.minV):
            if(value == self.median):
                return 101
            else:
                return -1
        if(value < self.median):
            return max(100*(value-self.minV)/(self.median-self.minV), 0)
        else:
            return max(100 - 100*(value - self.median)/(self.maxV-self.median), 0)


class Identifier2():
    def __init__(self, customer_car_id):
        test = []
        for j in range(14):
            test.append( [[],[],[]])
        
        drives = getDriveIDs(customer_car_id)
        for i in range(len(drives)):
            arr = []
            if(i == 0):
                arr = drives[i+1:len(drives)]
            elif(i == len(drives) - 1):
                arr = drives[0:i]
            else:
                arr = drives[0:i]
                arr.extend(drives[i+1:len(drives)])
            fs = []
            for d in arr:
                a = featurExtraction.loopExtract(str(d), 5)
                a.reverse()
                fs.extend(a)
            identifier = Identifier(fs)

            f = featurExtraction.loopExtract(str(drives[i]), 5)
            f.reverse()
            f = f[0]

            result = identifier.detect(f)
            for j in range(14):
                for k in range(3):
                    test[j][k].append(result[j][k])
        self.isToLearn = list(map(lambda row: list(map(lambda arr: (sum(map(lambda value: value >= 85 , arr)) / len(arr)) > 0.65, row)),test))
        self.weight =   [[1, 0, 1]
                        ,[1, 1, 1]
                        ,[0, 0, 0.5]
                        ,[0.5, 0, 0.5]
                        ,[0, 0, 0]
                        ,[0, 0, 0]
                        ,[1, 0, 0]
                        ,[0, 0, 0]
                        ,[0, 0, 0]
                        ,[0, 0, 0]
                        ,[0, 0, 0]
                        ,[0, 0, 0]
                        ,[0, 0, 0]
                        ,[0, 0, 0]]
        fs = []
        for drive in drives:
            a = featurExtraction.loopExtract(str(drive), 5)
            a.reverse()
            fs.extend(a)

        self.total = []
        for s in features.Feature:
            row = []
            for j in range(3):
                arr = []
                for k in range(len(fs)):
                    arr.append(fs[k][s][j])
                machine = Machine2(arr)
                row.append(machine)
            self.total.append(row)              
    def detect(self, f):
        result = []
        i = 0
        for s in features.Feature:
            row = []
            for j in range(3):
                row.append(self.total[i][j].detect(f[s][j]))
            result.append(row)
            i+=1

        answer = 0
        count = 0
        for i in range(14):
            for j in range(3):
                if(self.isToLearn[i][j]):
                    answer += result[i][j] * self.weight[i][j]
                    count += self.weight[i][j]
        return answer / count
class Identifier():
    def __init__(self, fs):
        self.total = []
        for s in features.Feature:
            row = []
            for j in range(3):
                arr = []
                for k in range(len(fs)):
                    arr.append(fs[k][s][j])
                machine = Machine2(arr)
                row.append(machine)
            self.total.append(row)              
    def detect(self, f):
        result = []
        i = 0
        for s in features.Feature:
            row = []
            for j in range(3):
                row.append(self.total[i][j].detect(f[s][j]))
            result.append(row)
            i+=1
        return result

def a():
    test = []
    for j in range(14):
        test.append( [[],[],[]])

    drives = getDriveIDs(16)
    if(len(drives) != 1):
        for i in range(len(drives)):
    
            arr = []
            if(i == 0):
                arr = drives[i+1:len(drives)]
            elif(i == len(drives) - 1):
                arr = drives[0:i]
            else:
                arr = drives[0:i]
                arr.extend(drives[i+1:len(drives)])
        
            fs = []
            for d in arr:
                a = featurExtraction.loopExtract(str(d), 5)
                a.reverse()
                fs.extend(a)
            identifier = Identifier(fs)

            f = featurExtraction.loopExtract(str(drives[i]), 5)
            f.reverse()
            f = f[0]

            result = identifier.detect(f)
            for j in range(14):
                for k in range(3):
                    test[j][k].append(result[j][k])

        for j in range(14):
                for k in range(3):
                    print(sum(map(lambda value: value >= 85, test[j][k])) / len(test[j][k]))
        

    if(False):
        for drive in drives:
            a = featurExtraction.loopExtract(str(drive), 5)
            a.reverse()
            fs.append(a[0])

        identifier = Identifier(fs)

        drives = getDriveIDs(int(input("enter:   ")))

        test = []
        for drive in drives:
            a = featurExtraction.loopExtract(str(drive), 5)
            a.reverse()
            f = a[0]
            test.append(identifier.detect(f)[0][0])

        print(test)

        drives = getDriveIDs(int(input("enter:   ")))

        test = []
        for drive in drives:
            a = featurExtraction.loopExtract(str(drive), 5)
            a.reverse()
            f = a[0]
            test.append(identifier.detect(f)[0][1])

        print(test)

def b():
    identifier = Identifier2(int(input("enter cutomer_car_id to learn:   ")))
    drives = getDriveIDs(int(input("enter cutomer_car_id to check:   ")))
    f = featurExtraction.loopExtract(str(drives[0]), 5)
    f.reverse()
    f = f[0]

    print(identifier.detect(f))

b()