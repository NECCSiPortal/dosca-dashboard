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

from django.conf.urls import patterns  # noqa
from django.conf.urls import url  # noqa

from nec_portal.dashboards.project.tosca_deployments import views


url_pattern = 'nec_portal.dashboards.project.tosca_deployments.views'
urlpatterns = patterns(
    url_pattern,
    url(r'^$', views.ToscaDeploymentView.as_view(), name='index'),
    url(
        r'^(?P<deployment_id>[^/]+)/executions/$',
        views.ToscaExecuionView.as_view(),
        name='executions'
    ),
    url(
        r'^(?P<execution_id>[^/]+)/detail/$',
        views.EventLogDetailView.as_view(),
        name='eventlog'
    ),
    url(r'^(?P<template_id>[^/]+)/create/$', views.CreateView.as_view(),
        name='create'),
)
