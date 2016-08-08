from SPTokenList import SPTokenList as spt
from SPTokenList import Token
from TokenDB import TokenDB
import sys
import re
import os
from datetime import date
from time import localtime as time
import subprocess
from subprocess import Popen, PIPE, check_output
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta
from datetime import datetime
import traceback

global p4
internEmail  = ["aaron.iniguez@spirent.com", "Somboon.Ongkamongkol@spirent.com"]
managerEmail = ["aaron.iniguez@spirent.com", "Somboon.Ongkamongkol@spirent.com"]
if sys.platform == 'win32':
    p4 = """C:\\Program Files\\Perforce\\p4"""
else:
    p4 = 'p4'
global branches
global path
path = os.path.dirname(os.path.realpath(__file__))
if sys.platform == 'win32':
    path += "\\"
else:
    path += '/'

def checkEnv():
    missing = ''
    if os.environ.get('P4PORT') == None:
        missing += '($P4PORT)'
    if os.environ.get('P4PASSWD') == None:
        missing += '($P4PASSWD)'
    if os.environ.get('P4USER') == None:
        missing += '($P4USER)'
    if os.environ.get('SPUSER') == None:
        missing += '($SPUSER)'
    if os.environ.get('SPPASSWD') == None:
        missing += '($SPPASSWD)'
    if missing != '':
        missing = 'Missing environment variable(s): ' + missing
        raise Exception(missing)
def resolveBranch(branchAlias, branches):
    i = branches.find(branchAlias)
    if i == -1:
        return [None]
    i2 = branches.find('\n',i)
    branch = branches[i:i2].split(' ')
    return [branch[1],branch[2]]
def log_append(log, string):
    t = time()
    #line = str(t.tm_hour) + ':' + str(t.tm_min) + ':' + str(t.tm_sec)+"  "
    line = string + '\n'
    log.write(line)
def getField(mail, field, pos):
    pos = mail.index(field, pos)
    return str(mail[pos + 1])
#given the user submitted username(s) from the token website, do a lookup for the perforce username
#input: username string
#returns: perforce username or False
def p4UserExists(user):
    cmd = [p4] + "users".split(' ')
    if sys.platform == 'win32':
        output = check_output(cmd, shell=True)
    else:
        output = check_output(cmd, shell=False)
    outputlist = output.split("\n")
    foundUsers = []
    for ioutput in outputlist:
    	if (str(user).lower() in ioutput.lower()):
		foundUsers.append(ioutput.split(" ")[0])
    #if user doesnt exist or there are multiple users found, return false
    if len(foundUsers) != 1:
    	return False
    return foundUsers[0]
#   Changes p4 permissions given a user, branch, and operation     #
def setPermission(user, branchTuple, op, db, log):
    branchCommonName = branchTuple[0]
    branch = branchTuple[1]
    if op == None:
        return False
    changed = False
    dbUpdate = False
    cmd = "group -a -o " + str(branch)
    cmd = [p4] + cmd.split(' ')
    if sys.platform == 'win32':
        output = check_output(cmd, shell=True)
    else:
        output = check_output(cmd, shell=False)
    index = output.find("\nUsers:")
    userIndex = output.find(str(user), index)
    authNum = db.getAuth(user,branchCommonName)
    #user is not a member of the branch
    if userIndex == -1:
        if op == 'add':
            authNum = authNum + 1
            index = output.find('\n',index+1)
            output = output[:index + 1] + '\t' + user + output[index:]
            f = open(path + 'input.txt','w')
            f.write(output)
            f.close()
            changed = True
            db.setAuth(user, branchCommonName, authNum)
            dbUpdate = True
        elif op == 'remove':
	    log_append(log, "User is not a member of the branch: no action needed")
            changed = False
    elif op == 'remove':
        authNum = authNum - 1
        if authNum <= 0:
            authNum = 0
	    outputlist = output.split("\n")
	    if "\t"+str(user) in outputlist: outputlist.remove("\t"+str(user))
	    output = "\n".join(outputlist)
            f = open(path + 'input.txt','w')
            f.write(output)
            f.close()
            changed = True
        db.setAuth(user, branchCommonName, authNum)
        dbUpdate = True
    elif op == 'add':
        changed = False
        authNum = authNum + 1
        db.setAuth(user, branchCommonName, authNum)
        dbUpdate = True
	log_append(log, "User already a member of the branch: no action needed")
    if changed == True:    
        f = path + 'input.txt'
        cmd = [p4] + "group -a -i".split(' ')
        ret = Popen(cmd, stdin=PIPE)
        ret.stdin.write(output)
        ret.stdin.close()
	log_append(log, "Updating Perforce successfully completed")
    return changed or dbUpdate
