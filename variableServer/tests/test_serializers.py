# -*- coding: utf-8 -*-
'''
Tests for variableServer.views.serializers
'''
import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.testcases import TestCase

from variableServer.models import Application, TestCase as TestCaseModel, \
    Variable
from variableServer.views.serializers import VariableSerializer, \
    _prevent_value_and_uploadfile_setting


class TestPreventValueAndUploadFileSetting(TestCase):
    """
    Tests for the helper function that makes sure 'value' and 'uploadFile' are not both set
    """

    def test_uploadFile_has_priority_over_value(self):
        """
        When both 'value' and 'uploadFile' are provided, 'uploadFile' should be kept and 'value' erased
        """
        uploaded_file = SimpleUploadedFile('file.txt', b'file content')
        validated_data = {'value': 'some value', 'uploadFile': uploaded_file}

        _prevent_value_and_uploadfile_setting(validated_data)

        self.assertEqual(validated_data['uploadFile'], uploaded_file)
        self.assertEqual(validated_data['value'], '')

    def test_value_kept_when_no_uploadFile(self):
        """
        When only 'value' is provided, it should not be changed and 'uploadFile' is explicitly cleared
        """
        validated_data = {'value': 'some value'}

        _prevent_value_and_uploadfile_setting(validated_data)

        self.assertEqual(validated_data['value'], 'some value')
        self.assertIsNone(validated_data['uploadFile'])

    def test_uploadFile_kept_when_no_value(self):
        """
        When only 'uploadFile' is provided, it should not be changed and 'value' is explicitly cleared
        """
        uploaded_file = SimpleUploadedFile('file.txt', b'file content')
        validated_data = {'uploadFile': uploaded_file}

        _prevent_value_and_uploadfile_setting(validated_data)

        self.assertEqual(validated_data['uploadFile'], uploaded_file)
        self.assertEqual(validated_data['value'], '')

    def test_uploadFile_set_to_none_when_value_only_and_uploadFile_present_but_falsy(self):
        """
        When 'uploadFile' key exists but is falsy (e.g None) and 'value' is set, 'uploadFile' should be reset to None
        """
        validated_data = {'value': 'some value', 'uploadFile': None}

        _prevent_value_and_uploadfile_setting(validated_data)

        self.assertEqual(validated_data['value'], 'some value')
        self.assertIsNone(validated_data['uploadFile'])

    def test_nothing_set(self):
        """
        When neither 'value' nor 'uploadFile' is provided, dict should not raise and stay empty
        """
        validated_data = {}

        _prevent_value_and_uploadfile_setting(validated_data)

        self.assertEqual(validated_data, {})


class TestVariableSerializer(TestCase):

    def setUp(self):
        self.application = Application.objects.create(name='app1')
        self.test_case = TestCaseModel.objects.create(name='test1', application=self.application)

    def test_serialize_variable(self):
        """
        Check that an existing Variable instance is correctly serialized
        """
        variable = Variable.objects.create(name='var1', value='value1', application=self.application, reservable=True)
        variable.test.add(self.test_case)

        data = VariableSerializer(variable).data

        self.assertEqual(data['name'], 'var1')
        self.assertEqual(data['value'], 'value1')
        self.assertEqual(data['application'], self.application.id)
        self.assertTrue(data['reservable'])
        self.assertEqual(data['test'], [self.test_case.id])

    def test_is_valid_with_minimal_data(self):
        """
        Only 'name' is mandatory to create a variable
        """
        serializer = VariableSerializer(data={'name': 'var1', 'test': []})

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_is_invalid_without_name(self):
        """
        'name' field is mandatory
        """
        serializer = VariableSerializer(data={'value': 'value1'})

        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_create_with_value_only(self):
        """
        Creating a variable with only a value should keep this value and leave uploadFile empty
        """
        serializer = VariableSerializer(data={'name': 'var1', 'value': 'value1', 'test': []})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        variable = serializer.save()

        self.assertEqual(variable.value, 'value1')
        self.assertFalse(variable.uploadFile)

    def test_create_with_uploadFile_only(self):
        """
        Creating a variable with only a file should keep this file and leave value empty
        """
        uploaded_file = SimpleUploadedFile('file.txt', b'file content')
        serializer = VariableSerializer(data={'name': 'var1', 'uploadFile': uploaded_file, 'test': []})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        variable = serializer.save()

        self.assertTrue(str(variable.uploadFile).startswith('file'))
        self.assertTrue(str(variable.uploadFile).endswith('.txt'))
        self.assertEqual(variable.value, '')

        os.remove(variable.uploadFile.path)

    def test_create_with_value_and_uploadFile_gives_priority_to_file(self):
        """
        When both value and file are given at creation, file has priority and value is erased
        """
        uploaded_file = SimpleUploadedFile('file.txt', b'file content')
        serializer = VariableSerializer(data={'name': 'var1', 'value': 'value1', 'uploadFile': uploaded_file, 'test': []})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        variable = serializer.save()

        self.assertTrue(str(variable.uploadFile).startswith('file'))
        self.assertTrue(str(variable.uploadFile).endswith('.txt'))
        self.assertEqual(variable.value, '')

        os.remove(variable.uploadFile.path)

    def test_update_with_value_and_uploadFile_gives_priority_to_file(self):
        """
        When both value and file are given on update, file has priority and value is erased
        """
        variable = Variable.objects.create(name='var1', value='value1')
        uploaded_file = SimpleUploadedFile('file.txt', b'file content')

        serializer = VariableSerializer(variable, data={'name': 'var1', 'value': 'value2', 'uploadFile': uploaded_file}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_variable = serializer.save()

        self.assertTrue(str(updated_variable.uploadFile).startswith('file'))
        self.assertTrue(str(updated_variable.uploadFile).endswith('.txt'))
        self.assertEqual(updated_variable.value, '')

        os.remove(updated_variable.uploadFile.path)

    def test_update_with_value_only_keeps_value(self):
        """
        Updating a variable with only a new value should keep it, uploadFile stays unset
        """
        variable = Variable.objects.create(name='var1', value='value1')

        serializer = VariableSerializer(variable, data={'value': 'value2'}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_variable = serializer.save()

        self.assertEqual(updated_variable.value, 'value2')
        self.assertFalse(updated_variable.uploadFile)

    def test_create_corrects_reservable_state_of_similar_variables(self):
        """
        Creating a variable should update the reservable state of other variables sharing the same scope
        (same name / application / version / environment / test), as done in Variable._correctReservableState
        """
        existing_variable = Variable.objects.create(name='var1', application=self.application, value='value0', reservable=True)

        serializer = VariableSerializer(data={'name': 'var1', 'application': self.application.id, 'value': 'value1', 'reservable': False, 'test': []})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        existing_variable.refresh_from_db()
        self.assertFalse(existing_variable.reservable)

    def test_create_with_test_relation(self):
        """
        Creating a variable providing a list of test ids should set the many to many 'test' relation
        """
        serializer = VariableSerializer(data={'name': 'var1', 'test': [self.test_case.id]})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        variable = serializer.save()

        self.assertEqual(list(variable.test.all()), [self.test_case])
