# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Violin Memory, Inc.
# All Rights Reserved.
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

"""
Violin Memory Fibrechannel (FCP) Driver for Openstack Cinder

Uses Violin REST API via XG-Tools to manage a standard V6000 series
flash array to provide network block-storage services.

by Ryan Lucio
Senior Software Engineer
Violin Memory

Driver support (verified for G6.3.0):
-------------------------------------
Driver Setup:                   YES
Volume Create/Delete:           YES
Export Create/Remove:           YES
Volume Attach/Detach:           YES
Snapshot Create/Delete:         NO
Create Volume from Snapshot:    NO
Get Volume Stats:               YES
Copy Image to Volume:           YES*
Copy Volume to Image:           YES*
Clone Volume:                   NO

* functionality inherited from built-in driver code (unverified)

To cleanup the volumes table:
mysql> delete from volumes where display_name="v4";
"""

import random
import re
import string
import time

from oslo.config import cfg

from cinder import exception
from cinder.openstack.common import log as logging
from cinder.openstack.common import timeutils
from cinder.volume.driver import FibreChannelDriver
from cinder.volume import volume_types

LOG = logging.getLogger(__name__)

try:
    from . import vxg
    from .vxg.core.node import XGNode
    from .vxg.core.session import XGSession
except ImportError:
    LOG.exception(
        _("The Violin v6000 driver for Cinder requires the presence of "
          "the Violin 'XG-Tools', python libraries for facilitating "
          "communication between applications and the v6000 XML API. "
          "The libraries can be downloaded from the Violin Memory "
          "support website at http://www.violin-memory.com/support"))
    raise
else:
    LOG.info(_("Running with xg-tools version: %s") % vxg.__version__)

violin_opts = [
    cfg.StrOpt('gateway_vip',
               default='',
               help='IP address or hostname of the v6000 master VIP'),
    cfg.StrOpt('gateway_mga',
               default='',
               help='IP address or hostname of mg-a'),
    cfg.StrOpt('gateway_mgb',
               default='',
               help='IP address or hostname of mg-b'),
    cfg.StrOpt('gateway_user',
               default='admin',
               help='User name for connecting to the Memory Gateway'),
    cfg.StrOpt('gateway_password',
               default='',
               help='User name for connecting to the Memory Gateway',
               secret=True),
    cfg.StrOpt('gateway_fcp_igroup_name',
               default='openstack',
               help='name of igroup for initiators'), ]

CONF = cfg.CONF
CONF.register_opts(violin_opts)


class InvalidBackendConfig(exception.CinderException):
    message = _("Volume backend config is invalid: %(reason)s")


