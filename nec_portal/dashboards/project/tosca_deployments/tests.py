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

import six

from django.core.urlresolvers import reverse
from django.test.utils import override_settings  # noqa

from mox3.mox import IsA, IgnoreArg  # noqa

from openstack_dashboard.test import helpers as test

from nec_portal import api
from nec_portal.dashboards.project.tosca_templates import fixture  # noqa


INDEX_URL = reverse('horizon:project:tosca_deployments:index')


class DummyDeployment(object):

    def __init__(self, manager, params, loaded=False):
        self.manager = manager
        self._params = params
        self._add_attr(params)
        self._loaded = loaded

    def __repr__(self):
        """String of catalog object."""
        return "<template %s>" % self._params

    def _add_attr(self, params):
        for (k, v) in six.iteritems(params):
            try:
                setattr(self, k, v)
                self._params[k] = v
            except AttributeError:
                # In this case we already defined the attribute on the class
                pass


class DeploymentViewTest(test.TestCase):
    """tosca_deployments view test class"""

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @test.create_stubs({api.cloudify.Cloudify: ('list_deployment',)})
    def test_deployments_list_one_data(self):
        deployments_list = \
            [DummyDeployment(self, fixture.DEPLOYMENT_LIST[0], loaded=True)]
        api.cloudify.Cloudify().list_deployment().AndReturn(deployments_list)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertNoFormErrors(res)
        self.assertTemplateUsed(res, 'project/tosca_deployments/index.html')
        self.assertEqual(res.status_code, 200)

    def test_ToscaExecutionView(self):
        url = reverse('horizon:project:tosca_deployments:executions',
                      args=['test_execution_a'])

        res = self.client.get(url)

        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 200)

    def test_EventlogDatailView(self):
        url = reverse('horizon:project:tosca_deployments:eventlog',
                      args=['test_execution_b'])

        res = self.client.get(url)

        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 200)

    def test_CreateView_RaiseException(self):
        url = reverse('horizon:project:tosca_deployments:create',
                      args=['test_template_a'])

        with self.assertRaises(BaseException):
            self.client.get(url)
