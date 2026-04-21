"""
Django Forms for Data Standardisation Workflow
Handles user input validation and data submission
"""
from django import forms
from django.core.exceptions import ValidationError


class SchemaMappingForm(forms.Form):
    """
    Form for editing column name mappings after schema generation
    Generated dynamically based on detected columns
    """
    def __init__(self, column_mappings, *args, **kwargs):
        """
        Initialize form with column mapping fields
        
        Args:
            column_mappings: Dict of {original_column: standardised_column}
        """
        super().__init__(*args, **kwargs)
        
        self.original_mappings = column_mappings.copy()
        
        # Create a field for each column mapping
        for original_col, standardised_col in column_mappings.items():
            field_name = f'map_{original_col}'
            self.fields[field_name] = forms.CharField(
                label=original_col,
                initial=standardised_col,
                required=True,
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'pattern': '^[a-zA-Z_][a-zA-Z0-9_]*$|^__DROP__$',  # Allow __DROP__ as special case
                    'data-original': original_col
                }),
                help_text='Column name must start with letter or underscore, or use __DROP__ to exclude'
            )
    
    def get_edited_mappings(self):
        """
        Extract edited mappings from form
        Returns dict of edited mappings (only changed ones)
        """
        edited = {}
        for original_col in self.original_mappings.keys():
            field_name = f'map_{original_col}'
            if field_name in self.cleaned_data:
                new_name = self.cleaned_data[field_name]
                if new_name != self.original_mappings[original_col]:
                    edited[original_col] = new_name
        return edited

    def get_full_mappings(self):
        """
        Extract ALL mappings from form (edited + unchanged)
        """
        full_map = {}
        for original_col in self.original_mappings.keys():
            field_name = f'map_{original_col}'
            if field_name in self.cleaned_data:
                full_map[original_col] = self.cleaned_data[field_name]
        return full_map
    
    def clean(self):
        """
        Validate all column names
        """
        cleaned_data = super().clean()
        
        # Check for duplicates (but allow __DROP__ to appear multiple times)
        used_names = {}
        for original_col in self.original_mappings.keys():
            field_name = f'map_{original_col}'
            if field_name in cleaned_data:
                new_name = cleaned_data[field_name]
                
                # Special case: __DROP__ is always allowed (no validation needed)
                if new_name == '__DROP__':
                    continue
                
                # Check valid identifier
                if not new_name.isidentifier():
                    raise ValidationError(f'"{new_name}" is not a valid column name. Must start with letter or underscore.')
                
                # Check for duplicates
                if new_name in used_names:
                    raise ValidationError(
                        f'Column name "{new_name}" is used multiple times. '
                        f'Original columns: {new_name} and {used_names[new_name]}'
                    )
                used_names[new_name] = original_col
        
        return cleaned_data


class ExportFormatForm(forms.Form):
    """
    Form for selecting export format for final download
    """
    FORMAT_CHOICES = [
        ('csv', 'CSV (Comma-Separated Values)'),
        ('parquet', 'Parquet (Apache Parquet Format)'),
    ]
    
    export_format = forms.ChoiceField(
        label='Export Format',
        choices=FORMAT_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        initial='csv',
        help_text='CSV is recommended for Excel compatibility. Parquet is better for large datasets.'
    )
    
    include_source_file = forms.BooleanField(
        label='Include Original Column Names (_source_file)',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Adds a _source_file column tracking the original column name'
    )
