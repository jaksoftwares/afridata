from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from dataset.models import Dataset
from metadata.models import PipelineRun, RunStatus, SourceType
from metadata.tasks import _infer_and_merge_dataset_metadata

User = get_user_model()

class DatasetMetadataTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123",
            full_name="Test User"
        )
        self.dataset = Dataset.objects.create(
            title="Afridata Test Dataset",
            bio="This is a test dataset for metadata.",
            topics="agriculture,africa",
            author=self.user,
            dataset_type="csv",
            language="Swahili", # user provided
            dataset_license="", # empty
            geographic_coverage="", # empty
        )

    @patch("google.genai.Client")
    def test_infer_and_merge_dataset_metadata(self, mock_genai_client_class):
        # Setup mock client response
        mock_client = MagicMock()
        mock_genai_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = '{"original_author": "AfriOrg", "data_source": "Open Data", "language": "English", "dataset_license": "MIT", "geographic_coverage": "Kenya"}'
        mock_client.models.generate_content.return_value = mock_response

        # Setup PipelineRun
        run = PipelineRun.objects.create(
            dataset=self.dataset,
            source=SourceType.CSV,
            status=RunStatus.RUNNING
        )

        mock_result = MagicMock()
        mock_result.profiles = {
            "col1": {"description": "desc1", "semantic_type": "id"},
            "col2": {"description": "desc2", "semantic_type": "unknown"}
        }

        # Run inference and merge
        with patch("django.conf.settings.GEMINI_API_KEY", "fake_key"):
            _infer_and_merge_dataset_metadata(run, mock_result, 2)

        # Reload from db
        self.dataset.refresh_from_db()

        # Assert merging rules:
        # 1. Blank fields populated from AI
        self.assertEqual(self.dataset.original_author, "AfriOrg")
        self.assertEqual(self.dataset.dataset_license, "MIT")
        self.assertEqual(self.dataset.geographic_coverage, "Kenya")
        # 2. Existing fields kept (not overwritten by AI "English")
        self.assertEqual(self.dataset.language, "Swahili")

        # Assert score calculation
        # Populated fields (out of 9):
        # All 9 fields are populated (some from user/AI, some from default fallbacks) -> 9/9 = 1.0
        # Schema completeness:
        # col1: desc yes, semantic yes -> 1.0
        # col2: desc yes, semantic no (unknown) -> 0.5
        # schema_score = (1.0 + 0.5) / 2 = 0.75
        # Weighted quality score = 0.6 * 1.0 + 0.4 * 0.75 = 0.6 + 0.3 = 0.9
        self.assertAlmostEqual(self.dataset.metadata_quality_score, 0.9, places=4)
