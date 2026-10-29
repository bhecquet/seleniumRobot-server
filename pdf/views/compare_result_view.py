import base64
import logging
import uuid
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.views import View

from pdf.controllers.comparison import ComparisonError
from pdf.controllers.comparison.azure_ocr_comparator import AzureOcrComparator
from pdf.controllers.comparison.mistral_document_annotation_comparator import MistralDocComparator
from pdf.controllers.comparison.stub_comparator import StubComparator
from pdf.forms import PdfCompareForm
from pdf.views.compare_view import PdfCompareView

logger = logging.getLogger(__name__)

class PdfCompareResultView(LoginRequiredMixin, View):
    """Display result of the last PDF comparison"""

    template_name = 'pdf/compare_result.html'

    def get(self, request):
        result = request.session.get('pdf_compare_result')
        if not result:
            return redirect('pdf-compare')

        payload = None
        token = request.session.get('pdf_compare_payload_token')
        if token:
            payload = cache.get(f'{PdfCompareView.cache_prefix}:{token}')

        context = {'result': result}
        if payload:
            context['left_pdf_name'] = payload.get('left_name')
            context['right_pdf_name'] = payload.get('right_name')
            context['left_pdf_src'] = PdfCompareView._build_pdf_data_uri(payload.get('left_content'))
            context['right_pdf_src'] = PdfCompareView._build_pdf_data_uri(payload.get('right_content'))

        return render(request, self.template_name, context)