def resolveNames(names):
	namesList  = [] 
	namesList2 = []
	namesList3 = []
	#users separated by a comma
	namesList1 = re.split(r",", names)
	#users separated by \r\n
	for name in namesList1:
		namesList2.extend(re.split(r"\r\n",name))
	#users separated by \n
	for name in namesList2:
		namesList3.extend(re.split(r"\n",name))
	#users separated by -
	for name in namesList3:
		namesList.extend(re.split(r"-",name))
	#remove p tags around users name
	for ind in range(len(namesList)):
		namesList[ind] = namesList[ind].replace("<p>","").replace("<\/p", "").strip().replace("</p>","")
	namesList = [x for x in namesList if x != "" ]
	p4Usernames = []
	for name in namesList:
		if not p4UserExists(name):
		   	raise Exception('Name not found: ' + name )
		p4Usernames.append(p4UserExists(name))
   	return p4Usernames
#       Looks up email based on username                           #
def lookupEmail(username):
    cmd = "users"
    cmd = [p4] + cmd.split(' ')
    names = check_output(cmd, shell=False)
    i = names.lower().find(username.lower())
    if i == -1:
        return None
    else:
        i = names.find('<',i) + 1
        i2 = names.find('>',i)
        return names[i:i2]
def sendEmail(sender, toList, ccList, subject, text, html):
    debug = False
    if html != '':
        mail = MIMEMultipart('alternative')
    else:
        mail = MIMEText(text)
    mail['Subject'] = subject
    mail['From'] = sender
    mail['To'] = ", ".join(toList)
    mail['CC'] = ", ".join(ccList)
    if html != '':
        part1 = MIMEText(text, 'plain')
        mail.attach(part1)
        part2 = MIMEText(html, 'html')
        mail.attach(part2)
    s = smtplib.SMTP('smtprelay.spirent.com')
    if not debug:
        s.sendmail('token_automation@spirent.com', toList + ccList, mail.as_string())
    else:
        s.sendmail('token_automation@spirent.com', [internEmail], mail.as_string())
    s.quit()
