import io
from unittest import mock

import pypdf
from django.core.files.uploadedfile import SimpleUploadedFile


def http_response(status=200, json_data=None, content=b'{}'):
    r = mock.Mock()
    r.status_code = status
    r.json.return_value = json_data
    r.content = content
    return r


def build_pdf(nb_pages=1, name='file.pdf'):
    writer = pypdf.PdfWriter()
    for _ in range(nb_pages):
        writer.add_blank_page(width=100, height=100)
    buf = io.BytesIO()
    writer.write(buf)
    return SimpleUploadedFile(name, buf.getvalue(), content_type='application/pdf')
