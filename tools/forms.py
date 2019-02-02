from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Div, Fieldset
from django import forms
from .models import ToolFieldWhiteList
import json


def map_galaxy_tool_input(attr):
    """Convert Galaxy tool input information to django field attribute dict"""
    # optional = attr.get('optional', False)
    field_map = {'initial': attr.get('default_value', attr.get('value', None)),
                 # 'required': not optional,
                 'required': False,
                 'help_text': attr.get('help', ""),
                 'label': attr.get('label', ""),
                 }
    
    if attr.get("type", "") == "select":
        field_map['choices'] = []
        for opt in attr.get("options", ""):
            # We filter configuration file in seqtype input
            if opt[1] != 'cfg':
                field_map['choices'].append((opt[1], opt[0]))

    if attr.get("type", "") == "boolean":
        default = attr.get("value", "false")
        field_map['initial'] = (default=="true")

    if attr.get("type", "") == "data":

        opt = attr.get("options", "").get('hda')
        if opt:
            field_map['choices'] = []
        # add dataset of history in a list
        for data in opt:
            field_map['choices'].append((data.get('id'), data.get('name')))

    return field_map


class ToolForm(forms.Form):
    """
    This class represents a Galaxy tool form.
    The fields of the form are created automatically using
    description of the tool given by Galaxy
    via bioblend ToolClient.show_tool()
    """

    tool_id = None
    tool_params = []
    # map field id to galaxy params name
    fields_ids_mapping = {}
    fields_ext_mapping = {}
    session_files = []
    visible_field = []
    prefix = ""
    tool_name = ""
    n = 0

    def create_field(self, attrfield):
        self.n += 1
        field_id = str(self.n)
        fieldtype = attrfield.get("type", "")
        if fieldtype == "data":
            choices = attrfield.get("options", "").get('hda')
            self.input_file_ids.append(field_id)
            if choices:
                self.fields[field_id] = forms.ChoiceField(
                    **map_galaxy_tool_input(attrfield))
            else:
                self.fields[field_id] = forms.FileField(
                    **map_galaxy_tool_input(attrfield))
                self.fields[field_id].widget.attrs = (
                    {'data-ext': json.dumps(attrfield.get('extensions')),
                     'data-name': json.dumps(attrfield.get('name')),
                     'data-compatible-inputs': json.dumps(
                         self.compatibleInputs(attrfield.get('extensions')))})
                # Update extensions associated to field => used in tools/views
                self.fields_ext_mapping[field_id] = attrfield.get('extensions')
        elif fieldtype == "select":
            if attrfield.get("display", "") == 'radio':
                self.fields[field_id] = forms.ChoiceField(
                    widget=forms.RadioSelect,
                    **map_galaxy_tool_input(attrfield))
            else:
                self.fields[field_id] = forms.ChoiceField(
                    **map_galaxy_tool_input(attrfield))
                
        elif fieldtype == "boolean":
            default = attrfield.get("value", "false")
            checkattr = {
                'data-toggle': "toggle",
                'data-on': 'true',
                'data-off': 'false',
                'value' : 'true',
            }
            if default == "true":
                checkattr['checked']=True
            self.fields[field_id] = forms.BooleanField(widget=forms.CheckboxInput(
                attrs=checkattr),
                **map_galaxy_tool_input(attrfield))
            
        elif fieldtype == "text":
            self.fields[field_id] = forms.CharField(
                **map_galaxy_tool_input(attrfield))

        elif fieldtype == "integer":
            self.fields[field_id] = forms.IntegerField(
                **map_galaxy_tool_input(attrfield))

        else:
            self.fields[field_id] = forms.CharField(
                **map_galaxy_tool_input(attrfield))
        # print(attrfield)
        # print(field_id)
        return field_id

    def parse_galaxy_input_tool(self, list_inputs,
                                cond_name='', whitelist=list()):

        fields_created = []
        for input_tool in list_inputs:
            if input_tool.get('type') == 'section':
                fields_created.append(Fieldset(
                    input_tool.get('title'),
                    *self.parse_galaxy_input_tool(input_tool.get('inputs'))))

            elif input_tool.get('name') in whitelist or not whitelist:
                cond_input = input_tool.get('test_param')
                if cond_input:
                    cond_name = input_tool.get('name') + '|'
                    conditional_field = self.create_field(cond_input)
                    self.fields_ids_mapping[conditional_field] = cond_name + \
                        cond_input['name']

                    nested_field = []
                    cases = input_tool.get('cases', '')
                    for case in cases:
                        case_inputs = case.get('inputs')
                        if case_inputs:
                            case_value = case.get('value')
                            if case_value is not None:
                                data_test = conditional_field
                                if self.prefix:
                                    data_test = self.prefix + '-' + data_test

                                nested_field.append(Div(data_test=data_test,
                                                        data_case=case_value,
                                                        css_class="well",
                                                        *self.parse_galaxy_input_tool(
                                                            case_inputs, cond_name)))

                    fields_created.append(
                        Div(conditional_field, *nested_field))
                    cond_name = ''

                elif input_tool.get('label', '') != "Config file":
                    new_field = self.create_field(input_tool)
                    fields_created.append(Field(new_field))
                    self.fields_ids_mapping[new_field] = cond_name + \
                        input_tool.get('name', '')
        return fields_created

    def compatibleInputs(self, extensions):
        """
        Returns a list of files [{ext:,history:,name:}] from self.session_files
        that are compatible with the given list of extenstions
        """
        outlist = []
        if self.session_files:
            for key, sf in self.session_files.iteritems():
                if sf.get('ext') in extensions:
                    outlist.append(sf)
        return outlist

    def __init__(self, tool_params=None,
                 tool_id=None, whitelist=None,
                 data=None, prefix=None, session_files=None,
                 fields_ids_mapping={}, n=0, tool_name=None):
        super(ToolForm, self).__init__(data=data, prefix=prefix)
        self.tool_params = tool_params or self.tool_params
        self.visible_field = whitelist or self.visible_field
        self.fields_ids_mapping = fields_ids_mapping
        self.tool_id = tool_id or self.tool_id
        self.input_file_ids = []
        self.n = n
        self.tool_name = tool_name
        # To propose compatible session files as input
        if session_files:
            self.session_files = session_files
        self.helper = FormHelper(self)
        self.helper.form_class = 'blueForms'
        self.helper.form_tag = False
        self.formset = self.parse_galaxy_input_tool(
            self.tool_params, whitelist=self.visible_field)
        self.helper.layout = Layout(FormActions(Field(*self.formset)))


class ToolFieldWhiteListForm(forms.ModelForm):
    _params = forms.MultipleChoiceField(label='Params')

    model = ToolFieldWhiteList
    fields = ['tool', 'context', '_params', ]

    def clean(self):
        cleaned_data = super(ToolFieldWhiteListForm, self).clean()
        cleaned_data['_params'] = ",".join(
            self.cleaned_data.get('_params', []))
        return cleaned_data
