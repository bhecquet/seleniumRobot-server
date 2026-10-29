from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from pdf.models import PdfRequestLog


class TestPdfRequestLog(TestCase):

    def _create(self, age_days):
        log = PdfRequestLog.objects.create(request_type=PdfRequestLog.TYPE_COMPARISON, nb_pages_1=1, nb_pages_2=1)
        # date is auto_now_add, so it must be changed through update()
        PdfRequestLog.objects.filter(pk=log.pk).update(date=timezone.now() - timedelta(days=age_days))
        return log

    def test_purge_old_removes_only_old_entries(self):
        """RG-LOG-06: only rows older than 183 days are deleted"""
        old = self._create(PdfRequestLog.RETENTION_DAYS + 1)
        recent = self._create(PdfRequestLog.RETENTION_DAYS - 1)

        PdfRequestLog.purge_old()

        self.assertEqual([recent.pk], list(PdfRequestLog.objects.values_list('pk', flat=True)))
        self.assertFalse(PdfRequestLog.objects.filter(pk=old.pk).exists())

    def test_purge_old_is_idempotent(self):
        """RG-LOG-06: purge is idempotent (repeated / concurrent calls)"""
        self._create(PdfRequestLog.RETENTION_DAYS + 10)
        self._create(1)

        PdfRequestLog.purge_old()
        PdfRequestLog.purge_old()

        self.assertEqual(1, PdfRequestLog.objects.count())
