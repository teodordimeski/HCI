from django.forms import ModelForm
from django import forms
from .models import Property

class PropertyForm(ModelForm):
    class Meta:
        model = Property
        fields = ['name','description','size','date','image','is_sold','is_reserved','characteristics']
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super(PropertyForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget

            # Checkbox (BooleanField)
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"

            # File upload (ImageField)
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs["class"] = "form-control"

            # Text/Number/Date/Textarea...
            else:
                widget.attrs["class"] = "form-control"
