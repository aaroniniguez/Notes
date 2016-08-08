# Create your views here.
from django.http import HttpResponse, HttpResponseBadRequest
from tracker.models import Ticket, Recovery, Syshealth
from stapp.models import TestSet
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import json
from django.shortcuts import render_to_response
from django.db.models import Q
from datetime import datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist
import subprocess

@csrf_exempt
def insert(request):
    if request.method == 'POST':
        bll = request.POST['bll']
        il = request.POST['il']
        ilpath = request.POST['ilpath']
        recipient_email = request.POST['recipient_email']
        shelved_changelist= request.POST['shelved_changelist']
        workspace_checksum= request.POST['workspace_checksum']
        targetsys= request.POST['targetsys']
        testsets = request.POST['testsets']
        try:
            t = Ticket(bll=bll, il=il,ilpath=ilpath, recipient_email=recipient_email,shelved_changelist=shelved_changelist,workspace_checksum=workspace_checksum, targetsys=targetsys, testsets=testsets)
            t.save()
        except Exception as e:
            if 'fk_sys' in str(e):
                err_msg = 'Bad system name from input. Contact admin to register ' + targetsys + ' system before use'
                return HttpResponseBadRequest(err_msg)
            return HttpResponseBadRequest(str(e))
        response_data = {}
        response_data['confirmation_number'] = t.id
        response_data['error_reason']=''
    else: 
        return HttpResponse('Not a valid request')
    return HttpResponse(json.dumps(response_data), content_type='application/json')


def piv_qemu_queue(request):
    day_to_display = 7 
    #filtered = Ticket.objects.using('piv_test').all().filter(added_time__gte=datetime.now()-timedelta(days=day_to_display)).order_by('-added_time') 
    filtered = Ticket.objects.using('piv_test').all()
    queues = []
    virt = [ticket for ticket in filtered if ticket.targetsys == 'SYS-04-QEMU']
    queues.append(('Virtual',virt))
    return render_to_response(
        'tracker/piv_qemu_queue.html',
        {'tickets': filtered,
         'queues':queues})

def getTest(request,myvar,listid):
    if myvar == "spirent":
    	myvar = ""
    filtered = Ticket.objects.using('piv_test').all().filter(workspace_checksum=myvar,id=listid,state="PENDING")
    #if you get 1 result update the database to cancel
    if len(filtered) == 1:
	    Ticket.objects.using('piv_test').all().filter(workspace_checksum=myvar,id=listid,state="PENDING").update(state="CANCELLED")
    queues = []
    hw = [ticket for ticket in filtered if ticket.targetsys == 'SYS-04-HW']
    queues.append(('Hardware',hw))
    return render_to_response(
        'tracker/changeTest.html',{
	'queues':queues}
	)
def piv_queue_hw(request):
    # filtered = Ticket.objects.using('piv_test').all().filter(state='INPROGRESS').order_by('-added_time')
    day_to_display = 7 
    #TODO: put back in production:
    #filtered = Ticket.objects.using('piv_test').all().filter(added_time__gte=datetime.now()-timedelta(days=day_to_display)).order_by('-added_time') 
    filtered = Ticket.objects.using('piv_test').all() 
    # response = ''
    # for items in filtered:
    #    response = response + str(items.id) + '\t' + items.recipient_email + '\t' + str(items.shelved_changelist) + '\n'
 
    # return HttpResponse(response)
    # return HttpResponse('Somboon' + str(len(filtered)))
    queues = []
    hw = [ticket for ticket in filtered if ticket.targetsys == 'SYS-04-HW']
    queues.append(('Hardware',hw))
    return render_to_response(
        'tracker/piv_queue_hw.html',
        {'tickets': filtered,
         'queues':queues})

def piv_osev_queue(request):
    day_to_display = 7 
    #filtered = Ticket.objects.using('piv_test').all().filter(added_time__gte=datetime.now()-timedelta(days=day_to_display)).order_by('-added_time') 
    filtered = Ticket.objects.using('piv_test').all()
    queues = []
    osev = [ticket for ticket in filtered if ticket.targetsys == 'SYS-04-OSEv']
    queues.append(('OSEv',osev))
    return render_to_response(
        'tracker/piv_osev_queue.html',
        {'tickets': filtered,
         'queues':queues})

def fetch_piv_result(request):
    suiteid = request.GET.get('suiteid')
    filtered = Ticket.objects.using('piv_test').all().filter(Q(test_suite_id=suiteid))
    # filtered = Ticket.objects.using('piv_test').all().filter(Q(id=suiteid))
    response = ''
    for items in filtered:
        response = response + str(items.pass_rate) + "," + str(items.workspace_checksum)
        break

    return HttpResponse(response)

def ackrecovery(request):
    print request
    sysid = request.GET.get('sys')
    ticketid = request.GET.get('ticket')
    print 'sysid', sysid, 'ticketid', ticketid
    recoverys = Recovery.objects.filter(ticket=ticketid, sys=sysid)
    print recoverys
    if recoverys:
        recovery=recoverys[0]
        if recovery.done:
            return HttpResponse(sysid + ' has been already recoverd')
        srcip = request.META.get('REMOTE_ADDR')

        output = subprocess.check_output(["host",srcip])
        if 'pointer' in output:
            srchost = output.split()[-1].rstrip('.')
            recovery.updated_user = srchost
        else:
            recovery.update_user=srcip
        recovery.done=True
        recovery.save()
        Syshealth.objects.filter(id=sysid).update(state='IDLE')
        return HttpResponse(sysid + ' just recovered')
    else:
        return HttpResponse('invalid url')
         

def validate(request):
    sysid = request.GET.get('sysid')
    testsets = request.GET.get('testsets').split(',')
    error_msg=[]
    if sysid and testsets:

        if sysid!='SYS-04':
            try:
                Syshealth.objects.get(id=sysid)
            except ObjectDoesNotExist:
                error_msg.append('sysid ' + sysid + ' does not exist in piv system')
     
        if sysid=='SYS-04' and  (len(testsets) !=1 or testsets[0] != 'SMT_CI'):
            error_msg.append('SYS-04 only allows SMT_CI testset')
            
            
        for testset in testsets:
            try:
                TestSet.objects.get(name=testset)
            except ObjectDoesNotExist:
                error_msg.append('testset ' + testset + ' does not exist in smt system')
    else:
        error_msg.append('parameter is not complete')
    if error_msg:
        return HttpResponseBadRequest(str(error_msg))
    else:
        return HttpResponse('good')
