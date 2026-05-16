from django.forms import ModelForm
from .models import Training

class TrainingForm(ModelForm):
    class Meta:
        model = Training
        fields = ['name','image','trainer','category','level','duration','capacity','price' ]

    def __init__(self, *args, **kwargs):
        super(TrainingForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
