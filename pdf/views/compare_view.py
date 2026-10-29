import base64
import logging
import uuid
import json

from django.core.cache import cache
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from pdf.controllers.comparison.comparison_service import run_comparison
from pdf.forms import PdfCompareForm
from pdf.models import PdfRequestLog

logger = logging.getLogger(__name__)

class PdfCompareView(LoginRequiredMixin, View):
    """
    Vue permettant de comparer deux fichiers PDF.
    GET  : affiche le formulaire d'upload.
    POST : lance la comparaison et redirige vers la page de résultats.
    """

    template_name = 'pdf/compare.html'
    result_template_name = 'pdf/compare_result.html'
    cache_prefix = 'pdf_compare_payload'
    cache_timeout_seconds = 15 * 60

    def get(self, request):

        form = PdfCompareForm()
        json_response = json.dumps({'bla': 'bidule', 'foo': 'truc'}, indent=3)
        return render(request, self.template_name, {'form': form, 'test_json': json_response})

    def post(self, request):
        form = PdfCompareForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        pdf1 = form.cleaned_data['pdf_file_1']
        pdf2 = form.cleaned_data['pdf_file_2']
        model = form.cleaned_data['model']
        user_prompt = form.cleaned_data['user_prompt']

        try:
            result, _ = run_comparison(request.user, PdfRequestLog.ORIGIN_UI, model, pdf1, pdf2, user_prompt)
        except Exception as e:
            return render(request, self.template_name, {
                'form': form,
                'error': f'Error occured during comparison : {e}'
            })

        request.session['pdf_compare_result'] = result
        token = self._store_uploaded_pdfs_temporarily(pdf1, pdf2)
        request.session['pdf_compare_payload_token'] = token
        return redirect('pdf-compare-result')

    def _store_uploaded_pdfs_temporarily(self, left_pdf_file, right_pdf_file):
        # Keep uploaded binaries for the result page rendered after redirect.
        left_pdf_file.seek(0)
        left_content = left_pdf_file.read()
        left_pdf_file.seek(0)

        right_pdf_file.seek(0)
        right_content = right_pdf_file.read()
        right_pdf_file.seek(0)

        token = uuid.uuid4().hex
        cache.set(
            f'{self.cache_prefix}:{token}',
            {
                'left_name': getattr(left_pdf_file, 'name', 'pdf_1.pdf'),
                'right_name': getattr(right_pdf_file, 'name', 'pdf_2.pdf'),
                'left_content': left_content,
                'right_content': right_content,
            },
            timeout=self.cache_timeout_seconds,
        )
        return token

    @staticmethod
    def _build_pdf_data_uri(content):
        if not content:
            return None
        return 'data:application/pdf;base64,' + base64.b64encode(content).decode('ascii')

