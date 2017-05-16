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

from django.conf.urls import include
from django.conf.urls import patterns  # noqa
from django.conf.urls import url  # noqa

from nec_portal.dashboards.project.tosca_templates.deployment \
    import urls as deployment_url
from nec_portal.dashboards.project.tosca_templates import views


url_pattern = 'nec_portal.dashboards.project.tosca_templates.views'
urlpatterns = patterns(
    url_pattern,
    url(r'^$', views.ToscaTemplateView.as_view(), name='index'),
    url(r'^upload/$', views.UploadView.as_view(), name='upload'),
    url(r'^(?P<template_id>[^/]+)/download/$',
        views.template_download, name='download'),
    url(r'^deployment/(?P<template_id>[^/]+)/create/$',
        include(deployment_url, namespace='deployment_create')),
)
