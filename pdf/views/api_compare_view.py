from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from pdf.controllers.comparison.comparison_service import run_comparison
from pdf.forms import PdfCompareForm
from pdf.models import PdfRequestLog


class PdfCompareApiView(APIView):
    """
    Compare two PDF files from an API call (e.g. a Selenium test).
    Any authenticated user can call it, no specific permission is required.

    POST multipart/form-data: 'reference' (PDF), 'file' (PDF), 'model', optional 'instructions'
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        # input names differ from the GUI, but validation rules must be the same
        form = PdfCompareForm(
            {
                'model': request.data.get('model', ''),
                'user_prompt': request.data.get('instructions', ''),
            },
            {
                'pdf_file_1': request.FILES.get('reference'),
                'pdf_file_2': request.FILES.get('file'),
            },
        )
        if not form.is_valid():
            return Response({'errors': self._map_errors(form.errors.get_json_data())}, status=400)

        try:
            result, duration = run_comparison(
                request.user,
                PdfRequestLog.ORIGIN_API,
                form.cleaned_data['model'],
                form.cleaned_data['pdf_file_1'],
                form.cleaned_data['pdf_file_2'],
                form.cleaned_data['user_prompt'],
            )
        except Exception as e:
            return Response({'error': f'Error occured during comparison : {e}'}, status=500)

        return Response({
            'differences': [
                {
                    'location': difference.get('location'),
                    'details': difference.get('details'),
                    'page': difference.get('page'),
                }
                for difference in result['differences']
            ],
            'duration': duration,
        })

    @staticmethod
    def _map_errors(errors):
        """Rename form fields to API parameter names"""
        names = {'pdf_file_1': 'reference', 'pdf_file_2': 'file', 'user_prompt': 'instructions', 'model': 'model'}
        return {names.get(field, field): [e['message'] for e in messages] for field, messages in errors.items()}
