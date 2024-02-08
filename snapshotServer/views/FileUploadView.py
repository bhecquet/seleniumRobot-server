from rest_framework import views
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.forms import ImageForComparisonUploadForm,\
    ImageForComparisonUploadFormNoStorage
from snapshotServer.models import Snapshot, StepResult
import json
from django.http.response import HttpResponse
import base64
import io
from PIL import Image
from tempfile import NamedTemporaryFile
import os



class FileUploadView(views.APIView):
    """
    View of the API to upload a file with snapshot informations
    It creates the snapshot and detects if a reference already exists for this snapshot
    """
    
    parser_classes = (MultiPartParser,)
    queryset = Snapshot.objects.all()

    # test with CURL
    # curl -u admin:adminServer -F "step=1" -F "stepResult=1234" -F "image=@/home/worm/Ibis Mulhouse.png" -F "compare=true"   http://127.0.0.1:8000/upload/toto
    def post(self, request, filename, format=None):
        
        form = ImageForComparisonUploadForm(request.POST, request.FILES)
        
        
        if form.is_valid():
            return self.compare_or_store_snapshot(form, StepResult.objects.get(id=form.cleaned_data['stepResult']))
        
        else:
            return Response(status=500, data=str(form.errors))
        
    def put(self, request, filename, format=None):
        
        form = ImageForComparisonUploadFormNoStorage(request.POST, request.FILES)
        
        if form.is_valid():
            return self.compare_or_store_snapshot(form, form.cleaned_data['stepResult'])
        
        else:
            return Response(status=500, data=str(form.errors))
    

    def compare_or_store_snapshot(self, form, step_result):
        
        image = form.cleaned_data['image']                              # the image file
        name = form.cleaned_data['name']                                # name of the image
        store_snapshot = form.cleaned_data['storeSnapshot']         # do we store the image or not. If False, only comparison is returned
        diff_tolerance = form.cleaned_data.get('diffTolerance', 0.0)    # percentage of admissible error
        compare_option = form.cleaned_data.get('compare', 'true')       # how we compare image
        exclude_zones = form.cleaned_data.get('excludeZones', [])       # the exclusion zones that will be taken into account when computing
        
        # check if a reference exists for this step in the same test case / same application / same version / same environment / same browser / same name
        most_recent_reference_snapshot = Snapshot.objects.filter(stepResult__step=step_result.step,                                                    # same step in the test case
                                                      stepResult__testCase__testCase__name=step_result.testCase.testCase.name,              # same test case
                                                      stepResult__testCase__session__version=step_result.testCase.session.version,          # same version
                                                      stepResult__testCase__session__environment=step_result.testCase.session.environment,  # same environment
                                                      stepResult__testCase__session__browser=step_result.testCase.session.browser,          # same browser
                                                      refSnapshot=None,                                                                     # a reference image
                                                      name=name).order_by('pk').last()                                                                          # same snapshot name
        
        # check for a reference in previous versions
        if not most_recent_reference_snapshot:
            for app_version in reversed(step_result.testCase.session.version.previousVersions()):
                most_recent_reference_snapshot = Snapshot.objects.filter(stepResult__step=step_result.step, 
                                                              stepResult__testCase__testCase__name=step_result.testCase.testCase.name, 
                                                              stepResult__testCase__session__version=app_version, 
                                                              stepResult__testCase__session__environment=step_result.testCase.session.environment, 
                                                              stepResult__testCase__session__browser=step_result.testCase.session.browser, 
                                                              refSnapshot=None,
                                                              name=name).order_by('pk').last()     
                if most_recent_reference_snapshot:
                    break
        
        diff_pixels_percentage = 0.0
        
        if most_recent_reference_snapshot:
            step_snapshot = Snapshot(stepResult=step_result, image=image, refSnapshot=most_recent_reference_snapshot, name=name, compareOption=compare_option, diffTolerance=diff_tolerance)
            
            # we store the snapshot for future use, when user needs to know why comparison failed
            if store_snapshot:
                step_snapshot.save()
                
                # store exclude zones with the snapshot, as we already store the snapshot
                for exclude_zone in exclude_zones:
                    exclude_zone.snapshot = step_snapshot
                    exclude_zone.save()
            
                # compute difference if a reference already exist
                DiffComputer.get_instance().add_jobs(most_recent_reference_snapshot, step_snapshot)
                
            # we want the comparison result now, to tell if the test should fail or not
            else:
                try:
                    
                    # as we don't save step_snapshot (it's temp computation), we still save the image data temporary at the location it's expected
                    with open(step_snapshot.image.path, 'wb') as img:
                        img.write(image.read())
                        img.flush()
                        
                        DiffComputer.get_instance().compute_now(most_recent_reference_snapshot, step_snapshot, save_snapshot=False, additional_exclude_zones=exclude_zones)
                finally:
                    try:
                        os.remove(step_snapshot.image.path)
                    except Exception as e:
                        pass
                
                if step_snapshot.pixelsDiff is not None:
                    with io.BytesIO(step_snapshot.pixelsDiff) as input:

                        # diff is represented by a red pixel
                        diff_pixels_percentage = 100 * (sum(list(Image.open(input).getdata(3))) / 255) / (step_snapshot.image.width * step_snapshot.image.height)

        else:
            # snapshot is marked as computed as this is a reference snapshot
            step_snapshot = Snapshot(stepResult=step_result, image=image, refSnapshot=None, name=name, compareOption=compare_option, computed=True, diffTolerance=diff_tolerance)
            if store_snapshot:
                step_snapshot.save()
            
        return HttpResponse(json.dumps({'id': step_snapshot.id, 
                                        'computed': step_snapshot.computed,
                                        'computingError': step_snapshot.computingError, 
                                        'diffPixelPercentage': diff_pixels_percentage, 
                                        'tooManyDiffs': step_snapshot.tooManyDiffs}), content_type='application/json', status=201)