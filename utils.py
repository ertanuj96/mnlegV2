import hmac
import hashlib
import string
import random
import json
import cgi
import re
import urllib2
import time
import datetime
from xml.dom import minidom
from google.appengine.api import memcache
from google.appengine.api import images
from bs4 import BeautifulSoup

user_re=re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
pass_re=re.compile(r"^.{3,20}$")
email_re=re.compile(r"^[\S]+@[\S]+\.[\S]+$")

var_re=re.compile(r'<var>[0-9]+\.[0-9]+</var>')
markup_id_re=re.compile(r'<a id="pl\.[0-9]+\.[0-9]+"></a>')
anchor_re=re.compile(r'<a id="bill[0-9.]+"></a>')

SECRET = 'somesecretshityo'
IP_URL="http://api.hostip.info/?ip="
mn_senate_base='http://www.senate.leg.state.mn.us'

def resize_image(image,width=0,height=0):
    return images.resize(image, width, height)

def convertDateToTimeStamp(date):
    date=substitute_char(date,'-','')
    date=substitute_char(date,':','')
    try:
        d=datetime.datetime.strptime(date, '%Y%m%d %H%M%S').date()
        t=int(time.mktime(d.timetuple()))
        return str(t)+'000'
    except Exception:
        return None

def convertDateTimeStringtoDateTime(date):
    try:
        d = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        return d
    except Exception:
        return None

def convertCommitteeDateStringtoDate(time_string):
    try:
        t = time.strptime(time_string,'%B %d, %Y %I:%M %p')
        return t
    except Exception:
        return None

def getMonthNumberFromString(s):
    return time.strptime(s,'%B').tm_mon

def getTodaysDate():
    return datetime.date.today()

def offsetDatebyDays(date,days):
    z=datetime.timedelta(days=days)
    return date-z

def getCurrentBillsDateString():
    d=offsetDatebyDays(getTodaysDate(),4)
    return str(d.year)+"-"+str(d.month)+"-"+str(d.day)

def getMNLegislatorByActive():
    url='http://openstates.org/api/v1/legislators/?state=mn&apikey=4a26c19c3cae4f6c843c3e7816475fae'
    return sendGetRequest(url)

def sendGetRequest(url):
    url=substitute_char(url,' ','%20')
    response = get_contents_of_url(url)
    if response:
        data=json.loads(response)
        return data
    else:
        return None

def getCurrentLegislators():
    data=getFromCache('legislators')
    if not data:
        data=getMNLegislatorByActive()
        if data:
            putInCache('legislators',data)
        else:
            return None
    return data

def getLegislatorIDByName(name):
    legs=getCurrentLegislators()
    for l in legs:
        if name.find(l['first_name'][0])>=0 and name.find(l['last_name'])>=0:
            return l['id']

def getSenateCommitteeByID(com_id):
    url='http://www.senate.mn/committees/committee_members.php?ls=&cmte_id='+com_id
    title,members,meetings=getSenateCommitteeMembers(url)
    committee={'committee':title,
                'members':members,
                'meetings':meetings,}
    return committee

def getSenateCommitteeMembers(url):
    response=get_contents_of_url(url)
    if response!=None:
        soup=BeautifulSoup(response)
        title = soup.find('div','leg_PageContent').h2.text
        title = title[:title.find('Membership')-1]
        info = soup.find_all('div','leg_Col3of4-First HRDFlyer')
        meetings = soup.find('div','leg_Col1of4-Last HRDFlyer')
        items=info[0].find_all('td')
        results=[]
        for i in items:
            t = [text for text in i.stripped_strings]
            if t:
                if t[0].find(':')>0:
                    m={'name': t[1][:t[1].find(' (')],
                        'role': t[0][:-1],
                        'leg_id': getLegislatorIDByName(t[1][:t[1].find(' (')]),}
                else:
                    m={'name': t[0][:t[0].find(' (')],
                        'role': 'member',
                        'leg_id': getLegislatorIDByName(t[0][:t[0].find(' (')]),}
                results.append(m)
        return title, results, meetings

def getSenateCommitteeSchedule(url):
    pass

def getSenateCommitteeAV(url):
    pass

def getCommitteeIDFromURL(url):
    #http://www.senate.mn/committees/committee_media_list.php?cmte_id=1002
    return url[url.find('cmte_id=')+len('cmte_id='):]

def getSenateCommittees():
    response=get_contents_of_url(mn_senate_base+'/committees/')
    if response!=None:
        soup=BeautifulSoup(response)
        info = soup.find_all('div','HRDFlyer')
        links = links=info[0].find_all('a')
        name=''
        committees=[]
        count=0
        for l in links:
            if l.text.find('Members')>=0:
                members=l['href']
            elif l.text.find('Schedule')>=0:
                schedule=l['href']
            elif l.text.find('Audio/Video')>=0:
                av=l['href']
                committee={'committee':name,
                            'chamber':'upper',
                            'id': getCommitteeIDFromURL(l['href']),
                            'members_url':members,
                            'meetings_url':schedule,
                            'media_url':av,}
                committees.append(committee)
            else:
                if l.text[1:].find('     ')>0:
                    name=l.text[1:l.text[1:].find('     ')]
                else:
                    name=l.text[1:]
        return committees
    else:
        return None

