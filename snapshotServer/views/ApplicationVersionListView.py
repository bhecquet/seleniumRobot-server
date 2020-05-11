from django.views.generic.list import ListView
from snapshotServer.models import Version
from django.shortcuts import render, redirect
from snapshotServer.views.LoginRequiredMixinConditional import LoginRequiredMixinConditional


class ApplicationVersionListView(LoginRequiredMixinConditional, ListView):
    """
    View displaying the application / version list and entry point for snapshot view or test result view
    """
    
    template_name = "snapshotServer/home.html"
    queryset = Version.objects.none()
    
    def get_queryset(self):
        return Version.objects.all()

    
    def post(self, request):
        try:
            Version.objects.get(pk=request.POST.get('application'))
        except:
            return render(request, self.template_name, {'error': "Application version %s does not exist" % request.POST.get('application'),
                                                           'object_list': self.get_queryset()})

        displayType = request.POST.get('display')

        if displayType == 'snapshot':
            return redirect('sessionListView', request.POST.get('application'))
        else:
            return redirect('testResultTableView', request.POST.get('application'))