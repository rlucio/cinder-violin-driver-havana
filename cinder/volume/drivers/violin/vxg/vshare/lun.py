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

class LUNManager_3(LUNManager_2):
    def __init__(self, basic):
        super(LUNManager_3, self).__init__(basic)

    def new_function(self, *args):
        pass

"""


class LUNManager(object):
    def __init__(self, basic):
        self._basic = basic

    def create_lun(self, container, name, size, quantity, nozero,
                   thin, readonly, startnum, blksize=None):
        """
        Create a LUN.

        Arguments:
            container -- string
            name      -- string
            size      -- string
            quantity  -- uint64
            nozero    -- string
            thin      -- string
            readonly  -- string
            startnum  -- uint64
            blksize   -- uint32 (optional)

        Returns:
            Action result as a dict.

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('name', 'string', name))
        nodes.append(XGNode('size', 'string', size))
        nodes.append(XGNode('quantity', 'uint64', quantity))
        nodes.append(XGNode('nozero', 'string', nozero))
        nodes.append(XGNode('thin', 'string', thin))
        nodes.append(XGNode('readonly', 'string', readonly))
        nodes.append(XGNode('action', 'string', 'c'))
        nodes.append(XGNode('startnum', 'uint64', startnum))
        if blksize is not None:
            nodes.append(XGNode('blksize', 'uint32', blksize))

        return self._basic.perform_action('/vshare/actions' +
                                          '/lun/create', nodes)

    def bulk_delete_luns(self, container, luns):
        """
        Delete one or more LUNs.

        Arguments:
            container -- string
            luns      -- string (string or list)

        Returns:
            Action result as a dict.

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.extend(XGNode.as_node_list('lun/{0}', 'string', luns))

        return self._basic.perform_action('/vshare/actions' +
                                          '/lun/bulk_delete', nodes)

    def export_lun(self, container, name, ports, initiators, lun_id):
        """
        Export a LUN.

        Arguments:
            container  -- string
            name       -- string
            ports      -- string
            initiators -- string
            lun_id     -- int16

        Returns:
            Action result as a dict.

        """
        return self._lun_export(container, name, ports,
                                initiators, lun_id, False)

    def unexport_lun(self, container, name, ports, initiators, lun_id):
        """
        Unexport a LUN.

        Arguments:
            container  -- string
            name       -- string
            ports      -- string
            initiators -- string
            lun_id     -- int16

        Returns:
            Action result as a dict.

        """
        return self._lun_export(container, name, ports,
                                initiators, lun_id, True)

    # Begin internal functions

    def _lun_export(self, container, name, ports,
                    initiators, lun_id, unexport):
        """
        Internal work function for:
            export_lun
            unexport_lun

        """

        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('name', 'string', name))
        nodes.append(XGNode('initiators', 'string', initiators))
        nodes.append(XGNode('ports', 'string', ports))
        if lun_id == 'auto':
            nodes.append(XGNode('lun_id', 'int16', -1))
        else:
            nodes.append(XGNode('lun_id', 'int16', lun_id))
        nodes.append(XGNode('unexport', 'bool', unexport))

        return self._basic.perform_action('/vshare/actions' +
                                          '/lun/export', nodes)


class LUNManager_1(LUNManager):
    def __init__(self, basic):
        super(LUNManager_1, self).__init__(basic)

    def export_lun(self, container, names, ports, initiators, lun_id):
        """
        Export a LUN.

        Arguments:
            container  -- string
            names      -- string (string or list)
            ports      -- string (string or list)
            initiators -- string (string or list)
            lun_id     -- int16

        Returns:
            Action result as a dict.

        """
        return self._lun_export(container, names, ports,
                                initiators, lun_id, False)

    def unexport_lun(self, container, names, ports, initiators, lun_id):
        """
        Unexport a LUN.

        Arguments:
            container  -- string
            names      -- string (string or list)
            ports      -- string (string or list)
            initiators -- string (string or list)
            lun_id     -- int16

        Returns:
            Action result as a dict.

        """
        return self._lun_export(container, names, ports,
                                initiators, lun_id, True)

    # Begin internal functions

    def _lun_export(self, container, names, ports,
                    initiators, lun_id, unexport):
        """
        Internal work function for:
            export_lun
            unexport_lun

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.extend(XGNode.as_node_list('names/{0}', 'string', names))
        nodes.extend(XGNode.as_node_list('initiators/{0}', 'string',
                                         initiators))
        nodes.extend(XGNode.as_node_list('ports/{0}', 'string', ports))
        if lun_id == 'auto':
            nodes.append(XGNode('lun_id', 'int16', -1))
        else:
            nodes.append(XGNode('lun_id', 'int16', lun_id))
        nodes.append(XGNode('unexport', 'bool', unexport))

        return self._basic.perform_action('/vshare/actions' +
                                          '/lun/export', nodes)