class ViolinFCDriver(FibreChannelDriver):
    """Executes commands relating to Violin Memory Arrays """

    def __init__(self, *args, **kwargs):
        super(ViolinFCDriver, self).__init__(*args, **kwargs)
        self.session_start_time = 0
        self.session_timeout = 900
        self.array_info = []
        self.vmem_vip = None
        self.vmem_mga = None
        self.vmem_mgb = None
        self.container = ""
        self.device_id = ""
        self.stats = {}
        self.gateway_fc_wwns = []
        self.config = kwargs.get('configuration', None)
        if self.config:
            self.config.append_config_values(violin_opts)

    def do_setup(self, context):
        """Any initialization the driver does while starting """
        if not self.config.gateway_vip:
            raise exception.InvalidInput(
                reason=_('Gateway VIP is not set'))
        if not self.config.gateway_mga:
            raise exception.InvalidInput(
                reason=_('Gateway IP for mg-a is not set'))
        if not self.config.gateway_mgb:
            raise exception.InvalidInput(
                reason=_('Gateway IP for mg-b is not set'))

        self.vmem_vip = vxg.open(self.config.gateway_vip,
                                 self.config.gateway_user,
                                 self.config.gateway_password)
        self.vmem_mga = vxg.open(self.config.gateway_mga,
                                 self.config.gateway_user,
                                 self.config.gateway_password)
        self.vmem_mgb = vxg.open(self.config.gateway_mgb,
                                 self.config.gateway_user,
                                 self.config.gateway_password)

        vip = self.vmem_vip.basic

        ret_dict = vip.get_node_values("/vshare/state/local/container/*")
        if ret_dict:
            self.container = ret_dict.items()[0][1]
        ret_dict = vip.get_node_values(
            "/media/state/array/%s/chassis/system/dev_id" % self.container)
        if ret_dict:
            self.device_id = ret_dict.items()[0][1]
        ret_dict = vip.get_node_values("/wsm/inactivity_timeout")
        if ret_dict:
            self.timeout = ret_dict.items()[0][1]

        # With FCP, the WWNs are created when the container is setup.
        #
        self.gateway_fc_wwns = self._get_active_fc_targets()

    def check_for_setup_error(self):
        """Returns an error if prerequisites aren't met"""
        vip = self.vmem_vip.basic

        if len(self.container) == 0:
            raise InvalidBackendConfig(reason=_('container is missing'))
        if len(self.device_id) == 0:
            raise InvalidBackendConfig(reason=_('device ID is missing'))

        bn = "/vshare/config/igroup/%s" \
            % self.config.gateway_fcp_igroup_name
        resp = vip.get_node_values(bn)
        if len(resp.keys()) == 0:
            raise InvalidBackendConfig(reason=_('igroup is missing'))

        if len(self.gateway_fc_wwns) == 0:
            raise InvalidBackendConfig(reason=_('No FCP targets found'))

    def create_volume(self, volume):
        """Creates a volume """
        self._login()
        self._create_lun(volume)

    def delete_volume(self, volume):
        """Deletes a volume """
        self._login()
        self._delete_lun(volume)

    def create_volume_from_snapshot(self, volume, snapshot):
        """Creates a volume from a snapshot """
        # NYI
        #
        raise NotImplementedError

    def create_cloned_volume(self, volume, src_vref):
        """Creates a clone of the specified volume."""
        # NYI
        #
        raise NotImplementedError

    def create_snapshot(self, snapshot):
        """Creates a snapshot from an existing volume """
        # NYI
        #
        raise NotImplementedError

    def delete_snapshot(self, snapshot):
        """Deletes a snapshot """
        # NYI
        #
        raise NotImplementedError

    def ensure_export(self, context, volume):
        """Synchronously checks and re-exports volumes at cinder start time """
        pass

    def create_export(self, context, volume):
        """Exports the volume """
        pass

    def remove_export(self, context, volume):
        """Removes an export for a logical volume """
        pass

    def initialize_connection(self, volume, connector):
        """Initializes the connection (target<-->initiator) """
        self._login()
        lun = self._export_lun(volume)
        self._add_igroup_member(connector)
        self.vmem_vip.basic.save_config()

        properties = {}
        properties['target_discovered'] = True
        properties['target_wwn'] = self.gateway_fc_wwns
        properties['target_lun'] = lun
        properties['access_mode'] = 'rw'

        return {'driver_volume_type': 'fibre_channel', 'data': properties}

    def terminate_connection(self, volume, connector, force=False, **kwargs):
        """Terminates the connection (target<-->initiator) """
        self._login()
        self._unexport_lun(volume)
        self.vmem_vip.basic.save_config()

    def get_volume_stats(self, refresh=False):
        """Get volume stats """
        if refresh or not self.stats:
            self._login()
            self._update_stats()
        return self.stats

    def _create_lun(self, volume):
        """
        Creates a new lun.

        The equivalent CLI command is "lun create container
        <container_name> name <lun_name> size <gb>"

        Arguments:
            volume -- volume object provided by the Manager
        """
        v = self.vmem_vip

        LOG.info(_("Creating lun %(name)s, %(size)s GB") % volume)

        # using the defaults for other fields: (container, name, size,
        # quantity, nozero, thin, readonly, startnum, blksize)
        #

        while(1):
            time.sleep(random.randint(0, 5))
            resp = v.lun.create_lun(self.container, volume['name'],
                                    volume['size'], 1, "0", "0", "w", 1, 512)
            if not resp['message']:
                resp['message'] = '<no data>'
            if resp['code'] == 0 and 'LUN create: success!' in resp['message']:
                break
            if self._fatal_error_code(resp):
                raise exception.Error(
                    _('LUN create failed: %(code)d, %(message)s') % resp)

        LOG.info(_('Leaving create_lun code:%(code)d, msg:%(message)s') % resp)

    def _delete_lun(self, volume):
        """
        Deletes a lun.

        The equivalent CLI command is "no lun create container
        <container_name> name <lun_name>"

        Arguments:
            volume -- volume object provided by the Manager
        """
        v = self.vmem_vip

        LOG.info(_("Deleting lun %s"), volume['name'])

        while(1):
            time.sleep(random.randint(0, 5))
            resp = v.lun.bulk_delete_luns(self.container, volume['name'])
            if not resp['message']:
                resp['message'] = '<no data>'
            if resp['code'] == 0 and 'LUN deletion started' in resp['message']:
                break
            if self._fatal_error_code(resp):
                raise exception.Error(
                    _('LUN delete failed: %(code)d, %(message)s') % resp)

        LOG.info(_('Leaving delete_lun code:%(code)d, msg:%(message)s') % resp)

    def _export_lun(self, volume):
        """
        Generates the export configuration for the given volume

        The equivalent CLI command is "lun export container
        <container_name> name <lun_name>"

        Arguments:
            volume -- volume object provided by the Manager

        Returns:
            lun_id -- the LUN ID assigned by the backend
        """
        v = self.vmem_vip

        LOG.info(_("Exporting lun %s"), volume['name'])

        resp = v.lun.export_lun(self.container, volume['name'], 'all',
                                self.config.gateway_fcp_igroup_name,
                                'auto')

        if resp['code'] != 0:
            raise exception.Error(
                _('LUN export failed: %(code)d, %(message)s') % resp)

        self._wait_for_exportstate(volume['name'], True)

        lun_id = self._get_lun_id(self.container, volume['name'],
                                  self.config.gateway_fcp_igroup_name)

        return lun_id

    def _unexport_lun(self, volume):
        """
        Removes the export configuration for the given volume.

        The equivalent CLI command is "no lun export container
        <container_name> name <lun_name>"

        Arguments:
            volume -- volume object provided by the Manager
        """
        v = self.vmem_vip

        LOG.info(_("Unexporting lun %s"), volume['name'])

        resp = v.lun.unexport_lun(self.container, volume['name'],
                                  'all', 'all', 'auto')

        if resp['code'] != 0:
            raise exception.Error(
                _("LUN unexport failed: %(code)d, %(message)s") % resp)

        self._wait_for_exportstate(volume['name'], False)

    def _add_igroup_member(self, connector):
        """
        Add an initiator to the openstack igroup so it can see exports.

        The equivalent CLI command is "igroup addto name <igroup_name>
        initiators <initiator_name>"

        Arguments:
            connector -- connector object provided by the Manager
        """
        v = self.vmem_vip
        wwpns = self._convert_wwns_openstack_to_vmem(connector['wwpns'])

        LOG.info(_("Adding initiators %s to igroup"), wwpns)

        resp = v.igroup.add_initiators(
            self.config.gateway_fcp_igroup_name, wwpns)

        if resp['code'] != 0:
            raise exception.Error(
                _('Failed to add igroup member: %(code)d, %(message)s') % resp)

    def _update_stats(self):
        data = {}
        total_gb = 'unknown'
        alloc_gb = 'unknown'
        free_gb = 'unknown'
        backend_name = 'unknown'
        vendor_name = 'Violin'
        v = self.vmem_vip

        bn1 = "/vshare/state/global/1/container/%s/total_bytes" \
            % self.container
        bn2 = "/vshare/state/global/1/container/%s/alloc_bytes" \
            % self.container
        bn3 = "/media/state/array/%s/chassis/system/type" % self.container
        bn4 = "/hwinfo/state/system_mfr"
        resp = v.basic.get_node_values([bn1, bn2, bn3, bn4])

        if len(resp.keys()) == 4:
            total_gb = resp[bn1] / 1024 / 1024 / 1024
            alloc_gb = resp[bn2] / 1024 / 1024 / 1024
            free_gb = total_gb - alloc_gb
            backend_name = resp[bn3]
            vendor_name = resp[bn4]

        data['volume_backend_name'] = backend_name
        data['vendor_name'] = vendor_name
        data['driver_version'] = '1.0'
        data['storage_protocol'] = 'fibre_channel'
        data['total_capacity_gb'] = total_gb
        data['free_capacity_gb'] = free_gb
        data['reserved_percentage'] = 0
        data['QoS_support'] = False
        self.stats = data

    def _login(self, force=False):
        """
        Get new api creds from the backend, only if needed.

        Arguments:
            force -- re-login on all sessions regardless of last login time

        Returns:
           True if sessions were refreshed, false otherwise.
        """
        now = time.time()
        if abs(now - self.session_start_time) >= self.session_timeout or \
                force == True:
            self.vmem_vip.basic.login()
            self.vmem_mga.basic.login()
            self.vmem_mgb.basic.login()
            self.session_start_time = now
            return True
        return False

    def _get_lun_id(self, container_name, volume_name, igroup_name):
        """
        Queries the gateway to find the lun id for the exported volume.

        Arguments:
            container_name -- backend array flash container name
            volume_name    -- LUN to query
            igroup_name    -- igroup associated with the LUN

        Returns:
            LUN ID for the exported lun as an integer.  If no LUN ID
            is found, return -1.
        """
        vip = self.vmem_vip.basic
        pattern = re.compile(".*lun_id$")
        lun_id = -1

        prefix = "/vshare/config/export/container"
        bn = "%s/%s/lun/%s/target/**" \
            % (prefix, container_name, volume_name)
        resp = vip.get_node_values(bn)

        # EX: /vshare/config/export/container/PROD08/lun/test1/target/hba-b2/
        #     initiator/openstack/lun_id = 1 (int16)
        #
        for node in resp:
            if re.match(pattern, node):
                lun_id = resp[node]
                break

        # TODO(rdl): add exception for case where no lun id found, or lun ids
        # do not match
        #
        return lun_id

    def _wait_for_exportstate(self, volume_name, state=False):
        """
        Polls volume's export configuration root.

        XG sets/queries following a request to create or delete a
        lun export may fail on the backend if vshared is still
        processing the export action.  We can check whether it is
        done by polling the export binding for a lun to
        ensure it is created or deleted.

        Arguments:
            volume_name -- name of volume to be polled
            state       -- True to poll for existence, False for lack of

        Returns:
            True if the export state was eventually found, false otherwise.
        """
        status = False
        vip = self.vmem_vip.basic

        # TODO(rdl): this implementation only waits on the master, but
        # may need to additionally wait for the standby to finish the
        # config sync
        #

        bn = "/vshare/config/export/container/%s/lun/%s" \
            % (self.container, volume_name)

        for i in range(30):
            resp = vip.get_node_values(bn)
            if state and len(resp.keys()):
                status = True
                break
            elif (not state) and (not len(resp.keys())):
                break
            else:
                time.sleep(1)
        return status

    def _get_active_fc_targets(self):
        """
        Get a list of gateway WWNs that can be used as FCP targets.

        Arguments:
            mg_conn -- active XG connection to one of the gateways

        Returns:
            active_gw_fcp_wwns -- list of WWNs
        """
        v = self.vmem_vip.basic
        active_gw_fcp_wwns = []
        pattern = re.compile(".*wwn$")

        ids = v.get_node_values('/vshare/state/global/*')

        for i in ids:
            bn = "/vshare/state/global/%d/target/fc/**" % ids[i]
            resp = v.get_node_values(bn)

            for node in resp:
                if re.match(pattern, node):
                    active_gw_fcp_wwns.append(resp[node])

        return self._convert_wwns_vmem_to_openstack(active_gw_fcp_wwns)

    def _convert_wwns_openstack_to_vmem(self, wwns):
        # input format is '50014380186b3f65', output format is
        # 'wwn.50:01:43:80:18:6b:3f:65'
        #
        output = []
        for w in wwns:
            output.append('wwn.' + w[0:2] + ':' + w[2:4] + ':' + w[4:6]
                          + ':' + w[6:8] + ':' + w[8:10] + ':' + w[10:12]
                          + ':' + w[12:14] + ':' + w[14:16])
        return output

    def _convert_wwns_vmem_to_openstack(self, wwns):
        # input format is 'wwn.50:01:43:80:18:6b:3f:65', output format
        # is '50014380186b3f65'
        #
        output = []
        for w in wwns:
            output.append(string.join(w[4:].split(':'), ''))
        return output

    def _fatal_error_code(self, response):
        # known fatal response codes (as seen in vdmd_mgmt.c)
        #
        error_codes = {14000: 'lc_generic_error',
                       14002: 'lc_err_assertion_failed',
                       14004: 'lc_err_not_found',
                       14005: 'lc_err_exists',
                       14008: 'lc_err_unexpected_arg',
                       14014: 'lc_err_io_error',
                       14016: 'lc_err_io_closed',
                       14017: 'lc_err_io_timeout',
                       14021: 'lc_err_unexpected_case',
                       14025: 'lc_err_no_fs_space',
                       14035: 'lc_err_range',
                       14036: 'lc_err_invalid_param',
                       14121: 'lc_err_cancelled_error'}

        # known non-fatal response codes
        #
        retry_codes = {1024: 'lun deletion in progress, try again later',
                       14032: 'lc_err_lock_busy'}

        if response['code'] in error_codes:
            return True

        return False
