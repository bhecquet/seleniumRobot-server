from django.shortcuts import render


def home(request):
    return render(request, 'pdf/home.html')



def validate(request):
    return render(request, 'pdf/validate.html')
