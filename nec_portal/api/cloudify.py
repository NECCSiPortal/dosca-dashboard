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

import json
import logging
from urlparse import urlparse

from django.conf import settings

from horizon.utils.memoized import memoized  # noqa

from heatclient import client as heat_client

from cloudify_rest_client.client import CloudifyClient  # noqa

from nec_portal.api.tosca_client import ToscaClient
from nec_portal.local import nec_portal_settings as nec_set


LOG = logging.getLogger(__name__)

STACK_OUTPUT_KEYDEF = 'output_key'
STACK_OUTPUT_VALDEF = 'output_value'


def get_stack_output_key():
    return getattr(nec_set, 'DOSCA_STACK_OUTPUT_KEY', None)


def get_dbg_cfy_url():
    return getattr(nec_set, 'DOSCA_DBG_CFY_URL', None)


@memoized
def heatclient(url_for_orchestration, token_id):
    """Create heat client
    :param url_for_orchestration: endpoint url of heat
    :param token_id: token id of keystone
    """
    api_version = "1"
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    endpoint = url_for_orchestration
    kwargs = {
        'token': token_id,
        'insecure': insecure,
        'ca_file': cacert,
        # 'username': request.user.username,
        # 'password': password
        # 'timeout': args.timeout,
        # 'ca_file': args.ca_file,
        # 'cert_file': args.cert_file,
        # 'key_file': args.key_file,
    }
    client = heat_client.Client(api_version, endpoint, **kwargs)
    return client


@memoized
def cloudifyclient(host, port):
    """Create Cloudify Rest Client"""
    api_version = 'v2'
    client = CloudifyClient(host=host, port=port, api_version=api_version)
    return client


