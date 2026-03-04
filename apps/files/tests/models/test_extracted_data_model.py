from django.test import TestCase, override_settings

from apps.files.tests.baker_recipes import extracted_data_recipe
from apps.files.models import ExtractedData
from apps.files.tests.conftest import IN_MEMORY_STORAGES


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class ExtractedDataModelTests(TestCase):
    def test_str_includes_file_name_and_extraction_name(self):
        extracted = extracted_data_recipe.make(
            file__name="Invoice.pdf",
            name="Summary",
        )

        self.assertEqual(str(extracted), "Invoice.pdf:Summary")

    def test_hidden_from_user_default_false(self):
        extracted = extracted_data_recipe.make(hidden_from_user=False)
        self.assertFalse(extracted.hidden_from_user)

    def test_can_store_arbitrary_text_data(self):
        data_text = "Some extracted content"
        extracted = extracted_data_recipe.make(data=data_text)

        self.assertEqual(extracted.data, data_text)
        self.assertIsInstance(extracted, ExtractedData)
