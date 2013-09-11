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

class SnapshotManager_3(SnapshotManager_2):
    def __init__(self, basic):
        super(SnapshotManager_3, self).__init__(basic)

    def new_function(self, *args):
        pass

"""


class SnapshotManager(object):
    def __init__(self, basic):
        self._basic = basic

    def rollback_lun(self, container, lun, name):
        """
        Rollback a LUN to the specified snapshot.

        Arguments:
            container -- string
            lun       -- string
            name      -- string

        Returns:
            Action result as a dict.

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('lun', 'string', lun))
        nodes.append(XGNode('name', 'string', name))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/snapshot/rollback', nodes)

    def rollback_lun_group(self, container, lungroup, name):
        """
        Rollback a LUN group to the specified snapshot.

        Arguments:
            container -- string
            lungroup -- string
            name      -- string

        Returns:
            Action result as a dict.

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('lungroup', 'string', lungroup))
        nodes.append(XGNode('name', 'string', name))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/snapgroup/rollback', nodes)

    def create_lun_group_snapshot(self, container, lungroup, name,
                                  description=None, readwrite=None,
                                  snap_protect=None):
        """
        Creates a LUN group snapshot.

        Arguments:
            container    -- string
            lungroup     -- string
            name         -- string
            description  -- string (optional)
            readwrite    -- bool (optional)
            snap_protect -- bool (optional)

        Returns:
            Action result as a dict.

        """
        return self._snapgroup_create(container, lungroup, name, 'create',
                                      description, readwrite, snap_protect)

    def delete_lun_group_snapshot(self, container, lungroup, name):
        """
        Deletes a LUN group snapshot.

        Arguments:
            container    -- string
            lungroup     -- string
            name         -- string

        Returns:
            Action result as a dict.

        """
        return self._snapgroup_create(container, lungroup, name, 'delete',
                                      None, None, None)

    def _snapgroup_create(self, container, lungroup, name, action,
                          description, readwrite, snap_protect):
        """
        Internal work function for:
            create_lun_group_snapshot
            delete_lun_group_snapshot

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('lungroup', 'string', lungroup))
        nodes.append(XGNode('name', 'string', name))
        nodes.append(XGNode('action', 'string', action))
        if description is not None:
            nodes.append(XGNode('description', 'string', description))
        if readwrite is not None:
            nodes.append(XGNode('readwrite', 'bool', readwrite))
        if snap_protect is not None:
            nodes.append(XGNode('snap_protect', 'bool', snap_protect))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/snapgroup/create', nodes)

    def export_lun_group_snapshot(self, container, lungroup, name,
                                  initiators=None, ports=None):
        """
        Export a LUN group snapshot.

        Arguments:
            container  -- string
            lungroup   -- string
            name       -- string
            initiators -- string (string or list)
            ports      -- string (string or list)

        Returns:
            Action result as a dict.

        """
        return self._snapgroup_export(container, lungroup, name,
                                      initiators, ports, False)

    def unexport_lun_group_snapshot(self, container, lungroup, name,
                                    initiators=None, ports=None):
        """
        Unexport a LUN group snapshot.

        Arguments:
            container  -- string
            lungroup   -- string
            name       -- string
            initiators -- string (string or list)
            ports      -- string (string or list)

        Returns:
            Action result as a dict.

        """
        return self._snapgroup_export(container, lungroup, name,
                                      initiators, ports, True)

    def _snapgroup_export(self, container, lungroup, name,
                          initiators, ports, unexport):
        """
        Internal work function for:
            export_lun_group_snapshot
            unexport_lun_group_snapshot

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('lungroup', 'string', lungroup))
        nodes.append(XGNode('name', 'string', name))
        nodes.extend(XGNode.as_node_list('initiators/{0}', 'string',
                                         initiators))
        nodes.extend(XGNode.as_node_list('ports/{0}', 'string', ports))
        nodes.append(XGNode('unexport', 'bool', unexport))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/snapgroup/export', nodes)

    def set_lun_group_snapshot(self, container, lungroup, name,
                               new_name=None, description=None,
                               readwrite=None, snap_protect=None):
        """
        Update a LUN group snapshot.

        Arguments:
            container    -- string
            lungroup     -- string
            name         -- string
            new_name     -- string (optional)
            description  -- string (optional)
            readwrite    -- bool (optional)
            snap_protect -- bool (optional)

        Returns:
            Action result as a dict.

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('lungroup', 'string', lungroup))
        nodes.append(XGNode('name', 'string', name))
        if new_name is not None:
            nodes.append(XGNode('new_name', 'string', new_name))
        if description is not None:
            nodes.append(XGNode('description', 'string', description))
        if readwrite is not None:
            nodes.append(XGNode('readwrite', 'bool', readwrite))
        if snap_protect is not None:
            nodes.append(XGNode('snap_protect', 'bool', snap_protect))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/snapgroup/update', nodes)

    def create_lun_snapshot(self, container, lun, name, description=None,
                            readwrite=None, snap_protect=None):
        """
        Create a LUN snapshot.

        Arguments:
            container    -- string
            lun          -- string
            name         -- string
            description  -- string (optional)
            readwrite    -- bool (optional)
            snap_protect -- bool (optional)

        Returns:
            Action result as a dict.

        """
        return self._snapshot_create(container, lun, name, 'create',
                                     description, readwrite, snap_protect)

    def delete_lun_snapshot(self, container, lun, name):
        """
        Delete a LUN snapshot.

        Arguments:
            container -- string
            lun       -- string
            name      -- string

        Returns:
            Action result as a dict.

        """
        return self._snapshot_create(container, lun, name,
                                     'delete', None, None, None)

    def _snapshot_create(self, container, lun, name, action,
                         description, readwrite, snap_protect):
        """
        Internal work function for:
            create_lun_snapshot
            delete_lun_snapshot

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('lun', 'string', lun))
        nodes.append(XGNode('name', 'string', name))
        nodes.append(XGNode('action', 'string', action))
        if description is not None:
            nodes.append(XGNode('description', 'string', description))
        if readwrite is not None:
            nodes.append(XGNode('readwrite', 'bool', readwrite))
        if snap_protect is not None:
            nodes.append(XGNode('snap_protect', 'bool', snap_protect))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/snapshot/create', nodes)

    def set_lun_snapshot(self, container, lun, name, new_name=None,
                         description=None, readwrite=None, snap_protect=None,
                         port_A=None, port_B=None):
        """
        Update a LUN snapshot.

        Arguments:
            container    -- string
            lun          -- string
            name         -- string
            new_name     -- string (optional)
            description  -- string (optional)
            readwrite    -- bool (optional)
            snap_protect -- bool (optional)
            port_A       -- bool (optional)
            port_B       -- bool (optional)

        Returns:
            Action result as a dict.

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('lun', 'string', lun))
        nodes.append(XGNode('name', 'string', name))
        if new_name is not None:
            nodes.append(XGNode('new_name', 'string', new_name))
        if description is not None:
            nodes.append(XGNode('description', 'string', description))
        if readwrite is not None:
            nodes.append(XGNode('readwrite', 'bool', readwrite))
        if snap_protect is not None:
            nodes.append(XGNode('snap_protect', 'bool', snap_protect))
        if port_A is not None:
            nodes.append(XGNode('port_A', 'bool', port_A))
        if port_B is not None:
            nodes.append(XGNode('port_B', 'bool', port_B))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/snapshot/set', nodes)

    def export_lun_snapshot(self, container, lun, names, initiators,
                            ports, lun_id):
        """
        Export a snapshot.

        Arguments:
            container  -- string
            lun        -- string
            names      -- string (string or list)
            initiators -- string (string or list)
            ports      -- string (string or list)
            lun_id     -- string

        Returns:
            Action result as a dict.

        """
        return self._snapshot_export(container, lun, names, initiators,
                                     ports, lun_id, False, None)

    def unexport_lun_snapshot(self, container, lun, names, initiators,
                              ports, lun_id, force):
        """
        Unexport a snapshot.

        Arguments:
            container  -- string
            lun        -- string
            names      -- string (string or list)
            initiators -- string (string or list)
            ports      -- string (string or list)
            lun_id     -- string
            force      -- bool (optional)

        Returns:
            Action result as a dict.

        """
        return self._snapshot_export(container, lun, names, initiators,
                                     ports, lun_id, True, force)

    def _snapshot_export(self, container, lun, names, initiators,
                         ports, lun_id, unexport, force):
        """
        Internal work function for:
            export_lun_snapshot
            unexport_lun_snapshot

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('lun', 'string', lun))
        nodes.extend(XGNode.as_node_list('names/{0}', 'string', names))
        nodes.extend(XGNode.as_node_list('initiators/{0}', 'string',
                                         initiators))
        nodes.extend(XGNode.as_node_list('ports/{0}', 'string', ports))
        nodes.append(XGNode('lun_id', 'string', lun_id))
        nodes.append(XGNode('unexport', 'bool', unexport))
        if force is not None:
            nodes.append(XGNode('force', 'bool', force))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/snapshot/export', nodes)

    def create_snapshot_schedule(self, container, schedule_name, type,
                                 is_lungroup_schedule, lun_or_group_name,
                                 description=None, date=None, time=None,
                                 start_date=None, start_time=None,
                                 end_date=None, end_time=None,
                                 periodicity=None, days_of_week=None,
                                 monthly_interval=None, day_of_month=None,
                                 readwrite=None, protected=None,
                                 max_keep=None, disabled=None):
        """
        Create a snapshot schedule.

        Arguments:
            container            -- string
            schedule_name        -- string
            type                 -- string
            is_lungroup_schedule -- bool
            lun_or_group_name    -- string
            description          -- string (optional)
            date                 -- date (string or datetime; optional)
            time                 -- time_sec (string or datetime; optional)
            start_date           -- date (string or datetime; optional)
            start_time           -- time_sec (string or datetime; optional)
            end_date             -- date (string or datetime; optional)
            end_time             -- time_sec (string or datetime; optional)
            periodicity          -- duration_sec (string; optional)
            days_of_week         -- string (optional)
            monthly_interval     -- uint32 (optional)
            day_of_month         -- int32 (optional)
            readwrite            -- bool (optional)
            protected            -- bool (optional)
            max_keep             -- int32 (optional)
            disabled             -- bool (optional)

        Returns:
            Action result as a dict.

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('schedule_name', 'string', schedule_name))
        nodes.append(XGNode('type', 'string', type))
        nodes.append(XGNode('is_lungroup_schedule', 'bool',
                            is_lungroup_schedule))
        nodes.append(XGNode('lun_or_group_name', 'string', lun_or_group_name))
        if description is not None:
            nodes.append(XGNode('description', 'string', description))
        if date is not None:
            nodes.append(XGNode('date', 'date', date))
        if time is not None:
            nodes.append(XGNode('time', 'time_sec', time))
        if start_date is not None:
            nodes.append(XGNode('start_date', 'date', start_date))
        if start_time is not None:
            nodes.append(XGNode('start_time', 'time_sec', start_time))
        if end_date is not None:
            nodes.append(XGNode('end_date', 'date', end_date))
        if end_time is not None:
            nodes.append(XGNode('end_time', 'time_sec', end_time))
        if periodicity is not None:
            nodes.append(XGNode('periodicity', 'duration_sec', periodicity))
        if days_of_week is not None:
            nodes.append(XGNode('days_of_week', 'string', days_of_week))
        if monthly_interval is not None:
            nodes.append(XGNode('monthly_interval', 'uint32',
                                monthly_interval))
        if day_of_month is not None:
            nodes.append(XGNode('day_of_month', 'int32', day_of_month))
        if readwrite is not None:
            nodes.append(XGNode('readwrite', 'bool', readwrite))
        if protected is not None:
            nodes.append(XGNode('protected', 'bool', protected))
        if max_keep is not None:
            nodes.append(XGNode('max_keep', 'int32', max_keep))
        if disabled is not None:
            nodes.append(XGNode('disabled', 'bool', disabled))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/schedule/snapshot/create', nodes)

    def modify_snapshot_schedule(self, container, schedule_name, type,
                                 is_lungroup_schedule, lun_or_group_name,
                                 new_schedule_name=None, description=None,
                                 date=None, time=None,
                                 start_date=None, start_time=None,
                                 end_date=None, end_time=None,
                                 periodicity=None, days_of_week=None,
                                 monthly_interval=None, day_of_month=None,
                                 readwrite=None, protect=None,
                                 max_keep=None, enable=None):
        """
        Modify a snapshot schedule.

        Arguments:
            container            -- string
            schedule_name        -- string
            type                 -- string
            is_lungroup_schedule -- bool
            lun_or_group_name    -- string
            new_schedule_name    -- string (optional)
            description          -- string (optional)
            date                 -- date (string or datetime; optional)
            time                 -- time_sec (string or datetime; optional)
            start_date           -- date (string or datetime; optional)
            start_time           -- time_sec (string or datetime; optional)
            end_date             -- date (string or datetime; optional)
            end_time             -- time_sec (string or datetime; optional)
            periodicity          -- duration_sec (string; optional)
            days_of_week         -- string (optional)
            monthly_interval     -- uint32 (optional)
            day_of_month         -- int32 (optional)
            readwrite            -- bool (optional)
            protect              -- bool (optional)
            max_keep             -- int32 (optional)
            enable               -- bool (optional)

        Returns:
            Action result as a dict.

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        nodes.append(XGNode('schedule_name', 'string', schedule_name))
        nodes.append(XGNode('type', 'string', type))
        nodes.append(XGNode('is_lungroup_schedule', 'bool',
                            is_lungroup_schedule))
        nodes.append(XGNode('lun_or_group_name', 'string', lun_or_group_name))
        if new_schedule_name is not None:
            nodes.append(XGNode('new_schedule_name', 'string',
                                new_schedule_name))
        if description is not None:
            nodes.append(XGNode('description', 'string', description))
        if date is not None:
            nodes.append(XGNode('date', 'date', date))
        if time is not None:
            nodes.append(XGNode('time', 'time_sec', time))
        if start_date is not None:
            nodes.append(XGNode('start_date', 'date', start_date))
        if start_time is not None:
            nodes.append(XGNode('start_time', 'time_sec', start_time))
        if end_date is not None:
            nodes.append(XGNode('end_date', 'date', end_date))
        if end_time is not None:
            nodes.append(XGNode('end_time', 'time_sec', end_time))
        if periodicity is not None:
            nodes.append(XGNode('periodicity', 'duration_sec', periodicity))
        if days_of_week is not None:
            nodes.append(XGNode('days_of_week', 'string', days_of_week))
        if monthly_interval is not None:
            nodes.append(XGNode('monthly_interval', 'uint32',
                                monthly_interval))
        if day_of_month is not None:
            nodes.append(XGNode('day_of_month', 'int32', day_of_month))
        if readwrite is not None:
            nodes.append(XGNode('readwrite', 'bool', readwrite))
        if protect is not None:
            nodes.append(XGNode('protect', 'bool', protect))
        if max_keep is not None:
            nodes.append(XGNode('max_keep', 'int32', max_keep))
        if enable is not None:
            nodes.append(XGNode('enable', 'bool', enable))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/schedule/snapshot/modify', nodes)

    def delete_snapshot_schedule(self, container, lun=None, lungroup=None,
                                 schedule_name=None, delete_snapshots=None):
        """
        Delete a snapshot schedule.

        Arguments:
            container        -- string
            lun              -- string (optional)
            lungroup         -- string (optional)
            schedule_name    -- string (optional)
            delete_snapshots -- bool (optional)

        Returns:
            Action result as a dict.

        """
        nodes = []
        nodes.append(XGNode('container', 'string', container))
        if lun is not None:
            nodes.append(XGNode('lun', 'string', lun))
        if lungroup is not None:
            nodes.append(XGNode('lungroup', 'string', lungroup))
        if schedule_name is not None:
            nodes.append(XGNode('schedule_name', 'string', schedule_name))
        if delete_snapshots is not None:
            nodes.append(XGNode('delete_snapshots', 'bool', delete_snapshots))

        return self._basic.perform_action('/vshare/actions/vdm' +
                                          '/schedule/snapshot/delete', nodes)
