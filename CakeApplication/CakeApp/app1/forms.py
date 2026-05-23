from django.forms import ModelForm
from .models import Cake

class CakeForm(ModelForm):
    class Meta:
        model = Cake
        fields = ['name', 'price', 'weight', 'description', 'image']

    def __init__(self, *args, **kwargs):
        super(CakeForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'