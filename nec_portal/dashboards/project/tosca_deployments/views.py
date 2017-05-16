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
import pytz

from django.core.urlresolvers import reverse_lazy
from django.utils.html import escape
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables
from horizon import tabs
from openstack_dashboard.api import base

from nec_portal.api.cloudify import Cloudify as cloudify_api
from nec_portal.dashboards.project.tosca_deployments \
    import forms as deployment_forms
from nec_portal.dashboards.project.tosca_deployments \
    import tables as tosca_tables
from nec_portal.dashboards.project.tosca_deployments \
    import tabs as detail_tabs


LOG = logging.getLogger(__name__)


class ToscaDeployment(object):
    """Tosca Deployment class"""
    def __init__(self, id, template_id, created_at, updated_at):
        self.id = id
        self.template_id = template_id
        self.created_at = created_at
        self.updated_at = updated_at


class ToscaExecution(object):
    """Tosca Execution class"""
    def __init__(self, id, workflow_id,
                 status, error, created_at):
        self.id = id
        self.workflow_id = workflow_id
        self.status = status
        self.error = error
        self.created_at, = created_at,


class ToscaDeploymentView(tables.DataTableView):
    """Tosca Template list view class"""
    table_class = tosca_tables.ToscaDeploymentTable
    template_name = 'project/tosca_deployments/index.html'

    def get_data(self):
        display_deployments = []
        deployment_data = None

        try:
            deployment_data = cloudify_api(
                url_for_orchestration=(
                    base.url_for(self.request, 'orchestration')
                ),
                token_id=self.request.user.token.id
            ).list_deployment()
        except Exception as e:
            messages.error(self.request, e.message)
            messages.error(self.request,
                           _('Unable to retrieve deployments.'))
            return display_deployments

        # Set View Rows
        for deployment in deployment_data:
            # Create View Rows
            display_deployment = ToscaDeployment(
                id=deployment.id,
                template_id=deployment.blueprint_id,
                created_at=datetime.datetime.strptime(
                    deployment.created_at, "%Y-%m-%d %H:%M:%S.%f"
                ).replace(tzinfo=pytz.UTC),
                updated_at=datetime.datetime.strptime(
                    deployment.updated_at, "%Y-%m-%d %H:%M:%S.%f"
                ).replace(tzinfo=pytz.UTC)
            )

            display_deployments.append(display_deployment)

        return display_deployments


class ToscaExecuionView(tables.DataTableView):
    """TOSCA Execution list view class"""
    table_class = tosca_tables.ToscaExecutionTable
    template_name = 'project/tosca_deployments/execution.html'

    def get_data(self):
        display_executions = []
        execution_data = None

        deployment_id = self.kwargs['deployment_id']
        self.page_title = string_concat(_("Executions of deployment"),
                                        (": %s") % escape(deployment_id))

        try:
            execution_data = cloudify_api(
                url_for_orchestration=(
                    base.url_for(self.request, 'orchestration')
                ),
                token_id=self.request.user.token.id
            ).list_execution(deployment_id)
        except Exception as e:
            messages.error(self.request, e.message)
            messages.error(self.request,
                           _('Unable to retrieve executions.'))
            return display_executions

        # Set View Rows
        for execution in execution_data:
            # Create View Rows
            display_execution = ToscaExecution(
                id=execution.id,
                workflow_id=execution.workflow_id,
                status=execution.status,
                error=execution.error,
                created_at=execution.created_at)

            display_executions.append(display_execution)

        if display_executions:
            display_executions.sort(
                cmp=lambda x, y: cmp(x.created_at, y.created_at)
            )

        return display_executions


class CreateView(forms.ModalFormView):
    form_class = deployment_forms.CreateForm
    form_id = 'create_deployment_form'
    modal_id = 'create_deployment_modal'
    modal_header = _('Create Deployment')
    submit_label = _('Create Deployment')
    success_url = reverse_lazy('horizon:project:tosca_deployments:index')
    template_name = 'project/tosca_deployments/create.html'
    page_title = _('Create a Deployment')

    def get_initial(self):

        initial = self._create_initial()

        params = {}
        template_id = self.kwargs['template_id']

        try:
            self.submit_url = reverse_lazy(
                'horizon:project:tosca_deployments:create',
                kwargs=self.kwargs
            )
            params = cloudify_api(
                url_for_orchestration=(
                    base.url_for(self.request, 'orchestration')
                ),
                token_id=self.request.user.token.id
            ).get_param_of_a_tosca(template_id)
        except Exception as e:
            LOG.error(e)
            exceptions.handle(self.request,
                              _('Unable to retrieve template.'))
            return initial

        initial['parameters'] = params

        return initial

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        return context

    def _create_initial(self):
        initial = {}

        initial['url_kwargs'] = {}
        for key, value in self.kwargs.items():
            initial['url_kwargs'][key] = value

        return initial


class EventLogDetailView(tabs.TabView):
    tab_group_class = detail_tabs.DetailTabs
    template_name = 'project/tosca_deployments/detail.html'
    page_title = None

    def get_context_data(self, **kwargs):
        context = super(EventLogDetailView, self).get_context_data(**kwargs)

        execution_id = self.kwargs['execution_id']
        self.page_title = string_concat(_('Event Logs of execution'),
                                        ": ",
                                        execution_id)  # noqa

        log_data = "[]"
        try:
            log_data = cloudify_api(
                url_for_orchestration=(
                    base.url_for(self.request, 'orchestration')
                ),
                token_id=self.request.user.token.id
            ).get_log(execution_id)
        except Exception as e:
            messages.error(self.request, e.message)
            messages.error(self.request,
                           _('Unable to retrieve event logs.'))
        finally:
            context['message'] = log_data

        return context
