import json
import requests

from django.conf import settings
from commonsServer import preferences
from pdf.controllers.comparison import ComparisonError
from pdf.controllers.comparison.comparison_result import ComparisonResult, Difference


class AzureOcrComparator:

    def __init__(self, user_prompt):

        self.azure_token_url = settings.AZURE_TOKEN_URL
        self.azure_keyvault_url = settings.AZURE_KEYVAULT_URL


    def _authenticate(self):
        # get keyvault token
        response = requests.get(settings.AZURE_TOKEN_URL, data={'grant_type': 'client_credentials',
                                                     'client_id': settings.AZURE_PLATFORM_CLIENT_ID,
                                                     'client_secret': settings.AZURE_PLATFORM_CLIENT_SECRET,
                                                     'scope': 'https://vault.azure.net/.default'})

        if response.status_code != 200:
            raise ComparisonError(f"Error authenticating with Azure: {response.content}")

        try:
            keyvault_token = response.json()['access_token']
        except KeyError as e:
            raise ComparisonError(f"Error getting Azure access token: {e}")

        # get API key from keyvault
        response = requests.get(settings.AZURE_KEYVAULT_URL, headers={'Authorization': f'Bearer {keyvault_token}'})

        if response.status_code != 200:
            raise ComparisonError(f"Error getting API key from Azure KeyVault: {response.content}")

        try:
            api_key = response.json()['value']
        except KeyError as e:
            raise ComparisonError(f"API key not returned from Azure KeyVault: {e}")

        # get backend token
        response = requests.get(settings.AZURE_TOKEN_URL, data={'grant_type': 'client_credentials',
                                                                'client_id': settings.AZURE_PLATFORM_CLIENT_ID,
                                                                'client_secret': settings.AZURE_PLATFORM_CLIENT_SECRET,
                                                                'scope': settings.AZURE_PDF_API_SCOPE})

        if response.status_code != 200:
            raise ComparisonError(f"Error authenticating with Azure API: {response.content}")

        try:
            backend_token = response.json()['access_token']
        except KeyError as e:
            raise ComparisonError(f"Error getting Azure access token for API: {e}")

        return api_key, backend_token




    def compare(self, pdf1, pdf2) -> ComparisonResult:
        """Simulate a PDF comparison by returning a fixed result."""
        differences = []

        api_key, backend_token = self._authenticate()

        response = requests.post(settings.AZURE_PDF_API_URL, headers={"Authorization": f"Bearer {backend_token}",
                                                           "ocp-apim-subscription-key": api_key},
                      files={'file1': pdf1.open('rb'), 'file2': pdf2.open('rb')})

        if response.status_code != 200:
            raise ComparisonError(f"Error Comparing documents {response.content}")

        try:
            json_content = response.json()
            detected_differences = json_content['content_differences']

            for difference in detected_differences:
                differences.append(Difference(difference.get('page', 'N/A'), difference.get('section', 'N/A'), format_details_for_content_difference(difference)))

        except Exception as e:
            raise ComparisonError(f"Error comparing documents: {str(e)}")

        return ComparisonResult(differences, response.content)

def format_details_for_content_difference(difference):

    return f'''{difference.get('difference_type', '')}
    field: '{difference.get('field', '')}'
    doc1: '{difference.get('document_1', '')}'
    doc2: '{difference.get('document_2', '')}'
    '''
