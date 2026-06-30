import base64
import io
import json

import pypdf
import requests
from django.conf import settings

from commonsServer import preferences
from pdf.controllers.comparison import ComparisonError
from pdf.controllers.comparison.comparison_result import ComparisonResult, Difference


class MistralDocComparator:


    def __init__(self, user_prompt):
        self.prompt = preferences.get_preference('MISTRAL_DOC_COMPARISON_SYSTEM_PROMPT') + "\n\n" + user_prompt
        self.difference_prompt = preferences.get_preference('MISTRAL_DOC_COMPARISON_DIFFERENCES_PROMPT')

    def compare(self, pdf1, pdf2) -> ComparisonResult:
        """Simulate a PDF comparison by returning a fixed result."""
        differences = []
        page_number_1, page_number_2, combined_pdfs = self.combine_pdf_for_comparison(pdf1, pdf2)

        if page_number_1 != page_number_2:
            differences.append(Difference(0, 'document', 'First document has %d pages, second has %d pages' % (page_number_1, page_number_2)))

        for page, combined_pdf in enumerate(combined_pdfs):
            data_with_comparison = {
                "model": "deploy-mistral-document-ai-2512",
                "document": {
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{combined_pdf}"
                },
                "document_annotation_prompt": self.prompt % {'page_number_1': page_number_1, 'page_number_2': page_number_2},
                "document_annotation_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "schema": {
                            "properties": {
                                "differences": {
                                    "title": "differences",
                                    "type": "string",
                                    "description": self.difference_prompt % {'page_number_1': page_number_1, 'page_number_2': page_number_2}
                                },
                                "explanation": {
                                    "title": "explanation",
                                    "type": "string",
                                    "description": """List sections / paragraphs / thematic blocks in each document."""
                                }
                            },
                            "required": ["differences"],
                            "title": "DocumentAnnotation",
                            "type": "object",
                            "additionalProperties": False
                        },
                        "name": "document_annotation",
                        "strict": True
                    }
                },
                "include_image_base64": True
            }

            response = requests.post(settings.MISTRAL_DOCUMENT_URL,
                                     json=data_with_comparison,
                                     headers={"Content-Type": "application/json",
                                              "Authorization": f"Bearer {settings.MISTRAL_DOCUMENT_API_KEY}"
                                              }
                                     )

            if response.status_code == 408:
                raise ComparisonError(f"Timeout getting response for page {page}")
            elif response.status_code >= 400:
                raise ComparisonError(f"Error Comparing documents {response.content} for page {page}")


            try:
                json_content = json.loads(response.content)
                mistral_content = json.loads(json_content['document_annotation'])
                detected_differences = json.loads(mistral_content['differences'])

                for difference in detected_differences:
                    differences.append(Difference(page + 1, difference['location'], difference['details']))

            except Exception as e:
                raise ComparisonError(f"Error comparing documents: {str(e)} for page {page}")

        return ComparisonResult(self._filter_differences(differences))

    def _filter_differences(self, differences: list[Difference]):
        """
        model may return the same difference several times (although told not to do it)
        So, remove duplications
        :param differences:
        :return:
        """
        new_differences = []

        for difference in differences:
            if difference not in new_differences:
                new_differences.append(difference)

        return new_differences

    def combine_pdf_for_comparison(self, pdf1: str, pdf2: str):
        """
        Writes a single PDF file with the 2 input PDF
        :param pdf1: First PDF to compare
        :param pdf2: Second PDF to compare
        :return: list of PDF content (base64 encoded). Each list is the concatenation of the Nth page of input document
        """
        out_pdf = []

        reader1 = pypdf.PdfReader(pdf1)
        reader2 = pypdf.PdfReader(pdf2)

        for i in range(0, min(len(reader1.pages), len(reader2.pages))):
            writer = pypdf.PdfWriter()
            writer.add_page(reader1.pages[i])
            writer.add_page(reader2.pages[i])

            buf = io.BytesIO()
            writer.write(buf)

            out_pdf.append(base64.b64encode(buf.getvalue()).decode())

        # writer.write(r"D:\tmp\out.pdf")
        return len(reader1.pages), len(reader2.pages), out_pdf