#!/bin/bash

##
## This file is for running tox, coverage test
##
## Jenkins tox or coverage test job will use this file on Jenkins slave server.
## The job name is "dosca-dashboard_coverage"
##
## The way of running tox test is a little bit special.
## So we write the code that way in this file.
##

##
## Variables determined by Jenkins
if [ "${WORKSPACE}" = "" ]; then
  echo "You need to export WORKSPACE env"
  exit 1
fi
if [ "${BUILD_NUMBER}" = "" ]; then
  echo "You need to export BUILD_NUMBER env"
  exit 1
fi
if [ "${GITHUB_BK_DIR}" = "" ]; then
  echo "You need to export GITHUB_BK_DIR env"
  exit 1
fi
if [ "${TARGET_HORIZON_BR}" = "" ]; then
  echo "You need to export TARGET_HORIZON_BR env"
  exit 1
fi
TARGET_HORIZON_BR_NM=${TARGET_HORIZON_BR//\//_}

if [ "${NECCSPORTAL_GIT}" = "" ]; then
  echo "You need to export NECCSPORTAL_GIT env"
  exit 1
fi
if [ "${TARGET_NECCSPORTAL_BR}" = "" ]; then
  echo "You need to export TARGET_NECCSPORTAL_BR env"
  exit 1
fi

##
## RPMs
yum install -y gcc libffi-devel openssl-devel

##
## Git clone Openstack/horizon
cd ${GITHUB_BK_DIR}

if ls ${GITHUB_BK_DIR}/horizon.${TARGET_HORIZON_BR_NM} > /dev/null 2>&1
then
  echo "Already github source is cloned"
else
  git clone -b ${TARGET_HORIZON_BR} --single-branch https://github.com/openstack/horizon.git
  mv horizon horizon.${TARGET_HORIZON_BR_NM}
fi
cd horizon.${TARGET_HORIZON_BR_NM}
git pull
git log -n 1 --format=%H

##
## Create temporary directory
rm -rf ${WORKSPACE}/.horizon
mkdir ${WORKSPACE}/.horizon
cp -prf ${GITHUB_BK_DIR}/horizon.${TARGET_HORIZON_BR_NM} ${WORKSPACE}/.horizon/horizon

##
## Git clone NECCSPortal-dashboard from GitLab
cd ${WORKSPACE}/.horizon
git clone -b ${TARGET_NECCSPORTAL_BR} --single-branch ${NECCSPORTAL_GIT}

##
## Put NECCSPortal-dashboard to horizon
\cp -prf ./NECCSPortal-dashboard/* ./horizon/

##
## Put Announce-dashboard to horizon
cd ${WORKSPACE}/../
rsync -a ${WORKSPACE}/* ${WORKSPACE}/.horizon/horizon/ --exclude .horizon

## Remove NECCSPortal-dashboard test
rm -f ${WORKSPACE}/.horizon/horizon/nec_portal/dashboards/project/history/tests.py
rm -f ${WORKSPACE}/.horizon/horizon/nec_portal/dashboards/admin/history/tests.py

##
## Apply patch of
## Heat has a bug that "Test output full of object comparison warnings"
## https://bugs.launchpad.net/horizon/+bug/1536892
##
cd ${WORKSPACE}/.horizon/horizon/
curl -k -o patch https://git.openstack.org/cgit/openstack/horizon/patch/?id=d8c0a7fac6dd37854ba8626f210002fdc94d99e4
patch -p1 < patch

##
## By Horizon version of Jenkins to get does not match the version of nova client,
## since the failure of jenkins occurs, corresponding to this.
TEMP_TARGET=${WORKSPACE}/.horizon/horizon/openstack_dashboard/test/helpers.py
sed -i -e "42a from novaclient import api_versions as nova_api_versions" ${TEMP_TARGET}
sed -i -e "370a \            api_version = nova_api_versions.APIVersion('2.1')" ${TEMP_TARGET}
sed -i -e "371a \            nova_client.Client.api_version = api_version" ${TEMP_TARGET}

##
## Add require pip module
cat <<EOF >> ${WORKSPACE}/.horizon/horizon/test-requirements.txt
# dosca need
cloudify-rest-client==3.3.1
EOF

##
## Run tox/coverage
./run_tests.sh -V $@

echo "bye"
