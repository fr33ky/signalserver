from django import forms
from operations.models import Configuration


class FileNameForm(forms.Form):
    file_name = forms.CharField(label='File name', max_length=200)


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file_name = forms.FileField()


def get_configurations():
    config_dic = {}

    cons = Configuration.objects.all().order_by('display_order')
    for con in cons:
        con_id = con.id
        con_name = con.configuration_name
        config_dic[con_id] = con_name

    return ((k, v) for k, v in config_dic.items())


class ConfigForm(forms.Form):
    config_fields = forms.ChoiceField(
        choices=get_configurations, required=True
    )


class GroupForm(forms.Form):
    group_name = forms.CharField(
        label='Please enter the group name'
    )


class VideoForm(forms.Form):
    videofile = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        label='Select a file',
        help_text='max. 42 megabytes'
    )