class Cloudify(ToscaClient):

    def __init__(self, *args, **kwargs):
        """NECCS TOSCA (using cloudify) implement

        :param url_for_orchestration: heat endpoint URL
        :param token_id: as the name suggests
        """
        super(Cloudify, self).__init__(args, kwargs)

        self.url_for_orchestration = kwargs.get('url_for_orchestration')
        self.token_id = kwargs.get('token_id')

    @memoized
    def heat_stack_list(self):
        """Client to access own heat component"""
        client = None
        stacks = []
        try:
            client = heatclient(
                self.url_for_orchestration,
                token_id=self.token_id,
            )
        except Exception as e:
            LOG.error('DOSCA: Failed to create heat client. (%s)' % e)
        if not client:
            LOG.error('DOSCA: Heat did not return client.')
            return stacks

        try:
            stacks = client.stacks.list()
        except Exception as e:
            LOG.error('DOSCA: Failed to list heat stacks. (%s)' % e)

        return stacks

    def get_cloudify_url(self):
        """Heat stack's output indicate the Cloudify URL """

        # For debugging
        cloudify_url = get_dbg_cfy_url()
        if cloudify_url:
            LOG.warn('DOSCA: Currently under debugging setting.')
            return cloudify_url

        # Get setting
        stack_output_key = get_stack_output_key()
        if not stack_output_key:
            LOG.warn('DOSCA: DOSCA_STACK_OUTPUT_KEY is not set.')
            return None

        # Generate heat client and list stacks
        cloudify_url = None
        stacks = self.heat_stack_list()
        if not stacks:
            LOG.debug('DOSCA: There is no stacks')
            return None

        # Pick up the stack has special output and return its data
        for stack in stacks:
            cloudify_url = self.get_cloudify_url_from_stack(
                stack,
                stack_output_key
            )
            if cloudify_url:
                break

        return cloudify_url

    def get_cloudify_url_from_stack(self, stack, output_key):
        """Cloudify heat stack has its URL

        :param stack: heat stack
        :param output_key: key name of cloudify URL
        """
        cloudify_url = None

        stack.get()
        if not hasattr(stack, 'outputs'):
            return None

        for output_dict in stack.outputs:
            key = output_dict.get(STACK_OUTPUT_KEYDEF)
            val = output_dict.get(STACK_OUTPUT_VALDEF)
            if key and key == output_key and val:
                cloudify_url = val
                LOG.debug(
                    'DOSCA: Stack %(stack_id)s has: %(cloudify_url)s' % {
                        'stack_id': stack.id,
                        'cloudify_url': cloudify_url
                    }
                )
                break

        return cloudify_url

    @memoized
    def cloudifyClient(self):
        """Generate alive cloudify client and return it.
        If no one alive, throw exception with message.
        """

        # Get cloudify URL by using Heat client
        self.url_for_cloudify = self.get_cloudify_url()
        if not self.url_for_cloudify:
            raise ValueError('Cloudify instance is not constructed.')

        # Managing url
        parsed_url = urlparse(self.url_for_cloudify)
        hostname = parsed_url.hostname
        port = parsed_url.port

        # Create cloudify client
        try:
            client = cloudifyclient(host=hostname, port=port)
        except Exception as e:
            LOG.warn(
                'DOSCA: Failed to create Cloudify %(url)s client. (%(e)s)' % {
                    'url': self.url_for_cloudify,
                    'e': e
                }
            )
            raise ValueError(
                'Failed to create Cloudify %s client.' %
                self.url_for_cloudify
            )
        if not client:
            LOG.warn(
                'DOSCA: Cloudify does not return client. (%s)' %
                self.url_for_cloudify
            )
            raise ValueError(
                'Cloudify does not return client. (%s)' %
                self.url_for_cloudify
            )

        # Check it as connectable
        try:
            version = client.manager.get_version()
        except Exception as e:
            LOG.warn(
                'DOSCA: Failed to check %(url)s as alive.(%(e)s)' % {
                    'url': self.url_for_cloudify,
                    'e': e
                }
            )
            raise ValueError(
                'Failed to check %s as alive.' %
                self.url_for_cloudify
            )
        if not version:
            LOG.warn(
                'DOSCA: Cloudify %s does not return version.' %
                self.url_for_cloudify
            )
            raise ValueError(
                'Cloudify does not return version. (%s)' %
                self.url_for_cloudify
            )

        return client

    def list_template(self):
        """List up blueprint to display"""
        client = self.cloudifyClient()
        blueprints = []
        try:
            blueprints = client.blueprints.list()
        except Exception as e:
            LOG.error(
                'DOSCA: Failed to get blueprint list from %(url)s. (%(e)s)' % {
                    'url': self.url_for_cloudify,
                    'e': e
                }
            )
            raise ValueError(
                'Failed to get blueprint list on %s' %
                self.url_for_cloudify
            )

        return blueprints

    def get_param_of_a_tosca(self, id):
        """Get 'inputs' from specified blueprint

        :param id: tosca (named blueprint in cloudify)
        """
        client = self.cloudifyClient()
        blueprint = None
        try:
            blueprint = client.blueprints.get(id)
        except Exception as e:
            LOG.error(
                'DOSCA: Failed to get %(id)s from %(url)s. (%(e)s)' % {
                    'url': self.url_for_cloudify,
                    'id': id,
                    'e': e
                }
            )
            raise ValueError('Failed to get %s.' % id)

        if not blueprint:
            LOG.error(
                'DOSCA: Cloudify %(url)s does not return %(id)s.' % {
                    'url': self.url_for_cloudify,
                    'id': id
                }
            )
            raise ValueError('Cloudify does not return %s.' % id)

        return blueprint.get('plan', {}).get('inputs')

    def upload_tosca(self, file_path, id):
        """Upload Blueprint

        :param file_path: upload file's path
        :param id: template id for creating one
        """
        client = self.cloudifyClient()
        try:
            client.blueprints.publish_archive(file_path, id)
        except Exception as e:
            LOG.error(
                'DOSCA: Failed to upload %(id)s to %(url)s. (%(e)s)' % {
                    'url': self.url_for_cloudify,
                    'id': id,
                    'e': e
                }
            )
            raise ValueError('Failed to upload. (%s)' % e)

    def delete_tosca(self, id):
        """Delete uploaded blueprint

        :param id: template (named blueprint in cloudify) id
        """
        client = self.cloudifyClient()
        try:
            client.blueprints.delete(id)
        except Exception as e:
            LOG.error(
                'DOSCA: Failed to delete %(id)s on %(url)s. (%(e)s)' % {
                    'url': self.url_for_cloudify,
                    'id': id,
                    'e': e
                }
            )
            raise ValueError('Failed to delete. (%s)' % e)

    def download_tosca(self, id, output_file):
        """Download uploaded blueprint

        :param id: template id for downloading one
        :param output_file: the file path wanted to create
        """
        client = self.cloudifyClient()
        LOG.debug(
            'DOSCA: Downloading %(id)s to %(output_file)s ' % {
                'id': id,
                'output_file': output_file
            }
        )
        path = None
        try:
            path = client.blueprints.download(
                id,
                output_file
            )
        except Exception as e:
            LOG.error(
                'DOSCA: Failed to download %(id)s from %(url)s. (%(e)s)' % {
                    'url': self.url_for_cloudify,
                    'id': id,
                    'e': e
                }
            )
            raise ValueError('Failed to download. (%s)' % e)

        if not path:
            LOG.error(
                'DOSCA: Cloudify %(url)s'
                ' does not return the path of %(id)s.' % {
                    'url': self.url_for_cloudify,
                    'id': id
                }
            )
            raise ValueError('Cloudify does not return the path.')

        return path

    def create_deployment(self, id, deployment_id, inputs):
        """Let cloudify create a new deployment

        :param id: template (named blueprint in cloudify) id
        :param deployment_id: the id for creating one
        :param inputs: dictionary params of the template
        """
        client = self.cloudifyClient()
        try:
            client.deployments.create(
                id,
                deployment_id,
                inputs
            )
        except Exception as e:
            LOG.error(
                'DOSCA: Failed to create deployment of'
                ' %(id)s on %(url)s. (%(e)s)' % {
                    'url': self.url_for_cloudify,
                    'id': id,
                    'e': e
                }
            )
            raise ValueError('Cloudify does not create deployment. (%s)' % e)

    def list_deployment(self):
        """List up deployments to display"""
        client = self.cloudifyClient()
        deployments = []
        try:
            deployments = client.deployments.list()
        except Exception as e:
            LOG.error(
                'DOSCA: Failed to get deployment list on %(url)s. (%(e)s)' % {
                    'url': self.url_for_cloudify,
                    'e': e
                }
            )
            raise ValueError(
                'Failed to get deployment list on %s' %
                self.url_for_cloudify
            )

        for deployment in deployments:
            setattr(deployment, 'created_at', deployment['created_at'])
            setattr(deployment, 'updated_at', deployment['updated_at'])

        return deployments

    def delete_deployment(self, deployment_id):
        """Delete uploaded blueprint

        :param deployment_id: the id for deleting one
        """
        client = self.cloudifyClient()
        try:
            client.deployments.delete(deployment_id)
        except Exception as e:
            LOG.error(
                'DOSCA: Failed to delete deployment '
                '%(did)s on %(url)s. (%(e)s)' % {
                    'did': deployment_id,
                    'url': self.url_for_cloudify,
                    'e': e
                }
            )
            raise ValueError(
                'Failed to delete delete deployment. (%s)' % e
            )

    def do_install(self, deployment_id):
        """Let cloudify start 'install' workflow

        :param deployment_id: the id for start workflow
        """
        client = self.cloudifyClient()
        execution = None
        try:
            execution = client.executions.start(deployment_id=deployment_id,
                                                workflow_id='install')
        except Exception as e:
            LOG.error(
                'DOSCA: Failed to start to install of'
                ' %(did)s on %(url)s. (%(e)s)' % {
                    'did': deployment_id,
                    'url': self.url_for_cloudify,
                    'e': e
                }
            )
            raise ValueError('Failed to start to install. (%s)' % e)

        if not execution:
            LOG.error(
                'DOSCA: Execution of'
                ' %(d)s %(w)s is not started on %(url)s.' % {
                    'd': deployment_id,
                    'url': self.url_for_cloudify,
                    'w': 'install'
                }
            )
            raise ValueError('Execution is not stated.')

        LOG.info(
            'DOSCA: Started %(did)s install workflow (%(eid)s)' % {
                'did': deployment_id,
                'eid': execution.id
            }
        )

    def do_uninstall(self, deployment_id):
        """Let cloudify start 'uninstall' workflow

        :param deployment_id: the id for start workflow
        """
        client = self.cloudifyClient()
        execution = None
        try:
            execution = client.executions.start(deployment_id=deployment_id,
                                                workflow_id='uninstall')
        except Exception as e:
            LOG.error(
                'DOSCA: Failed to start to uninstall of'
                ' %(did)s on %(url)s. (%(e)s)' % {
                    'did': deployment_id,
                    'url': self.url_for_cloudify,
                    'e': e
                }
            )
            raise ValueError('Failed to start to uninstall. (%s)' % e)

        if not execution:
            LOG.error(
                'DOSCA: Execution of'
                ' %(d)s %(w)s is not started on %(url)s.' % {
                    'd': deployment_id,
                    'url': self.url_for_cloudify,
                    'w': 'uninstall'
                }
            )
            raise ValueError('Execution is not started.')

        LOG.info(
            'DOSCA: Started %(did)s uninstall workflow %(eid)s' % {
                'did': deployment_id,
                'eid': execution.id
            }
        )

    def cancel_execution(self, execution_id, force=False):
        """Let cloudify cancel running workflow

        :param execution_id: the id for cancelling one
        :param force: make its status as force-cancel
        """
        client = self.cloudifyClient()
        try:
            client.executions.cancel(execution_id, force)
        except Exception as e:
            LOG.error(
                'DOSCA: Failed to start to cancel of'
                ' %(eid)s on %(url)s. (%(e)s)' % {
                    'eid': execution_id,
                    'url': self.url_for_cloudify,
                    'e': e
                }
            )
            raise ValueError('Failed to cancel the workflow. (%s)' % e)

    def list_execution(self, deployment_id):
        """List up Executions to display

        :param deployment_id: the id for getting executions one
        """
        client = self.cloudifyClient()
        executions = []
        try:
            executions = client.executions.list(
                deployment_id=deployment_id,
                include_system_workflows=True
            )
        except Exception as e:
            LOG.error(
                'DOSCA: Failed to get execution list of'
                ' %(d)s on %(url)s. (%(e)s)' % {
                    'd': deployment_id,
                    'url': self.url_for_cloudify,
                    'e': e
                }
            )
            raise ValueError('Failed to get execution list. (%s)' % e)

        return executions

    def get_log(self, execution_id):
        """Get event log data to display

        :param execution_id: the id for getting events and logs
        """
        client = self.cloudifyClient()
        logs = []
        try:
            # Determine size of log to retrieve
            logs, size = client.events.get(execution_id=execution_id,
                                           from_event=0,
                                           batch_size=0,
                                           include_logs=True)
            # Retrieve all logs
            logs, size = client.events.get(execution_id=execution_id,
                                           from_event=0,
                                           batch_size=size,
                                           include_logs=True)
        except Exception as e:
            LOG.error(
                'DOSCA: Failed to get logs of'
                ' %(eid)s on %(url)s. (%(e)s)' % {
                    'eid': execution_id,
                    'url': self.url_for_cloudify,
                    'e': e
                }
            )
            raise ValueError('Failed to get logs. (%s)' % e)

        return json.dumps(logs, indent=4)
