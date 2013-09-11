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


class Format(object):
    def __init__(self, basic):
        self._basic = basic

    def format_array(self, percentage, volumeid=None):
        """
        Format the array.

        Arguments:
            percentage -- uint8
            volumeid   -- uint32

        """

        nodes = []
        nodes.append(XGNode('percentage', 'uint8', percentage))
        if volumeid:
            nodes.append(XGNode('volumeid', 'uint32', volumeid))

        return self._basic.perform_action('/array/actions' +
                                          '/format', nodes)
