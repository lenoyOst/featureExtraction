import features
import featurExtraction
class Machine():
    def __init__(self, lst):
        self.median = statistics.median(lst)
        minV = min(lst)
        maxV = max(lst)
        self.minV = minV - (median - minV)
        self.maxV = maxV + (maxV - median)
    def detect(self, value):
        if(value < self.median):
            return max(100*(value-self.minV)/(self.median-self.minV), 0)
        else:
            return max(100 - 100*(value - self.median)/(self.maxV-self.median), 0)

class Identifier():
    def __init__(self, fs):
        self.total = []
        for i in range(14):
            row = []
            for j in range(3):
                arr = []
                for k in range(len(fs)):
                    arr.append(fs[k][i][j])
                machine = Machine(arr)
                row.append(machine)
            self.total.append(row)              
    def detect(self, f):
        result = []
        for i in range(14):
            row = []
            for j in range(3):
                row.append(self.total[i][j].detect(f[i][j]))
            result.append(row)
        return result

mayas = [98, 100, 101, 103, 105, 106, 112, 113]
omers = [93, 94, 96]
rans = [109, 111]

maya = 107
omer = 95
ran = 110

fs = []
for drive in mayas:
    fs.extend(featurExtraction.loopExtract(str(drive), 5))

lst = featurExtraction.loopExtract(str(maya), 5).reverse()
f = lst[0]

identifier = Identifier(fs)
result = identifier.detect(f)

for i in range(14):
    print(result[i])