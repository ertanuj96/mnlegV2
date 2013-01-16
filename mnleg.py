
import json
from utils import get_contents_of_url,getFromCache,putInCache,substitute_char

API_KEY='4a26c19c3cae4f6c843c3e7816475fae'
base_url='http://openstates.org/api/v1/'
apikey_url="apikey="

def getMNLegAllDistricts():
	#http://openstates.org/api/v1/districts/mn/?apikey=4a26c19c3cae4f6c843c3e7816475fae
	url=base_url+'districts/mn/?'+apikey_url+API_KEY
	return sendGetRequest(url)

def getLegislatorByDistrict(district):
	url=base_url+'legislators/?state=mn&district='+district+'&'+apikey_url+API_KEY
	return sendGetRequest(url)

def getMNLegDistrictById(district_id):
	#http://openstates.org/api/v1/districts/boundary/sldu/mn-11/?apikey=4a26c19c3cae4f6c843c3e7816475fae
	url=base_url+'districts/boundary/'+district_id+'/?'+apikey_url+API_KEY
	return sendGetRequest(url)

def getMNLegAllEvents():
	#http://openstates.org/api/v1/events/?state=mn&apikey=4a26c19c3cae4f6c843c3e7816475fae
	url=base_url+'events/?state=mn&'+apikey_url+API_KEY
	return sendGetRequest(url)

def getMNLegEventById(event_id):
	#http://openstates.org/api/v1/events/MNE00000095/?apikey=4a26c19c3cae4f6c843c3e7816475fae
	url=base_url+'events/'+event_id+'/?'+apikey_url+API_KEY
	return sendGetRequest(url)

def getMNLegAllCommittees():
	url=base_url+'committees/?state=mn&'+apikey_url+API_KEY
	return sendGetRequest(url)

def getMNLegCommitteeById(com_id):
	url=base_url+'committees/'+com_id+'/?'+apikey_url+API_KEY
	return sendGetRequest(url)

def getMNLegislatorById(leg_id):
	url=base_url+'legislators/'+leg_id+'/?'+apikey_url+API_KEY
	return sendGetRequest(url)

def getMNLegislatorByActive():
	url=base_url+'legislators/?state=mn&'+apikey_url+API_KEY
	return sendGetRequest(url)

def getMNLegMetaData():
	url=base_url+'metadata/mn/?'+apikey_url+API_KEY
	return sendGetRequest(url)

def getMNLegBillsbySession(session,per_page='2000',page='1'):
	session_url='state=mn&search_window=session:'+session+'&'
	url=base_url+'bills/?'+session_url+'&per_page='+per_page+'&page='+page+'&'+apikey_url+API_KEY
	return sendGetRequest(url)

def getMNLegBillInfobyId(bill,session):
	url=base_url+'bills/mn/'+session+'/'+bill+'?'+apikey_url+API_KEY
	return sendGetRequest(url)

def sendGetRequest(url):
	url=substitute_char(url,' ','%20')
	response = get_contents_of_url(url)
	if response:
		data=json.loads(response)
		return data
	else:
		return None

def getAllDistricts():
	data=getFromCache('districts')
	if not data:
		data=getMNLegAllDistricts()
		if data:
	 		putInCache('districts',data)
		else:
			return None
	return data

def getDistrictById(district_id):
	data=getFromCache(district_id)
	if not data:
		data=getMNLegDistrictById(district_id)
		if data:
			new_shape=[]
	 		for p in data['shape'][0][0]:
	 			new_shape.append([p[1],p[0]])
	 		data['shape'][0][0]=new_shape
	 		putInCache(district_id,data)
		else:
			return None
	return data

def getAllEvents():
	data=getFromCache('events')
	if not data:
		data=getMNLegAllEvents()
		if data:
	 		putInCache('events',data)
		else:
			return None
	return data

def getEventById(event_id):
	data=getFromCache(event_id)
	if not data:
		data=getMNLegEventById(event_id)
		if data:
	 		putInCache(event_id,data)
		else:
			return None
	return data

def getAllCommittees():
	data=getFromCache('committees')
	if not data:
		data=getMNLegAllCommittees()
		if data:
	 		putInCache('committees',data)
		else:
			return None
	return data

def getCommitteeById(com_id):
	data=getFromCache(com_id)
	if not data:
		data=getMNLegCommitteeById(com_id)
		if data:
	 		putInCache(com_id,data)
		else:
			return None
	return data

def getCurrentLegislators():
	data=getFromCache('legislators')
	if not data:
		data=getMNLegislatorByActive()
		if data:
	 		putInCache('legislators',data)
		else:
			return None
	return data

def getLegislatorByID(leg_id):
	data=getFromCache(leg_id)
	if not data:
		data=getMNLegislatorById(leg_id)
		if data:
	 		putInCache(leg_id,data)
		else:
			return None
	return data

def getBillInfo(bill,session):
	path=session+bill
	data=getFromCache(path)
	if not data:
		data=getMNLegBillInfobyId(bill,session)
		if data:
	 		putInCache(path,data)
		else:
			return None
	return data

def getBillNames(session):
	data=getFromCache(session)
	if not data:
		data=getMNLegBillsbySession(session)
		if data:
			putInCache(session,data)
		else:
			return None
	bills=[]
	for d in data:
		bills.append(d)
	return bills

def getSessionNames():
	data=getFromCache("sessions")
	if not data:
		data=getMNLegMetaData()
		if data:
			putInCache("sessions",data)
		else:
			return None
	session_details=data["session_details"]
	sessions=[]
	for s in session_details:
		sessions.append(s)
	sessions.sort()
	return sessions


