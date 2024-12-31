from django.views.generic.list import ListView
from snapshotServer.models import Version
from django.shortcuts import render, redirect
from snapshotServer.views.login_required_mixin_conditional import LoginRequiredMixinConditional


class ApplicationVersionListView(LoginRequiredMixinConditional, ListView):
    """
    View displaying the application / version list and entry point for snapshot view or test result view
    """
    
    template_name = "snapshotServer/home.html"
    queryset = Version.objects.none()
    
    def get_queryset(self):
        return Version.objects.all()

    
    def get(self, request):
        try:
            Version.objects.get(pk=request.GET.get('application'))
        except:
            return render(request, self.template_name, {'error': "Application version %s does not exist" % request.POST.get('application'),
                                                           'object_list': self.get_queryset()})

        display_type = request.GET.get('display')

        if display_type == 'snapshot':
            return redirect('sessionListView', request.GET.get('application'))
        else:
            return redirect('testResultTableView', request.GET.get('application'))