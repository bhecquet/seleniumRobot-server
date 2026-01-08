
from django.urls.base import reverse
from variableServer.utils.utils import  updateVariables
from variableServer.models import Variable, Version,\
    TestEnvironment, TestCase, Application
import time
import datetime
from django.utils import timezone
from django.db.models import Q

from django.contrib.auth.models import Permission
from commonsServer.tests.test_api import TestApi

class TestApiView(TestApi):
    '''
    Using APITestCase as we call the REST Framework API
    Client handles patch / put cases
    '''
    fixtures = ['varServer.yaml']
    
    # tests for permissions on API
    # - API
    #    . no security => access all resource (create / delete / modify)
    #    . security enabled
    #        * without token => access denied (for all operations)

    #        * with token / staff / rights for view applications => can view all application data
    #    . remove authenticate_test_client & authenticate_test_client_with_see_protected_vars
    # - IHM
    #    . permission on results based on a specific group
    #    . global groups are not set anymore
    

    
    
    def setUp(self):
        Application.objects.get(pk=1).save()
        
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
               
    def test_get_all_variables_no_permissions_and_api_security_disabled(self):
        """
        Check that without API security, no permission is required to get variables
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1})
            self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
     
    def test_get_all_variables_no_permissions(self):
        """
        Check that at least 'view_variable' permissions is required to get variables
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.none())
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))
       
    def test_get_all_variables_view_permissions(self):
        """
        Check that at least 'view_variable' permissions is required to get variables
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        
        apps = []
        for variable in response.data:
            apps.append(variable['application'])
            
        # check we have variables from 1 application and not linked to any application
        self.assertTrue(len(list(set(apps))) > 1)
       
    def test_get_all_variables_view_application_restriction(self):
        """
        Application restriction is set
        User:
        - has NOT permission on app1
        - has NOT view permission
        
        User can NOT get variables
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1})
            self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))
       
    def test_get_all_variables_view_permission_and_application_permission(self):
        """
        Check that at least 'view_variable' permissions is required to get variables
        
        Application restriction is set
        User:
        - has NOT permission on app1
        - has view permission
        
        User can get variables
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
            response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1})
            self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            
            apps = []
            for variable in response.data:
                apps.append(variable['application'])
                
            # check we have variables from 1 application and not linked to any application
            self.assertTrue(len(list(set(apps))) > 1)   
       
    def test_get_all_variables_view_application_restriction_and_app1_permission(self):
        """
        Application restriction is set
        User:
        - has permission on app1
        - has NOT view permission
        
        User can get variables of app1 only
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1})
            self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            
            # check we get only variables from app1
            for variable in response.data:
                self.assertTrue(variable['application'] == 1)
                
       
    def test_get_all_variables_add_permissions(self):
        """
        Check that add_variable permission does not allow to get variables
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))
       
    def test_get_all_variables(self):
        """
        Check a reference is created when none is found
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'test': 1})
        self.assertEqual(response.status_code, 400, 'status code should be 400: ' + str(response.content))
         
    def test_get_all_variables_without_version(self):
        """
        Check that environment parameter is  mandatory
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        response = self.client.get(reverse('variableApi'), data={'test': 1, 'environment': 3})
        self.assertEqual(response.status_code, 400, 'status code should be 400: ' + str(response.content))
            
       
    def test_get_all_variables_with_text(self):
        """
        Check Variables are get when requesting them with environment name, application name, test name, ...
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        response = self.client.get(reverse('variableApi'), data={'version': '2.5', 'environment': 'DEV1', 'test': 'test1 with some spaces'})
        self.assertEqual(response.status_code, 400, 'status code should be 400: ' + str(response.content))
   
            
    def test_get_all_variables_with_release_date(self):
        """
        Check that release dates are correctly managed
        variable is returned if
        - releaseDate is None
        - releaseDate is in the past (then it should be set to None)
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
             
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
             
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
         
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))    
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
           
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))  
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
            
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable'))) 
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
           
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))  
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
             
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
        
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))     
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
        
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))     
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
        
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))     
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
        
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))     
        response = self.client.get(reverse('variableApi'), data={'version': version.id, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        all_variables = self._convert_to_dict(response.data)
             
        # check overriding of variables
        self.assertEqual(all_variables['var0']['value'], 'value1')
             
    def test_get_all_variables_with_same_name(self):
        """
        Check we get only one value for the variable 'dupVariable'
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        response = self.client.get(reverse('variableApi'), data={'version': 4, 'environment': 3, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
           
        self.assertEqual(1, len([v for v in response.data if v['name'] == 'login']), "Only one value should be get")
        all_variables = self._convert_to_dict(response.data)
        self.assertIsNotNone(all_variables['login']['releaseDate'], 'releaseDate should not be null as variable is reserved')
        
        releaseDate = datetime.datetime.strptime(all_variables['login']['releaseDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
        delta = (releaseDate - datetime.datetime.utcnow()).seconds
        self.assertTrue(895 < delta < 905)
                 
    def test_reserve_variable_no_api_security(self):
        """
        Check it's possible to reserve variable without API security and no permissions
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
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
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        response = self.client.get(reverse('variableApi'), data={'version': 4, 'environment': 3, 'test': 1, 'reserve': 'true'})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
           
        self.assertEqual(1, len([v for v in response.data if v['name'] == 'login']), "Only one value should be get")
        all_variables = self._convert_to_dict(response.data)
        self.assertIsNotNone(all_variables['login']['releaseDate'], 'releaseDate should not be null as variable is reserved')
             
    def test_do_not_reserve_variable(self):
        """
        Check we get only one value for the variable 'login' and this is marked not reserved if we request not to reserve it via 'reserve=False' parameter
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        response = self.client.get(reverse('variableApi'), data={'version': 4, 'environment': 3, 'test': 1, 'reserve': 'false'})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
           
        self.assertEqual(1, len([v for v in response.data if v['name'] == 'login']), "Only one value should be get")
        all_variables = self._convert_to_dict(response.data)
        self.assertIsNone(all_variables['login']['releaseDate'], 'releaseDate should be null as variable should not be reserved')
             
    def test_reservable_state_correction_without_permission(self):
        """
        Check 'add_variable' permission is required to set reservable state
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        version = Version.objects.get(pk=3)
        Variable(name='var0', value='value0', application=version.application, reservable=True).save()
             
        response = self.client.post(reverse('variableApi'), data={'name': 'var0', 'value': 'value1', 'application': version.application.id, 'reservable': False})
        self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))

    def test_create_variable(self):
        """
        Check it's possible to create a variable
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
        version = Version.objects.get(pk=3)
             
        response = self.client.post(reverse('variableApi'), data={'name': 'var0', 'value': 'value1', 'application': version.application.id, 'reservable': False})
        self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))

        self.assertEqual('value1', Variable.objects.get(name='var0').value)

    def test_create_variable_no_api_security(self):
        """
        Check it's possible to create a variable when API security is disabled and no permissions are set
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            version = Version.objects.get(pk=3)
                 
            response = self.client.post(reverse('variableApi'), data={'name': 'var0', 'value': 'value1', 'application': version.application.id, 'reservable': False})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
    
            self.assertEqual('value1', Variable.objects.get(name='var0').value)

    def test_create_variable_no_permission(self):
        """
        Check it's NOT possible to create a variable without add_variable permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        version = Version.objects.get(pk=3)
             
        response = self.client.post(reverse('variableApi'), data={'name': 'var0', 'value': 'value1', 'application': version.application.id, 'reservable': False})
        self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))
        
    def test_create_variable_with_application_restriction(self):
        """
        Check its possible to create a variable with application restriction when app1 permission is set
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            version = Version.objects.get(pk=1)

            response = self.client.post(reverse('variableApi'), data={'name': 'var0', 'value': 'value1', 'application': version.application.id, 'reservable': False})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
               
            self.assertEqual('value1', Variable.objects.get(name='var0').value)

    def test_create_variable_with_application_restriction2(self):
        """
        Check its possible to create a variable with application restriction when 'add_variable' permission is set
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
            version = Version.objects.get(pk=1)
                 
            response = self.client.post(reverse('variableApi'), data={'name': 'var0', 'value': 'value1', 'application': version.application.id, 'reservable': False})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
               
            self.assertEqual('value1', Variable.objects.get(name='var0').value)

    def test_create_variable_with_application_restriction_and_no_permission_on_variable(self):
        """
        Check its NOT possible to create a variable with application restriction when app1 permission is set and variable does not belong to this application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            version = Version.objects.get(pk=3)
                 
            response = self.client.post(reverse('variableApi'), data={'name': 'var0', 'value': 'value1', 'application': version.application.id, 'reservable': False})
            self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))

    def test_create_variable_with_application_restriction_and_no_permissions(self):
        """
        Check its NOT possible to create a variable with application restriction
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            version = Version.objects.get(pk=3)
                 
            response = self.client.post(reverse('variableApi'), data={'name': 'var0', 'value': 'value1', 'application': version.application.id, 'reservable': False})
            self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))

    def test_reservable_state_correction(self):
        """
        Check that when a variable is added with the same characteristics of another, reservable state is set to the newly created variable
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
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
          
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))   
        response = self.client.post(reverse('variableApi'), data={'name': 'var0', 'value': 'value1', 'application': version.application.id, 'reservable': False, 'test': [1]})
        self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
           
        for v in Variable.objects.filter(name='var0'):
            self.assertFalse(v.reservable)
        
    def test_update_variable(self):
        """
        Check that the 'change_variable' permissions is required to change variable reservable state
        """
        test = TestCase.objects.get(pk=1)
        version = Version.objects.get(pk=3)
        var0 = Variable(name='var0', value='value0', application=version.application, reservable=True)
        var0.save()
        var0.test.add(test)

        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
        response = self.client.patch(reverse('variableApiPut', args=[var0.id]), {'reservable': False, 'test': [1]})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        
        self.assertFalse(Variable.objects.get(pk=var0.id).reservable)
        
    def test_update_variable_no_api_security(self):
        """
        Check it's possible to update a variable when API security is disabled and no permissions are set
        """
        with self.settings(SECURITY_API_ENABLED=''):
            test = TestCase.objects.get(pk=1)
            version = Version.objects.get(pk=3)
            var0 = Variable(name='var0', value='value0', application=version.application, reservable=True)
            var0.save()
            var0.test.add(test)
    
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            response = self.client.patch(reverse('variableApiPut', args=[var0.id]), {'reservable': False, 'test': [1]})
            self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            
            self.assertFalse(Variable.objects.get(pk=var0.id).reservable)
        
    def test_update_variable_no_permission(self):
        """
        Check that the 'change_variable' permissions is required to update variable
        """
        test = TestCase.objects.get(pk=1)
        version = Version.objects.get(pk=3)
        var0 = Variable(name='var0', value='value0', application=version.application, reservable=True)
        var0.save()
        var0.test.add(test)

        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        response = self.client.patch(reverse('variableApiPut', args=[var0.id]), {'reservable': False, 'test': [1]})
        self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))
    
    def test_update_variable_with_application_restriction(self):
        """
        Check that with application restriction set, it's possible to update a variable if it's linked to the application user is authorized on
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            test = TestCase.objects.get(pk=1)
            version = Version.objects.get(pk=1)
            var0 = Variable(name='var0', value='value0', application=version.application, reservable=True)
            var0.save()
            var0.test.add(test)
    
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            response = self.client.patch(reverse('variableApiPut', args=[var0.id]), {'reservable': False, 'test': [1]})
            self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            
            self.assertFalse(Variable.objects.get(pk=var0.id).reservable)
    
    def test_update_variable_with_application_restriction2(self):
        """
        Check that with application restriction set, it's possible to update a variable if it's linked to the application user is authorized on
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            test = TestCase.objects.get(pk=1)
            version = Version.objects.get(pk=3)
            var0 = Variable(name='var0', value='value0', application=version.application, reservable=True)
            var0.save()
            var0.test.add(test)
    
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            response = self.client.patch(reverse('variableApiPut', args=[var0.id]), {'reservable': False, 'test': [1]})
            self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            
            self.assertFalse(Variable.objects.get(pk=var0.id).reservable)
    
    def test_update_variable_with_application_restriction_and_no_permission_on_variable(self):
        """
        Check that with application restriction set, it's not possible to update a variable on an application user has no permission
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            test = TestCase.objects.get(pk=1)
            version = Version.objects.get(pk=3)
            var0 = Variable(name='var0', value='value0', application=version.application, reservable=True)
            var0.save()
            var0.test.add(test)
    
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            response = self.client.patch(reverse('variableApiPut', args=[var0.id]), {'reservable': False, 'test': [1]})
            self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))
            
    def test_update_variable_with_application_restriction_and_no_permission(self):
        """
        Check that with application restriction set, it's not possible to update a variable on an application user has no permission
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            test = TestCase.objects.get(pk=1)
            version = Version.objects.get(pk=3)
            var0 = Variable(name='var0', value='value0', application=version.application, reservable=True)
            var0.save()
            var0.test.add(test)
    
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            response = self.client.patch(reverse('variableApiPut', args=[var0.id]), {'reservable': False, 'test': [1]})
            self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))

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
            
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
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
            
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
        response = self.client.patch(reverse('variableApiPut', args=[var1.id]), {'reservable': False, 'test': [1]})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
          
        # var0 and var1 are similar, except for test list, so when 'reservable' is updated on var1, var0 is not updated
        self.assertTrue(Variable.objects.get(pk=var0.id).reservable)
        self.assertFalse(Variable.objects.get(pk=var1.id).reservable)
              
    def test_variable_already_reserved(self):
        """
        When variable cannot be reserved because all are already taken by other test, an error should be raised
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        
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
        
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))    
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
        
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))    
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
        
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))     
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
    
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1, 'olderThan': -1})
            
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            
        all_variables = self._convert_to_dict(response.data)
            
        self.assertIn('oldVar', all_variables, "oldVar should be get as it's older than requested")
        self.assertIn('oldVar2', all_variables, "oldVar2 should not be get as it's younger than requested")
        
     
    def test_get_all_variables_with_linked_application(self):
        """
        Check that if a linked application is defined, it's variables are get
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        response = self.client.get(reverse('variableApi'), data={'version': 5, 'environment': 1, 'test': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        
        all_variables = self._convert_to_dict(response.data)
             
        # check filtering is correct. 
        self.assertTrue('varApp4' in all_variables)
        self.assertTrue('varApp4Env' in all_variables)
        self.assertTrue('linkedApp4.varApp4Linked' in all_variables) # variable without environment
        self.assertTrue('linkedApp4.varApp4EnvLinked' in all_variables) # variable with environment
        self.assertEqual(17, all_variables['linkedApp4.varApp4EnvLinked']['id']) # check id is provided
        self.assertEqual('linkedApp4.varApp4EnvLinked', all_variables['linkedApp4.varApp4EnvLinked']['name']) # check name is provided
        self.assertEqual(41, all_variables['linkedApp4.varApp4EnvLinked']['application']) # check application is provided
        self.assertEqual(1, all_variables['linkedApp4.varApp4EnvLinked']['environment']) # check environment is provided
        self.assertFalse('linkedApp4.varApp4EnvLinked2' in all_variables) # variable with specific version will not be returned
        self.assertFalse('linkedApp4.varApp4EnvLinkedReservable' in all_variables) # variable is reservable, it should not be retrieved
        
     
    def test_get_all_variables_with_reverse_linked_application(self):
        """
        Check that application that the link between application is not in both directions
        app1 => app2 does not mean app2 => app1
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
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
        
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
        response = self.client.delete(reverse('variableApiPut', args=[var0.id]))
        self.assertEqual(response.status_code, 204, 'status code should be 204: ' + str(response.content))
        
    def test_delete_internal_variable_no_api_security(self):
        """
        Test custom variable deletion when API security is disabled
        It should be allowed
        """
        with self.settings(SECURITY_API_ENABLED=''):
            test = TestCase.objects.get(pk=1)
            version = Version.objects.get(pk=3)
            var0 = Variable(name='var0', value='value0', application=version.application, reservable=True, internal=True)
            var0.save()
            var0.test.add(test)
            
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            response = self.client.delete(reverse('variableApiPut', args=[var0.id]))
            self.assertEqual(response.status_code, 204, 'status code should be 204: ' + str(response.content))
        
    def test_delete_internal_variable_no_permission(self):
        """
        Test custom variable deletion without 'delete_variable' permission
        """
        test = TestCase.objects.get(pk=1)
        version = Version.objects.get(pk=3)
        var0 = Variable(name='var0', value='value0', application=version.application, reservable=True, internal=True)
        var0.save()
        var0.test.add(test)
        
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        response = self.client.delete(reverse('variableApiPut', args=[var0.id]))
        self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))
        
    def test_delete_internal_variable_with_application_restriction(self):
        """
        Test custom variable deletion with application restriction and user has permission on the application linked to variable
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            test = TestCase.objects.get(pk=1)
            version = Version.objects.get(pk=1)
            var0 = Variable(name='var0', value='value0', application=version.application, reservable=True, internal=True)
            var0.save()
            var0.test.add(test)
            
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            response = self.client.delete(reverse('variableApiPut', args=[var0.id]))
            self.assertEqual(response.status_code, 204, 'status code should be 204: ' + str(response.content))
        
    def test_delete_internal_variable_with_application_restriction2(self):
        """
        Test custom variable deletion with application restriction and user has permission on all variables
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            test = TestCase.objects.get(pk=1)
            version = Version.objects.get(pk=1)
            var0 = Variable(name='var0', value='value0', application=version.application, reservable=True, internal=True)
            var0.save()
            var0.test.add(test)
            
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
            response = self.client.delete(reverse('variableApiPut', args=[var0.id]))
            self.assertEqual(response.status_code, 204, 'status code should be 204: ' + str(response.content))
        
    def test_delete_internal_variable_with_application_restriction_and_no_permission_on_variable(self):
        """
        Test custom variable deletion with application restriction and user has permission on app1, not app2
        It should not be able to delete the variable
        We get a 404 because in this case, no variable is returned by the filter
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            test = TestCase.objects.get(pk=1)
            version = Version.objects.get(pk=3)
            var0 = Variable(name='var0', value='value0', application=version.application, reservable=True, internal=True)
            var0.save()
            var0.test.add(test)
            
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            response = self.client.delete(reverse('variableApiPut', args=[var0.id]))
            self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))
        
    def test_delete_internal_variable_with_application_restriction_and_no_permission(self):
        """
        Test custom variable deletion with application restriction and no permission for user
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            test = TestCase.objects.get(pk=1)
            version = Version.objects.get(pk=3)
            var0 = Variable(name='var0', value='value0', application=version.application, reservable=True, internal=True)
            var0.save()
            var0.test.add(test)
            
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            response = self.client.delete(reverse('variableApiPut', args=[var0.id]))
            self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))
        
    def test_delete_internal_variable_without_permission(self):
        """
        Test custom variable deletion
        It should be allowed
        """
        test = TestCase.objects.get(pk=1)
        version = Version.objects.get(pk=3)
        var0 = Variable(name='var0', value='value0', application=version.application, reservable=True, internal=True)
        var0.save()
        var0.test.add(test)
        
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        response = self.client.delete(reverse('variableApiPut', args=[var0.id]))
        self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))
        
            
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
        
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
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