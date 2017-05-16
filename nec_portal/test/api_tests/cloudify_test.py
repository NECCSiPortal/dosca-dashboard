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

from openstack_dashboard.test import helpers as test

import cloudify_rest_client  # noqa
import heatclient  # noqa

from cloudify_rest_client.blueprints import BlueprintsClient
from cloudify_rest_client.client import CloudifyClient
from cloudify_rest_client.deployments import DeploymentsClient
from cloudify_rest_client.events import EventsClient
from cloudify_rest_client.executions import ExecutionsClient
from nec_portal.api import cloudify  # noqa
from nec_portal.api.cloudify import Cloudify  # noqa


from nec_portal.dashboards.project.tosca_templates import fixture  # noqa


class CloudifyApiTests(test.APITestCase):

    def setUp(self):
        super(CloudifyApiTests, self).setUp()
        # Store original client
        self._original_cloudifyClient = \
            cloudify_rest_client.client
        # Replace client with stub
        cloudify_rest_client.client = (
            lambda request: self.stub_cloudify_rest_client()
        )  # noqa

    def tearDown(self):
        super(CloudifyApiTests, self).tearDown()
        # Restore
        cloudify_rest_client.client = \
            self._original_cloudifyClient  # noqa

    def stub_cloudify_rest_client(self):
        if not hasattr(self, "moxedCloudifyClient"):
            self.mox.StubOutWithMock(cloudify_rest_client, 'client')
            self.moxedCloudifyClient = self.mox.CreateMock(
                cloudify_rest_client.client
            )
        return self.moxedCloudifyClient

    @test.create_stubs({cloudify: ('get_stack_output_key',)})
    def test_get_stack_output_key_defaultStgsWillReturnIfDefStgs(self):
        cloudify.get_stack_output_key().AndReturn('test_TPTVWebOutput')
        self.mox.ReplayAll()

        res = cloudify.get_stack_output_key()
        self.assertEqual(res, 'test_TPTVWebOutput')

    @test.create_stubs({cloudify: ('get_stack_output_key',)})
    def test_get_stack_output_key_noneWillReturnIfNoStgs(self):
        cloudify.get_stack_output_key().AndReturn(None)
        self.mox.ReplayAll()

        res = cloudify.get_stack_output_key()
        self.assertEqual(res, None)

    @test.create_stubs({cloudify: ('get_dbg_cfy_url',)})
    def test_get_dbg_cfy_url_defaultStgsWillReturnIfDefStgs(self):
        cloudify.get_dbg_cfy_url().AndReturn('http://somewhere.com:9696')
        self.mox.ReplayAll()

        res = cloudify.get_dbg_cfy_url()
        self.assertEqual(res, 'http://somewhere.com:9696')

    @test.create_stubs({cloudify: ('get_dbg_cfy_url',)})
    def test_get_dbg_cfy_url_noneWillReturnIfNoStgs(self):
        cloudify.get_dbg_cfy_url().AndReturn(None)
        self.mox.ReplayAll()

        res = cloudify.get_dbg_cfy_url()
        self.assertEqual(res, None)

    @test.create_stubs({cloudify: ('get_dbg_cfy_url',)})
    def test_get_cloudify_url_debugUrlWillBeReturnedIfSettingAsIs(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        debug_url = 'http://somewhere.com:9696'
        cloudify.get_dbg_cfy_url().AndReturn(debug_url)
        self.mox.ReplayAll()

        client = Cloudify(**kwargs)
        res = client.get_cloudify_url()
        self.assertEqual(res, debug_url)

    @test.create_stubs(
        {
            cloudify.Cloudify: ('heat_stack_list',),
            cloudify: ('get_dbg_cfy_url',)
        }
    )
    def test_get_cloudify_url_noneWillBeReturnedIfHeatReturnNoStacks(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        cloudify.get_dbg_cfy_url().AndReturn(None)
        cloudify.Cloudify.heat_stack_list().AndReturn(None)
        self.mox.ReplayAll()

        client = Cloudify(**kwargs)
        res = client.get_cloudify_url()
        self.assertEqual(res, None)

    @test.create_stubs(
        {
            cloudify: ('get_dbg_cfy_url', 'get_stack_output_key',)
        }
    )
    def test_get_cloudify_url_noneWillBeReturnedIfNoSetting(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        cloudify.get_dbg_cfy_url().AndReturn(None)
        cloudify.get_stack_output_key().AndReturn(None)
        self.mox.ReplayAll()

        client = Cloudify(**kwargs)
        res = client.get_cloudify_url()
        self.assertEqual(res, None)

    @test.create_stubs(
        {
            cloudify.Cloudify: ('get_cloudify_url_from_stack',),
            cloudify: ('get_dbg_cfy_url', 'get_stack_output_key', 'heatclient')
        }
    )
    def test_get_cloudify_url_noneWillBeReturnedIfHeatStacksHasNoUrl(self):
        kwargs = {
            'url_for_orchestration': 'http://somewhere.to:5/orchestration',
            'token_id': 'this_is_token_id'
        }
        cloudify.get_dbg_cfy_url().AndReturn(None)
        cloudify.get_stack_output_key().AndReturn('ZoomZoom')
        cloudify.heatclient(
            kwargs['url_for_orchestration'],
            token_id=kwargs['token_id']
        ).AndReturn(
            self.stub_heatclient()
        )
        self.stub_heatclient().stacks = self.mox.CreateMockAnything()
        api_stacks = self.stacks.list()
        self.stub_heatclient().stacks.list().AndReturn(iter(api_stacks))
        for api_stack in api_stacks:
            cloudify.Cloudify.get_cloudify_url_from_stack(
                api_stack,
                'ZoomZoom'
            ).AndReturn(None)
        self.mox.ReplayAll()

        client = Cloudify(**kwargs)
        res = client.get_cloudify_url()

        self.assertEqual(res, None)

    @test.create_stubs(
        {
            cloudify.Cloudify: ('get_cloudify_url_from_stack',),
            cloudify: ('get_dbg_cfy_url', 'get_stack_output_key', 'heatclient')
        }
    )
    def test_get_cloudify_url_urlWillBeReturnedIfHeatStacksHasUrl(self):
        kwargs = {
            'url_for_orchestration': 'http://somewhere.to:5/orchestration',
            'token_id': 'this_is_token_id'
        }
        cloudify.get_dbg_cfy_url().AndReturn(None)
        cloudify.get_stack_output_key().AndReturn('ZoomZoom')
        cloudify.heatclient(
            kwargs['url_for_orchestration'],
            token_id=kwargs['token_id']
        ).AndReturn(
            self.stub_heatclient()
        )
        self.stub_heatclient().stacks = self.mox.CreateMockAnything()
        api_stacks = self.stacks.list()
        self.stub_heatclient().stacks.list().AndReturn(iter(api_stacks))
        cloudify.Cloudify.get_cloudify_url_from_stack(
            api_stacks[0],
            'ZoomZoom'
        ).AndReturn('Studium')
        self.mox.ReplayAll()

        client = Cloudify(**kwargs)
        res = client.get_cloudify_url()

        self.assertEqual(res, 'Studium')

    @test.create_stubs(
        {
            cloudify: ('get_dbg_cfy_url', 'get_stack_output_key',)
        }
    )
    def test_cloudifyClient_willRaiseIfget_cloudify_urlReturnNone(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        cloudify.get_dbg_cfy_url().AndReturn(None)
        cloudify.get_stack_output_key().AndReturn(None)
        self.mox.ReplayAll()

        client = Cloudify(**kwargs)
        with self.assertRaises(ValueError):
            client.cloudifyClient()

    @test.create_stubs(
        {
            cloudify.Cloudify: ('get_cloudify_url',),
            cloudify: ('cloudifyclient',)
        }
    )
    def test_cloudifyClient_willRaiseIfgetFailToCreateClient(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        cloudify.Cloudify.get_cloudify_url().AndReturn(
            'http://somewhere.to:5/anything'
        )
        cloudify.cloudifyclient(
            host='somewhere.to',
            port=5
        ).AndReturn(None)
        self.mox.ReplayAll()

        client = Cloudify(**kwargs)
        with self.assertRaises(ValueError):
            client.cloudifyClient()

    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_list_template_returnNone(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)
        mocked_client.blueprints = self.mox.CreateMock(BlueprintsClient)
        mocked_client.blueprints.list().AndReturn(None)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        res = client.list_template()
        self.assertEqual(res, None)
        self.mox.VerifyAll()

    @test.create_stubs({BlueprintsClient: ('list',)})
    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_list_template_willRaiseException(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        self.assertRaises(ValueError,
                          client.list_template)
        self.mox.VerifyAll()

    @test.create_stubs({BlueprintsClient: ('get',)})
    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_get_param_of_a_tosca_willRaiseException(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)
        # BlueprintsClient.get("test_blueprint_id").AndRaise(ValueError)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        self.assertRaises(ValueError,
                          client.get_param_of_a_tosca,
                          "test_blueprint_id")
        self.mox.VerifyAll()

    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_get_param_of_a_tosca_willRaiseIfgetNone(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)
        mocked_client.blueprints = self.mox.CreateMock(BlueprintsClient)
        mocked_client.blueprints.get("test_blueprint_id").AndReturn(None)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        self.assertRaises(ValueError,
                          client.get_param_of_a_tosca,
                          "test_blueprint_id")
        self.mox.VerifyAll()

    @test.create_stubs({BlueprintsClient: ('publish_archive',)})
    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_upload_tosca_willRaiseException(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        with self.assertRaises(ValueError):
            client.upload_tosca("file_path", "test_blueprint_id")
        self.mox.VerifyAll()

    @test.create_stubs({BlueprintsClient: ('delete',)})
    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_delete_tosca_willRaiseException(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)
        # BlueprintsClient.delete("test_blueprint_id",).AndRaise(ValueError)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        self.assertRaises(ValueError,
                          client.delete_tosca,
                          "test_blueprint_id")
        self.mox.VerifyAll()

    @test.create_stubs({BlueprintsClient: ('download',)})
    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_download_tosca_willRaiseException(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        with self.assertRaises(ValueError):
            client.download_tosca("test_blueprint_id", "outputfile0.zip")
        self.mox.VerifyAll()

    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_download_tosca_willRaiseIfReturnNone(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)
        mocked_client.blueprints = self.mox.CreateMock(BlueprintsClient)
        mocked_client.blueprints.download("test_blueprint_id",
                                          "outputfile1.zip") \
            .AndReturn(None)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        with self.assertRaises(ValueError):
            client.download_tosca("test_blueprint_id",
                                  "outputfile1.zip")
        self.mox.VerifyAll()

    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_download_tosca_willreturnPath(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        ret_path = "/nec_portal/dosca/unittest"
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)
        mocked_client.blueprints = self.mox.CreateMock(BlueprintsClient)
        mocked_client.blueprints.download('test_bid',
                                          'outputfile.zip') \
            .AndReturn(ret_path)
        self.mox.ReplayAll()

        client = Cloudify(**kwargs)
        res = client.download_tosca("test_bid",
                                    'outputfile.zip')
        self.assertEqual(ret_path, res)

    @test.create_stubs({DeploymentsClient: ('create',)})
    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_create_deployment_willRaiseException(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        with self.assertRaises(ValueError):
            client.create_deployment("bid", "did", "cpu=small")
        self.mox.VerifyAll()

    @test.create_stubs({DeploymentsClient: ('list',)})
    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_list_deployment_willRaiseException(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        self.assertRaises(ValueError,
                          client.list_deployment)
        self.mox.VerifyAll()

    @test.create_stubs({DeploymentsClient: ('delete',)})
    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_delete_deployment_____willRaiseException(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        self.assertRaises(ValueError,
                          client.delete_deployment,
                          "test_deployment_id")
        self.mox.VerifyAll()

    @test.create_stubs({ExecutionsClient: ('start',)})
    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_do_install_willRaiseException(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        self.assertRaises(ValueError,
                          client.do_install,
                          "test_deployment_id")
        self.mox.VerifyAll()

    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_do_install_willRaiseExceptionIfNone(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)
        mocked_client.executions = self.mox.CreateMock(ExecutionsClient)
        mocked_client.executions.start("test_deployment_id",
                                       'install') \
            .AndReturn(None)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        self.assertRaises(ValueError,
                          client.do_install,
                          "test_deployment_id")
        self.mox.VerifyAll()

    @test.create_stubs({ExecutionsClient: ('start',)})
    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_do_uninstall_willeRaiseException(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        self.assertRaises(ValueError,
                          client.do_install,
                          "test_deployment_id")
        self.mox.VerifyAll()

    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_do_uninstall_willRaiseExceptionIfNone(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)
        mocked_client.executions = self.mox.CreateMock(ExecutionsClient)
        mocked_client.executions.start('test_deployment_id',
                                       'uninstall') \
            .AndReturn(None)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        self.assertRaises(ValueError,
                          client.do_uninstall,
                          "test_deployment_id")
        self.mox.VerifyAll()

    @test.create_stubs({ExecutionsClient: ('cancel',)})
    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_cancel_execution_willRaiseException(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        self.assertRaises(ValueError,
                          client.cancel_execution,
                          "test_execution_id")
        self.mox.VerifyAll()

    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_list_execution_willreturnNone(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)
        mocked_client.executions = self.mox.CreateMock(ExecutionsClient)
        mocked_client.executions.list(deployment_id="test_deployment_id",
                                      include_system_workflows=True) \
            .AndReturn(None)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        res = client.list_execution("test_deployment_id")
        self.assertEqual(None, res)
        self.mox.VerifyAll()

    @test.create_stubs({ExecutionsClient: ('list',)})
    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_list_execution_willRaiseException(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        self.assertRaises(ValueError,
                          client.list_execution,
                          "test_deployment_id")
        self.mox.VerifyAll()

    @test.create_stubs({EventsClient: ('get',)})
    @test.create_stubs({Cloudify: ('cloudifyClient',)})
    def test_get_log_willRaiseException(self):
        kwargs = {
            'url_for_orchestration': None,
            'token_id': None
        }
        mocked_client = self.mox.CreateMock(CloudifyClient)
        Cloudify.cloudifyClient().AndReturn(mocked_client)

        self.mox.ReplayAll()
        client = Cloudify(**kwargs)
        client.url_for_cloudify = 'http://dosca.api.test.jp'
        self.assertRaises(ValueError,
                          client.get_log,
                          "ex_id")
        self.mox.VerifyAll()
