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
#  COPYRIGHT  (C)  NEC  CORPORATION  2015

import datetime
import logging
import mimetypes
import os
import os.path
import pytz
import shutil
import tempfile

from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.http import StreamingHttpResponse
from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import messages
from horizon import tables
from openstack_dashboard.api import base

from nec_portal.api.cloudify import Cloudify as cloudify_api
from nec_portal.dashboards.project.tosca_templates \
    import forms as template_forms
from nec_portal.dashboards.project.tosca_templates \
    import tables as tosca_tables


LOG = logging.getLogger(__name__)


class ToscaTemplate(object):
    """Tosca Template class"""
    def __init__(self, main_file_name, id, plan, description, created_at):
        self.template_name = os.path.basename(main_file_name)
        self.id = id
        self.description = description
        self.created_at = created_at


class ToscaTemplateView(tables.DataTableView):
    """TOSCA Template list view class"""
    table_class = tosca_tables.ToscaTemplateTable
    template_name = 'project/tosca_templates/index.html'

    def get_data(self):
        display_templates = []
        templates_data = None

        try:
            templates_data = cloudify_api(
                url_for_orchestration=(
                    base.url_for(self.request, 'orchestration')
                ),
                token_id=self.request.user.token.id
            ).list_template()

        except Exception as e:
            messages.error(self.request, e.message)
            messages.error(self.request,
                           _('Unable to retrieve TOSCA templates.'))
            return display_templates

        # Set View Rows
        for template in templates_data:
            # Create View Rows
            display_template = ToscaTemplate(
                main_file_name=template.main_file_name,
                id=template.id,
                plan=template.plan,
                description=template.description,
                created_at=datetime.datetime.strptime(
                    template.created_at, "%Y-%m-%d %H:%M:%S.%f"
                ).replace(tzinfo=pytz.UTC)
            )

            display_templates.append(display_template)

        return display_templates


class UploadView(forms.ModalFormView):
    form_class = template_forms.UploadForm
    form_id = 'upload_template_form'
    modal_id = 'upload_template_modal'
    modal_header = _('Upload Template')
    submit_label = _('Upload Template')
    submit_url = reverse_lazy('horizon:project:tosca_templates:upload')
    success_url = reverse_lazy('horizon:project:tosca_templates:index')
    template_name = 'project/tosca_templates/upload.html'
    page_title = _('Upload a Template')

    def get_context_data(self, **kwargs):
        context = super(UploadView, self).get_context_data(**kwargs)
        return context


def template_download(request, template_id):

    try:
        # create temporary file to save the download file
        temp_dir = tempfile.mkdtemp(suffix='dosca')
        file_name = "%s.tar.gz" % template_id
        file_name = file_name.replace(",", "").encode('utf-8')
        file_path = os.path.join(temp_dir, file_name)

        cloudify_api(
            url_for_orchestration=(
                base.url_for(request, 'orchestration')
            ),
            token_id=request.user.token.id
        ).download_tosca(template_id, file_path)

        chunk_size = 8192
        response = StreamingHttpResponse(
            FileWrapper(open(file_path), chunk_size),
            content_type=mimetypes.guess_type(file_path)[0]
        )
        response['Content-Length'] = os.path.getsize(file_path)
        response['Content-Disposition'] = (
            'attachment; filename="{0}"'.format(file_name)
        )

    except Exception as e:
        LOG.error('DOSCA: Failed to download template. (%s)' % e)
        messages.error(request, e.message)
        messages.error(request, _('Unable to download TOSCA templates.'))
        return HttpResponseRedirect(
            reverse_lazy('horizon:project:tosca_templates:index')
        )

    finally:
        shutil.rmtree(temp_dir)

    return response
