import requests
from requests.auth import HTTPBasicAuth
import pickle
import datetime
from datetime import timedelta
from datetime import date
import json

class SPTokenList:
    def __init__(self, name, password, URL='http://srs.spirent.com/STCRelPlan/'):
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(name, password)
        self.url = URL
    #argument: date from the json file
    #returns: datetime object in isoformat(a string)(so we can compare/sort the date etc)
    @staticmethod 
    def convertDate(unicodeDate):
    	date = str(unicodeDate).lower().split(" ")
	dateDetails = [month, day, year] = date[0].split("/")
	timeday = date[1]+" "+date[2]
	if len(day) != 2:
		day = "0"+day
	if len(month) != 2:
		month = "0"+month
	dateE = year+"-"+month+"-"+day+" "
	#subtract 7 hours because date in json files is 7 hours ahead
	return (datetime.datetime.strptime(dateE+timeday, "%Y-%m-%d %I:%M:%S %p")-timedelta(hours=7)).isoformat()
    def getDate(self, entry):
    	return self.convertDate(entry["Modified"])
    def getList(self):
	r = self.session.get(self.url)
	#throw error if 4xx 5xx response
	r.raise_for_status()
	#order the json file by most recent modified time
	requestList = r.json()["Requests"]
	sortedList = sorted(requestList,key = self.getDate,reverse = True )
	return sortedList
    @staticmethod
    def flush(dictionary):
        f = open("db.p","wb")
        pickle.dump(dictionary, f)
        f.close()
    @staticmethod
    def buildDictFromFile():
        try:
            f = open('db.p','rb')
        except:
            return {}
        dictionary = pickle.load(f)
        f.close()
        return dictionary
    #gets 250 most recent token requests(ordered by modified key)
    def buildDictFromSP(self):
        return self.processList(self.getList(), entries = 250)
    #get a particular token
    def getSPToken(self,created):
        tokenList = self.processList(self.getList(), update=False)
        for requestToken in tokenList:
		if self.convertDate(requestToken["Created"]) == created:
			return requestToken
	return None
    def processList(self, requestList, entries, update=True):
        #get only the first entries(int) entry's
    	requestList = requestList[0:entries]
	data = []
        if update:
            try:
                stamp = open('lastUpdate','r+')
                last = stamp.read()
            except:
                stamp = open('lastUpdate', 'w+')
                last = '0'
        else:
            last = '0'
        if update:
            stamp.seek(0)
	    #always look back 5 minutes to avoid missing a token
            stamp.write((datetime.datetime.now() - timedelta(minutes = 5)).isoformat())
            stamp.close()
        for entry in requestList:
	    modified = self.convertDate(entry["Modified"])
            if modified < last.strip():
                print 'Entries already updated after this point'
                break
	    branch = str(";".join(entry["Branches"]))
            user = str(entry["Users"])
            reason = entry["Reason"]
            status = str(entry["Status"])
	    created = self.convertDate(entry["Created"])
            e = Token(user,reason,branch,status,modified, created)
            data.append(e)
	    if len(data) == 0:
	    	print "Entries already updated after this point"
	#return tokens in reverse so you process the tokens in order of age(process oldest tokens first, then the newer ones. )
        return data[::-1]
class Token:
    def __init__(self, user, reason, branch, status, modDate, created):
        self.user = user
        self.reason = reason
        self.branch = branch
        self.status = status
        self.modDate = modDate
	self.created = created
    def __str__(self):
        return  "User: "+self.user + "\n" +" "*5 +"Reason: "+self.reason + "\n" +" "*5 + "Branch:" +self.branch + "\n"+" "*5 + "Status: "+self.status +"\n" +" "*5 +"Modified: "+ self.modDate +"\n" + " "*5+ "Created: "+self.created
