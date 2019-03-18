# -*- coding: utf-8 -*-
'''
'''
from django.test.client import Client
from django.core.urlresolvers import reverse
from variableServer.models import Variable
from django.test.testcases import TestCase

class TestVarActionView(TestCase):
    
    fixtures = ['varServer']
    
    def test_copyVariables_ok(self):
        """
        Nominal case, copy one variable
        """
        response = self.client.post(reverse('copyVariables'), data={'ids': '1', 'application': '1', 'nexturl': '/admin/variableServer/variable/?application__id__exact=1'})
        self.assertEquals(response.status_code, 302, "server did not reply as expected")
        
        # check new var has been created
        var1 = Variable.objects.get(id=1)
        
        self.assertEqual(len(Variable.objects.filter(name=var1.name).filter(value=var1.value).filter(application__id=1)), 1, "new variable has not been created" )
    
    def test_copyVariables_ok_with_reservable(self):
        """
        Nominal case, copy one variable which is reservable
        """
        response = self.client.post(reverse('copyVariables'), data={'ids': '1', 'application': '1', 'reservable': 'on', 'nexturl': '/admin/variableServer/variable/?application__id__exact=1'})
        self.assertEquals(response.status_code, 302, "server did not reply as expected")
        
        # check new var has been created
        var1 = Variable.objects.get(id=1)
        
        self.assertEqual(len(Variable.objects.filter(name=var1.name, value=var1.value, application__id=1, reservable=True)), 1, "new variable has not been created" )
         
    def test_copyVariables_ko(self):
        """
        Try to copy a variable with an application that does not exist
        """
        response = self.client.post(reverse('copyVariables'), data={'ids': '1', 'application': '120', 'nexturl': '/admin/variableServer/variable/?application__id__exact=1'})
        self.assertEquals(response.status_code, 302, "server did not reply as expected")
        
        var1 = Variable.objects.get(id=1)
       
        self.assertEqual(len(Variable.objects.filter(name=var1.name).filter(value=var1.value)), 2, "new variable should have been created" )
        
    def test_copyVariables_ko2(self):
        """
        Try to copy a variable that does not exist
        """
        response = self.client.post(reverse('copyVariables'), data={'ids': '550', 'nexturl': '/admin/variableServer/variable/?application__id__exact=1'}, follow=True)
        self.assertEquals(response.status_code, 200, "server did not reply as expected")
        
        self.assertTrue(list(response.context['messages'])[0].message.find("has not been copied"))
        
    def test_changeVariables_ok(self):
        """
        Change one variable from app1 to app2
        """
        response = self.client.post(reverse('changeVariables'), data={'ids': '3', 'application': '2', 'nexturl': '/admin/variableServer/variable/?application__id__exact=1'})
        self.assertEquals(response.status_code, 302, "server did not reply as expected")
        
        var1 = Variable.objects.get(id=3)
        self.assertEqual(var1.application.name, "app2", "application for variable should have been moved to 'app2'")
        
    def test_changeVariables_ok_with_reservable(self):
        """
        Change 'reservable'
        """
        response = self.client.post(reverse('changeVariables'), data={'ids': '3', 'reservable': 'on', 'nexturl': '/admin/variableServer/variable/?application__id__exact=1'})
        self.assertEquals(response.status_code, 302, "server did not reply as expected")
        
        var1 = Variable.objects.get(id=3)
        self.assertTrue(var1.reservable, "variable should become reservable")
        
        # change state of variable to 'not reservable'
        response = self.client.post(reverse('changeVariables'), data={'ids': '3', 'nexturl': '/admin/variableServer/variable/?application__id__exact=1'})
        self.assertEquals(response.status_code, 302, "server did not reply as expected")
        
        var1 = Variable.objects.get(id=3)
        self.assertFalse(var1.reservable, "variable should become unreservable")
        
    def test_changeVariables_ko(self):
        """
        Check we cannot change a variable that does not exist
        """
        response = self.client.post(reverse('changeVariables'), data={'ids': '550', 'nexturl': '/admin/variableServer/variable/?application__id__exact=1'}, follow=True)
        self.assertEquals(response.status_code, 200, "server did not reply as expected")
        self.assertTrue(list(response.context['messages'])[0].message.find("has not been modified") > -1)