def getCommitteeMeetings(url):
    response=get_contents_of_url(url)
    if response!=None:
        soup=BeautifulSoup(response)
        meeting_text = soup.find_all('div','leg_col1of3-Last')
        if meeting_text[0]:
            return meeting_text[0]
    return None

def parseCommitteeMeetings(url):
    response=get_contents_of_url(url)
    if response!=None:
        soup=BeautifulSoup(response)
        meeting_text = soup.find_all('div','leg_col1of3-Last')
        if meeting_text[0]:
            if meeting_text[0].p.p:
                m=meeting_text[0].p.p
                return [text for text in m.stripped_strings]
            return meeting_text[0]
    return None

def getBillText(url):
    bill_page=get_contents_of_url(url)
    clean_bill=substitute_char(bill_page,var_re,'')
    clean_bill=substitute_char(clean_bill,markup_id_re,'')
    soup=BeautifulSoup(clean_bill)
    for e in soup.find_all('br'):
        e.extract()
    br = soup.new_tag('br')
    
    bill_text = soup.find_all('div','xtend')

    for e in bill_text[0]('a'):
        bill_text[0].a.insert_before(br)
        first_link = bill_text[0].a
        first_link.find_next("a")

    return bill_text[0]

def merge_dict(d1, d2):
    ''' Merge two dictionaries. '''
    merged = {}
    merged.update(d1)
    merged.update(d2)
    return merged

def clear_cache(key):
    if key!=None:
        memcache.delete(key)
    else:
        memcache.flush_all()

def getFromCache(key):
    result=memcache.get(key)
    return result

def putInCache(key,data,time=86400):
    memcache.set(key,data,time=time)

def get_contents_of_url(url):
    try:
        content=urllib2.urlopen(url).read()
        return content
    except urllib2.HTTPError, e:
        #checksLogger.error('HTTPError = ' + str(e.code))
        return None
    except urllib2.URLError, e:
        #checksLogger.error('URLError = ' + str(e.reason))
        return None
    except Exception:
        #import traceback
        #checksLogger.error('generic exception: ' + traceback.format_exc())
        return None

def get_coords(ip):
    url=IP_URL+ip
    content=get_contents_of_url(url)

    if content:
        results=minidom.parseString(content)
        coords=results.getElementsByTagName("gml:coordinates")
        if coords and coords[0].childNodes[0].nodeValue:
            lon,lat=coords[0].childNodes[0].nodeValue.split(',')
            return db.GeoPt(lat,lon)

def substitute_char(s,char,sub):
    result = re.sub(char,sub,s)
    return result

def bill_text_remove_markup(text):
    text=substitute_char(text,var_re,'')
    return text

def check_valid_entry(entry,check):
    result=""
    if check.match(entry)!=None:
        result=entry
    return result

def make_secure_val(s):
    return "%s|%s" % (s, hmac.new(SECRET, s).hexdigest())

def check_secure_val(h):
    val=h.split('|')[0]
    if h == make_secure_val(val):
        return val

def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt=make_salt()
    h=hashlib.sha256(name+pw+salt).hexdigest()
    return "%s|%s" % (h,salt)

def valid_pw(name, pw, h):
    salt=h.split('|')[1]
    return make_pw_hash(name, pw, salt)==h

def escape_html(s):
    return cgi.escape(s, quote= True)

def check_valid_signup(username,pasw,verify,email):
    have_error=False

    params=dict(username=username,
                email=email)

    if not check_valid_entry(username,user_re):
        params["user_error"]="That's not a valid username."
        have_error=True
    
    if not check_valid_entry(pasw,pass_re):
        params["verify_error"]="That's not a valid password."
        have_error=True
    elif pasw!=verify:
        params["verify_error"]="Your passwords didn't match."
        have_error=True

    if not check_valid_entry(email,email_re):
        params["email_error"]="That's not a valid email."
        have_error=True

    return have_error,params

def send_email(sender,to,subject,body):
    try:
      message = mail.EmailMessage(sender=sender,
                                  to=to,
                                  subject=subject,
                                  body=body)

      message.check_initialized()

    except mail.InvalidEmailError:
      self.handle_error('Invalid email recipient.')
      return
    except mail.MissingRecipientsError:
      self.handle_error('You must provide a recipient.')
      return
    except mail.MissingBodyError:
      self.handle_error('You must provide a mail format.')
      return

    message.send()
