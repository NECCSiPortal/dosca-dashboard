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


class ExecuteInstall(tables.BatchAction):
    """Execute install class"""
    name = 'execute_install'
    verbose_name = _('Execute Install')
    policy_rules = (("tosca", "tosca:execution_install"), )
    classes = ('tosca_confirm',)

    @staticmethod
    def action_present(count):
        return _('Execute Install')

    @staticmethod
    def action_past(count):
        return _('Executed Install')

    def action(self, request, object_id):
        try:
            cloudify_api(
                url_for_orchestration=(
                    base.url_for(request, 'orchestration')
                ),
                token_id=request.user.token.id
            ).do_install(object_id)
        except Exception as e:
            LOG.error('DOSCA: Failed to start install. (%s)' % e)
            messages.error(request, e.message)
            raise Exception()


class ExecuteUninstall(tables.DeleteAction):
    """Execute uninstall class"""
    name = 'execute_uninstall'
    verbose_name = _('Execute Uninstall')
    policy_rules = (("tosca", "tosca:execution_uninstall"), )
    classes = ('btn-danger',)

    @staticmethod
    def action_present(count):
        return _('Execute Uninstall')

    @staticmethod
    def action_past(count):
        return _('Executed Uninstall')

    def delete(self, request, object_id):
        try:
            cloudify_api(
                url_for_orchestration=(
                    base.url_for(request, 'orchestration')
                ),
                token_id=request.user.token.id
            ).do_uninstall(object_id)
        except Exception as e:
            LOG.error('DOSCA: Failed to uninstall. (%s)' % e)
            messages.error(request, e.message)
            raise Exception()


class DeleteDeployment(tables.DeleteAction):
    """Delete deployment class"""
    name = 'delete_deployment'
    success_url = 'horizon:project:tosca_deployments:index'
    policy_rules = (("tosca", "tosca:deployment_delete"), )

    @staticmethod
    def action_present(count):
        return _('Delete Deployment')

    @staticmethod
    def action_past(count):
        return _('Delete Deployment')

    def delete(self, request, object_id):
        try:
            cloudify_api(
                url_for_orchestration=(
                    base.url_for(request, 'orchestration')
                ),
                token_id=request.user.token.id
            ).delete_deployment(object_id)
        except Exception as e:
            LOG.error('DOSCA: Failed to delete demployment. (%s)' % e)
            messages.error(request, e.message)
            raise Exception()


class CancelExecution(tables.DeleteAction):
    """Cancel execution class"""
    name = 'cancel_execution'
    verbose_name = _('Cancel Execution')
    force = False

    @staticmethod
    def action_present(count):
        return _('Cancel Execution')

    @staticmethod
    def action_past(count):
        return _('Canceled Execution')

    def delete(self, request, object_id):
        try:
            cloudify_api(
                url_for_orchestration=(
                    base.url_for(request, 'orchestration')
                ),
                token_id=request.user.token.id
            ).cancel_execution(object_id, self.force)
        except Exception as e:
            LOG.error('DOSCA: Failed to cancel. (%s)' % e)
            messages.error(request, e.message)
            raise Exception()

    def allowed(self, request, object):
        if object.status:
            if object.status == 'cancelling':
                self.force = True
            if object.status in ['started', 'cancelling']:
                return True
        return False


def get_execution_link_url(deployment):
    url = 'horizon:project:tosca_deployments:executions'
    return reverse(url, args=[deployment.id])


def get_eventlog_link_url(execution):
    url = 'horizon:project:tosca_deployments:eventlog'
    return reverse(url, args=[execution.id])


class ToscaDeploymentTable(tables.DataTable):
    """Tosca Deployment Table class"""
    deployment_name = tables.Column('id',
                                    verbose_name=_('Deployment Name'),
                                    link=get_execution_link_url)
    template_name = tables.Column('template_id',
                                  verbose_name=_('Template Name'))
    created_at = tables.Column('created_at',
                               verbose_name=_('Created At'))

    def get_object_id(self, deployment):
        return deployment.id

    class Meta(object):
        """Meta class"""
        name = 'tosca_deployment_list'
        verbose_name = 'Deployments'

        row_actions = (ExecuteInstall, ExecuteUninstall,
                       DeleteDeployment,)
        multi_select = False


class ToscaExecutionTable(tables.DataTable):
    """Tosca Execution Table class"""
    id = tables.Column('id',
                       verbose_name=_('Execution ID'),
                       link=get_eventlog_link_url,
                       sortable=False)
    workflow_id = tables.Column('workflow_id',
                                verbose_name=_('Workflow ID'),
                                sortable=False)
    status = tables.Column('status',
                           verbose_name=_('Status'),
                           sortable=False)
    error = tables.Column('error',
                          verbose_name=_('Error'),
                          sortable=False)
    created_at = tables.Column('created_at',
                               verbose_name=_('Created At'),
                               sortable=False)

    def get_object_id(self, execution):
        return execution.id

    class Meta(object):
        """Meta class"""
        name = 'tosca_deployment_list'
        verbose_name = 'Deployments'

        row_actions = (CancelExecution,)
        multi_select = False