def updateP4(token, log):
    names = token.user
    status = token.status
    branch = token.branch
    reason = token.reason
    #input validation
    nameList = resolveNames(names)
    #legacy compatibility for when Release had a space
    branch = branch.replace('Release (', 'Release(')
    branch = re.sub("\s",'',branch,200)
    branch = branch.split(';')
    #Update Perforce if needed
    restricted = False
    changed = False
    for b in branch:
        resolved = resolveBranch(b, branches)
        if resolved[0] == None:
            log_append(log, "branch not found in branches.txt: " + b)
            continue
        if resolved[1] == 'r' and status[0] == '1':
            restricted = True
            log_append(log, "requested a restricted branch: " + str(resolved[0]))
        else:
            if status[0] == '1':
                op = 'add'
            elif status[0] == '2':
                op = 'null'
                log_append(log, "status pending")
            else:
                op = 'remove'
            for name in nameList:
	    	if op == "add":
			log_append(log, "Updating Perforce: "+op+"ing "+name+" to branch: "+b)
		elif op == "remove":
			log_append(log, "Updating Perforce: "+op[0:len(op)-1]+"ing "+name+" from branch: "+b)
		else: 
			log_append(log, "Updating Perforce: "+op+" "+name+" from branch: "+b)
                changed = (setPermission(name, (b, resolved[0]), op, db, log) or changed)
    #Send emails if needed
    addresses = db.getEmails()
    errStr = ''
    if changed:
        userEmails = []
        for name in nameList:
            eaddr = lookupEmail(str(name))
            if eaddr != None:
                userEmails += [lookupEmail(str(name))]
            else:
                errStr += 'Error: Cannot find user email for ' + str(name)
        if op == 'add':
                notification = str(nameList) + ' granted access to '
                for b in branch:
                	notification += str(b) + ', '
        else:
            notification = str(nameList) + ' completed work with and removed access to '
            for b in branch:
                notification += str(b) + ', '
        notification += errStr
        to = userEmails + addresses[0]
	to = internEmail
        cc = addresses[1]
	cc = internEmail
	log_append(log, "Sending Email: "+notification)
	try:
		sendEmail('token_automation@spirent.com', to, cc, notification, notification, html = '')
	except Exception:
		log_append(log, "\n Sending Email Failed")
		print "Sending Email Failed"
    #send email to managers to approve the request
    if restricted:
        log_append(log, 'sending restricted access email')
        userEmails = []
        for name in nameList:
            email = lookupEmail(str(name))
            if email != None: 
                userEmails += [email]
        txt = "Wating for manager approval for restricted branch: %s" % (str(branch[0]))
        subject = txt
        to = userEmails + addresses[0]
	to = internEmail
        cc = addresses[1]
	cc = internEmail
        txt += errStr
	try:
		sendEmail('token_automation@spirent.com', to, cc, subject, txt, '')
	except Exception:
		log_append(log, "\n Sending Email Failed")
		print "Sending Email Failed"
        URL = "http://jenkins-devops.cal.ci.spirentcom.com:8080/job/token_automation/buildWithParameters?token=tok&operation=addRestricted&branch="+str(branch[0])+"&created="+token.created
        txt = str(nameList) + ' requested restricted branch ' + str(branch[0])
        txt += '\nReason: ' + str(reason)
        txt += "\nPlease navigate to %s to approve"%(URL)
        html = """
        <html>
            <head></head>
            <body>
                <p>
                    User %s requested restricted branch %s <br>
                    Reason: %s <br>
                    <a href=%s>Accept</a><br>
                </p>
            </body>
        </html>
        """ % (str(nameList), str(branch[0]), str(reason), URL)
        subject = '(Automated Message) ' + str(nameList) + ' requested restricted branch ' + str(branch[0])
	#to: the managers(so they can approve), and cc: devops@spirent.com
        to = db.getEmails()[0]
	to = internEmail
        cc = db.getEmails()[1]
	cc = internEmail 
        txt += errStr
	try:
		sendEmail('token_automation@spirent.com', to, cc, subject, txt, html)
	except Exception:
		log_append(log, "\n Sending Email Failed")
		print "Sending Email Failed"
def addRestricted(created, branch, log):
    branchDoc = open(path + 'branches.txt', 'r')
    branches = branchDoc.read(1024)
    branchDoc.close()
    db = TokenDB()
    tok = db.getToken(created)
    diff = ''
    if created != tok.created.isoformat():
        diff += 'created '
    if tok.status[0] != '1':
        diff += 'status '
    branchList = tok.branch.split(';')
    match = False
    for br in branchList:
        if br == branch:
            match = True
    if match == False:
        diff += 'Branch '
    if diff != '':
        raise Exception('Request does not match database! ' + str(diff))
    branch_name = resolveBranch(branch, branches)[0]
    userList = resolveNames(tok.user)
    for user in userList:
        setPermission(user, (branch, branch_name), 'add', db, log)
        log_append(log, 'adding user ' + (user) + ' to restricted branch ' + str(branch))
        userEmail = lookupEmail(str(user))
        if userEmail != None:
            notification = str(user) + '  was granted access to ' + branch
            to = [managerEmail, userEmail]
	    to = internEmail
            cc = [lookupEmail(str(user)), internEmail, 'Somboon.Ongkamongkol@spirent.com', 'DevOpsTeam@spirent.com']
	    cc = internEmail
	    log_append(log, notification)
	    try:
		sendEmail('token_automation@spirent.com', to, cc, notification, notification, html = '')
       	    except Exception:
		log_append(log, "\n Sending Email Failed")
		print "Sending Email Failed"
	else: 
		log_append(log, "user does not have email")
