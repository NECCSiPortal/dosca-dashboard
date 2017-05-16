#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#
#  COPYRIGHT  (C)  NEC  CORPORATION  2016

import logging
import six

from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import messages
from openstack_dashboard.api import base

from nec_portal.api.cloudify import Cloudify as cloudify_api


LOG = logging.getLogger(__name__)

TOSCA_TEMPLATES_LIST_URL = 'project/tosca_templates/index.html'
TOSCA_DEPLOYMENTS_LIST_URL = 'project/tosca_deployments/index.html'


class BuildParameterFieldMixin(object):
    """Methods in this class are copying some implementation from other panel.
    Because this panel has to work without other panels.
    So, basically we don't have to change methods in this class
    in order to reflect original changes easily.
    """
    def _build_parameter_fields(self, parameters):
        """Create input field object at form.
        :param parameters: (dict)
        """
        self.fields['deployment_id'] = forms.CharField(
            label=_('Deployment Name'),
            max_length=255,
            required=True,
            help_text=_('Input deployment name.'))

        for key, value in parameters.iteritems():
            field = None

            field_key = self.param_prefix + key
            # Set common field properties
            field_args = {
                'initial': value.get('default', None),
                'label': key,
                'help_text': value.get('description', None),
            }
            param_type = value.get('type', None)

            # Create a field object
            if param_type == 'integer':
                field = forms.IntegerField(**field_args)

            elif param_type == 'boolean':
                field = forms.BooleanField(**field_args)

            else:
                field = forms.CharField(**field_args)

            if field:
                self.fields[field_key] = field


class CreateForm(forms.SelfHandlingForm, BuildParameterFieldMixin):
    param_prefix = '__param_'
    url_param_prefix = '__url_param_'

    def __init__(self, *args, **kwargs):
        super(CreateForm, self).__init__(*args, **kwargs)

        initial = kwargs['initial']

        # Create url kwargs fields.
        url_kwargs = initial.pop('url_kwargs')
        self._build_url_kwargs_fields(url_kwargs)

        # Create parameter fields.
        parameters = initial.pop('parameters')
        self._build_parameter_fields(parameters)

    def _build_url_kwargs_fields(self, url_kwargs):
        """Create hidden field object at form."""
        for key, value in url_kwargs.items():
            field = forms.CharField(widget=forms.HiddenInput())
            field.initial = value
            self.fields[self.url_param_prefix + key] = field

    def _get_url_kwargs_fields(self, data):
        prefix_length = len(self.url_param_prefix)
        return {
            k[prefix_length:]: v for k, v in six.iteritems(data)
            if k.startswith(self.url_param_prefix)
        }

    def _get_params_list(self, data):
        """Get input parameter values on html submit form
        :param data: Handle data
        """
        prefix_length = len(self.param_prefix)
        return {
            k[prefix_length:]: v for (k, v) in six.iteritems(data)
            if k.startswith(self.param_prefix)
        }

    def handle(self, request, data):
        url_kwargs_list = self._get_url_kwargs_fields(data)
        params_list = self._get_params_list(data)
        for key, value in url_kwargs_list.items():
            if key != 'template_id':
                params_list[key] = value

        try:
            cloudify_api(
                url_for_orchestration=(
                    base.url_for(self.request, 'orchestration')
                ),
                token_id=self.request.user.token.id
            ).create_deployment(
                url_kwargs_list['template_id'],
                data.get('deployment_id'),
                params_list
            )
        except Exception as e:
            LOG.error(e)
            messages.error(
                request,
                _('An error has occurred while processing your request.'))

        messages.success(request, _('Succeeded to registrate a request.'))

        return True
