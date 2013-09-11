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

class IGroupManager_1(IGroupManager):
    def __init__(self, basic):
        super(IGroupManager_1, self).__init__(basic)

    def new_function(self, *args):
        pass

"""


class IGroupManager(object):
    def __init__(self, basic):
        self._basic = basic

    def create_igroup(self, igroup):
        """
        Create an igroup.

        Arguments:
            igroup -- string

        Returns:
            Action result as a dict.

        """
        return self._igroup_create(igroup, False)

    def delete_igroup(self, igroup):
        """
        Deletes an igroup.

        Arguments:
            igroup -- string

        Returns:
            Action result as a dict.

        """
        return self._igroup_create(igroup, True)

    def add_initiators(self, igroup, initiators):
        """
        Add initiators to an igroup.

        Arguments:
            igroup     -- string
            initiators -- string (string or list)

        Returns:
            Action result as a dict.

        """
        return self._igroup_modify(igroup, initiators, False)

    def delete_initiators(self, igroup, initiators):
        """
        Delete initiators to an igroup.

        Arguments:
            igroup     -- string
            initiators -- string (string or list)

        Returns:
            Action result as a dict.

        """
        return self._igroup_modify(igroup, initiators, True)

    # Begin internal functions

    def _igroup_create(self, igroup, delete):
        """
        Internal work function for:
            create_igroup
            delete_igroup

        """

        nodes = []
        nodes.append(XGNode('igroup', 'string', igroup))
        nodes.append(XGNode('delete', 'bool', delete))
        return self._basic.perform_action('/vshare/actions' +
                                          '/igroup/create', nodes)

    def _igroup_modify(self, igroup, initiators, delete):
        """
        Internal work function for:
            add_initiators
            delete_initiators

        """
        nodes = []
        nodes.append(XGNode('igroup', 'string', igroup))
        nodes.extend(XGNode.as_node_list('initiators/{0}', 'string',
                                         initiators))
        nodes.append(XGNode('delete', 'bool', delete))

        return self._basic.perform_action('/vshare/actions' +
                                          '/igroup/modify', nodes)


class IGroupManager_1(IGroupManager):
    def __init__(self, basic):
        super(IGroupManager_1, self).__init__(basic)

    def rename_igroup(self, old_igroup, new_igroup):
        """
        Renames an igroup.

        Arguments:
            old_igroup -- string
            new_igroup -- string

        Returns:
            Action result as a dict.

        """
        nodes = []
        nodes.append(XGNode('old_igroup', 'string', old_igroup))
        nodes.append(XGNode('new_igroup', 'string', new_igroup))

        return self._basic.perform_action('/vshare/actions' +
                                          '/igroup/rename', nodes)
