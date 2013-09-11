#!/usr/bin/env python

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

from cinder.volume.drivers.violin.vxg.core.node import XGNode
from cinder.volume.drivers.violin.vxg.core.error import *
from cinder.volume.drivers.violin.vxg.core.request import XGAction
from cinder.volume.drivers.violin.vxg.core.request import XGEvent
from cinder.volume.drivers.violin.vxg.core.request import XGQuery
from cinder.volume.drivers.violin.vxg.core.request import XGSet

"""
Here's an example of how to extend the functionality in this module:

class ISCSIManager_1(ISCSIManager):
    def __init__(self, basic):
        super(ISCSIManager_1, self).__init__(basic)

    def new_function(self, *args):
        pass

"""


class ISCSIManager(object):
    def __init__(self, basic):
        self._basic = basic

    def enable_iscsi_locally(self):
        """
        Enable local node iSCSI.

        Returns:
            Action result as a dict.

        """
        return self._iscsi_local(True)

    def disable_iscsi_locally(self):
        """
        Disable local node iSCSI.

        Returns:
            Action result as a dict.

        """
        return self._iscsi_local(False)

    def enable_iscsi_globally(self):
        """
        Enable iSCSI for all nodes.

        Returns:
            Action result as a dict.

        """
        return self._iscsi_global(True)

    def disable_iscsi_globally(self):
        """
        Disable iSCSI for all nodes.

        Returns:
            Action result as a dict.

        """
        return self._iscsi_global(False)

    def create_iscsi_target(self, target):
        """
        Create an iSCSI target.

        Arguments:
            target -- string

        Returns:
            Action result as a dict.

        """
        return self._iscsi_target_create(target, True)

    def delete_iscsi_target(self, target):
        """
        Deletes an iSCSI target.

        Arguments:
            target -- string

        Returns:
            Action result as a dict.

        """
        return self._iscsi_target_create(target, False)

    def bind_ip_to_target(self, target, ip):
        """
        Binds an IP to an iSCSI target.

        Arguments:
            target -- string
            ip     -- string (string or list)

        Returns:
            Action result as a dict.

        """
        return self._iscsi_target_bind(target, ip, True)

    def unbind_ip_from_target(self, target, ip):
        """
        Unbinds an IP from an iSCSI target.

        Arguments:
            target -- string
            ip     -- string (string or list)

        Returns:
            Action result as a dict.

        """
        return self._iscsi_target_bind(target, ip, False)

    def _iscsi_local(self, enable):
        """
        Internal work function for:
            enable_iscsi_locally
            disable_iscsi_locally

        """
        nodes = []
        nodes.append(XGNode('enable', 'bool', enable))

        return self._basic.perform_action('/vshare/actions' +
                                          '/iscsi/enable_local', nodes)

    def _iscsi_global(self, enable):
        """
        Internal work function for:
            enable_iscsi_globally
            disable_iscsi_globally

        """
        nodes = []
        nodes.append(XGNode('enable', 'bool', enable))

        return self._basic.perform_action('/vshare/actions' +
                                          '/iscsi/enable_global', nodes)

    def _iscsi_target_create(self, target, create):
        """
        Internal work function for:
            create_iscsi_target
            delete_iscsi_target

        """
        nodes = []
        nodes.append(XGNode('target', 'string', target))
        nodes.append(XGNode('create', 'bool', create))

        return self._basic.perform_action('/vshare/actions' +
                                          '/iscsi/target/create', nodes)

    def _iscsi_target_bind(self, target, ip, add):
        """
        Internal work function for:
            bind_ip_to_target
            unbind_ip_from_target

        """
        nodes = []
        nodes.append(XGNode('target', 'string', target))
        nodes.extend(XGNode.as_node_list('ip/{0}', 'string', ip))
        nodes.append(XGNode('add', 'bool', add))

        return self._basic.perform_action('/vshare/actions' +
                                          '/iscsi/target/bind', nodes)
