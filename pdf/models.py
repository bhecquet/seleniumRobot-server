from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class PdfRequestLog(models.Model):
    """Trace of a request made on PDF tools (comparison or file test)"""

    RETENTION_DAYS = 183  # about 6 months

    TYPE_COMPARISON = 'comparison'
    TYPE_VALIDATION = 'validation'
    TYPE_CHOICES = [
        (TYPE_COMPARISON, 'PDF comparison'),
        (TYPE_VALIDATION, 'PDF file test'),
    ]

    ORIGIN_UI = 'ui'
    ORIGIN_API = 'api'
    ORIGIN_CHOICES = [
        (ORIGIN_UI, 'UI'),
        (ORIGIN_API, 'API'),
    ]

    date = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='pdf_request_logs')
    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    origin = models.CharField(max_length=10, choices=ORIGIN_CHOICES, default=ORIGIN_UI)
    # number of pages of the first (or only) file. Null if file could not be read
    nb_pages_1 = models.PositiveIntegerField(null=True, blank=True)
    # number of pages of the second file. Null for a PDF file test or unreadable file
    nb_pages_2 = models.PositiveIntegerField(null=True, blank=True)
    user_instructions = models.TextField(blank=True, default='')
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-date']

    @classmethod
    def purge_old(cls):
        """Delete entries older than the retention period. Return number of deleted rows.

        A single DELETE with a date filter is idempotent: concurrent calls simply delete
        overlapping sets of rows, and rows already deleted by another call are ignored.
        """
        limit = timezone.now() - timedelta(days=cls.RETENTION_DAYS)
        deleted_count, _ = cls.objects.filter(date__lt=limit).delete()
        return deleted_count

    def __str__(self):
        return f'{self.request_type} by {self.user} on {self.date}'
