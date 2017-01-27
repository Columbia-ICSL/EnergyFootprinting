import json
import web
import cloudserver
from KNNalgo import KNearestNeighbors

urls = (
"/","train")

class LocationPredictor:
    def __init__(self):
        #read sample data from DB
        samples=cloudserver.db.getAllLocationSamples()
        pairs=[(s["sample"],s["label"]) for s in samples]

        #prepare KNN
        self.KNN=KNearestNeighbors(pairs)

        #list_of_rooms={}
        list_of_rooms_each_lab={}
        for room in cloudserver.db.ROOM_DEFINITION:
            id=room["id"]
            lab=room["lab"]
            #if id not in list_of_rooms:
            #    list_of_rooms[id]=id

            if lab not in list_of_rooms_each_lab:
                list_of_rooms_each_lab[lab]=[]
            list_of_rooms_each_lab[lab]+=[id]

        #prepare lab prior, as a list of votes (roomID, #vote)
        prior_vote_const=2
        self.prior_votes={}
        self.prior_votes[0]=[]
        for lab in list_of_rooms_each_lab:
            if lab>0:
                prior=[]
                for id in list_of_rooms_each_lab[lab]:
                    prior.append((id,prior_vote_const))
                self.prior_votes[lab]=prior

        print("prior votes:")
        print(self.prior_votes)


    def personal_classifier(self, ID, sample):
        prior=[]
        screenName=cloudserver.db.userIDLookup(ID)
        if screenName!=None:
            usernameAttributes = cloudserver.db.getAttributes(screenName, False)
            labInt = usernameAttributes["lab"]
            prior=self.prior_votes[labInt]

        nearest_votes=self.KNN.get_nearest_pairs(sample)
        result_pair=self.KNN.majority_vote(prior+nearest_votes)

        return result_pair[0]
     
        #prepare prior knowledge, or None
        #run KNN
        #find maximum
        #return roomID

class train:
    trainingData = []
    trainingLabels = []
    def generate(self):
        infile = "backup2.txt"
        f = open(infile, 'r')
        x = f.readlines()
        for i in range(len(x)):
            y = x[i].split('\t')
            last = y[-1].split('\n')
            y[-1] = last[0]
            y=[int(v) for v in y]
            self.trainingData.append(y)

        infile = "backuplabels2.txt"
        f = open(infile, 'r')
        x = f.readlines()
        for j in range(len(x)):
            y = x[j]
            last = y.split('\n')
            y = last[0]
            self.trainingLabels.append(y)

        #if(len(self.trainingData)!=len(self.trainingLabels)):
        #    raise Exception("Training data and Training label length don't match.")
        #cloudserver.db.DestroyLocationSamples()
        #for i in range(len(self.trainingLabels)):
        #    cloudserver.db.addLocationSample(self.trainingLabels[i],self.trainingData[i])
        #print(str(len(self.trainingLabels))+" samples Added to database from text file.")

    def POST(self):
        raw_data=web.data()
        locs = raw_data.split(',')

        if (locs[0] == "REUP"):
            infile = "backup.txt"
            f = open(infile, 'r')
            x = f.readlines()
            self.trainingData = []
            for i in range(len(x)):
                y = x[i].split('\t')
                last = y[-1].split('\n')
                y[-1] = last[0]
                y = map(int, y)
                self.trainingData.append(y)
            infile = "backuplabels.txt"
            f = open(infile, 'r')
            x = f.readlines()
            self.trainingLabels = []
            for j in range(len(x)):
                y = x[j]
                last = y.split('\n')
                y = last[0]
                self.trainingLabels.append(y)
            infile = "backup2.txt"
            f = open(infile, 'r')
            x = f.readlines()
            for i in range(len(x)):
                y = x[i].split('\t')
                last = y[-1].split('\n')
                y[-1] = last[0]
                y = map(int, y)
                self.trainingData.append(y)
            infile = "backuplabels2.txt"
            f = open(infile, 'r')
            x = f.readlines()
            for j in range(len(x)):
                y = x[j]
                last = y.split('\n')
                y = last[0]
                self.trainingLabels.append(y)                
            return "successful reupload"
        if (locs[0] == "DES"):
            self.trainingData = []
            self.trainingLabels = []
            return "successful destroy"

        l = locs[1:]
        if (locs[0] == "GET"):
            #outfile = "backup2.txt"
            #with open(outfile, 'w') as file:
            #    file.writelines('\t'.join(str(j) for j in i) + '\n' for i in self.trainingData)
            #outfile2 = "backuplabels2.txt"
            #with open(outfile2, 'w') as file:
            #    file.writelines(str(self.rooms[i]) + '\n' for i in self.trainingLabels)
            #locs = map(int, l)
            #if (len(self.trainingLabels) < self.K):
            #    ret = "not enough data,"
            #    ret += str(len(self.trainingLabels))
            #    return ret

            locs = map(int, l)
            print('Location Predict request:',locs)
            KNN = KNearestNeighbors(list(zip(self.trainingData, self.trainingLabels)))
            pairs=KNN.get_nearest_pairs(locs)
            print('Predicted pairs:',pairs)
            location = KNN.majority_vote(pairs)
            print(location)
            return str(location[0])+':'+str(location[1]) + ",LOL"
        ID = locs[0]
        intID = ID
        locs = map(int, l)
        self.trainingData.append(locs)
        self.trainingLabels.append(intID)
        print('Submitted ID=',ID)
        print('Training sample=',locs)
        cloudserver.db.addLocationSample(ID, locs)
        return str(cloudserver.db.countLocationSamples())+" LOL"

    def GET(self):
        #result = cloudserver.db.QueryLocationData(0)
        return

locationTraining = web.application(urls, locals());
