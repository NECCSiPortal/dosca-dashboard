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

from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import messages
from openstack_dashboard.api import base

from nec_portal.api.cloudify import Cloudify as cloudify_api

import os.path
import shutil
import tempfile

LOG = logging.getLogger(__name__)

TOSCA_TEMPLATES_LIST_URL = 'project/tosca_templates/index.html'


class UploadForm(forms.SelfHandlingForm):
    template_name = forms.CharField(
        label=_('Template Name'),
        max_length=255,
        required=True,
        help_text=_('Input template name.'))
    template_upload = forms.FileField(
        label=_('Template File'),
        help_text=_('A local compressed template file to upload.'),
        required=True,
        widget=forms.FileInput())

    def handle(self, request, data):
        uploaded_file = request.FILES['template_upload']
        LOG.debug('DOSCA: Uploaded %s' % uploaded_file.name)

        # create temporary directory to store uploaded data
        temp_dir = tempfile.mkdtemp(suffix='dosca')

        try:
            temp_path = os.path.join(temp_dir, uploaded_file.name)

            # save uploaded file to temporary area
            temp_fd = open(temp_path, 'w+b')
            for chunk in uploaded_file.chunks():
                temp_fd.write(chunk)
            temp_fd.close()

            try:
                cloudify_api(
                    url_for_orchestration=(
                        base.url_for(self.request, 'orchestration')
                    ),
                    token_id=self.request.user.token.id
                ).upload_tosca(
                    temp_path,
                    data.get('template_name')
                )

            except Exception as e:
                LOG.error('DOSCA: Failed to upload template. (%s)' % e)
                messages.error(request, e.message)
                raise Exception()

        finally:
            shutil.rmtree(temp_dir)

        messages.success(request, _('Succeeded to registrate a request.'))

        return True
