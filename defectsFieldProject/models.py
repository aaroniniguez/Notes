from django.db import models
from django.contrib.auth.models import User
import datetime
from django.core.validators import MinValueValidator
import re

TC_STATE_ACTIVE = 0
TC_STATE_INACTIVE = 1
TC_STATE_DEPRICATED = 2
TC_STATE_BF = 3
TC_STATE_AW = 4
TC_STATE_FAILING_WITH_CR = 5
TC_STATE_NEW = 6
TC_STATE_UNDER_INVESTIGATION = 7

TESTTYPE_UNIT = 0
TESTTYPE_FUNCTIONAL = 1
TESTTYPE_USECASE = 2
TESTTYPE_PORTSCALE = 3

TC_VERDICT_PASS = 0
TC_VERDICT_FAIL = 1
TC_VERDICT_NA = 2
TC_VERDICT_UNTESTED = 3

BRANCH_RELEASE = 0
BRANCH_INTEGRATION = 1
BRANCH_OTHER = 2

PORT_OK = 0
PORT_DOWN = 1
NOT_CHECKED = 2

# Create your models here.

class MarketSegment(models.Model):
    name = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.name

class FailedReason(models.Model):
    reason = models.CharField(max_length=200)
    segment = models.CharField(max_length=200)
    
    def __unicode__(self):
        return self.reason
		
class TestCaseAuthor(models.Model):
    name = models.SlugField(primary_key=True)
    last_name = models.CharField(max_length=20)
    first_name = models.CharField(max_length=20)
    email = models.EmailField()

    def __unicode__(self):
        return self.name

class ScriptType(models.Model):
    interpreter = models.CharField(max_length=10)
    min_version = models.IntegerField(null=True)

    def __unicode__(self):
        return self.interpreter


