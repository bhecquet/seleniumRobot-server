from django.urls import path
from pdf.compare_view import PdfCompareResultView, PdfCompareView
from pdf import views

urlpatterns = [
    path('home/', views.home, name='pdf-home'),
    path('compare/', PdfCompareView.as_view(), name='pdf-compare'),
    path('compare/result/', PdfCompareResultView.as_view(), name='pdf-compare-result'),
    path('validate/', views.validate, name='pdf-validate'),
]
