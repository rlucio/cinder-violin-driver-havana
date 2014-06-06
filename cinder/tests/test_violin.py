# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Violin Memory, Inc.
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
Violin Memory tests for iSCSI driver

by Ryan Lucio
Senior Software Engineer
Violin Memory

Note: python documentation for unit testing can be found at
http://docs.python.org/2/library/unittest.html

Note: cinder documentation for development can be found at
http://docs.openstack.org/developer/cinder/devref/development.environment.html
"""


import mox
import time
import unittest

# TODO(rlucio): workaround for gettext '_' not defined bug, must be done before
# importing any cinder libraries.  This should be removed when the bug is
# fixed.
import gettext
gettext.install("cinder", unicode=1)

from cinder.volume.drivers.violin import vxg
from cinder.volume.drivers.violin.vxg.core.node import XGNode
from cinder.volume.drivers.violin.vxg.core.session import XGSession
from cinder.volume.drivers.violin.vxg.vshare.igroup import IGroupManager
from cinder.volume.drivers.violin.vxg.vshare.iscsi import ISCSIManager
from cinder.volume.drivers.violin.vxg.vshare.lun import LUNManager
from cinder.volume.drivers.violin.vxg.vshare.vshare import VShare

from cinder.volume import configuration as conf
from cinder.volume.drivers.violin import violin


class testViolin(unittest.TestCase):
    """
    A test class for the violin driver module.
    """
    def setUp(self):
        self.m = mox.Mox()
        self.m_conn = self.m.CreateMock(VShare)
        self.m_conn.basic = self.m.CreateMock(XGSession)
        self.m_conn.lun = self.m.CreateMock(LUNManager)
        self.m_conn.iscsi = self.m.CreateMock(ISCSIManager)
        self.m_conn.igroup = self.m.CreateMock(IGroupManager)
        self.config = mox.MockObject(conf.Configuration)
        self.config.append_config_values(mox.IgnoreArg())
        self.config.gateway_vip = '1.1.1.1'
        self.config.gateway_mga = '2.2.2.2'
        self.config.gateway_mgb = '3.3.3.3'
        self.config.gateway_user = 'admin'
        self.config.gateway_password = ''
        self.config.use_thin_luns = False
        self.config.use_igroups = False
        self.config.volume_backend_name = 'violin'
        self.config.gateway_iscsi_target_prefix = 'iqn.2004-02.com.vmem:'
        self.driver = violin.ViolinDriver(configuration=self.config)
        self.driver.vmem_vip = self.m_conn
        self.driver.vmem_mga = self.m_conn
        self.driver.vmem_mgb = self.m_conn
        self.driver.container = 'myContainer'
        self.driver.gateway_iscsi_ip_addresses_mga = '1.2.3.4'
        self.driver.gateway_iscsi_ip_addresses_mgb = '1.2.3.4'
        self.driver.array_info = [{"node": 'hostname_mga',
                                   "addr": '1.2.3.4',
                                   "conn": self.driver.vmem_mga},
                                  {"node": 'hostname_mgb',
                                   "addr": '1.2.3.4',
                                   "conn": self.driver.vmem_mgb}]

    def tearDown(self):
        self.m.UnsetStubs()

    def testSetup(self):
        emptyContext = []
        self.driver.vmem_vip = None
        self.driver.vmem_mga = None
        self.driver.vmem_mgb = None
        self.driver.container = ""
        self.driver.gateway_iscsi_ip_addresses_mga = ""
        self.driver.gateway_iscsi_ip_addresses_mgb = ""
        self.driver.array_info = []
        self.m.StubOutWithMock(vxg, 'open')
        self.m.StubOutWithMock(self.driver, '_get_active_iscsi_ips')
        vxg.open(mox.IsA(str), mox.IsA(str),
                 mox.IsA(str)).AndReturn(self.m_conn)
        vxg.open(mox.IsA(str), mox.IsA(str),
                 mox.IsA(str)).AndReturn(self.m_conn)
        vxg.open(mox.IsA(str), mox.IsA(str),
                 mox.IsA(str)).AndReturn(self.m_conn)
        self.driver._get_active_iscsi_ips(self.m_conn).AndReturn([])
        self.driver._get_active_iscsi_ips(self.m_conn).AndReturn([])
        self.m_conn.basic.get_node_values(mox.IsA(str))
        self.m_conn.basic.get_node_values(mox.IsA(str))
        self.m.ReplayAll()
        self.assertTrue(self.driver.do_setup(emptyContext) is None)
        self.m.VerifyAll()

    def testCheckForSetupError(self):
        bn_enable = {"/vshare/config/iscsi/enable": True}
        self.m_conn.basic.get_node_values(mox.IsA(str)
                                          ).AndReturn(bn_enable)
        self.m.ReplayAll()
        self.assertTrue(self.driver.check_for_setup_error() is None)
        self.m.VerifyAll()

    def testCheckForSetupError_NoContainer(self):
        '''container name is empty '''
        self.driver.container = ""
        self.assertRaises(violin.InvalidBackendConfig,
                          self.driver.check_for_setup_error)

    def testCheckForSetupError_IscsiDisabled(self):
        '''iscsi is disabled '''
        bn_enable = {"/vshare/config/iscsi/enable": False}
        self.m_conn.basic.get_node_values(mox.IsA(str)
                                          ).AndReturn(bn_enable)
        self.m.ReplayAll()
        self.assertRaises(violin.InvalidBackendConfig,
                          self.driver.check_for_setup_error)
        self.m.VerifyAll()

    def testCheckForSetupError_NoIscsiIPsMga(self):
        '''iscsi interface binding for mg-a is empty '''
        self.driver.gateway_iscsi_ip_addresses_mga = ''
        bn_enable = {"/vshare/config/iscsi/enable": True}
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn(bn_enable)
        self.m.ReplayAll()
        self.assertRaises(violin.InvalidBackendConfig,
                          self.driver.check_for_setup_error)
        self.m.VerifyAll()

    def testCheckForSetupError_NoIscsiIPsMgb(self):
        '''iscsi interface binding for mg-a is empty '''
        self.driver.gateway_iscsi_ip_addresses_mgb = ''
        bn_enable = {"/vshare/config/iscsi/enable": True}
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn(bn_enable)
        self.m.ReplayAll()
        self.assertRaises(violin.InvalidBackendConfig,
                          self.driver.check_for_setup_error)
        self.m.VerifyAll()

    def testCreateVolume(self):
        volume = {'name': 'vol-01', 'size': '1'}
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_create_lun')
        self.driver._login()
        self.driver._create_lun(volume)
        self.m.ReplayAll()
        self.assertTrue(self.driver.create_volume(volume) is None)
        self.m.VerifyAll()

    def testDeleteVolume(self):
        volume = {'name': 'vol-01', 'size': '1'}
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_delete_lun')
        self.driver._login()
        self.driver._delete_lun(volume)
        self.m.ReplayAll()
        self.assertTrue(self.driver.delete_volume(volume) is None)
        self.m.VerifyAll()

    def testInitializeConnection(self):
        igroup = None
        volume = {'name': 'vol-01', 'size': '1', 'id': '12345'}
        connector = {'initiator': 'iqn.1993-08.org.debian:8d3a79542d'}
        vol = volume['name']
        tgt = self.driver.array_info[0]
        lun = 1
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_get_short_name')
        self.m.StubOutWithMock(self.driver, '_create_iscsi_target')
        self.m.StubOutWithMock(self.driver, '_export_lun')
        self.driver._login()
        self.driver._get_short_name(volume['name']).AndReturn(vol)
        self.driver._create_iscsi_target(volume).AndReturn(tgt)
        self.driver._export_lun(volume, connector, igroup).AndReturn(lun)
        self.m_conn.basic.save_config()
        self.m.ReplayAll()
        props = self.driver.initialize_connection(volume, connector)
        self.assertEqual(props['data']['target_portal'], "1.2.3.4:3260")
        self.assertEqual(props['data']['target_iqn'],
                         "iqn.2004-02.com.vmem:hostname_mga:vol-01")
        self.assertEqual(props['data']['target_lun'], lun)
        self.assertEqual(props['data']['volume_id'], "12345")
        self.m.VerifyAll()

    def testInitializeConnection_WithIgroupsEnabled(self):
        self.config.use_igroups = True
        igroup = 'test-igroup-1'
        volume = {'name': 'vol-01', 'size': '1', 'id': '12345'}
        connector = {'initiator': 'iqn.1993-08.org.debian:8d3a79542d'}
        vol = volume['name']
        tgt = self.driver.array_info[0]
        lun = 1
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_get_igroup')
        self.m.StubOutWithMock(self.driver, '_add_igroup_member')
        self.m.StubOutWithMock(self.driver, '_get_short_name')
        self.m.StubOutWithMock(self.driver, '_create_iscsi_target')
        self.m.StubOutWithMock(self.driver, '_export_lun')
        self.driver._login()
        self.driver._get_igroup(volume, connector).AndReturn(igroup)
        self.driver._add_igroup_member(connector, igroup)
        self.driver._get_short_name(volume['name']).AndReturn(vol)
        self.driver._create_iscsi_target(volume).AndReturn(tgt)
        self.driver._export_lun(volume, connector, igroup).AndReturn(lun)
        self.m_conn.basic.save_config()
        self.m.ReplayAll()
        props = self.driver.initialize_connection(volume, connector)
        self.assertEqual(props['data']['target_portal'], "1.2.3.4:3260")
        self.assertEqual(props['data']['target_iqn'],
                         "iqn.2004-02.com.vmem:hostname_mga:vol-01")
        self.assertEqual(props['data']['target_lun'], lun)
        self.assertEqual(props['data']['volume_id'], "12345")
        self.m.VerifyAll()

    def testTerminateConnection(self):
        volume = {'name': 'vol-01', 'size': '1', 'id': '12345'}
        connector = {'initiator': 'iqn.1993-08.org.debian:8d3a79542d'}
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_unexport_lun')
        self.m.StubOutWithMock(self.driver, '_delete_iscsi_target')
        self.driver._login()
        self.driver._unexport_lun(volume)
        self.driver._delete_iscsi_target(volume)
        self.m_conn.basic.save_config()
        self.m.ReplayAll()
        self.driver.terminate_connection(volume, connector)
        self.m.VerifyAll()

    def testGetVolumeStats(self):
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_update_stats')
        self.driver._login()
        self.driver._update_stats()
        self.m.ReplayAll()
        self.assertEqual(self.driver.get_volume_stats(True), self.driver.stats)
        self.m.VerifyAll()

    def testCreateLun(self):
        volume = {'name': 'vol-01', 'size': '1'}
        response = {'code': 0, 'message': 'LUN create: success!'}
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.driver._send_cmd(self.m_conn.lun.create_lun,
                              mox.IsA(str),
                              self.driver.container, volume['name'],
                              volume['size'], 1, "0", "0", "w", 1,
                              512).AndReturn(response)
        self.m.ReplayAll()
        self.assertTrue(self.driver._create_lun(volume) is None)
        self.m.VerifyAll()

    def testCreateLun_LunAlreadyExists(self):
        volume = {'name': 'vol-01', 'size': '1'}
        response = {'code': 0, 'message': 'LUN create: success!'}
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.driver._send_cmd(self.m_conn.lun.create_lun,
                              mox.IsA(str),
                              self.driver.container, volume['name'],
                              volume['size'], 1, "0", "0", "w", 1,
                              512).AndRaise(violin.ViolinBackendErrExists())
        self.m.ReplayAll()
        self.assertTrue(self.driver._create_lun(volume) is None)
        self.m.VerifyAll()

    def testCreateLun_CreateFailsWithException(self):
        volume = {'name': 'vol-01', 'size': '1'}
        response = {'code': 0, 'message': 'LUN create: success!'}
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.driver._send_cmd(self.m_conn.lun.create_lun,
                              mox.IsA(str),
                              self.driver.container, volume['name'],
                              volume['size'], 1, "0", "0", "w", 1,
                              512).AndRaise(violin.ViolinBackendErr('failed'))
        self.m.ReplayAll()
        self.assertRaises(violin.ViolinBackendErr, self.driver._create_lun,
                          volume)
        self.m.VerifyAll()

    def testDeleteLun(self):
        volume = {'name': 'vol-01', 'size': '1'}
        response = {'code': 0, 'message': 'LUN deletion started'}
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.driver._send_cmd(self.m_conn.lun.bulk_delete_luns,
                              mox.IsA(str),
                              self.driver.container,
                              volume['name']).AndReturn(response)
        self.m.ReplayAll()
        self.assertTrue(self.driver._delete_lun(volume) is None)
        self.m.VerifyAll()

    def testDeleteLun_LunAlreadyDeleted(self):
        volume = {'name': 'vol-01', 'size': '1'}
        response = {'code': 0, 'message': 'LUN deletion started'}
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.driver._send_cmd(self.m_conn.lun.bulk_delete_luns,
                              mox.IsA(str),
                              self.driver.container,
                              volume['name']
                              ).AndRaise(violin.ViolinBackendErrNotFound)
        self.m.ReplayAll()
        self.assertTrue(self.driver._delete_lun(volume) is None)
        self.m.VerifyAll()

    def testDeleteLun_DeleteFailsWithException(self):
        volume = {'name': 'vol-01', 'size': '1'}
        response = {'code': 0, 'message': 'LUN deletion started'}
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.driver._send_cmd(self.m_conn.lun.bulk_delete_luns,
                              mox.IsA(str),
                              self.driver.container,
                              volume['name']
                              ).AndRaise(violin.ViolinBackendErr('failed!'))
        self.m.ReplayAll()
        self.assertRaises(violin.ViolinBackendErr, self.driver._delete_lun, volume)
        self.m.VerifyAll()

    def testCreateIscsiTarget(self):
        volume = {'name': 'vol-01', 'size': '1'}
        response = {'code': 0, 'message': 'success'}
        self.m.StubOutWithMock(self.driver, '_get_short_name')
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.driver._get_short_name(mox.IsA(str)).AndReturn(volume['name'])
        self.driver._send_cmd(self.m_conn.iscsi.create_iscsi_target,
                              mox.IsA(str), mox.IsA(str)).AndReturn(response)
        self.driver._send_cmd(self.m_conn.iscsi.bind_ip_to_target,
                              mox.IsA(str), mox.IsA(str),
                              mox.IsA(str)).AndReturn(response)
        self.driver._send_cmd(self.m_conn.iscsi.bind_ip_to_target,
                              mox.IsA(str), mox.IsA(str),
                              mox.IsA(str)).AndReturn(response)
        self.m.ReplayAll()
        self.assertTrue(self.driver._create_iscsi_target(volume) in
                        self.driver.array_info)
        self.m.VerifyAll()

    def testDeleteIscsiTarget(self):
        volume = {'name': 'vol-01', 'size': '1'}
        response = {'code': 0, 'message': 'success'}
        self.m.StubOutWithMock(self.driver, '_get_short_name')
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.driver._get_short_name(mox.IsA(str)).AndReturn(volume['name'])
        self.driver._send_cmd(self.m_conn.iscsi.unbind_ip_from_target,
                              mox.IsA(str), mox.IsA(str),
                              mox.IsA(str)).AndReturn(response)
        self.driver._send_cmd(self.m_conn.iscsi.unbind_ip_from_target,
                              mox.IsA(str), mox.IsA(str),
                              mox.IsA(str)).AndReturn(response)
        self.driver._send_cmd(self.m_conn.iscsi.delete_iscsi_target,
                              mox.IsA(str), mox.IsA(str)).AndReturn(response)
        self.m.ReplayAll()
        self.assertTrue(self.driver._delete_iscsi_target(volume) is None)
        self.m.VerifyAll()

    def testDeleteIscsiTarget_AnUnbindFailsWithException(self):
        volume = {'name': 'vol-01', 'size': '1'}
        response = {'code': 0, 'message': 'success'}
        self.m.StubOutWithMock(self.driver, '_get_short_name')
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.driver._get_short_name(mox.IsA(str)).AndReturn(volume['name'])
        self.driver._send_cmd(self.m_conn.iscsi.unbind_ip_from_target,
                              mox.IsA(str), mox.IsA(str),
                              mox.IsA(str)).AndReturn(response)
        self.driver._send_cmd(self.m_conn.iscsi.unbind_ip_from_target,
                              mox.IsA(str), mox.IsA(str),
                              mox.IsA(str)
                              ).AndRaise(violin.ViolinBackendErr('failed!'))
        self.m.ReplayAll()
        self.assertRaises(violin.ViolinBackendErr,
                          self.driver._delete_iscsi_target, volume)
        self.m.VerifyAll()

    def testDeleteIscsiTarget_TargetDeleteFailsWithException(self):
        volume = {'name': 'vol-01', 'size': '1'}
        response = {'code': 0, 'message': 'success'}
        self.m.StubOutWithMock(self.driver, '_get_short_name')
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.driver._get_short_name(mox.IsA(str)).AndReturn(volume['name'])
        self.driver._send_cmd(self.m_conn.iscsi.unbind_ip_from_target,
                              mox.IsA(str), mox.IsA(str),
                              mox.IsA(str)).AndReturn(response)
        self.driver._send_cmd(self.m_conn.iscsi.unbind_ip_from_target,
                              mox.IsA(str), mox.IsA(str),
                              mox.IsA(str)).AndReturn(response)
        self.driver._send_cmd(self.m_conn.iscsi.delete_iscsi_target,
                              mox.IsA(str), mox.IsA(str)
                              ).AndRaise(violin.ViolinBackendErr('failed!'))
        self.m.ReplayAll()
        self.assertRaises(violin.ViolinBackendErr,
                          self.driver._delete_iscsi_target, volume)
        self.m.VerifyAll()

    def testExportLun(self):
        volume = {'name': 'vol-01', 'size': '1'}
        igroup = 'test-igroup-1'
        response = {'code': 0, 'message': ''}
        connector = {'initiator': 'iqn.1993-08.org.debian:8d3a79542d'}
        self.m.StubOutWithMock(self.driver, '_get_short_name')
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.m.StubOutWithMock(self.driver, '_wait_for_exportstate')
        self.m.StubOutWithMock(self.driver, '_get_lun_id')
        self.driver._get_short_name(mox.IsA(str)).AndReturn(volume['name'])
        self.driver._send_cmd(self.m_conn.lun.export_lun,
                              mox.IsA(str), mox.IsA(str), mox.IsA(str),
                              mox.IsA(str), mox.IsA(str), mox.IsA(str)
                              ).AndReturn(response)
        self.driver._wait_for_exportstate(mox.IsA(str), mox.IsA(bool))
        self.driver._get_lun_id(mox.IsA(str)).AndReturn(1)
        self.m.ReplayAll()
        self.assertEqual(self.driver._export_lun(volume, connector, igroup), 1)
        self.m.VerifyAll()

    def testExportLun_ExportFailsWithException(self):
        volume = {'name': 'vol-01', 'size': '1'}
        igroup = 'test-igroup-1'
        response = {'code': 0, 'message': ''}
        connector = {'initiator': 'iqn.1993-08.org.debian:8d3a79542d'}
        self.m.StubOutWithMock(self.driver, '_get_short_name')
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.m.StubOutWithMock(self.driver, '_wait_for_exportstate')
        self.m.StubOutWithMock(self.driver, '_get_lun_id')
        self.driver._get_short_name(mox.IsA(str)).AndReturn(volume['name'])
        self.driver._send_cmd(self.m_conn.lun.export_lun,
                              mox.IsA(str), mox.IsA(str), mox.IsA(str),
                              mox.IsA(str), mox.IsA(str), mox.IsA(str)
                              ).AndRaise(violin.ViolinBackendErr('failed!'))
        self.m.ReplayAll()
        self.assertRaises(violin.ViolinBackendErr,
                          self.driver._export_lun, volume, connector, igroup)
        self.m.VerifyAll()

    def testUnexportLun(self):
        volume = {'name': 'vol-01', 'size': '1'}
        lun_id = 1
        response = {'code': 0, 'message': ''}
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.m.StubOutWithMock(self.driver, '_wait_for_exportstate')
        self.driver._send_cmd(self.m_conn.lun.unexport_lun,
                              mox.IsA(str),
                              self.driver.container, volume['name'],
                              'all', 'all', 'auto').AndReturn(response)
        self.driver._wait_for_exportstate(volume['name'], False)
        self.m.ReplayAll()
        self.assertTrue(self.driver._unexport_lun(volume) is None)
        self.m.VerifyAll()

    def testUnexportLun_UnexportFailsWithException(self):
        volume = {'name': 'vol-01', 'size': '1'}
        lun_id = 1
        response = {'code': 0, 'message': ''}
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.m.StubOutWithMock(self.driver, '_wait_for_exportstate')
        self.driver._send_cmd(self.m_conn.lun.unexport_lun,
                              mox.IsA(str),
                              self.driver.container, volume['name'],
                              'all', 'all', 'auto'
                              ).AndRaise(violin.ViolinBackendErr('failed!'))
        self.m.ReplayAll()
        self.assertRaises(violin.ViolinBackendErr, self.driver._unexport_lun,
                          volume)
        self.m.VerifyAll()

    def testAddIgroupMember(self):
        igroup = 'test-group-1'
        connector = {'initiator': 'foo'}
        response = {'code': 0, 'message': 'success'}
        self.m_conn.igroup.add_initiators(mox.IsA(str),
                                          mox.IsA(str)).AndReturn(response)
        self.m.ReplayAll()
        self.assertTrue(self.driver._add_igroup_member(connector, igroup)
                        is None)
        self.m.VerifyAll()

    def testUpdateStats(self):
        backend_name = self.config.volume_backend_name
        vendor_name = "Violin Memory, Inc."
        tot_bytes = 100 * 1024 * 1024 * 1024
        alloc_bytes = 50 * 1024 * 1024 * 1024
        free_bytes = 50 * 1024 * 1024 * 1024
        bn1 = "/vshare/state/global/1/container/myContainer/total_bytes"
        bn2 = "/vshare/state/global/1/container/myContainer/alloc_bytes"
        response = {bn1: tot_bytes, bn2: alloc_bytes}
        self.m_conn.basic.get_node_values([bn1, bn2]).AndReturn(response)
        self.m.ReplayAll()
        self.assertTrue(self.driver._update_stats() is None)
        self.assertEqual(self.driver.stats['total_capacity_gb'], 100)
        self.assertEqual(self.driver.stats['free_capacity_gb'], 50)
        self.assertEqual(self.driver.stats['volume_backend_name'],
                         backend_name)
        self.assertEqual(self.driver.stats['vendor_name'], vendor_name)
        self.m.VerifyAll()

    def testUpdateStats_DataQueryFails(self):
        backend_name = self.config.volume_backend_name
        vendor_name = "Violin Memory, Inc."
        bn1 = "/vshare/state/global/1/container/myContainer/total_bytes"
        bn2 = "/vshare/state/global/1/container/myContainer/alloc_bytes"
        self.m_conn.basic.get_node_values([bn1, bn2]).AndReturn({})
        self.m.ReplayAll()
        self.assertTrue(self.driver._update_stats() is None)
        self.assertEqual(self.driver.stats['total_capacity_gb'], "unknown")
        self.assertEqual(self.driver.stats['free_capacity_gb'], "unknown")
        self.assertEqual(self.driver.stats['volume_backend_name'], backend_name)
        self.assertEqual(self.driver.stats['vendor_name'], vendor_name)
        self.m.VerifyAll()

    def testLogin(self):
        self.driver.session_start_time = 0
        self.m_conn.basic.login()
        self.m_conn.basic.login()
        self.m_conn.basic.login()
        self.m.ReplayAll()
        self.assertTrue(self.driver._login(False))
        self.m.VerifyAll()

    def testLogin_Force(self):
        self.m_conn.basic.login()
        self.m_conn.basic.login()
        self.m_conn.basic.login()
        self.m.ReplayAll()
        self.assertTrue(self.driver._login(True))
        self.m.VerifyAll()

    def testLogin_NoUpdate(self):
        self.driver.session_start_time = time.time()
        self.assertFalse(self.driver._login(False))

    def testGetLunID(self):
        volume = {'name': 'vol-01', 'size': '1'}
        bn = '/vshare/config/export/container/myContainer/lun/vol-01/target/**'
        resp = {'/vshare/config/export/container/myContainer/lun'
                '/vol-01/target/hba-a1/initiator/openstack/lun_id': 1}
        self.m_conn.basic.get_node_values(bn).AndReturn(resp)
        self.m.ReplayAll()
        self.assertEqual(self.driver._get_lun_id(volume['name']), 1)
        self.m.VerifyAll()

    def testGetLunID_NoLunConfig(self):
        volume = {'name': 'vol-01', 'size': '1'}
        bn = '/vshare/config/export/container/myContainer/lun/vol-01/target/**'
        resp = {}
        self.m_conn.basic.get_node_values(bn).AndReturn(resp)
        self.m.ReplayAll()
        self.assertEqual(self.driver._get_lun_id(volume['name']), -1)
        self.m.VerifyAll()

    def testGetShortName_LongName(self):
        long_name = "abcdefghijklmnopqrstuvwxyz1234567890"
        short_name = "abcdefghijklmnopqrstuvwxyz123456"
        self.assertEqual(self.driver._get_short_name(long_name), short_name)

    def testGetShortName_ShortName(self):
        long_name = "abcdef"
        short_name = "abcdef"
        self.assertEqual(self.driver._get_short_name(long_name), short_name)

    def testGetShortName_EmptyName(self):
        long_name = ""
        short_name = ""
        self.assertEqual(self.driver._get_short_name(long_name), short_name)

    def testWaitForExportState(self):
        response = {"/vshare/config/export/container/1/lun/vol-01": "vol-01"}
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn(response)
        self.m.ReplayAll()
        self.assertTrue(self.driver._wait_for_exportstate("vol-01", True))
        self.m.VerifyAll()

    def testWaitForExportState_NoState(self):
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn({})
        self.m.ReplayAll()
        self.assertFalse(self.driver._wait_for_exportstate("vol-01", False))
        self.m.VerifyAll()

    def testGetActiveIscsiIPs(self):
        request = ["/net/interface/state/eth4/addr/ipv4/1/ip",
                   "/net/interface/state/eth4/flags/link_up"]
        response1 = {"/net/interface/config/eth4": "eth4"}
        response2 = {"/net/interface/state/eth4/addr/ipv4/1/ip": "1.1.1.1",
                     "/net/interface/state/eth4/flags/link_up": True}
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn(response1)
        self.m_conn.basic.get_node_values(request).AndReturn(response2)
        self.m.ReplayAll()
        ips = self.driver._get_active_iscsi_ips(self.m_conn)
        self.assertEqual(len(ips), 1)
        self.assertEqual(ips[0], "1.1.1.1")
        self.m.VerifyAll()

    def testGetActiveIscsiIPs_InvalidIntfs(self):
        response = {"/net/interface/config/lo": "lo",
                    "/net/interface/config/vlan10": "vlan10",
                    "/net/interface/config/eth1": "eth1",
                    "/net/interface/config/eth2": "eth2",
                    "/net/interface/config/eth3": "eth3"}
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn(response)
        self.m.ReplayAll()
        ips = self.driver._get_active_iscsi_ips(self.m_conn)
        self.assertEqual(len(ips), 0)
        self.m.VerifyAll()

    def testGetActiveIscsiIps_NoIntfs(self):
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn({})
        self.m.ReplayAll()
        ips = self.driver._get_active_iscsi_ips(self.m_conn)
        self.assertEqual(len(ips), 0)
        self.m.VerifyAll()

    def testGetHostname(self):
        response = {"/system/hostname": "MYHOST"}
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn(response)
        self.m.ReplayAll()
        self.assertEqual(self.driver._get_hostname(None), "MYHOST")
        self.m.VerifyAll()

    def testGetHostname_QueryFails(self):
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn({})
        self.m.ReplayAll()
        self.assertEqual(self.driver._get_hostname(None),
                         self.driver.config.gateway_vip)
        self.m.VerifyAll()

    def testGetHostname_Mga(self):
        response = {"/system/hostname": "MYHOST"}
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn(response)
        self.m.ReplayAll()
        self.assertEqual(self.driver._get_hostname('mga'), "MYHOST")
        self.m.VerifyAll()

    def testGetHostName_MgaQueryFails(self):
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn({})
        self.m.ReplayAll()
        self.assertEqual(self.driver._get_hostname('mga'),
                         self.driver.config.gateway_mga)
        self.m.VerifyAll()

    def testGetHostname_Mgb(self):
        response = {"/system/hostname": "MYHOST"}
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn(response)
        self.m.ReplayAll()
        self.assertEqual(self.driver._get_hostname('mgb'), "MYHOST")
        self.m.VerifyAll()

    def testGetHostName_MgbQueryFails(self):
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn({})
        self.m.ReplayAll()
        self.assertEqual(self.driver._get_hostname('mgb'),
                         self.driver.config.gateway_mgb)
        self.m.VerifyAll()
