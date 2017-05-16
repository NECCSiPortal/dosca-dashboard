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

TEMPLATE_LIST = [
    {
        "main_file_name": "blueprint.yaml",
        "description": None,
        "id": "with_key-001",
        "created_at": "2016-08-15 02:14:05.116111",
        "updated_at": "2016-08-15 02:14:05.116111",
        "plan": {
            "relationships": {},
            "inputs": {
                "keystone_url": {
                    "default": "",
                    "type": "string"
                },
                "keystone_password": {
                    "default": "",
                    "type": "string"
                },
                "keystone_username": {
                    "default": "",
                    "type": "string"
                },
                "keystone_tenant_name": {
                    "default": "",
                    "type": "string"
                }
            },
            "description": None,
            "deployment_plugins_to_install": [],
            "policy_types": {},
            "outputs": {},
            "version": {
                "definitions_name": "cloudify_dsl",
                "raw": "cloudify_dsl_1_2",
                "definitions_version": [
                    1,
                    2
                ]
            },
            "workflow_plugins_to_install": [
                {
                    "distribution_release": None,
                    "install_arguments": None,
                    "name": "default_workflows",
                    "package_name": None,
                    "distribution_version": None,
                    "package_version": None,
                    "supported_platform": None,
                    "source": None,
                    "install": False,
                    "executor": "central_deployment_agent",
                    "distribution": None
                }
            ],
            "groups": {},
            "workflows": {
                "scale": {
                    "operation": "cloudify.plugins.workflows.scale",
                    "parameters": {},
                    "plugin": "default_workflows"
                },
                "execute_operation": {},
                "install": {
                    "operation": "cloudify.plugins.workflows.install",
                    "parameters": {},
                    "plugin": "default_workflows"
                },
                "install_new_agents": {},
                "uninstall": {
                    "operation": "cloudify.plugins.workflows.uninstall",
                    "parameters": {},
                    "plugin": "default_workflows"
                }
            },
            "nodes": [],
            "policy_triggers": {}
        }
    },
]

PARAM_LIST_DEF_DATA = "Default value"

PARAM_LIST = [
    {
        "keystone_url": {
            "default": PARAM_LIST_DEF_DATA,
            "type": "string"
        },
        "keystone_password": {
            "default": "",
            "type": "string"
        },
        "keystone_username": {
            "default": "",
            "type": "string"
        },
        "keystone_tenant_name": {
            "default": "",
            "type": "string"
        }
    }
]

DEPLOYMENT_LIST = [
    {
        "inputs": {
            "keystone_url": "b",
            "keystone_password": "c",
            "keystone_username": "d",
            "keystone_tenant_name": "e"
        },
        "blueprint_id": "with_key-001",
        "policy_types": {
            "cloudify.policies.types.host_failure": {},
            "cloudify.policies.types.ewma_stabilized": {},
            "cloudify.policies.types.threshold": {}
        },
        "outputs": {},
        "created_at": "2016-08-15 04:18:30.892892",
        "updated_at": "2016-08-15 04:18:30.892892",
        "policy_triggers": {
            "cloudify.policies.triggers.execute_workflow": {}
        },
        "groups": {},
        "workflows": [],
        "id": "a"
    }
]

EXECUTION_LIST = [
    {
        "status": "failed",
        "parameters": {},
        "is_system_workflow": False,
        "blueprint_id": "with_input_aaa",
        "created_at": "2016-08-18 03:34:58.491794",
        "workflow_id": "install",
        "error": "Traceback (most recent call last):\n  context',)\n",
        "deployment_id": "with_input-001",
        "id": "9ad44615-0fb9-47d8-aa58-85d813eaa9cf"
    }
]
