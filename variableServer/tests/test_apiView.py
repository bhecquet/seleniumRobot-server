
from django.urls.base import reverse
from variableServer.utils.utils import  updateVariables
from variableServer.models import Variable, Version,\
    TestEnvironment, TestCase
import time
import datetime
from django.utils import timezone
from variableServer.tests import authenticate_test_client

from rest_framework.test import APITestCase

class TestApiView(APITestCase):
    '''
    Using APITestCase as we call the REST Framework API
    Client handles patch / put cases
    '''
    fixtures = ['varServer.yaml']

    
    
    def setUp(self):
        authenticate_test_client(self.client)
        
         
    def test_ping(self):
        """
        Check 'ping' api can be called without security token
        """
        self.client.credentials()
        response = self.client.get(reverse('variablePing'))
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
    
    def test_update_variables(self):
        """
        check that updateVariable keeps the variable from additional_query_set parameters when it overrides one from source_query_set
        """
        source_query_set = Variable.objects.filter(application=None, version=None, environment=None, test=None)
        additional_query_set = Variable.objects.filter(application=None, version=None, environment=1, test=None)
         
        resulting_qs = updateVariables(source_query_set, additional_query_set)
         
        self.assertEqual(resulting_qs.get(name='proxyPassword').value, 'azerty')
     
    def test_several_update_variables(self):
        """
        check that several updateVariables calls can be chained
        """
        source_query_set = Variable.objects.filter(application=None, version=None, environment=None, test=None)
        additional_query_set = Variable.objects.filter(application=None, version=None, environment=1, test=None)
         
        resulting_qs = updateVariables(source_query_set, additional_query_set)
        other_query_set = Variable.objects.filter(application=2, version=None, environment=None, test=None)
        resulting_qs = updateVariables(resulting_qs, other_query_set)
         
        self.assertEqual(resulting_qs.get(name='proxyPassword').value, 'azerty')
        self.assertEqual(resulting_qs.get(name='appName').value, 'myOtherApp')

    def _convert_to_dict(self, responseData):
        variable_dict = {}
        for variable in responseData:
            variable_dict[variable['name']] = variable
             
        return variable_dict
     
    def test_get_all_variables_no_security(self):
        """
        Check we cannot access API without API token
        """
        self.client.credentials()
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 401, 'status code should be 401: ' + str(response.content))
     
    def test_get_all_variables(self):
        """
        Check a reference is created when none is found
        """
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
             
        # check filtering is correct. We should not get any variable corresponding to an other environment, test or version
        for variable in response.data:
            self.assertTrue(variable['environment'] in [1, 3, None], "variable %s should not be get as environment is different from 1, 3 and None" % variable['name'])
            self.assertTrue(variable['version'] in [2, None], "variable %s should not be get as version is different from 2 and None" % variable['name'])
            self.assertTrue(variable['test'] in [[1], []], "variable %s should not be get as test is different from 1 and []" % variable['name'])
                 
        # check we get variables from the generic environment
        for variable in response.data:
            if variable['name'] == 'logs' and variable['environment'] == 1:
                break
        else:
            self.fail("No variable from generic environment get")
            
        self.assertTrue(len(response.data) > 5)
            
         
    def test_get_all_variables_with_name(self):
        """
        Check we filter variables by name and get only one variable
        """
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1, 'name': 'proxyPassword'})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
             
        # check filtering is correct. We should not get any variable corresponding to an other environment, test or version
        for variable in response.data:
            self.assertEqual(variable['name'], 'proxyPassword')
        
        self.assertEqual(len(response.data), 1)
        
    def test_get_all_variables_with_value(self):
        """
        Check we filter variables by value and get only one variable
        """
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1, 'value': 'logs_dev'})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
             
        # check filtering is correct. We should not get any variable corresponding to an other environment, test or version
        for variable in response.data:
            self.assertEqual(variable['value'], 'logs_dev')
            self.assertEqual(variable['name'], 'logs')
        
        self.assertEqual(len(response.data), 1)
    
    def test_get_all_variables_with_name_and_value(self):
        """
        Check we filter variables by value/name and get only one variable
        """
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1, 'name': 'logs', 'value': 'logs_dev'})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
             
        # check filtering is correct. We should not get any variable corresponding to an other environment, test or version
        for variable in response.data:
            self.assertEqual(variable['value'], 'logs_dev')
            self.assertEqual(variable['name'], 'logs')
        
        self.assertEqual(len(response.data), 1)
    
    def test_get_all_variables_with_name_and_value_reserved(self):
        """
        Check we filter variables by value/name and get only one variable
        """
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1, 'name': 'login'})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
             
        # check filtering is correct. We should not get any variable corresponding to an other environment, test or version
        for variable in response.data:
            self.assertEqual(variable['name'], 'login')
            
        self.assertTrue(Variable.objects.get(pk=response.data[0]['id']), "returned variable should be reserved")
        self.assertIsNotNone(Variable.objects.get(pk=response.data[0]['id']).releaseDate, "returned variable should be reserved")

             
    def test_get_all_variables_without_test(self):
        """
        Check that test parameter is not mandatory
        """
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            
        # check filtering is correct. We should not get any variable corresponding to an other environment, test or version
        for variable in response.data:
            self.assertTrue(variable['environment'] in [1, 3, None], "variable %s should not be get as environment is different from 1, 3 and None" % variable['name'])
            self.assertTrue(variable['version'] in [2, None], "variable %s should not be get as version is different from 2 and None" % variable['name'])
            self.assertTrue(variable['test'] in [[1], []], "variable %s should not be get as test is different from 1 and []" % variable['name'])
                
        # check we get variables from the generic environment
        for variable in response.data:
            if variable['name'] == 'logs' and variable['environment'] == 1:
                break
        else:
            self.fail("No variable from generic environment get")
             
    def test_get_all_variables_without_environment(self):
        """
        Check that environment parameter is  mandatory
        """
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'test': 1})
        self.assertEqual(response.status_code, 400, 'status code should be 400: ' + str(response.content))
         
    def test_get_all_variables_without_version(self):
        """
        Check that environment parameter is  mandatory
        """
        response = self.client.get(reverse('variableApi'), data={'test': 1, 'environment': 3})
        self.assertEqual(response.status_code, 400, 'status code should be 400: ' + str(response.content))
            
       
    def test_get_all_variables_with_text(self):
        """
        Check Variables are get when requesting them with environment name, application name, test name, ...
        """
        response = self.client.get(reverse('variableApi'), data={'application': 'app1', 'version': '2.5', 'environment': 'DEV1', 'test': 'test1 with some spaces'})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            
        # check filtering is correct. We should not get any variable corresponding to an other environment, test or version
        for variable in response.data:
            self.assertTrue(variable['environment'] in [1, 3, None], "variable %s should not be get as environment is different from 1, 3 and None" % variable['name'])
            self.assertTrue(variable['version'] in [2, None], "variable %s should not be get as version is different from 2 and None" % variable['name'])
            self.assertTrue(variable['test'] in [[1], []], "variable %s should not be get as test is different from 1 and None" % variable['name'])
                
        # check we get variables from the generic environment
        for variable in response.data:
            if variable['name'] == 'logs' and variable['environment'] == 1:
                break
        else:
            self.fail("No variable from generic environment get");
              
    def test_get_all_variables_with_text_missing_application(self):
        """
        Check error is raised when application name is missing (mandatory for finding version from its name)
        """
        response = self.client.get(reverse('variableApi'), data={'version': '2.5', 'environment': 'DEV1', 'test': 'test1 with some spaces'})
        self.assertEqual(response.status_code, 400, 'status code should be 400: ' + str(response.content))
   
            
    def test_get_all_variables_with_release_date(self):
        """
        Check that release dates are correctly managed
        variable is returned if
        - releaseDate is None
        - releaseDate is in the past (then it should be set to None)
        """
        version = Version.objects.get(pk=3)
        Variable(name='var0', value='value0', application=version.application, version=version).save()
        Variable(name='var1', value='value1', application=version.application, version=version, releaseDate=timezone.now() + datetime.timedelta(seconds=60)).save()
        Variable(name='var1', value='value2', application=version.application, version=version, releaseDate=timezone.now() - datetime.timedelta(seconds=60)).save()
             
        response = self.client.get(reverse('variableApi'), data={'version': 3, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        self.assertEqual(1, len([v for v in response.data if v['name'] == 'var1']), "Only one value should be get")
             
        all_variables = self._convert_to_dict(response.data)
             
        # check we only get variable where release date is before now and variables without release date
        self.assertTrue('var1' in all_variables)                 # release date in the past, should be removed
        self.assertEqual("value2", all_variables['var1']['value'])
        self.assertIsNone(all_variables['var1']['releaseDate'])  # release date should be reset 
        self.assertTrue('var0' in all_variables)                 # no release date
             
    def test_get_variables_override_global(self):
        """
        Check that global variables are overriden by application specific variables
        Order is (bottom take precedence):
        - global (no app, no env, no version, no test)
        - specific to on of the parameter (matching app or matching version or matching env or matching test in this order)
        - specific to tuple (application / environment)
        - specific to tuple (application / version / environment)
        - specific to tuple (application / environment / test)
        - specific to tuple (application / version / environment / test)
        """
        version = Version.objects.get(pk=3)
        Variable(name='var0', value='value0').save()
        Variable(name='var0', value='value1', application=version.application).save()
             
        response = self.client.get(reverse('variableApi'), data={'version': version.id, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        all_variables = self._convert_to_dict(response.data)
             
        # check overriding of variables
        self.assertEqual(all_variables['var0']['value'], 'value1')
             
    def test_get_variables_override_app_specific(self):
        """
        Check that application specific variables are overriden by application/version specific
        Order is (bottom take precedence):
        - global (no app, no env, no version, no test)
        - specific to on of the parameter (matching app or matching version or matching env or matching test in this order)
        - specific to tuple (application / environment)
        - specific to tuple (application / version / environment)
        - specific to tuple (application / environment / test)
        - specific to tuple (application / version / environment / test)
        """
        version = Version.objects.get(pk=3)
        Variable(name='var0', value='value0', application=version.application).save()
        Variable(name='var0', value='value1', application=version.application, version=version).save()
             
        response = self.client.get(reverse('variableApi'), data={'version': version.id, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        all_variables = self._convert_to_dict(response.data)
             
        # check overriding of variables
        self.assertEqual(all_variables['var0']['value'], 'value1')
             
    def test_get_variables_override_version_specific(self):
        """
        Check that application/version specific variables are overriden by environment specific
        Order is (bottom take precedence):
        - global (no app, no env, no version, no test)
        - specific to on of the parameter (matching app or matching version or matching env or matching test in this order)
        - specific to tuple (application / environment)
        - specific to tuple (application / version / environment)
        - specific to tuple (application / environment / test)
        - specific to tuple (application / version / environment / test)
        """
        version = Version.objects.get(pk=3)
        env = TestEnvironment.objects.get(pk=3)
        Variable(name='var0', value='value0', application=version.application, version=version).save()
        Variable(name='var0', value='value1', environment=env).save()
             
        response = self.client.get(reverse('variableApi'), data={'version': version.id, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        all_variables = self._convert_to_dict(response.data)
             
        # check overriding of variables
        self.assertEqual(all_variables['var0']['value'], 'value1')
                 
    def test_get_variables_override_generic_environment(self):
        """
        Check that application/version specific variables are overriden by environment specific
        Order is (bottom take precedence):
        - global (no app, no env, no version, no test)
        - specific to on of the parameter (matching app or matching version or matching env or matching test in this order)
        - specific to tuple (application / environment)
        - specific to tuple (application / version / environment)
        - specific to tuple (application / environment / test)
        - specific to tuple (application / version / environment / test)
        """
        version = Version.objects.get(pk=3)
        env = TestEnvironment.objects.get(pk=3)
        gen_env = TestEnvironment.objects.get(pk=1)
        Variable(name='var0', value='value0', environment=gen_env).save()
        Variable(name='var0', value='value1', environment=env).save()
             
        response = self.client.get(reverse('variableApi'), data={'version': version.id, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        all_variables = self._convert_to_dict(response.data)
             
        # check overriding of variables
        self.assertEqual(all_variables['var0']['value'], 'value1')
                 
    def test_get_variables_override_multiple_generic_environment(self):
        """
        Check that application/version specific variables are overriden by environment specific. Here, we have multiple parents for environment
        Order is (bottom take precedence):
        - global (no app, no env, no version, no test)
        - specific to on of the parameter (matching app or matching version or matching env or matching test in this order)
        - specific to tuple (application / environment)
        - specific to tuple (application / version / environment)
        - specific to tuple (application / environment / test)
        - specific to tuple (application / version / environment / test)
        """
        version = Version.objects.get(pk=3)
        env = TestEnvironment.objects.get(pk=4)
        gen_env1 = TestEnvironment.objects.get(pk=3)
        gen_env2 = TestEnvironment.objects.get(pk=1)
        Variable(name='var0', value='value0', environment=gen_env2).save()
        Variable(name='var0', value='value1', environment=gen_env1).save()
        Variable(name='var0', value='value2', environment=env).save()
             
        response = self.client.get(reverse('variableApi'), data={'version': version.id, 'environment': 4, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        all_variables = self._convert_to_dict(response.data)
             
        # check overriding of variables
        self.assertEqual(all_variables['var0']['value'], 'value2')
                 
    def test_get_variables_override_multiple_generic_environment2(self):
        """
        Check that application/version specific variables are overriden by environment specific. Here, we have multiple parents for environment
        Order is (bottom take precedence):
        - global (no app, no env, no version, no test)
        - specific to on of the parameter (matching app or matching version or matching env or matching test in this order)
        - specific to tuple (application / environment)
        - specific to tuple (application / version / environment)
        - specific to tuple (application / environment / test)
        - specific to tuple (application / version / environment / test)
        """
        version = Version.objects.get(pk=3)
        env = TestEnvironment.objects.get(pk=4)
        gen_env1 = TestEnvironment.objects.get(pk=3)
        gen_env2 = TestEnvironment.objects.get(pk=1)
        Variable(name='var0', value='value0', environment=gen_env2).save()
        Variable(name='var0', value='value1', environment=gen_env1).save()
             
        response = self.client.get(reverse('variableApi'), data={'version': version.id, 'environment': 4, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        all_variables = self._convert_to_dict(response.data)
             
        # check overriding of variables
        self.assertEqual(all_variables['var0']['value'], 'value1')
                 
    def test_get_variables_override_environment(self):
        """
        Check that environment specific variables are overriden by test specific
        Order is (bottom take precedence):
        - global (no app, no env, no version, no test)
        - specific to on of the parameter (matching app or matching version or matching env or matching test in this order)
        - specific to tuple (application / environment)
        - specific to tuple (application / version / environment)
        - specific to tuple (application / environment / test)
        - specific to tuple (application / version / environment / test)
        """
        version = Version.objects.get(pk=3)
        env = TestEnvironment.objects.get(pk=3)
        test = TestCase.objects.get(pk=1)
        Variable(name='var0', value='value0', environment=env).save()
        var1 = Variable(name='var0', value='value1', application=version.application)
        var1.save()
        var1.test.add(test)
             
        response = self.client.get(reverse('variableApi'), data={'version': version.id, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        all_variables = self._convert_to_dict(response.data)
             
        # check overriding of variables
        self.assertEqual(all_variables['var0']['value'], 'value1')
                 
    def test_get_variables_override_test(self):
        """
        Check that test specific variables are overriden by application/env specific
        Order is (bottom take precedence):
        - global (no app, no env, no version, no test)
        - specific to on of the parameter (matching app or matching version or matching env or matching test in this order)
        - specific to tuple (application / environment)
        - specific to tuple (application / version / environment)
        - specific to tuple (application / environment / test)
        - specific to tuple (application / version / environment / test)
        """
        version = Version.objects.get(pk=3)
        env = TestEnvironment.objects.get(pk=3)
        test = TestCase.objects.get(pk=1)
        var0 = Variable(name='var0', value='value0')
        var0.save()
        var0.test.add(test)
        Variable(name='var0', value='value1', application=version.application, environment=env).save()
             
        response = self.client.get(reverse('variableApi'), data={'version': version.id, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        all_variables = self._convert_to_dict(response.data)
             
        # check overriding of variables
        self.assertEqual(all_variables['var0']['value'], 'value1')
                 
    def test_get_variables_override_app_env(self):
        """
        Check that application/env specific variables are overriden by application/version/env specific
        Order is (bottom take precedence):
        - global (no app, no env, no version, no test)
        - specific to on of the parameter (matching app or matching version or matching env or matching test in this order)
        - specific to tuple (application / environment)
        - specific to tuple (application / version / environment)
        - specific to tuple (application / environment / test)
        - specific to tuple (application / version / environment / test)
        """
        version = Version.objects.get(pk=3)
        env = TestEnvironment.objects.get(pk=3)
        Variable(name='var0', value='value0', application=version.application, environment=env).save()
        Variable(name='var0', value='value1', application=version.application, version=version, environment=env).save()
             
        response = self.client.get(reverse('variableApi'), data={'version': version.id, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        all_variables = self._convert_to_dict(response.data)
             
        # check overriding of variables
        self.assertEqual(all_variables['var0']['value'], 'value1')
                 
    def test_get_variables_override_app_version_env(self):
        """
        Check that application/version/env specific variables are overriden by application/version/env/test specific
        Order is (bottom take precedence):
        - global (no app, no env, no version, no test)
        - specific to on of the parameter (matching app or matching version or matching env or matching test in this order)
        - specific to tuple (application / environment)
        - specific to tuple (application / version / environment)
        - specific to tuple (application / environment / test)
        - specific to tuple (application / version / environment / test)
        """
        version = Version.objects.get(pk=3)
        env = TestEnvironment.objects.get(pk=3)
        test = TestCase.objects.get(pk=1)
        Variable(name='var0', value='value0', application=version.application, version=version, environment=env).save()
        var1 = Variable(name='var0', value='value1', application=version.application, version=version, environment=env)
        var1.save()
        var1.test.add(test)
             
        response = self.client.get(reverse('variableApi'), data={'version': version.id, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        all_variables = self._convert_to_dict(response.data)
             
        # check overriding of variables
        self.assertEqual(all_variables['var0']['value'], 'value1')
                 
    def test_get_variables_override_app_env_test(self):
        """
        Check that application/version/env specific variables are overriden by application/env/test specific
        Order is (bottom take precedence):
        - global (no app, no env, no version, no test)
        - specific to on of the parameter (matching app or matching version or matching env or matching test in this order)
        - specific to tuple (application / environment)
        - specific to tuple (application / version / environment)
        - specific to tuple (application / environment / test)
        - specific to tuple (application / version / environment / test)
        """
        version = Version.objects.get(pk=3)
        env = TestEnvironment.objects.get(pk=3)
        test = TestCase.objects.get(pk=1)
        Variable(name='var0', value='value0', application=version.application, version=version, environment=env).save()
        var1 = Variable(name='var0', value='value1', application=version.application, environment=env)
        var1.save()
        var1.test.add(test)
             
        response = self.client.get(reverse('variableApi'), data={'version': version.id, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        all_variables = self._convert_to_dict(response.data)
             
        # check overriding of variables
        self.assertEqual(all_variables['var0']['value'], 'value1')
             
    def test_get_all_variables_with_same_name(self):
        """
        Check we get only one value for the variable 'dupVariable'
        """
        response = self.client.get(reverse('variableApi'), data={'version': 4, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
             
        self.assertEqual(1, len([v for v in response.data if v['name'] == 'dupVariable']), "Only one value should be get")
             
        all_variables = self._convert_to_dict(response.data)
        self.assertIsNone(all_variables['dupVariable']['releaseDate'], 'releaseDate should be null as variable is not reservable')
                 
    def test_reserve_variable(self):
        """
        Check we get only one value for the variable 'login' and this is marked as reserved (release date not null)
        This is the default behaviour when 'reserve' parameter is not given
        """
        response = self.client.get(reverse('variableApi'), data={'version': 4, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
           
        self.assertEqual(1, len([v for v in response.data if v['name'] == 'login']), "Only one value should be get")
        all_variables = self._convert_to_dict(response.data)
        self.assertIsNotNone(all_variables['login']['releaseDate'], 'releaseDate should not be null as variable is reserved')
        
        releaseDate = datetime.datetime.strptime(all_variables['login']['releaseDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
        delta = (releaseDate - datetime.datetime.utcnow()).seconds
        self.assertTrue(895 < delta < 905)
        
        
    def test_reserve_variable_with_increased_duration(self):
        """
        Check that we can specify an other duration for reservation
        """
        response = self.client.get(reverse('variableApi'), data={'version': 4, 'environment': 3, 'test': 1, 'reservationDuration': 1000})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
           
        self.assertEqual(1, len([v for v in response.data if v['name'] == 'login']), "Only one value should be get")
        all_variables = self._convert_to_dict(response.data)
        self.assertIsNotNone(all_variables['login']['releaseDate'], 'releaseDate should not be null as variable is reserved')
        
        releaseDate = datetime.datetime.strptime(all_variables['login']['releaseDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
        delta = (releaseDate - datetime.datetime.utcnow()).seconds
        self.assertTrue(995 < delta < 1005)
             
    def test_reserve_variable_with_parameter(self):
        """
        Check we get only one value for the variable 'login' and this is marked as reserved (release date not null)
        We request to reserve it via 'reserve=True' parameter
        """
        response = self.client.get(reverse('variableApi'), data={'version': 4, 'environment': 3, 'test': 1, 'reserve': 'true'})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
           
        self.assertEqual(1, len([v for v in response.data if v['name'] == 'login']), "Only one value should be get")
        all_variables = self._convert_to_dict(response.data)
        self.assertIsNotNone(all_variables['login']['releaseDate'], 'releaseDate should not be null as variable is reserved')
             
    def test_do_not_reserve_variable(self):
        """
        Check we get only one value for the variable 'login' and this is marked not reserved if we request not to reserve it via 'reserve=False' parameter
        """
        response = self.client.get(reverse('variableApi'), data={'version': 4, 'environment': 3, 'test': 1, 'reserve': 'false'})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
           
        self.assertEqual(1, len([v for v in response.data if v['name'] == 'login']), "Only one value should be get")
        all_variables = self._convert_to_dict(response.data)
        self.assertIsNone(all_variables['login']['releaseDate'], 'releaseDate should be null as variable should not be reserved')
             
    def test_reservable_state_correction(self):
        """
        Check that when a variable is added with the same characteristics of another, reservable state is set to the newly created variable
        """
        version = Version.objects.get(pk=3)
        Variable(name='var0', value='value0', application=version.application, reservable=True).save()
             
        response = self.client.post(reverse('variableApi'), data={'name': 'var0', 'value': 'value1', 'application': version.application.id, 'reservable': False})
        self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
           
        for v in Variable.objects.filter(name='var0'):
            self.assertFalse(v.reservable)
              
             
    def test_reservable_state_correction_with_test(self):
        """
        Check that when a variable is added with the same characteristics of another, reservable state is set to the newly created variable
        Check with test as ManyToMany relationship must be treated seperately
        """
        test = TestCase.objects.get(pk=1)
        version = Version.objects.get(pk=3)
        var0 = Variable(name='var0', value='value0', application=version.application, reservable=True)
        var0.save()
        var0.test.add(test)
             
        response = self.client.post(reverse('variableApi'), data={'name': 'var0', 'value': 'value1', 'application': version.application.id, 'reservable': False, 'test': [1]})
        self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
           
        for v in Variable.objects.filter(name='var0'):
            self.assertFalse(v.reservable)
            
    def test_update_reservable_state_correction_with_test(self):
        """
        Check that when a variable is changed with the same characteristics of another, reservable state is set to the updated variable
        Check with test as ManyToMany relationship must be treated seperately
        """
        test = TestCase.objects.get(pk=1)
        version = Version.objects.get(pk=3)
        var0 = Variable(name='var0', value='value0', application=version.application, reservable=True)
        var0.save()
        var0.test.add(test)
        var1 = Variable(name='var0', value='value0', application=version.application, reservable=True)
        var1.save()
        var1.test.add(test)
            
        response = self.client.patch(reverse('variableApiPut', args=[var1.id]), {'reservable': False, 'test': [1]})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
          
        # var0 and var1 are similar, so when 'reservable' is updated on var1, var0 is also updated
        self.assertFalse(Variable.objects.get(pk=var0.id).reservable)
        self.assertFalse(Variable.objects.get(pk=var1.id).reservable)
        
    def test_update_reservable_state_correction_with_different_tests(self):
        """
        Check that when a variable with the same characteristics of another (except test list) is not changed
        """
        test = TestCase.objects.get(pk=1)
        version = Version.objects.get(pk=3)
        var0 = Variable(name='var0', value='value0', application=version.application, reservable=True)
        var0.save()
        var0.test.add(test)
        var1 = Variable(name='var0', value='value0', application=version.application, reservable=True)
        var1.save()
            
        response = self.client.patch(reverse('variableApiPut', args=[var1.id]), {'reservable': False, 'test': [1]})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
          
        # var0 and var1 are similar, except for test list, so when 'reservable' is updated on var1, var0 is not updated
        self.assertTrue(Variable.objects.get(pk=var0.id).reservable)
        self.assertFalse(Variable.objects.get(pk=var1.id).reservable)
              
          
    def test_variable_already_reserved(self):
        """
        When variable cannot be reserved because all are alrealdy taken by other test, an error should be raised
        """
        # login variable is defined twice, reserve it 3 times
        self.client.get(reverse('variableApi'), data={'version': 4, 'environment': 3, 'test': 1})
        self.client.get(reverse('variableApi'), data={'version': 4, 'environment': 3, 'test': 1})
        response = self.client.get(reverse('variableApi'), data={'version': 4, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 423, 'status code should be 423: ' + str(response.content))
        self.assertTrue(b'login' in response.content)
           
        
    def test_destroy_old_variables(self):
        """
        Check that if a variable reached its max number of days, it's automatically removed
        """
            
        version = Version.objects.get(pk=2)
        env = TestEnvironment.objects.get(pk=3)
        Variable(name='oldVar', value='oldValue', application=version.application, version=version, environment=env, 
                 creationDate=timezone.now() - datetime.timedelta(2), 
                 timeToLive=1).save()
            
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1})
            
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            
        all_variables = self._convert_to_dict(response.data)
           
        self.assertNotIn('oldVar', all_variables, "oldVar should be removed, as it's too old")
            
    def test_do_not_destroy_not_so_old_variables(self):
        """
        Check that if a variable did not reach its max number of days, it's not removed
        """
            
        version = Version.objects.get(pk=2)
        env = TestEnvironment.objects.get(pk=3)
        Variable(name='oldVar', value='oldValue', application=version.application, version=version, environment=env, 
                 creationDate=timezone.now() - datetime.timedelta(0, 23 * 60 * 60), 
                 timeToLive=1).save()
            
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1})
            
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            
        all_variables = self._convert_to_dict(response.data)
           
        self.assertIn('oldVar', all_variables, "oldVar should not be removed, as it's not old enough")
    
    def test_return_variables_older_than_x_days(self):
        """
        Check that we get only variables older than X days
        """
             
        version = Version.objects.get(pk=2)
        env = TestEnvironment.objects.get(pk=3)
        Variable(name='oldVar', value='oldValue1', application=version.application, version=version, environment=env, 
                 creationDate=timezone.now() - datetime.timedelta(2), 
                 timeToLive=5).save()
        Variable(name='oldVar2', value='oldValue2', application=version.application, version=version, environment=env, 
                 creationDate=timezone.now() - datetime.timedelta(seconds=23 * 60 * 60), # almost 1 day
                 timeToLive=5).save()
             
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1, 'olderThan': 1})
             
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
             
        all_variables = self._convert_to_dict(response.data)
            
        self.assertIn('oldVar', all_variables, "oldVar should be get as it's older than requested")
        self.assertNotIn('oldVar2', all_variables, "oldVar2 should not be get as it's younger than requested")
    
    def test_return_all_variables_if_no_older_than_provided(self):
        """
        Check that we get all variables if 'olderThan' param is not provided
        """
             
        version = Version.objects.get(pk=2)
        env = TestEnvironment.objects.get(pk=3)
        Variable(name='oldVar', value='oldValue1', application=version.application, version=version, environment=env, 
                 creationDate=timezone.now() - datetime.timedelta(2), 
                 timeToLive=5).save()
        Variable(name='oldVar2', value='oldValue2', application=version.application, version=version, environment=env, 
                 creationDate=timezone.now() - datetime.timedelta(1), 
                 timeToLive=5).save()
    
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1})
             
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
             
        all_variables = self._convert_to_dict(response.data)
             
        self.assertIn('oldVar', all_variables, "oldVar should be get as it's older than requested")
        self.assertIn('oldVar2', all_variables, "oldVar2 should not be get as it's younger than requested")
           
   
    def test_return_all_variables_if_older_than_0_days(self):
        """
        Check that we get all variables if 'olderThan' param is 0
        """
            
        version = Version.objects.get(pk=2)
        env = TestEnvironment.objects.get(pk=3)
        Variable(name='oldVar', value='oldValue1', application=version.application, version=version, environment=env, 
                 creationDate=timezone.now(), 
                 timeToLive=5).save()
        Variable(name='oldVar2', value='oldValue2', application=version.application, version=version, environment=env, 
                 creationDate=timezone.now() - datetime.timedelta(1), 
                 timeToLive=5).save()
   
        time.sleep(0.5) # wait so that comparing variable time is not a problem
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1, 'olderThan': 0})
            
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            
        all_variables = self._convert_to_dict(response.data)
            
        self.assertIn('oldVar', all_variables, "oldVar should be get as it's older than requested")
        self.assertIn('oldVar2', all_variables, "oldVar2 should not be get as it's younger than requested")
           
   
    def test_return_all_variables_if_older_than_negative_days(self):
        """
        Check that we get all variables if 'olderThan' param is negative
        """
            
        version = Version.objects.get(pk=2)
        env = TestEnvironment.objects.get(pk=3)
        Variable(name='oldVar', value='oldValue1', application=version.application, version=version, environment=env, 
                 creationDate=timezone.now(), 
                 timeToLive=5).save()
        Variable(name='oldVar2', value='oldValue2', application=version.application, version=version, environment=env, 
                 creationDate=timezone.now() - datetime.timedelta(1), 
                 timeToLive=5).save()
   
        time.sleep(0.5) # wait so that comparing variable time is not a problem
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1, 'olderThan': -1})
            
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            
        all_variables = self._convert_to_dict(response.data)
            
        self.assertIn('oldVar', all_variables, "oldVar should be get as it's older than requested")
        self.assertIn('oldVar2', all_variables, "oldVar2 should not be get as it's younger than requested")
        
     
    def test_get_all_variables_with_linked_application(self):
        """
        Check that if a linked application is defined, it's variables are get
        """
        response = self.client.get(reverse('variableApi'), data={'version': 5, 'environment': 1, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        
        all_variables = self._convert_to_dict(response.data)
             
        # check filtering is correct. 
        self.assertTrue('varApp4' in all_variables)
        self.assertTrue('varApp4Env' in all_variables)
        self.assertTrue('linkedApp4.varApp4Linked' in all_variables) # variable without environment
        self.assertTrue('linkedApp4.varApp4EnvLinked' in all_variables) # variable with environment
        self.assertFalse('linkedApp4.varApp4EnvLinked2' in all_variables) # variable with specific version will not be returned
        self.assertFalse('linkedApp4.varApp4EnvLinkedReservable' in all_variables) # variable is reservable, it should not be retrieved
        
     
    def test_get_all_variables_with_reverse_linked_application(self):
        """
        Check that application that the link between application is not in both directions
        app1 => app2 does not mean app2 => app1
        """
        response = self.client.get(reverse('variableApi'), data={'version': 6, 'environment': 1, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        
        all_variables = self._convert_to_dict(response.data)
             
        # check we only get variables from 'app4Linked' application
        self.assertFalse('app4.varApp4' in all_variables)
        self.assertFalse('app4.varApp4Env' in all_variables)
        self.assertTrue('varApp4Linked' in all_variables) 
        self.assertTrue('varApp4EnvLinked' in all_variables) 
        self.assertTrue('varApp4EnvLinked2' in all_variables) 
        self.assertTrue('varApp4EnvLinkedReservable' in all_variables) 
        
    def test_delete_internal_variable(self):
        """
        Test custom variable deletion
        It should be allowed
        """
        test = TestCase.objects.get(pk=1)
        version = Version.objects.get(pk=3)
        var0 = Variable(name='var0', value='value0', application=version.application, reservable=True, internal=True)
        var0.save()
        var0.test.add(test)
        
        response = self.client.delete(reverse('variableApiPut', args=[var0.id]))
        self.assertEqual(response.status_code, 204, 'status code should be 204: ' + str(response.content))
        
            
    def test_delete_variable_forbidden(self):
        """
        Test non internal variable deletion
        It should not be allowed => renders a 404 as if variable did not exist
        """
        test = TestCase.objects.get(pk=1)
        version = Version.objects.get(pk=3)
        var0 = Variable(name='var0', value='value0', application=version.application, reservable=True, internal=False)
        var0.save()
        var0.test.add(test)
        
        response = self.client.delete(reverse('variableApiPut', args=[var0.id]))
        self.assertEqual(response.status_code, 404, 'status code should be 404: ' + str(response.content))
        
    def test_delete_variable_no_security(self):
        """
        Test custom variable deletion without security
        It should not be allowed
        """
        test = TestCase.objects.get(pk=1)
        version = Version.objects.get(pk=3)
        var0 = Variable(name='var0', value='value0', application=version.application, reservable=True)
        var0.save()
        var0.test.add(test)
        
        self.client.credentials()
        response = self.client.delete(reverse('variableApiPut', args=[var0.id]))
        self.assertEqual(response.status_code, 401, 'status code should be 401: ' + str(response.content))