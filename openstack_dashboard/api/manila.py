# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 OpenStack Foundation
# Copyright 2012 Nebula, Inc.
# Copyright (c) 2012 X.commerce, a business unit of eBay Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import absolute_import

import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from manilaclient.v1 import client as manila_client
from manilaclient.v1.contrib import list_extensions as manila_list_extensions

from horizon import exceptions
from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard.api import base

LOG = logging.getLogger(__name__)


# API static values
SHARE_STATE_AVAILABLE = "available"
DEFAULT_QUOTA_NAME = 'default'


def manilaclient(request):
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    manila_url = ""
    try:
        manila_url = base.url_for(request, 'share')
    except exceptions.ServiceCatalogException:
        LOG.debug('no share service configured.')
        return None
    LOG.debug('manilaclient connection created using token "%s" and url "%s"' %
              (request.user.token.id, manila_url))
    c = manila_client.Client(request.user.username,
                             request.user.token.id,
                             project_id=request.user.tenant_id,
                             auth_url=manila_url,
                             insecure=insecure,
                             cacert=cacert,
                             http_log_debug=settings.DEBUG)
    c.client.auth_token = request.user.token.id
    c.client.management_url = manila_url
    return c


def share_list(request, search_opts=None):
    return manilaclient(request).shares.list(search_opts=search_opts)


def share_get(request, share_id):
    share_data = manilaclient(request).shares.get(share_id)
    return share_data


def share_create(request, size, name, description, proto, snapshot_id=None,
                 metadata=None, share_network_id=None):
    return manilaclient(request).shares.create(proto, size, name=name,
            description=description, share_network_id=share_network_id,
            snapshot_id=snapshot_id, metadata=metadata)


def share_delete(request, share_id):
    return manilaclient(request).shares.delete(share_id)


def share_update(request, share_id, name, description):
    share_data = {'display_name': name,
                  'display_description': description}
    return manilaclient(request).shares.update(share_id, **share_data)


def share_snapshot_get(request, snapshot_id):
    return manilaclient(request).share_snapshots.get(snapshot_id)


def share_snapshot_list(request):
    return manilaclient(request).share_snapshots.list()


def share_snapshot_create(request, share_id, name=None,
                           description=None, force=False):
    return manilaclient(request).share_snapshots.create(
        share_id, force=force, name=name, description=description)


def share_snapshot_delete(request, snapshot_id):
    return manilaclient(request).share_snapshots.delete(snapshot_id)


def share_network_list(request, search_opts=None):
    return manilaclient(request).share_networks.list(search_opts=search_opts)


def share_network_create(request, neutron_net_id=None, neutron_subnet_id=None,
                         name=None, description=None):
    return manilaclient(request).share_networks.create(
        neutron_net_id=neutron_net_id, neutron_subnet_id=neutron_subnet_id,
        name=name, description=description)


def share_network_delete(request, share_network_id):
    return manilaclient(request).share_networks.delete(share_network_id)


def security_service_list(request, search_opts=None):
    return manilaclient(request).security_services.list(detailed=True,
        search_opts=search_opts)


def security_service_create(request, type, dns_ip=None, server=None,
                            domain=None, sid=None, password=None, name=None,
                            description=None):
    return manilaclient(request).security_services.create(
        type, dns_ip=dns_ip, server=server, domain=domain, sid=sid,
        password=password, name=name, description=description)


def security_service_delete(request, security_service_id):
    return manilaclient(request).security_services.delete(security_service_id)


def share_network_security_service_add(request, share_network_id,
                                       security_service_id):
    return manilaclient(request).share_networks.add_security_service(
        share_network_id, security_service_id)


def share_network_security_service_remove(request, share_network_id,
                                          security_service_id):
    return manilaclient(request).share_networks.remove_security_service(
        share_network_id, security_service_id)


def tenant_quota_get(request, tenant_id):
    return base.QuotaSet(manilaclient(request).quotas.get(tenant_id))


def tenant_quota_update(request, tenant_id, **kwargs):
    return manilaclient(request).quotas.update(tenant_id, **kwargs)


def default_quota_get(request, tenant_id):
    return base.QuotaSet(manilaclient(request).quotas.defaults(tenant_id))


def default_quota_update(request, **kwargs):
    manilaclient(request).quota_classes.update(DEFAULT_QUOTA_NAME, **kwargs)


def tenant_absolute_limits(request):
    limits = manilaclient(request).limits.get().absolute
    limits_dict = {}
    for limit in limits:
        # -1 is used to represent unlimited quotas
        if limit.value == -1:
            limits_dict[limit.name] = float("inf")
        else:
            limits_dict[limit.name] = limit.value
    return limits_dict


@memoized
def list_extensions(request):
    return manila_list_extensions.ListExtManager(manilaclient(request))\
        .show_all()


@memoized
def extension_supported(request, extension_name):
    """This method will determine if manila supports a given extension name.
    """
    extensions = list_extensions(request)
    for extension in extensions:
        if extension.name == extension_name:
            return True
    return False
