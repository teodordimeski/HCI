from django.forms import ModelForm
from .models import Event

# class EventForm(ModelForm):
#     class Meta:
#         model = Event
#         fields = ['name','date','posterImage','onOpenSky']
#
#         def __init__(self, *args, **kwargs):
#             super(EventForm,self).__init__(*args, **kwargs)
#             for field_name, field in self.fields.items():
#                 field.widget.attrs['class'] = 'form-control'

class EventForm(ModelForm):
    class Meta:
        model = Event
        exclude = ('user',)