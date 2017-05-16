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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import messages
from horizon import tables
from openstack_dashboard.api import base

from nec_portal.api.cloudify import Cloudify as cloudify_api


LOG = logging.getLogger(__name__)


class UploadTemplate(tables.LinkAction):
    """Create template class"""
    name = 'upload_template'
    verbose_name = _('Upload Template')
    policy_rules = (("tosca", "tosca:template_upload"), )
    icon = 'pencil'
    classes = ('ajax-modal', 'btn-edit')

    def get_link_url(self, template=None):
        return reverse('horizon:project:tosca_templates:upload')


class CreateDeployment(tables.LinkAction):
    """Create deployment class"""
    name = 'create_deployment'
    verbose_name = _('Create Deployment')
    policy_rules = (("tosca", "tosca:deployment_create"), )
    classes = ('ajax-modal', 'btn-edit')

    def get_link_url(self, template=None):
        url = 'horizon:project:tosca_templates:deployment_create:index'
        return reverse(url, args=[template.id])


class DeleteTemplates(tables.DeleteAction):
    """Delete template class"""
    verbose_name = _('Delete Template')
    policy_rules = (("tosca", "tosca:template_delete"),)
    success_url = 'horizon:project:tosca_templates:index'

    @staticmethod
    def action_present(count):
        return _("Delete Template")

    @staticmethod
    def action_past(count):
        return _("Deleted Template")

    def delete(self, request, object_id):
        try:
            cloudify_api(
                url_for_orchestration=(
                    base.url_for(request, 'orchestration')
                ),
                token_id=request.user.token.id
            ).delete_tosca(object_id)
        except Exception as e:
            LOG.error('DOSCA: Failed to delete template. (%s)' % e)
            messages.error(request, e.message)
            raise Exception()


class DownloadTemplate(tables.LinkAction):
    """Download template data class"""
    name = 'download_template'
    verbose_name = _('Download Template')
    policy_rules = (("tosca", "tosca:template_download"),)
    classes = ('tosca_confirm',)
    allowed_data_types = ('tosca_templates',)

    def get_link_url(self, template=None):
        url = 'horizon:project:tosca_templates:download'
        return reverse(url, args=[template.id])


class ToscaTemplateTable(tables.DataTable):
    """Tosca Template Table class"""
    tosca_name = tables.Column('id',
                               verbose_name=_('Template Name'))
    created_at = tables.Column('created_at',
                               verbose_name=_('Created At'))

    def get_object_id(self, template):
        return template.id

    class Meta(object):
        """Meta class"""
        name = 'tosca_template_list'
        verbose_name = 'Templates'

        row_actions = (CreateDeployment,
                       DeleteTemplates, DownloadTemplate)
        multi_select = False

        table_actions = (UploadTemplate,)
