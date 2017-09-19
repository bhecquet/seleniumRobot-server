'''
Created on 19 sept. 2017

@author: worm
'''
from django.views.generic.base import View
from django.views.generic.detail import DetailView

class ApplicationView(DetailView):
    
    def get(self, *args, **kwargs):
        pass
        