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
Violin Memory tests for FCP driver

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

# TODO(rdl): import and use test utils (cinder.tests.utils)
from cinder import exception
from cinder.db.sqlalchemy import models
from cinder.volume.drivers.violin import vxg
from cinder.volume.drivers.violin.vxg.core.node import XGNode
from cinder.volume.drivers.violin.vxg.core.session import XGSession
from cinder.volume.drivers.violin.vxg.vshare.igroup import IGroupManager
from cinder.volume.drivers.violin.vxg.vshare.iscsi import ISCSIManager
from cinder.volume.drivers.violin.vxg.vshare.lun import LUNManager
from cinder.volume.drivers.violin.vxg.vshare.snapshot import SnapshotManager
from cinder.volume.drivers.violin.vxg.vshare.vshare import VShare

from cinder.volume import configuration as conf
from cinder.volume.drivers.violin import violin_fc as violin


class testViolinFC(unittest.TestCase):
    """
    A test class for the violin Fibrechannel driver module.
    """
    def setUp(self):
        self.m = mox.Mox()
        self.m_conn = self.m.CreateMock(VShare)
        self.m_conn.basic = self.m.CreateMock(XGSession)
        self.m_conn.lun = self.m.CreateMock(LUNManager)
        self.m_conn.iscsi = self.m.CreateMock(ISCSIManager)
        self.m_conn.igroup = self.m.CreateMock(IGroupManager)
        self.m_conn.snapshot = self.m.CreateMock(SnapshotManager)
        self.config = mox.MockObject(conf.Configuration)
        self.config.append_config_values(mox.IgnoreArg())
        self.config.gateway_vip = '1.1.1.1'
        self.config.gateway_mga = '2.2.2.2'
        self.config.gateway_mgb = '3.3.3.3'
        self.config.gateway_user = 'admin'
        self.config.gateway_password = ''
        self.config.gateway_fcp_igroup_name = 'openstack'
        self.driver = violin.ViolinFCDriver(configuration=self.config)
        self.driver.vmem_vip = self.m_conn
        self.driver.vmem_mga = self.m_conn
        self.driver.vmem_mgb = self.m_conn
        self.driver.container = 'myContainer'
        self.driver.device_id = 'ata-VIOLIN_MEMORY_ARRAY_23109R00000022'
        self.stats = {}
        self.driver.gateway_fc_wwns = ['wwn.21:00:00:24:ff:45:fb:22',
                                       'wwn.21:00:00:24:ff:45:fb:23',
                                       'wwn.21:00:00:24:ff:45:f1:be',
                                       'wwn.21:00:00:24:ff:45:f1:bf',
                                       'wwn.21:00:00:24:ff:45:e2:30',
                                       'wwn.21:00:00:24:ff:45:e2:31',
                                       'wwn.21:00:00:24:ff:45:e2:5e',
                                       'wwn.21:00:00:24:ff:45:e2:5f']
        self.volume1 = mox.MockObject(models.Volume)
        self.volume1.name = 'vol-01'
        self.volume1.size = 1
        self.volume2 = mox.MockObject(models.Volume)
        self.volume2.name = 'vol-02'
        self.volume2.size = 2
        self.snapshot1 = mox.MockObject(models.Snapshot)
        self.snapshot1.name = 'snap-01'
        self.snapshot1.snapshot_id = 1
        self.snapshot1.volume_id = 1
        self.snapshot1.volume_name = 'vol-01'
        self.snapshot2 = mox.MockObject(models.Snapshot)
        self.snapshot2.name = 'snap-02'
        self.snapshot2.snapshot_id = 2
        self.snapshot2.volume_id = 2
        self.snapshot2.volume_name = 'vol-02'

    def tearDown(self):
        self.m.UnsetStubs()

    def testSetup(self):
        emptyContext = []
        self.driver.vmem_vip = None
        self.driver.vmem_mga = None
        self.driver.vmem_mgb = None
        self.driver.container = ""
        self.driver.device_id = ""
        self.driver.array_info = []
        self.m.StubOutWithMock(vxg, 'open')
        self.m.StubOutWithMock(self.driver, '_get_active_fc_targets')
        vxg.open(mox.IsA(str), mox.IsA(str),
                 mox.IsA(str)).AndReturn(self.m_conn)
        vxg.open(mox.IsA(str), mox.IsA(str),
                 mox.IsA(str)).AndReturn(self.m_conn)
        vxg.open(mox.IsA(str), mox.IsA(str),
                 mox.IsA(str)).AndReturn(self.m_conn)
        self.m_conn.basic.get_node_values(mox.IsA(str))
        self.m_conn.basic.get_node_values(mox.IsA(str))
        self.m_conn.basic.get_node_values(mox.IsA(str))
        self.driver._get_active_fc_targets()
        self.m.ReplayAll()
        self.assertTrue(self.driver.do_setup(emptyContext) is None)
        self.m.VerifyAll()

    def testCheckForSetupError(self):
        bn_igroup = {"/vshare/config/igroup/openstack": "openstack"}
        self.m_conn.basic.get_node_values(mox.IsA(str)
                                          ).AndReturn(bn_igroup)
        self.m.ReplayAll()
        self.assertTrue(self.driver.check_for_setup_error() is None)
        self.m.VerifyAll()

    def testCheckForSetupError_NoContainer(self):
        '''container name is empty '''
        self.driver.container = ""
        self.assertRaises(violin.InvalidBackendConfig,
                          self.driver.check_for_setup_error)

    def testCheckForSetupError_NoDeviceId(self):
        '''device id is empty '''
        self.driver.device_id = ""
        self.assertRaises(violin.InvalidBackendConfig,
                          self.driver.check_for_setup_error)

    def testCheckForSetupError_NoIgroupConfig(self):
        '''igroup config binding is empty '''
        self.m_conn.basic.get_node_values(mox.IsA(str)).AndReturn({})
        self.m.ReplayAll()
        self.assertRaises(violin.InvalidBackendConfig,
                          self.driver.check_for_setup_error)
        self.m.VerifyAll()

    def testCheckForSetupError_NoWWNConfig(self):
        '''no wwns were found during setup '''
        bn_igroup = {"/vshare/config/igroup/openstack": "openstack"}
        self.driver.gateway_fc_wwns = []
        self.m_conn.basic.get_node_values(mox.IsA(str)
                                          ).AndReturn(bn_igroup)
        self.m.ReplayAll()
        self.assertRaises(violin.InvalidBackendConfig,
                          self.driver.check_for_setup_error)
        self.m.VerifyAll()

    def testCreateVolume(self):
        volume = self.volume1
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_create_lun')
        self.driver._login()
        self.driver._create_lun(volume)
        self.m.ReplayAll()
        self.assertTrue(self.driver.create_volume(volume) is None)
        self.m.VerifyAll()

    def testDeleteVolume(self):
        volume = self.volume1
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_delete_lun')
        self.driver._login()
        self.driver._delete_lun(volume)
        self.m.ReplayAll()
        self.assertTrue(self.driver.delete_volume(volume) is None)
        self.m.VerifyAll()

    #def testCreateVolumeFromSnapshot(self):
    #    src_snap = self.snapshot1
    #    dest_vol = self.volume2
    #    self.m.StubOutWithMock(self.driver, '_login')
    #    self.m.StubOutWithMock(self.driver, '_create_lun')
    #    self.m.StubOutWithMock(self.driver, 'copy_volume_data')
    #    self.driver._login()
    #    self.driver._create_lun(dest_vol)
    #    self.driver.copy_volume_data(self.driver.context, dest_vol, src_snap)
    #    self.m.ReplayAll()
    #    self.assertTrue(self.driver.create_volume_from_snapshot
    #                    (dest_vol, src_snap) is None)
    #    self.m.VerifyAll()

    def testCreateClonedVolume(self):
        src_vol = self.volume1
        dest_vol = self.volume2
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_create_lun')
        self.m.StubOutWithMock(self.driver, 'copy_volume_data')
        self.driver._login()
        self.driver._create_lun(dest_vol)
        self.driver.copy_volume_data(self.driver.context, src_vol, dest_vol)
        self.m.ReplayAll()
        self.assertTrue(self.driver.create_cloned_volume
                        (src_vol, dest_vol) is None)
        self.m.VerifyAll()

    def testCreateSnapshot(self):
        snapshot = self.snapshot1
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_create_lun_snapshot')
        self.driver._login()
        self.driver._create_lun_snapshot(snapshot)
        self.m.ReplayAll()
        self.assertTrue(self.driver.create_snapshot(snapshot) is None)
        self.m.VerifyAll()

    def testDeleteSnapshot(self):
        snapshot = self.snapshot1
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_delete_lun_snapshot')
        self.driver._login()
        self.driver._delete_lun_snapshot(snapshot)
        self.m.ReplayAll()
        self.assertTrue(self.driver.delete_snapshot(snapshot) is None)
        self.m.VerifyAll()

    def testEnsureExport(self):
        # nothing to test here
        #
        pass

    def testCreateExport(self):
        # nothing to test here
        #
        pass

    def testRemoveExport(self):
        # nothing to test here
        #
        pass

    def testInitializeConnection(self):
        lun_id = 1
        vol = self.volume1
        connector = {'wwpns': [u'50014380186b3f65', u'50014380186b3f67']}
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_export_lun')
        self.m.StubOutWithMock(self.driver, '_add_igroup_member')
        self.driver._login()
        self.driver._export_lun(vol).AndReturn(lun_id)
        self.driver._add_igroup_member(connector)
        self.m_conn.basic.save_config()
        self.m.ReplayAll()
        props = self.driver.initialize_connection(vol, connector)
        self.assertEqual(props['driver_volume_type'], "fibre_channel")
        self.assertEqual(props['data']['target_discovered'], True)
        self.assertEqual(props['data']['target_wwn'],
                         self.driver.gateway_fc_wwns)
        self.assertEqual(props['data']['target_lun'], lun_id)
        self.m.VerifyAll()

    def testInitializeConnection_SnapshotObject(self):
        lun_id = 1
        connector = {'wwpns': [u'50014380186b3f65', u'50014380186b3f67']}
        snap = self.snapshot1
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_export_snapshot')
        self.m.StubOutWithMock(self.driver, '_add_igroup_member')
        self.driver._login()
        self.driver._export_snapshot(snap).AndReturn(lun_id)
        self.driver._add_igroup_member(connector)
        self.m_conn.basic.save_config()
        self.m.ReplayAll()
        props = self.driver.initialize_connection(snap, connector)
        self.assertEqual(props['driver_volume_type'], "fibre_channel")
        self.assertEqual(props['data']['target_discovered'], True)
        self.assertEqual(props['data']['target_wwn'],
                         self.driver.gateway_fc_wwns)
        self.assertEqual(props['data']['target_lun'], lun_id)
        self.m.VerifyAll()

    def testTerminateConnection(self):
        volume = self.volume1
        connector = {'wwpns': [u'50014380186b3f65', u'50014380186b3f67']}
        lun = 1
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_unexport_lun')
        self.driver._login()
        self.driver._unexport_lun(volume)
        self.m_conn.basic.save_config()
        self.m.ReplayAll()
        self.driver.terminate_connection(volume, connector)
        self.m.VerifyAll()

    def testTerminateConnection_SnapshotObject(self):
        snap = self.snapshot1
        connector = {'wwpns': [u'50014380186b3f65', u'50014380186b3f67']}
        lun = 1
        self.m.StubOutWithMock(self.driver, '_login')
        self.m.StubOutWithMock(self.driver, '_unexport_snapshot')
        self.driver._login()
        self.driver._unexport_snapshot(snap)
        self.m_conn.basic.save_config()
        self.m.ReplayAll()
        self.driver.terminate_connection(snap, connector)
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
                              mox.IsA(str),
                              self.driver.container, volume['name'],
                              volume['size'], 1, "0", "0", "w", 1,
                              512).AndReturn(response)
        self.m.ReplayAll()
        self.assertTrue(self.driver._create_lun(volume) is None)
        self.m.VerifyAll()

    def testDeleteLun(self):
        volume = {'name': 'vol-01', 'size': '1'}
        response = {'code': 0, 'message': 'LUN deletion started'}
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.driver._send_cmd(self.m_conn.lun.bulk_delete_luns,
                              mox.IsA(str),
                              mox.IsA(str),
                              self.driver.container,
                              volume['name']).AndReturn(response)
        self.m.ReplayAll()
        self.assertTrue(self.driver._delete_lun(volume) is None)
        self.m.VerifyAll()

    def testCreateLunSnapshot(self):
        snapshot = {'snapshot_id': 1, 'volume_id': 1,
                    'volume_name': 'vol-01', 'name': 'snap-01'}
        response = {'code': 0, 'message': 'success'}
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.driver._send_cmd(self.m_conn.snapshot.create_lun_snapshot,
                              mox.IsA(str),
                              mox.IsA(str),
                              self.driver.container,
                              snapshot['volume_name'],
                              snapshot['name']).AndReturn(response)
        self.m.ReplayAll()
        self.assertTrue(self.driver._create_lun_snapshot(snapshot) is None)
        self.m.VerifyAll()

    def testDeleteLunSnapshot(self):
        snapshot = self.snapshot1
        response = {'code': 0, 'message': 'success'}
        self.m.StubOutWithMock(self.driver, '_send_cmd')
        self.driver._send_cmd(self.m_conn.snapshot.delete_lun_snapshot,
                              mox.IsA(str),
                              mox.IsA(str),
                              self.driver.container,
                              snapshot['volume_name'],
                              snapshot['name']).AndReturn(response)
        self.m.ReplayAll()
        self.assertTrue(self.driver._delete_lun_snapshot(snapshot) is None)
        self.m.VerifyAll()

    def testExportLun(self):
        volume = self.volume1
        lun_id = 1
        response = {'code': 0, 'message': 'success'}
        self.m.StubOutWithMock(self.driver, '_wait_for_exportstate')
        self.m.StubOutWithMock(self.driver, '_get_lun_id')
        self.m_conn.lun.export_lun(self.driver.container, volume['name'],
                                   'all', self.config.gateway_fcp_igroup_name,
                                   'auto').AndReturn(response)
        self.driver._wait_for_exportstate(volume['name'], True)
        self.driver._get_lun_id(volume['name']).AndReturn(lun_id)
        self.m.ReplayAll()
        self.assertEqual(self.driver._export_lun(volume), lun_id)
        self.m.VerifyAll()

    def testUnexportLun(self):
        volume = self.volume1
        lun_id = 1
        response = {'code': 0, 'message': 'success'}
        self.m.StubOutWithMock(self.driver, '_wait_for_exportstate')
        self.m_conn.lun.unexport_lun(self.driver.container, volume['name'],
                                     'all', 'all', 'auto').AndReturn(response)
        self.driver._wait_for_exportstate(volume['name'], False)
        self.m.ReplayAll()
        self.assertTrue(self.driver._unexport_lun(volume) is None)
        self.m.VerifyAll()

    def testAddIgroupMember(self):
        connector = {'wwpns': [u'50014380186b3f65', u'50014380186b3f67']}
        wwpns = ['wwn.50:01:43:80:18:6b:3f:65', 'wwn.50:01:43:80:18:6b:3f:67']
        response = {'code': 0, 'message': 'success'}
        self.m.StubOutWithMock(self.driver, '_convert_wwns_openstack_to_vmem')
        self.driver._convert_wwns_openstack_to_vmem(
            connector['wwpns']).AndReturn(wwpns)
        self.m_conn.igroup.add_initiators(mox.IsA(str),
                                          wwpns).AndReturn(response)
        self.m.ReplayAll()
        self.assertTrue(self.driver._add_igroup_member(connector) is None)
        self.m.VerifyAll()

    def testUpdateStats(self):
        alloc_bytes = 0
        backend_string = "V6000"
        vendor_string = "Violin Memory, Inc."
        tot_bytes = 100 * 1024 * 1024 * 1024
        bn1 = "/vshare/state/global/1/container/myContainer/total_bytes"
        bn2 = "/vshare/state/global/1/container/myContainer/alloc_bytes"
        bn3 = "/media/state/array/myContainer/chassis/system/type"
        bn4 = "/hwinfo/state/system_mfr"
        response = {
            bn1: tot_bytes,
            bn2: alloc_bytes,
            bn3: backend_string,
            bn4: vendor_string}
        self.m_conn.basic.get_node_values([bn1, bn2, bn3, bn4]
                                          ).AndReturn(response)
        self.m.ReplayAll()
        self.assertTrue(self.driver._update_stats() is None)
        self.assertEqual(self.driver.stats['total_capacity_gb'], 100)
        self.assertEqual(self.driver.stats['free_capacity_gb'], 100)
        self.assertEqual(self.driver.stats['volume_backend_name'],
                         backend_string)
        self.assertEqual(self.driver.stats['vendor_name'], vendor_string)
        self.m.VerifyAll()

    def testUpdateStats_DataQueryFails(self):
        bn1 = "/vshare/state/global/1/container/myContainer/total_bytes"
        bn2 = "/vshare/state/global/1/container/myContainer/alloc_bytes"
        bn3 = "/media/state/array/myContainer/chassis/system/type"
        bn4 = "/hwinfo/state/system_mfr"
        self.m_conn.basic.get_node_values([bn1, bn2, bn3, bn4]).AndReturn({})
        self.m.ReplayAll()
        self.assertTrue(self.driver._update_stats() is None)
        self.assertEqual(self.driver.stats['total_capacity_gb'], "unknown")
        self.assertEqual(self.driver.stats['free_capacity_gb'], "unknown")
        self.assertEqual(self.driver.stats['volume_backend_name'], "unknown")
        self.assertEqual(self.driver.stats['vendor_name'], "Violin")
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

    def testSendCmd(self):
        request_func = self.m.CreateMockAnything()
        success_msg = 'success'
        exception_msg = 'failed'
        request_args = ['arg1', 'arg2', 'arg3']
        response = {'code': 0, 'message': 'success'}
        self.m.StubOutWithMock(time, 'sleep')
        time.sleep(mox.IsA(int))
        request_func(request_args).AndReturn(response)
        self.m.ReplayAll()
        self.assertEqual(self.driver._send_cmd
                         (request_func, success_msg,
                          exception_msg, request_args),
                         response)
        self.m.VerifyAll()

    def testSendCmd_RequestTimedout(self):
        ''' the retry timeout is hit '''
        request_func = self.m.CreateMockAnything()
        success_msg = 'success'
        exception_msg = 'failed'
        request_args = ['arg1', 'arg2', 'arg3']
        self.driver.request_timeout = 0
        self.m.ReplayAll()
        self.assertRaises(violin.RequestRetryTimeout,
                          self.driver._send_cmd,
                          request_func, success_msg,
                          exception_msg, request_args)
        self.m.VerifyAll()

    def testSendCmd_ResponseHasNoMessage(self):
        ''' the callback response dict has a NULL message field '''
        request_func = self.m.CreateMockAnything()
        success_msg = 'success'
        exception_msg = 'failed'
        request_args = ['arg1', 'arg2', 'arg3']
        response1 = {'code': 0, 'message': None}
        response2 = {'code': 0, 'message': 'success'}
        self.m.StubOutWithMock(time, 'sleep')
        time.sleep(mox.IsA(int))
        request_func(request_args).AndReturn(response1)
        time.sleep(mox.IsA(int))
        request_func(request_args).AndReturn(response2)
        self.m.ReplayAll()
        self.assertEqual(self.driver._send_cmd
                         (request_func, success_msg,
                          exception_msg, request_args),
                         response2)
        self.m.VerifyAll()

    def testSendCmd_ResponseHasFatalError(self):
        ''' the callback response dict contains a fatal error code '''
        request_func = self.m.CreateMockAnything()
        success_msg = 'success'
        exception_msg = 'failed'
        request_args = ['arg1', 'arg2', 'arg3']
        response = {'code': 14000, 'message': 'try again later.'}
        self.m.StubOutWithMock(time, 'sleep')
        time.sleep(mox.IsA(int))
        request_func(request_args).AndReturn(response)
        self.m.ReplayAll()
        self.assertRaises(exception.Error,
                          self.driver._send_cmd,
                          request_func, success_msg,
                          exception_msg, request_args)
        self.m.VerifyAll()

    def testGetLunID(self):
        volume = {'name': 'vol-01', 'size': '1'}
        bn = '/vshare/config/export/container/myContainer/lun/vol-01/target/**'
        resp = {'/vshare/config/export/container/myContainer/lun'
                '/vol-01/target/hba-a1/initiator/openstack/lun_id' : 1}
        self.m_conn.basic.get_node_values(bn).AndReturn(resp)
        self.m.ReplayAll()
        self.assertEqual(self.driver._get_lun_id(volume['name']), 1)
        self.m.VerifyAll()

    def testWaitForExportState(self):
        bn = '/vshare/config/export/container/myContainer/lun/vol-01'
        resp = {'/vshare/config/export/container/myContainer/lun/vol-01': 'vol-01'}
        self.m_conn.basic.get_node_values(bn).AndReturn(resp)
        self.m.ReplayAll()
        self.assertEqual(self.driver._wait_for_exportstate('vol-01', True), True)
        self.m.VerifyAll()

    def testGetActiveFcTargets(self):
        bn1 = '/vshare/state/global/*'
        resp1 = {'/vshare/state/global/1' : 1, '/vshare/state/global/2' : 2}
        bn2 = '/vshare/state/global/2/target/fc/**'
        resp2 = {'/vshare/state/global/2/target/fc/hba-a1/wwn' : 'wwn.21:00:00:24:ff:45:fb:22'}
        bn3 = '/vshare/state/global/1/target/fc/**'
        resp3 = {'/vshare/state/global/1/target/fc/hba-a1/wwn' : 'wwn.21:00:00:24:ff:45:e2:30'}
        self.m_conn.basic.get_node_values(bn1).AndReturn(resp1)
        self.m_conn.basic.get_node_values(bn2).AndReturn(resp2)
        self.m_conn.basic.get_node_values(bn3).AndReturn(resp3)
        result = ['21000024ff45fb22', '21000024ff45e230']
        self.m.ReplayAll()
        self.assertEqual(self.driver._get_active_fc_targets(), result)
        self.m.VerifyAll()

    def testConvertWWNsOpenstackToVMEM(self):
        vmem_wwns = ['wwn.50:01:43:80:18:6b:3f:65']
        openstack_wwns = ['50014380186b3f65']
        result = self.driver._convert_wwns_openstack_to_vmem(openstack_wwns)
        self.assertEqual(result, vmem_wwns)

    def testsConvertWWNsVMEMToOpenstack(self):
        vmem_wwns = ['wwn.50:01:43:80:18:6b:3f:65']
        openstack_wwns = ['50014380186b3f65']
        result = self.driver._convert_wwns_vmem_to_openstack(vmem_wwns)
        self.assertEqual(result, openstack_wwns)

    def testFatalErrorCode(self):
        # NYI
        #
        pass