class Tag(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class TestSet(models.Model):
    """
    RC2, RC3, etc.

    """
    name = models.CharField(max_length=13)
    priority = models.IntegerField(null=True)

    def __unicode__(self):
        return self.name

class MiscFileLocation(models.Model):
    perforce_location = models.CharField(max_length=100)

    def __unicode__(self):
        return self.perforce_location

class ScriptMiscFile(models.Model):
    path = models.CharField(max_length=200)

    def __unicode__(self):
        return self.path

class Dependency(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __unicode__(self):
        return self.name

class ExecHarness(models.Model):
    """
    Execution Engine (ie. THoT, iTest, etc)

    """
    exec_harness = models.CharField(max_length=20)

    def __unicode__(self):
        return self.exec_harness


class Variable(models.Model):
    """
    A script variable.

    There may be multiple variables with the same, and different values.

    """
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name + u'=' + self.value

class TestModule(models.Model):
    """
    Name of a test module (e.g. 'MX-10G', 'MX-100G')

    """
    name = models.CharField(max_length=15, primary_key=True)
    STC_Name = models.TextField()
    min_stc_version = models.CharField(max_length=10)
    rerun_on_not_pass = models.BooleanField()
    threshold_for_rerun_pass = models.DecimalField(max_digits=4,decimal_places=2, validators=[MinValueValidator(0.0)])
    module_generation = models.CharField(max_length=10)
    def __unicode__(self):
        return self.name

class DBFlag(models.Model):
	name = models.CharField(max_length=50, primary_key=True)
	value = models.BooleanField(default=True)
	last_update = models.DateTimeField(auto_now=True)
	
	def tf_value(self):
		if self.value:
			return u'True'
		else:
			return u'False'
	tf_value.short_description=u'Value'
	
	def __unicode__(self):
		return self.name


class TestCase_Base(models.Model):
    class Meta:
        abstract = True
    STATE_CHOICES = (
        (TC_STATE_ACTIVE, u'active'),
        (TC_STATE_INACTIVE, u'inactive'),
        (TC_STATE_DEPRICATED, u'depricated'),
        (TC_STATE_BF, u'being fixed'),
        (TC_STATE_AW, u'awaiting test'),
        (TC_STATE_FAILING_WITH_CR, u'failing with CR'),
        (TC_STATE_NEW, u'new'),
        (TC_STATE_UNDER_INVESTIGATION, u'under investigation'),)

    TESTTYPE_CHOICES = (
        (TESTTYPE_UNIT, u'unit'),
        (TESTTYPE_FUNCTIONAL, u'functional'),
        (TESTTYPE_USECASE, u'usecase'),
        (TESTTYPE_PORTSCALE, u'portscale'),)
    name = models.CharField(max_length=200, db_index=True)
    script_name = models.CharField(max_length=200)
    author = models.ForeignKey(TestCaseAuthor)
    p4_script_version = models.IntegerField()
    script_type = models.ForeignKey(ScriptType)
    duration_seconds = models.IntegerField()
    defects = models.CharField(max_length=200, default='', blank=True)
    timeout_seconds = models.IntegerField()
    tags = models.ManyToManyField(Tag, verbose_name='list of tags')
    variables = models.ManyToManyField(Variable, null=True, blank=True)
    misc_file_location = models.ManyToManyField(MiscFileLocation, null=True, blank=True)
    exec_harness = models.ForeignKey(ExecHarness)
    mrq_number = models.IntegerField(null=True)
    procedure = models.TextField(null=True, blank=True)
    testsets = models.ManyToManyField(TestSet)
    testtype = models.IntegerField(choices=TESTTYPE_CHOICES, db_index=True)
    min_stc_version = models.CharField(max_length=10)
    state = models.IntegerField(choices=STATE_CHOICES)
    testmodules = models.ManyToManyField(
        TestModule, verbose_name='modules script needs to run on')
    modified = models.DateTimeField(auto_now=True)
    priority = models.IntegerField(null=True)
    mst = models.ForeignKey(MarketSegment, default=1)
    
    objective = models.TextField(default='', blank=True)
    test_plan_section = models.CharField(max_length=200, default='', blank=True)
    environment = models.TextField(default='', blank=True)
    expected_results = models.TextField(default='', blank=True)
    initial_configuration = models.TextField(default='', blank=True)
    dependencies = models.ManyToManyField(Dependency, blank=True)
    
    script_misc_files = models.ManyToManyField(ScriptMiscFile, blank=True)
    
    #version = models.IntegerField()

    def __unicode__(self):
        return self.name

    def get_testtype(self):
        return dict(TestCase.TESTTYPE_CHOICES).get(self.testtype)

    def get_state(self):
        return dict(TestCase.STATE_CHOICES).get(self.state)

    def get_testmodule_names(self):
        return [str(tm.name)
                for tm in TestModule.objects.filter(testcase=self)]

    def colored_name(self):
        scriptNFound = 'Script is not in Perforce'
        VariableError = 'Variables are not valid'
        errors = []
        try:
            script = TestScript.objects.get(name=self.script_name.strip())
        except:
            errors.append(scriptNFound)
        if scriptNFound not in errors:
            if self.exec_harness.exec_harness == 'thot' and self.script_type.interpreter == 'tcl':
                if script.variables is None:
                    scr_variables = []
                else:
                    scr_variables = script.variables.split(',')
                #valid = True
                self_vname = []
                for var in self.variables.all():
                    if var.name not in scr_variables:
                        #valid = False
                        if VariableError not in errors:
                            errors.append(VariableError)
                        break
                    self_vname.append(var.name)
                if len(errors) == 0:
                    for var_name in scr_variables:
                        if var_name not in self_vname:
                            #valid = False
                            if VariableError not in errors:
                                errors.append(VariableError)
                            break
        if len(errors) == 0:
            return self.name
        elif len(errors) == 1:
            return '<span title="%s" style="color: %s;">%s</span>' % (errors[0],'red', self.name)
        else:
            return '<span title="Multiple errors" style="color: %s;">%s</span>' % ('red', self.name)
    colored_name.allow_tags = True
    colored_name.admin_order_field = 'name'
    colored_name.short_description = 'Name'
    

class TestCase(TestCase_Base):
    previous_version = models.ForeignKey('self',null=True, blank=True)

class OperatingSystem(models.Model):
    # ('fedora', 'centos', 'freebsd', 'windows', 'solaris', 'android')
    osname = models.CharField(max_length=20)
    osversion = models.CharField(max_length=20)

    def __unicode__(self):
        return self.osname

class suiteDisplay(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    def __unicode__(self):
        return self.name
class JenkinsJob(models.Model):
    name = models.CharField(max_length=20, primary_key=True)
    number = models.IntegerField()
    status = models.CharField(max_length=10)

    def __unicode__(self):
        return self.name


class TestResult(models.Model):
    testcase = models.ForeignKey(TestCase)
    sccl_version = models.CharField(max_length=30)
    il_version = models.CharField(max_length=30)
    start_time = models.DateTimeField()
    execution_seconds = models.IntegerField()
    failed = models.NullBooleanField() # Null = in progress
    change_request = models.IntegerField(null=True)
    operatingsystem = models.ForeignKey(OperatingSystem, null=True)
    jenkinsjob = models.ForeignKey(JenkinsJob)

    def __unicode__(self):
        return self.testcase.name + u'-result'

class SMTVersionId(models.Model):
    connection_name='result'
    ver_id = models.IntegerField(primary_key=True)
    #promoted = models.BooleanField()
    
    def __unicode__(self):
        return str(self.ver_id)

class P4_Changelists(models.Model):
    connection_name='result'
    class Meta:
        db_table = 'perforce_changelist_details'
    
    changelist = models.IntegerField(primary_key=True)
    cl_timestamp = models.DateTimeField()
    cl_user = models.CharField(max_length=20)
    email = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    
    
    
    def __unicode__(self):
        return str(self.changelist)

class TestSuite(models.Model):
    
    connection_name='result'
    
    BRANCH_CHOICES = (
        (BRANCH_RELEASE, u'release'),
        (BRANCH_INTEGRATION, u'integration'),
        (BRANCH_OTHER, u'na'))
    
    name = models.CharField(max_length=200, primary_key=True)
    bll = models.CharField(max_length=30)
    il = models.CharField(max_length=30)
    start_time = models.DateTimeField()
    branch = models.IntegerField(choices=BRANCH_CHOICES)
    owner = models.CharField(max_length=200)
    link = models.CharField(max_length=400)
    reserve_1 = models.CharField(max_length=200, null=True)
    reserve_2 = models.CharField(max_length=200, null=True)
    reserve_3 = models.CharField(max_length=200, null=True)
    end_time = models.DateTimeField(null=True)
    status = models.CharField(max_length=16)
    hostname = models.CharField(max_length=64)
    changelists = models.ManyToManyField(P4_Changelists)
    #smtVersionId = models.ManyToManyField(SMTVersionId, null=True, blank=True, through='TestSuite_smtVersionId')
    
    def __unicode__(self):
        return self.name

    @property
    def pass_count(self):
        return TestExecutionHistory.objects.filter(test_suite__name=self.name).filter(verdict = 0).count()

    @property
    def fail_na_count(self):
        return TestExecutionHistory.objects.filter(test_suite__name=self.name).filter(verdict__in=[1,2]).count()


    @property
    def pass_rate(self):
        tot_notun = self.pass_count + self.fail_na_count
        if tot_notun > 0:
            pass_rate = int(float(self.pass_count) /tot_notun * 100)
        else:
            pass_rate = 0
        return pass_rate

    @property
    def pass_color(self):
        if self.pass_rate == 100:
            pass_color = 'lime'
        elif self.pass_rate >= 90:
            pass_color = 'orange'
        else:
            pass_color = 'red'
        return pass_color
    @property
    def module_counts(self):
        modules = {}
        for entry in TestExecutionHistory.objects.filter(test_suite__name=self.name).all():
            if entry.module in modules:        
                if entry.verdict == 0:     
                    modules[entry.module] = (modules[entry.module][0]+1, modules[entry.module][1])
                else:       
                    modules[entry.module] = (modules[entry.module][0], modules[entry.module][1]+1)        
            else:
                if entry.verdict == 0:
                    modules[entry.module] = (1,0)      
                else:
                    modules[entry.module] = (0,1)    
        return modules
    @property
    def good_build(self):
        modules = self.module_counts
        if self.pass_rate < 99:
            return False
        for key in modules:
            if modules[key][1] >= 5:
                return False
        return True
    @property
    def nameurl(self):
        return self.name.replace(" ", "%20")

    @property
    def name_nodate(self):
        finddash = self.name.rfind(' - ')
        if finddash != -1:
            return self.name[:finddash]
        else:
            return self.name

    @property
    def name_noname(self):
        finddash = self.name.rfind(' - ')
        if finddash != -1:
            suite_start_time = self.name[finddash+3:]
            date_time = re.split('@',suite_start_time)
            date_only = re.split('\.',date_time[0])
            time_only = re.split('\.',date_time[1])
            final_date_time = date_only[0] + '-' + date_only[1] + '-' + date_only[2] + ' ' + time_only[0] + ':' + time_only[1]
            '''+ ':' + time_only[2]'''
            return final_date_time
            
        #else:
        #    return self.start_time

    @property
    def color(self):
        suite_color =  '#088A08'
    #Must use UTC timezone, otherwise comparing with suite_start_time results in bugs
        today_time = datetime.datetime.utcnow()
        try:
            suite_status = self.status
            if "COMPLETE" in suite_status.upper() or "STOPPED" in suite_status.upper():
                suite_color = '#005ea7'
            else:
                end_time = self.start_time + datetime.timedelta(days=3)
                if end_time.replace(tzinfo=None)>today_time:
                    suite_color = "#088A08"
                else:
                    suite_color = "#005ea7"
        except:
            end_time = self.start_time + datetime.timedelta(days=3)
            if end_time.replace(tzinfo=None)>today_time:
                suite_color = "#088A08"
            else:
                suite_color = "005ea7"
        return suite_color
 
    @property
    def status_color(self):
        if self.status == 'COMPLETE' or self.status == 'IDLE':
            return "lime"
        elif self.status == 'RUNNING' or self.status == 'BUSY' or self.status == 'REGISTERED':
            return 'orange'
        elif self.status == 'STOPPED':
            return 'red'
        elif self.status == 'SETUP':
            return 'orange'
        else:
            return 'white'

class BuildInfo(models.Model):
    connection_name='build_info'
    class Meta:
        db_table = 'build_info_table'
    
    build_number_info = models.CharField(max_length=9, primary_key=True)
    ui_changelist = models.IntegerField()
    bll_changelist = models.IntegerField()
    il_changelist = models.IntegerField()
    branch_name = models.CharField(max_length=15)
    time_stamp = models.DateTimeField()
    ci = models.BooleanField()
    
    def __unicode__(self):
        return self.build_number_info

class GoodBuildHistory(models.Model):
    connection_name='build_info'
    class Meta:
        db_table = 'good_build_history'
    build = models.ForeignKey(BuildInfo,primary_key=True, db_column='build_number')
    create_timestamp = models.DateTimeField(auto_now_add=True)
    
    
class TestSuite_smtVersionId(models.Model):
    connection_name='result'
    
    class Meta:
        unique_together = ("testsuite", "smtVersionId")
        
    testsuite = models.CharField(max_length=200)
    smtVersionId = models.ForeignKey(SMTVersionId)

class ChangeRequest(models.Model):
    connection_name='result'
    cr_id = models.CharField(max_length=30, primary_key=True)
    cr_link = models.TextField()
    cr_engproj = models.CharField(max_length=200, null=True)
    reserve_2 = models.CharField(max_length=200, null=True)
    reserve_3 = models.CharField(max_length=200, null=True)
    
    def __unicode__(self):
        return self.cr_id

class TestExecutionHistory(models.Model):
    
    connection_name='result'

    VERDICT_CHOICES = (
        (TC_VERDICT_PASS, u'pass'),
        (TC_VERDICT_FAIL, u'fail'),
        (TC_VERDICT_NA, u'na'),
        (TC_VERDICT_UNTESTED, u'untested'))

    PORTSTATUS_CHOICES = (
        (PORT_OK, u'OK'),
        (PORT_DOWN, u'DOWN'),
        (NOT_CHECKED, u'Not Checked'))
    
    script_name = models.CharField(max_length=200)
    module = models.CharField(max_length=200)
    verdict = models.IntegerField(choices=VERDICT_CHOICES)
    test_suite = models.ForeignKey(TestSuite)
    fail_reason = models.TextField()
    duration_seconds = models.IntegerField()
    port_status = models.IntegerField(choices=PORTSTATUS_CHOICES)
    test_detail = models.CharField(max_length=200)
    reserve_1 = models.CharField(max_length=400, null=True)
    reserve_2 = models.CharField(max_length=200, null=True)
    reserve_3 = models.CharField(max_length=200, null=True)
    cr = models.ManyToManyField(ChangeRequest, null=True, blank=True, through='TestExecutionHistory_cr')

class SmartTestTestCase(models.Model):
    connection_name='result'
    testcase_name = models.CharField(max_length=200, primary_key=True)
    mst = models.CharField(max_length=100)
    attr1 = models.CharField(max_length=200, default='')
    attr2 = models.CharField(max_length=200, default='')
    attr3 = models.CharField(max_length=200, default='')
    def __unicode__(self):
        return self.testcase_name

class TestExecutionHistory_bak(models.Model):

    VERDICT_CHOICES = (
        (TC_VERDICT_PASS, u'pass'),
        (TC_VERDICT_FAIL, u'fail'),
        (TC_VERDICT_NA, u'na'))

    PORTSTATUS_CHOICES = (
        (PORT_OK, u'OK'),
        (PORT_DOWN, u'DOWN'),
        (NOT_CHECKED, u'Not Checked'))
    
    testcase = models.ForeignKey(TestCase)
    module = models.ForeignKey(TestModule)
    verdict = models.IntegerField(choices=VERDICT_CHOICES)
    test_suite = models.ForeignKey(TestSuite)
    fail_reason = models.TextField()
    duration_seconds = models.IntegerField()

class TestSuite_bak(models.Model):
    
    BRANCH_CHOICES = (
        (BRANCH_RELEASE, u'release'),
        (BRANCH_INTEGRATION, u'integration'),
        (BRANCH_OTHER, u'na'))
    
    name = models.CharField(max_length=200, primary_key=True)
    bll = models.CharField(max_length=30)
    il = models.CharField(max_length=30)
    start_time = models.DateTimeField()
    branch = models.IntegerField(choices=BRANCH_CHOICES)

class TestExecutionHistory_cr(models.Model):
    connection_name='result'
    
    class Meta:
        unique_together = ("record", "cr")
        
    record = models.ForeignKey(TestExecutionHistory)
    cr = models.ForeignKey(ChangeRequest)
    
class TestScript(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    variables = models.CharField(max_length=200, null=True)

class TagManager(models.Model):
    user = models.OneToOneField(User)
    tags = models.ManyToManyField(Tag, null=True, blank=True)

    def __unicode__(self):
        return self.user.username + u'\'s tags'

class branchLocation(models.Model):
    branch = models.CharField(max_length=200, unique=True)
    location = models.CharField(max_length=200)
    
class Testsuite_Incident(models.Model):
    connection_name='result'
    
    class Meta:
        db_table = 'testsuite_incident'
    
    testsuite = models.CharField(max_length=200)
    # fake primary key to make django work
    incident_time = models.DateTimeField(primary_key=True)
    owner = models.CharField(max_length=200)
    incident_level = models.CharField(max_length=20)
    incident_desc = models.TextField()
    incident_type = models.CharField(max_length=64)
    incident_timeframe = models.CharField(max_length=128)

class TopFailures(models.Model):
    
    connection_name='result'   
    class Meta:
        db_table = 'topfailures'
        
    section_name = models.CharField(max_length=128)
    precedence = models.IntegerField()
    failure_name = models.CharField(max_length=256, primary_key=True)
    value_f = models.CharField(max_length=256)
    value_p = models.CharField(max_length=256)
    value_c = models.CharField(max_length=256)
    mst = models.CharField(max_length=256)
    last_update = models.DateTimeField(null=True)
