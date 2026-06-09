from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from dataset.models import Dataset
from metadata.models import PipelineRun, RunStatus

User = get_user_model()

class GenerateMetadataViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(  # pyrefly: ignore[missing-attribute]
            username="testuser",
            email="testuser@example.com",
            password="password123",
            full_name="Test User"
        )
        # Create a mock file
        self.mock_file = SimpleUploadedFile("test_data.csv", b"col1,col2\n1,2\n3,4", content_type="text/csv")
        self.dataset = Dataset.objects.create(  # pyrefly: ignore[missing-attribute]
            title="Test CSV Dataset",
            bio="A description of the test CSV dataset.",
            topics="test,csv",
            author=self.user,
            dataset_type="csv",
            file=self.mock_file
        )
        self.generate_url = reverse("generate_metadata", kwargs={"slug": self.dataset.slug})  # pyrefly: ignore[missing-attribute]

    def test_anonymous_user_cannot_generate_metadata(self):
        response = self.client.post(self.generate_url)
        self.assertEqual(response.status_code, 302)  # pyrefly: ignore[missing-attribute]  # Redirects to login

    def test_get_request_not_allowed(self):
        login_success = self.client.login(username="testuser@example.com", password="password123")
        self.assertTrue(login_success)
        response = self.client.get(self.generate_url)
        self.assertEqual(response.status_code, 405)  # pyrefly: ignore[missing-attribute]

    def test_generate_metadata_success(self):
        login_success = self.client.login(username="testuser@example.com", password="password123")
        self.assertTrue(login_success)
        
        # Verify no run exists initially
        self.assertEqual(PipelineRun.objects.filter(dataset=self.dataset).count(), 0)  # pyrefly: ignore[missing-attribute]
        
        response = self.client.post(self.generate_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)  # pyrefly: ignore[missing-attribute]
        
        data = response.json()  # pyrefly: ignore[missing-attribute]
        self.assertTrue(data["success"])
        self.assertIn("run_id", data)
        
        # Verify run was created
        run = PipelineRun.objects.get(id=data["run_id"])  # pyrefly: ignore[missing-attribute]
        self.assertEqual(run.dataset, self.dataset)
        self.assertEqual(run.status, RunStatus.PENDING)

    def test_generate_metadata_already_in_progress(self):
        login_success = self.client.login(username="testuser@example.com", password="password123")
        self.assertTrue(login_success)
        
        # Create an active pipeline run
        active_run = PipelineRun.objects.create(  # pyrefly: ignore[missing-attribute]
            dataset=self.dataset,
            source="csv",
            status=RunStatus.RUNNING
        )
        
        response = self.client.post(self.generate_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)  # pyrefly: ignore[missing-attribute]
        
        data = response.json()  # pyrefly: ignore[missing-attribute]
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Metadata generation is already in progress.")
        self.assertEqual(data["run_id"], str(active_run.id))

