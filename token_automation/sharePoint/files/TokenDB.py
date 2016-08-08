import psycopg2
from SPTokenList import Token
from datetime import datetime
import re
import traceback
class TokenDB:
    def __init__(self):
        self.conn = psycopg2.connect("dbname=tokenrequests user=spirent password=spirent123 host=smarttestdb.cal.ci.spirentcom.com")
        self.cur = self.conn.cursor()
    def giveManagerApproval(self, created, branchIn):
        branch = self.formatBranch(branchIn)
        time = datetime.now().isoformat()
        statement="""
            UPDATE %s
                SET manapprovaltime = '%s'
                WHERE created = '%s';
        """%(branch, time, created)
        self.cur.execute(statement)
        self.conn.commit()
    def tableExists(self, table):
        statement="""
            SELECT EXISTS(SELECT 1 FROM information_schema.tables 
                WHERE table_catalog='tokenrequests' AND 
                    table_schema='public' AND 
                    table_name='%s');
            """%(str(table))
        try:
            self.cur.execute(statement)
            return self.cur.fetchone()[0]
        except Exception as e:
	            traceback.print_exc()
		    self.conn.rollback()
		    return False
    def getEmails(self):
        statement="""
            SELECT address FROM emails
                WHERE manager=True;
        """
        self.cur.execute(statement)
        to = self.cur.fetchall()
        for index in range(len(to)):
            to[index] = to[index][0]        
        statement="""
            SELECT address FROM emails
                WHERE manager=False;
        """
        self.cur.execute(statement)
        cc = self.cur.fetchall()
        for index in range(len(cc)):
            cc[index] = cc[index][0]
        return (to,cc)
    def tokenExists(self, created):
		statement="""
            SELECT EXISTS(SELECT 1 FROM tokenv1
                WHERE created='%s');
        """%(created)
		try:
			self.cur.execute(statement)
			return self.cur.fetchone()[0]
		except Exception as e:
			traceback.print_exc()
			self.conn.rollback()
			return False
    def branchTokenExists(self, created, branch):
        statement="""
            SELECT EXISTS(SELECT 1 FROM %s
                WHERE created='%s');
        """%(branch, created)
        try:
            self.cur.execute(statement)
            return self.cur.fetchone()[0]
        except Exception as e:
	    traceback.print_exc()
            self.conn.rollback()
            return False
    def addBranch(self, branch):
        statement="""
            CREATE TABLE %s (
                created         timestamp(0) without time zone references tokenv1(created),
                reqTime         timestamp,
                approvalTime    timestamp,
                manApprovalTime timestamp,
                completionTime  timestamp
            )
        """ % (str(branch))
        self.cur.execute(statement)
        self.conn.commit()
    def addToken(self, token):
        time = datetime.now().isoformat()
        statement="""
            INSERT INTO tokenv1 (username, status, branches, created, lastmodified, reason)
                VALUES('%s', '%s', '%s', '%s', '%s', '%s');
        """ % (token.user, token.status, token.branch, token.created, time, token.reason) 
        self.cur.execute(statement)
        self.conn.commit()
    def updateToken(self, token):
        time = datetime.now().isoformat()
        statement="""
            UPDATE tokenv1
                SET username = '%s', status = '%s', branches = '%s', lastmodified = '%s', reason = '%s'
                WHERE created = '%s';
        """ %  (token.user, token.status, token.branch, time, token.reason, token.created)
        self.cur.execute(statement)
        self.conn.commit()
    def getToken(self, created):
        statement = """
            SELECT * from tokenv1
                WHERE created = '%s';
            """%(created)
        self.cur.execute(statement)
        tok = self.cur.fetchone()
        return Token(tok[0], tok[5], tok[2], tok[1], tok[4], tok[3])
    def addBranchToken(self, branch, token):
        time = datetime.now().isoformat()
        zero = datetime.min.isoformat()
        statement="""
            INSERT INTO %s (created, reqTime, approvalTime, manApprovalTime, completionTime)
                VALUES('%s', '%s', '%s', '%s', '%s');
        """ % (branch, token.created, time, zero, zero, zero) 
        self.cur.execute(statement)
        self.conn.commit()
    def updateBranchToken(self, branch, token):
        time = datetime.now().isoformat()
        if token.status[0] == '1': #approved
            setString = "approvalTime = '" + str(time) + "'"
        elif token.status[0] == '3': #complete
            setString = "completionTime = '" + str(time) + "'"
        else:
            setString = "reqTime = '" + str(time) + "'"
        statement="""
            UPDATE %s
                SET %s
                WHERE created = '%s';
        """%(branch, setString, token.created)
        self.cur.execute(statement)
        self.conn.commit()
    def processToken(self, tokenIn):
    	print "processToken(): processing token"
        token = tokenIn
        token.reason = token.reason.replace('\'', '')
        if token.user:
            token.user = token.user.replace('\'', '')
        #check if token exists
        if self.tokenExists(token.created):
            self.updateToken(token)
        else:
            self.addToken(token)
        branches = token.branch.replace('Release (', 'Release(')
        branches = re.sub("\s",'',branches,200)
        branches = branches.split(';')
        #update branch docs if branch exists
        for branch in branches:
            branch = self.formatBranch(branch)
            if self.tableExists(branch):
                if self.branchTokenExists(token.created, branch):
                    self.updateBranchToken(branch, token)
                else:
                    self.addBranchToken(branch, token)
            else:
                self.addBranch(branch)
                self.addBranchToken(branch, token)
    def authExists(self, user):
        statement="""
            SELECT EXISTS(SELECT 1 FROM tokenauth
                WHERE username='%s');
        """%(str(user))
        try:
            self.cur.execute(statement)
            return self.cur.fetchone()[0]
        except Exception as e:
	    traceback.print_exc()
            self.conn.rollback()
            return False
    def authBranchExists(self, branch):
        statement="""
            SELECT column_name from information_schema.columns
                WHERE table_name='tokenauth' and column_name='%s'
        """%(str(branch))
        self.cur.execute(statement)
        if self.cur.fetchone() == None:
            return False
        else:
            return True
    def addAuthBranch(self, branch):
        statement="""
            ALTER TABLE tokenauth ADD COLUMN %s integer
        """ %(branch)
        self.cur.execute(statement)
        self.conn.commit()
    def addAuth(self, user):
        
        time = datetime.now().isoformat()
        statement="""
            INSERT INTO tokenauth (username)
                VALUES('%s')
        """ %(user)
        self.cur.execute(statement)
        self.conn.commit()
    def setAuth(self, user, branchIn, num):
        branch = self.formatBranch(branchIn)
        if self.authBranchExists(branch) == False:
            self.addAuthBranch(branch)
        if self.authExists(user) == False:
            self.addAuth(user)
        setString = str(branch) + " = " + str(num) 
        statement="""
            UPDATE tokenauth
                SET %s
                WHERE username = '%s';
        """%(setString, user)
        self.cur.execute(statement)
        self.conn.commit()
    def getAuth(self, user, branchIn):
        #check to see if the branch is in the tokenauth table before selecting
    	if self.authBranchExists(branchIn):
		print "getAuth(): getting auth val for user "+user+" and branch "+branchIn
		branch = self.formatBranch(branchIn)
		ret = None
		statement = """
		    select %s from tokenauth
			where username = '%s'
		"""%(str(branch), str(user))
		try:
		    self.cur.execute(statement)
		    ret = self.cur.fetchone()
		except Exception as e:
		    traceback.print_exc()
		    self.conn.rollback()
		if ret == None or ret[0] == None:
		    ret = 0
		else: 
		    ret = ret[0]
		return ret
	else:
		return 0
    def getAllIds(self):
        statement = """
        select created from tokenv1	
        """    
        self.cur.execute(statement)
        createds = []
        for entry in self.cur.fetchall(quit):
            createds.append(entry[3])
        return createds

    def getStats(self, created):
        stats = {}
        statement = """
            select username, status, branches from tokenv1
                where created = '%s'
        """%(created)
        self.cur.execute(statement)
        returned = self.cur.fetchone()
        try:
            stats['username'] = returned[0]
            stats['status'] = returned[1]
            stats['branches'] = returned[2]
            branches = stats['branches']
            branches = branches.replace('Release (', 'Release(')
            branches = re.sub("\s", '',branches,200)
            branches = branches.split(';')
            stats['branches'] = branches	
            for index in range(len(stats['branches'])):
                branches[index] = self.formatBranch(branches[index])
                branch = branches[index]
                if self.tableExists(branch):
                    statement = """
                        select completiontime - manapprovaltime, completiontime - approvaltime, manapprovaltime - approvaltime from %s 
                        where created = '%s'
                    """%(str(branch),created)
                    self.cur.execute(statement)
                    returned = self.cur.fetchone()
                    stats[str(branch) + '_worktimeFromMan'] = returned[0]
                    stats[str(branch) + '_worktimeFromApp'] = returned[1]
                    stats[str(branch) + '_timeForManager'] = returned[2]
            return stats
        except Exception as e:
	    traceback.print_exc()
            return {}
    def formatBranch(self, branchIn):
        branch = branchIn
        branch = 'b' + branch.replace('.', '_').replace('(', '_').replace(')', '_')
        branch = branch.lower()
        return branch
