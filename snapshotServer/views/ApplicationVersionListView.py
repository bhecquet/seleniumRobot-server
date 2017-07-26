from django.views.generic.list import ListView
from snapshotServer.models import Version
from django.shortcuts import render_to_response, redirect


class ApplicationVersionListView(ListView):
    template_name = "snapshotServer/home.html"
    
    def get_queryset(self):
        return Version.objects.all()

    
    def post(self, request):
        try:
            Version.objects.get(pk=request.POST.get('application'))
        except:
            return render_to_response(self.template_name, {'error': "Application version %s does not exist" % request.POST.get('application'),
                                                           'object_list': self.get_queryset()})

        return redirect('sessionListView', request.POST.get('application'))