from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View


class PdfValidateView(LoginRequiredMixin, View):
    template_name = 'pdf/validate.html'

    def get(self, request):
        return render(request, self.template_name)