def printStatsTable(db):
    ids = db.getAllIds()
    for i in ids:
        tok = db.getStats(i)
    if len(tok) > 0 :
        print "|  %20.20s |  %20.20s | %20.20s | %21.20s | %20.20s |"%(tok['username'], tok['status'], ' ', ' ', ' ')
        for branch in tok['branches']:
            manTime = tok[branch + '_worktimeFromMan']
            compTime = tok[branch + '_worktimeFromApp']
            man2Time = tok[branch + '_timeForManager']
        pos = timedelta(days=100)
        neg = timedelta(days = -100)
        
        if manTime > pos or manTime < neg:
            manTime = 'insufficient data'
        if compTime > pos or compTime < neg:
            compTime = 'insufficient data'
        if man2Time > pos or man2Time < neg:
            man2Time = 'insufficient data'
        print "|  %20.20s |  %20.20s | %20.20s |  %20.20s | %20.20s |"%('', str(branch), str(manTime),str(compTime),str(man2Time))      
if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise Exception('invalid arguments ' + str(sys.argv))
    print "Arguments given:" 
    print sys.argv
    checkEnv()
    branchDoc = open( path + 'branches.txt', "r")
    if not branchDoc:
        print 'branches.txt does not exist'
        raise Exception('branches.txt does not exist')
    branches = branchDoc.read()
    branchDoc.close()
    if sys.platform == 'win32':
        try:
            log = open(path + "logs\\" + str(date.today()) + "_log.txt", "a")
        except Exception: 
            log = open(path + "logs\\" + str(date.today()) + "_log.txt", "w") 
    else:
        try:
            log = open(path + "logs/" + str(date.today()) + "_log.txt", "a")
        except Exception:
            log = open(path + "logs/" + str(date.today()) + "_log.txt", "w")
    log_append(log, ("-"*100+"\n"+datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" Ran "+" ".join(sys.argv[0:])))
    db = TokenDB()
    if sys.argv[1] == 'update':
        spList = spt(os.environ.get('SPUSER'), os.environ.get('SPPASSWD'))
        pulledList = spList.buildDictFromSP()
	tmpCounter = 0 
	if len(pulledList) == 0:
		log_append(log, "\nNo new token requests found")
        for token in pulledList: 
	    tmpCounter = tmpCounter + 1 
	    try:
	    	print "updating perforce for the current token("+str(tmpCounter)+" of "+str(len(pulledList))+"), token.created = "+token.created+" token.user = "+token.user + " , token.branch: "+token.branch
		log_append(log, "\nProcessing token request("+str(tmpCounter)+" of "+str(len(pulledList))+"):")
		#logs the token iformation
		log_append(log, " "*5 + str(token))
		updateP4(token, log)
		print "done updating perforce for the current token"
		db.processToken(token)
	    except Exception as e:
	    	log_append(log, "\n"+traceback.format_exc())
	        traceback.print_exc()
    elif sys.argv[1] == 'addRestricted':
        created = sys.argv[2]
        branch = sys.argv[3]      
        addRestricted(created, branch, log)
        db.giveManagerApproval(created, branch)
    elif sys.argv[1] == 'buildDB':
        spList = spt(os.environ.get('SPUSER'),os.environ.get('SPPASSWD'))
        pulledList = spList.buildDictFromSP()
        for key in pulledList:
            db.processToken(pulledList[key])
    elif sys.argv[1] == 'refreshToken':
        try:
	    spList = spt(os.environ.get('SPUSER'),os.environ.get('SPPASSWD')) 
            token = spList.getSPToken(sys.argv[2])
	    if (token):
		    updateP4(token, log)
		    db.processToken(token)
	    else:
	    	raise Exception("Error: getSPToken() returned None")
        except Exception as e:
	    log_append(log, "\n"+traceback.format_exc())
	    traceback.print_exc()
    elif sys.argv[1] == 'dumpStats':
        printStatsTable(db)
    log.close()
