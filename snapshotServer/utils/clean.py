import logging
from snapshotServer.models import StepReference, Snapshot, TestSession,\
    TestCaseInSession, File
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db.models import F
from PIL import Image
from pathlib import Path

logger = logging.getLogger(__name__)

HTML_OPTIMIZED = 10
IMAGES_OPTIMIZED = 20
VIDEO_OPTIMIZED = 30

def clean_old_references():
    # Your job processing logic here...
    logger.info("clean_old_references")

    """
    Clean old step references every day
    This will only 
    - delete reference from database
    - delete files associated to StepReference model
    
    Files in "detect" folder won't be deleted this way but it's not a problem, as FieldDetector has it's own cleaning method which already deletes old files
    """
    logger.info('deleting old references')
    StepReference.objects.filter(date__lt=timezone.now() - timedelta(seconds=60 * 60 * 24 * settings.DELETE_STEP_REFERENCE_AFTER_DAYS)).delete()

def clean_old_sessions():
    """
    search all sessions whose date is older than defined 'ttl' (ttl > 0)
    do not select sessions whose snapshot number is > 0 and reference snapshot number is > 0
    a sub query is used because we need 'inner join' when filtering and django creates 'left outer join' which gets more than necessary
    """
    
    for session in TestSession.objects.filter(ttl__gt=timedelta(days=0), 
                                              date__lt=timezone.now() - F('ttl'))\
                                        .exclude(id__in=[s.stepResult.testCase.session.id for s in Snapshot.objects.filter(refSnapshot=None).select_related('stepResult__testCase__session')]).distinct():
        logger.info("deleting session {}-{} of the {}".format(session.id, str(session), session.date))
        session.delete()
        
def compress_images():
    """
    Compress images for tests in success and failed tests
    This is done in 2 steps as delay differ
    """
    logger.info("compressing images")
    
    # get test cases older than N days which are not optimized
    for test_case_in_session in TestCaseInSession.objects.filter(optimized__lt=IMAGES_OPTIMIZED, status='SUCCESS', session__date__lt=timezone.now() - timedelta(days=settings.COMPRESS_IMAGE_FOR_SUCCESS_AFTER_DAYS)):
        _compress_image_files(test_case_in_session)
        
    for test_case_in_session in TestCaseInSession.objects.filter(optimized__lt=IMAGES_OPTIMIZED, status='FAILURE', session__date__lt=timezone.now() - timedelta(days=settings.COMPRESS_IMAGE_FOR_FAILURE_AFTER_DAYS)):
        _compress_image_files(test_case_in_session)

    
def _compress_image_files(test_case_in_session):
    
    for file in File.objects.filter(stepResult__testCase=test_case_in_session):
        if file.file.name.lower().endswith('.jpg') or file.file.name.lower().endswith('.png'): 
            try:
                with Image.open(file.file.path) as img:
                    img = img.resize((int(img.width * 0.4), int(img.height * 0.4)), Image.LANCZOS)
                    img.save(file.file.path, quality=85, optimize=True)
            except Exception as e:
                logger.warn(f"Cannot compress image {file.file.path}: {str(e)}")
        
    test_case_in_session.optimized = IMAGES_OPTIMIZED
    test_case_in_session.save()
    
def replace_html():
    """
    After some days, remove the original HTML zipped file and replace it with a file that states it has been removed 
    """
    logger.info("deleting old HTML")
        
    # get test cases older than N days which are not optimized
    for test_case_in_session in TestCaseInSession.objects.filter(optimized__lt=HTML_OPTIMIZED, status='SUCCESS', session__date__lt=timezone.now() - timedelta(days=settings.DELETE_HTML_FOR_SUCCESS_AFTER_DAYS)):
        _replace_html_files(test_case_in_session)
        
    for test_case_in_session in TestCaseInSession.objects.filter(optimized__lt=HTML_OPTIMIZED, status='FAILURE', session__date__lt=timezone.now() - timedelta(days=settings.DELETE_HTML_FOR_FAILURE_AFTER_DAYS)):
        _replace_html_files(test_case_in_session)

        
def _replace_html_files(test_case_in_session):
    for file in File.objects.filter(stepResult__testCase=test_case_in_session):
        if file.file.name.lower().endswith('.zip') or file.file.name.lower().endswith('.html'):
            try:
                new_file_path = Path(file.file.path).parent / 'replaced.txt'
                if not new_file_path.exists():
                    with open(new_file_path, 'w') as new_html:
                        new_html.write('File has been removed to free space')

                file.file.delete()
                file.file = new_file_path.relative_to(settings.MEDIA_ROOT).as_posix()
                file.save()
            except Exception as e:
                logger.warn(f"Cannot delete html {file.file.path}: {str(e)}")
        
    test_case_in_session.optimized = HTML_OPTIMIZED
    test_case_in_session.save()
    
        
def replace_video():
    """
    After some days, remove video files
    """
    logger.info("deleting old videos")
    
    # get test cases older than N days which are not optimized
    for test_case_in_session in TestCaseInSession.objects.filter(optimized__lt=VIDEO_OPTIMIZED, status='SUCCESS', session__date__lt=timezone.now() - timedelta(days=settings.DELETE_VIDEO_FOR_SUCCESS_AFTER_DAYS)):
        for file in File.objects.filter(stepResult__testCase=test_case_in_session):
            if file.file.name.lower().endswith('.avi'):
                try:
                    new_file_path = Path(file.file.path).parent / 'replaced_video.txt'
                    if not new_file_path.exists():
                        with open(new_file_path, 'w') as new_html:
                            new_html.write('Video file has been removed to free space')
    
                    file.file.delete()
                    file.file = new_file_path.relative_to(settings.MEDIA_ROOT).as_posix()
                    file.save()
                except Exception as e:
                    logger.warn(f"Cannot delete video {file.file.path}: {str(e)}")
            
        test_case_in_session.optimized = VIDEO_OPTIMIZED
        test_case_in_session.save()