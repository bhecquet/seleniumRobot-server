import django.test
from django.urls.base import reverse
from variableServer.utils.utils import SPECIAL_NONE, updateVariables
from variableServer.models import Variable

class test_FileUploadView(django.test.TestCase):
    fixtures = ['varServer.yaml']

    
    def setUp(self):
        pass
    
#     def test__updateVariables(self):
#         """
#         check that updateVariable keeps the variable from additionalQuerySet parameters when it overrides one from sourceQuerySet
#         """
#         sourceQuerySet = Variable.objects.filter(application=None, version=None, environment=None, test=None)
#         additionalQuerySet = Variable.objects.filter(application=None, version=None, environment=1, test=None)
#         
#         resultingQS = updateVariables(sourceQuerySet, additionalQuerySet)
#         
#         self.assertEquals(resultingQS.get(name='proxyPassword').value, 'devPassword')
#     
#     def test_severalUpdateVariables(self):
#         """
#         check that several updateVariables calls can be chained
#         """
#         sourceQuerySet = Variable.objects.filter(application=None, version=None, environment=None, test=None)
#         additionalQuerySet = Variable.objects.filter(application=None, version=None, environment=1, test=None)
#         
#         resultingQS = updateVariables(sourceQuerySet, additionalQuerySet)
#         otherQuerySet = Variable.objects.filter(application=2, version=None, environment=None, test=None)
#         resultingQS = updateVariables(resultingQS, otherQuerySet)
#         
#         self.assertEquals(resultingQS.get(name='proxyPassword').value, 'devPassword')
#         self.assertEquals(resultingQS.get(name='appName').value, 'myApp')
    
    def test_getAllVariables(self):
        """
        Check a reference is created when non is found
        """
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        
        # check filtering is correct. We should not get any variable corresponding to an other environment, test or version
        for variable in response.data:
            self.assertTrue(variable['environment'] in [1, 3, None], "variable %s should not be get as environment is different from 1 and None" % variable['name'])
            self.assertTrue(variable['version'] in [2, None], "variable %s should not be get as version is different from 2 and None" % variable['name'])
            self.assertTrue(variable['test'] in [1, None], "variable %s should not be get as test is different from 1 and None" % variable['name'])
            
        # check we get variables from the generic environment
        for variable in response.data:
            if variable['name'] == 'logs' and variable['environment'] == 1:
                break
        else:
            self.fail("No variable from generic environment get");
        
        # check we only get variable where release date is before now and variables without release date
        
        # check overriding of variables