class LUNManager_2(LUNManager_1):
    def __init__(self, basic):
        super(LUNManager_2, self).__init__(basic)

    def set(self, container, lun, read_only, port_A, port_B):
        """
        Perform LUN modification.

        Arguments:
            container -- string
            lun       -- string
            read_only -- bool
            port_A    -- bool
            port_B    -- bool

        Returns:
            Action result as a dict.

        """

        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('lun', 'string', lun))
        nodes.append(XGNode('read_only', 'bool', read_only))
        nodes.append(XGNode('port_A', 'bool', port_A))
        nodes.append(XGNode('port_B', 'bool', port_B))

        return self._basic.perform_action('/vshare/actions' +
                                          '/lun/set', nodes)

    def rename_lun(self, container, lun_old, lun_new):
        """
        Rename a LUN.

        Arguments:
            container -- string
            lun_old   -- string
            lun_new   -- string

        Returns:
            Action result as a dict.

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('lun_old', 'string', lun_old))
        nodes.append(XGNode('lun_new', 'string', lun_new))

        return self._basic.perform_action('/vshare/actions' +
                                          '/lun/rename', nodes)


class LUNManager_3(LUNManager_2):
    def __init__(self, basic):
        super(LUNManager_3, self).__init__(basic)

    def create_lun_group(self, container, name,
                         lun_names, description=None):
        """
        Create a LUN group.

        Arguments:
            container   -- string
            name        -- string
            lun_names   -- string (string or list)
            description -- string (optional)

        Returns:
            Action result as a dict.

        """
        return self._lungroup_create(container, name, lun_names,
                                     'create', description)

    def delete_lun_group(self, container, name):
        """
        Deletes a LUN group.

        Arguments:
            container -- string
            name      -- string

        Returns:
            Action result as a dict.

        """
        return self._lungroup_create(container, name, None,
                                     'delete', None)

    def _lungroup_create(self, container, name,
                         lun_names, action, description):
        """
        Internal work function for:
            create_lun_group
            delete_lun_group

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('name', 'string', name))
        nodes.extend(XGNode.as_node_list('lun_names/{0}', 'string', lun_names))
        nodes.append(XGNode('action', 'string', action))
        if description is not None:
            nodes.append(XGNode('description', 'string', description))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/lungroup/create', nodes)

    def add_to_lun_group(self, container, name, lun_names=None,
                         new_name=None, description=None):
        """
        Update a LUN group and add LUNs.

        Arguments:
            container   -- string
            name        -- string
            lun_names   -- string (string or list, optional)
            new_name    -- string (optional)
            description -- string (optional)

        Returns:
            Action result as a dict.

        """
        return self._lungroup_update(container, name, new_name,
                                     lun_names, False, description)

    def remove_from_lun_group(self, container, name, lun_names=None,
                              new_name=None, description=None):
        """
        Update a LUN group and remove LUNs.

        Arguments:
            container   -- string
            name        -- string
            lun_names   -- string (string or list, optional)
            new_name    -- string (optional)
            description -- string

        Returns:
            Action result as a dict.

        """
        return self._lungroup_update(container, name, new_name,
                                     lun_names, True, description)

    def _lungroup_update(self, container, name, new_name,
                         lun_names, remove, description):
        """
        Internal work function for:
            add_to_lun_group
            remove_from_lun_group

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('name', 'string', name))
        if new_name is not None:
            nodes.append(XGNode('new_name', 'string', new_name))
        nodes.extend(XGNode.as_node_list('lun_names/{0}', 'string', lun_names))
        if remove is not None:
            nodes.append(XGNode('remove', 'bool', remove))
        if description is not None:
            nodes.append(XGNode('description', 'string', description))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/lungroup/update', nodes)

    def export_lun_group(self, container, name, initiators,
                         ports):
        """
        Exports a LUN group.

        Arguments:
            container  -- string
            name       -- string
            initiators -- string (string or list)
            ports      -- string (string or list)

        Returns:
            Action result as a dict.

        """
        return self._lungroup_export(container, name,
                                     initiators, ports, False)

    def unexport_lun_group(self, container, name,
                           initiators, ports):
        """
        Unexports a LUN group.

        Arguments:
            container  -- string
            name       -- string
            initiators -- string (string or list)
            ports      -- string (string or list)

        Returns:
            Action result as a dict.

        """
        return self._lungroup_export(container, name,
                                     initiators, ports, True)

    def _lungroup_export(self, container, name, initiators,
                         ports, unexport):
        """
        Internal work function for:
            export_lun_group
            unexport_lun_group

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('name', 'string', name))
        nodes.extend(XGNode.as_node_list('initiators/{0}', 'string',
                                         initiators))
        nodes.extend(XGNode.as_node_list('ports/{0}', 'string', ports))
        nodes.append(XGNode('unexport', 'bool', unexport))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/lungroup/export', nodes)

    def create_lun(self, container, name, size, quantity, nozero,
                   thin, readonly, startnum, blksize=None,
                   naca=None, alua=None, preferredport=None):
        """
        Create a LUN.

        Arguments:
            container        -- string
            name             -- string
            size             -- string
            quantity         -- uint64
            nozero           -- string
            thin             -- string
            readonly         -- string
            startnum         -- uint64
            blksize          -- uint32 (optional)
            naca             -- bool (optional)
            alua             -- bool (optional)
            preferredport    -- uint8 (optional)

        Returns:
            Action result as a dict.

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('name', 'string', name))
        nodes.append(XGNode('size', 'string', size))
        nodes.append(XGNode('quantity', 'uint64', quantity))
        nodes.append(XGNode('nozero', 'string', nozero))
        nodes.append(XGNode('thin', 'string', thin))
        nodes.append(XGNode('readonly', 'string', readonly))
        nodes.append(XGNode('action', 'string', 'c'))
        nodes.append(XGNode('startnum', 'uint64', startnum))
        if blksize is not None:
            nodes.append(XGNode('blksize', 'uint32', blksize))
        if naca is not None:
            nodes.append(XGNode('naca', 'bool', naca))
        if alua is not None:
            nodes.append(XGNode('alua', 'bool', alua))
        if preferredport is not None:
            nodes.append(XGNode('preferredport', 'uint8', preferredport))

        return self._basic.perform_action('/vshare/actions' +
                                          '/lun/create', nodes)

    def set(self, container, lun=None, read_only=None, port_A=None,
            port_B=None, devid=None, naca=None, alua=None,
            preferredport=None, encrypted=None, threshold_type=None,
            threshold_hard_val=None, threshold_soft_val=None):
        """
        Perform LUN modification.

        Arguments:
            container          -- string
            lun                -- string (optional)
            read_only          -- bool (optional)
            port_A             -- bool (optional)
            port_B             -- bool (optional)
            devid              -- string (optional)
            naca               -- bool (optional)
            alua               -- bool (optional)
            preferredport      -- uint8 (optional)
            encrypted          -- bool (optional)
            threshold_type     -- string (optional)
            threshold_hard_val -- uint32 (optional)
            threshold_soft_val -- uint32 (optional)

        Returns:
            Action result as a dict.

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        if lun is not None:
            nodes.append(XGNode('lun', 'string', lun))
        if read_only is not None:
            nodes.append(XGNode('read_only', 'bool', read_only))
        if port_A is not None:
            nodes.append(XGNode('port_A', 'bool', port_A))
        if port_B is not None:
            nodes.append(XGNode('port_B', 'bool', port_B))
        if devid is not None:
            nodes.append(XGNode('devid', 'string', devid))
        if naca is not None:
            nodes.append(XGNode('naca', 'bool', naca))
        if alua is not None:
            nodes.append(XGNode('alua', 'bool', alua))
        if preferredport is not None:
            nodes.append(XGNode('preferredport', 'uint8', preferredport))
        if encrypted is not None:
            nodes.append(XGNode('encrypted', 'bool', encrypted))
        if threshold_type is not None:
            nodes.append(XGNode('threshold_type', 'string', threshold_type))
        if threshold_hard_val is not None:
            nodes.append(XGNode('threshold_hard_val', 'uint32',
                                threshold_hard_val))
        if threshold_soft_val is not None:
            nodes.append(XGNode('threshold_soft_val', 'uint32',
                                threshold_soft_val))

        return self._basic.perform_action('/vshare/actions' +
                                          '/lun/set', nodes)
