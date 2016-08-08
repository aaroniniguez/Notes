from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView

urlpatterns = patterns('tracker.views',
        url(r'^getTest&var=(.{1,8})&id=(\d+)','getTest'),
        url(r'^insert','insert'),
        url(r'^piv_queue_hw','piv_queue_hw'),
        url(r'^piv_queue',RedirectView.as_view(url='http://smarttestdb.cal.ci.spirentcom.com/tracker/piv_queue_hw.html')),
        url(r'^piv_qemu_queue','piv_qemu_queue'),
        url(r'^fetch_piv_result','fetch_piv_result'),
        url(r'^ackrecovery', 'ackrecovery'),
        url(r'^validate','validate'),
        url(r'^piv_osev_queue','piv_osev_queue'),
)

urlpatterns += staticfiles_urlpatterns()
