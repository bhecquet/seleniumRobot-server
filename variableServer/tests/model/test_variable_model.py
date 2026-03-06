

from django.test.testcases import TestCase
from django.db import connection

from variableServer.models import Variable, Value, Application


class TestAdmin(TestCase):

    def test_save_protected_variable(self):
        """
        Check protected variable is encrypted in database
        """
        var = Variable(name="key", value="myValue", protected=True)
        var.save()
        self.assertEqual(var.value, 'myValue')
        self.assertTrue(isinstance(var.value, Value))

        with connection.cursor() as cursor:
            cursor.execute("SELECT value from variableServer_variable WHERE name = 'key'")
            row = cursor.fetchone()
            self.assertTrue(row[0].startswith('aes_str::::'))

    def test_save_not_protected_to_protected_variable(self):
        """
        Check protected variable is encrypted on further save
        """
        var = Variable(name="key", value="myValue", protected=False)
        var.save()
        self.assertEqual(var.value, 'myValue')
        self.assertTrue(isinstance(var.value, str))

        with connection.cursor() as cursor:
            cursor.execute("SELECT value from variableServer_variable WHERE name = 'key'")
            row = cursor.fetchone()
            self.assertEqual(row[0], 'myValue')

        var.protected = True
        var.save()
        self.assertEqual(var.value, 'myValue')

        with connection.cursor() as cursor:
            cursor.execute("SELECT value from variableServer_variable WHERE name = 'key'")
            row = cursor.fetchone()
            self.assertTrue(row[0].startswith('aes_str::::'))

    def test_save_protected_variable_empty_value(self):
        """
        Check protected empty variable is not encrypted in database
        """
        var = Variable(name="key", value='', protected=True)
        var.save()
        self.assertEqual(var.value, '')
        self.assertTrue(isinstance(var.value, Value))

        with connection.cursor() as cursor:
            cursor.execute("SELECT value from variableServer_variable WHERE name = 'key'")
            row = cursor.fetchone()
            self.assertEqual(row[0], '')

    def test_save_non_protected_variable(self):
        """
        Check unprotected variable is not encrypted
        """
        var = Variable(name="key", value="myValue", protected=False)
        var.save()
        self.assertEqual(var.value, 'myValue')
        self.assertFalse(isinstance(var.value, Value))

        with connection.cursor() as cursor:
            cursor.execute("SELECT value from variableServer_variable WHERE name = 'key'")
            row = cursor.fetchone()
            self.assertEqual(row[0], 'myValue')

    def test_name_with_app_without_app(self):
        var = Variable(name="key", value="myValue", protected=False)
        self.assertEqual(var.nameWithApp(), 'key')

    def test_name_with_app_with_app(self):
        app = Application(name="app")
        var = Variable(name="key", value="myValue", protected=False, application=app)
        self.assertEqual(var.nameWithApp(), 'app.key')

    def test_get_file_path_with_application(self):
        app = Application(name="app")
        var = Variable(name="key", value="myValue", protected=False, application=app)
        self.assertTrue(var.get_file_path().replace('\\', '/').endswith('/media/variables/app/'))

    def test_get_file_path_no_application(self):
        var = Variable(name="key", value="myValue", protected=False)
        self.assertTrue(var.get_file_path().replace('\\', '/').endswith('/media/variables/'))

