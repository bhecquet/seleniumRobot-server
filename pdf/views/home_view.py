from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View


class PdfHomeView(LoginRequiredMixin, View):
    template_name = 'pdf/home.html'

    def get(self, request):
        return render(request, self.template_name)
