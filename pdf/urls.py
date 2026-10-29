from django.urls import path
from pdf.views.api_compare_view import PdfCompareApiView
from pdf.views.compare_result_view import PdfCompareResultView
from pdf.views.compare_view import PdfCompareView
from pdf.views.home_view import PdfHomeView
from pdf.views.validate_view import PdfValidateView

urlpatterns = [
    path('home/', PdfHomeView.as_view(), name='pdf-home'),
    path('compare/', PdfCompareView.as_view(), name='pdf-compare'),
    path('compare/result/', PdfCompareResultView.as_view(), name='pdf-compare-result'),
    path('validate/', PdfValidateView.as_view(), name='pdf-validate'),
    path('api/compare/', PdfCompareApiView.as_view(), name='pdf-api-compare'),
]
