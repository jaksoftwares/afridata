# dataset/forms.py
from django import forms
from .models import Dataset

# Define choices at module level so they can be accessed everywhere
DATASET_TYPE_CHOICES = [
    ('', 'Select dataset type'),
    ('csv', 'CSV'),
    ('excel', 'Excel'),
    ('pdf', 'PDF'),
    ('txt', 'Text'),
    ('json', 'JSON'),
    ('xml', 'XML'),
    ('zip', 'ZIP Archive'),
    ('yaml', 'YAML'),
    ('parquet', 'Parquet'),
    ('unstructured', 'Unstructured ML/AI Data'),
]

class DatasetUploadForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['title', 'file', 'cover_photo', 'dataset_type', 'bio', 'topics', 'original_author', 'data_source', 'collection_date', 'language', 'dataset_license', 'update_frequency', 'geographic_coverage', 'temporal_coverage', 'usage_notes']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter a descriptive title for your dataset',
                'maxlength': '255'
            }),
            'file': forms.FileInput(attrs={
                'accept': '.csv,.xlsx,.xls,.pdf,.txt,.json,.xml,.zip,.yaml,.yml,.parquet,.bin,.dat,.pt,.pkl,.h5,.safetensors,.onnx,.joblib',
                'style': 'display: none;'  # Hidden as we use custom upload area
            }),
            'cover_photo': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'dataset_type': forms.Select(
                choices=DATASET_TYPE_CHOICES,
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-vertical',
                'rows': 4,
                'placeholder': 'Describe your dataset, its contents, and potential use cases...'
            }),
            'topics': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'machine learning, data science, statistics, finance',
                'maxlength': '500'
            }),
            'original_author': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'The person or organization who created it'
            }),
            'data_source': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Source URL or organization'
            }),
            'collection_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
            'language': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., English, Swahili'
            }),
            'dataset_license': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., CC-BY-SA, MIT'
            }),
            'update_frequency': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., Monthly, Daily, One-time'
            }),
            'geographic_coverage': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., East Africa, Global'
            }),
            'temporal_coverage': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., 2015-2022'
            }),
            'usage_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-vertical',
                'rows': 3,
                'placeholder': 'Any specific instructions for users...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make core fields required, metadata fields optional
        core_fields = ['title', 'file', 'dataset_type', 'bio', 'topics']
        for field_name in self.fields:
            if field_name in core_fields:
                self.fields[field_name].required = True
            else:
                self.fields[field_name].required = False
    
    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError('This field is required')
        if len(title) < 3:
            raise forms.ValidationError('Title must be at least 3 characters long')
        return title
    
    def clean_bio(self):
        bio = self.cleaned_data.get('bio', '').strip()
        if not bio:
            raise forms.ValidationError('This field is required')
        if len(bio) < 10:
            raise forms.ValidationError('Description must be at least 10 characters long')
        return bio
    
    def clean_topics(self):
        topics = self.cleaned_data.get('topics', '').strip()
        if not topics:
            raise forms.ValidationError('This field is required')
        
        # Split topics by comma and validate
        topic_list = [topic.strip() for topic in topics.split(',') if topic.strip()]
        if len(topic_list) < 1:
            raise forms.ValidationError('Please enter at least one topic')
        if len(topic_list) > 10:
            raise forms.ValidationError('Maximum 10 topics allowed')
        
        # Rejoin cleaned topics
        return ', '.join(topic_list)
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError('Please select a file to upload')
            
        # Check file size (limit to 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            raise forms.ValidationError('File size cannot exceed 10MB')
        
        # Check file extension
        allowed_extensions = ['.csv', '.xlsx', '.xls', '.pdf', '.txt', '.json', '.xml', '.zip', '.yaml', '.yml', '.parquet', '.bin', '.dat', '.pt', '.pkl', '.h5', '.safetensors', '.onnx', '.joblib']
        file_extension = '.' + file.name.lower().split('.')[-1]
        if file_extension not in allowed_extensions:
            raise forms.ValidationError(
                f'Only these file types are allowed: {", ".join(allowed_extensions)}'
            )
            
        # --- Security Validation Pipeline ---
        import filetype
        import tempfile
        import os
        from picklescan.scanner import scan_file_path

        # 1. Magic Number Check to prevent executable disguising
        try:
            chunk = file.read(2048)
            file.seek(0)
            kind = filetype.guess(chunk)
            
            # If we detect dangerous executable mime types, immediately reject
            if kind and kind.mime in ['application/x-msdownload', 'application/x-executable', 'application/x-sh', 'application/x-mach-binary']:
                raise forms.ValidationError("Security Error: Executable files are strictly prohibited.")
        except Exception as e:
            if isinstance(e, forms.ValidationError):
                raise e
            pass # Non-fatal if filetype module fails to guess
            
        # 2. ML Tensor Vulnerability Scan (Picklescan)
        if file_extension in ['.pkl', '.pt']:
            try:
                # Write to temp file because picklescan requires a file path
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
                    for c in file.chunks():
                        tmp.write(c)
                    tmp_path = tmp.name
                
                scan_result = scan_file_path(tmp_path)
                os.unlink(tmp_path)
                
                if scan_result.issues_count > 0:
                    raise forms.ValidationError(
                        f"Security Error: Malicious or unsafe code detected in this {file_extension} file. "
                        f"Please convert to .safetensors and try again."
                    )
            except Exception as e:
                # Reset file pointer if temp file writing failed midway
                file.seek(0)
                if isinstance(e, forms.ValidationError):
                    raise e
                raise forms.ValidationError(f"Security Error: Unable to verify the safety of this {file_extension} file.")
            
        file.seek(0) # Always reset file pointer before returning
        
        return file
    
    def clean_dataset_type(self):
        dataset_type = self.cleaned_data.get('dataset_type')
        if not dataset_type:
            raise forms.ValidationError('Please select a dataset type')
        return dataset_type
    
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        dataset_type = cleaned_data.get('dataset_type')
        
        # Validate that file type matches selected dataset type
        if file and dataset_type:
            file_extension = '.' + file.name.lower().split('.')[-1]
            type_extension_map = {
                'csv': ['.csv'],
                'excel': ['.xlsx', '.xls'],
                'pdf': ['.pdf'],
                'txt': ['.txt'],
                'json': ['.json'],
                'xml': ['.xml'],
                'zip': ['.zip'],
                'yaml': ['.yaml', '.yml'],
                'parquet': ['.parquet'],
                'unstructured': ['.bin', '.dat', '.pt', '.pkl', '.h5', '.safetensors', '.onnx', '.joblib']
            }
            
            expected_extensions = type_extension_map.get(dataset_type, [])
            if file_extension not in expected_extensions:
                raise forms.ValidationError(
                    f'Selected file type does not match the dataset type. '
                    f'Expected: {", ".join(expected_extensions)}, got: {file_extension}'
                )
        
        return cleaned_data

class DatasetEditForm(DatasetUploadForm):
    class Meta(DatasetUploadForm.Meta):
        fields = ['title', 'cover_photo', 'dataset_type', 'bio', 'topics', 'original_author', 'data_source', 'collection_date', 'language', 'dataset_license', 'update_frequency', 'geographic_coverage', 'temporal_coverage', 'usage_notes']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # file is not required when editing
        if 'file' in self.fields:
            self.fields['file'].required = False