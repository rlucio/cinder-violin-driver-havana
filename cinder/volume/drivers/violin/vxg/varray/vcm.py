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


class VCM(object):
    def __init__(self, basic):
        self._basic = basic

    def alarms(self, vcms=None):
        """
        This performs the equivilent of "show system alarms".

        If no VCM is given, then this will retrieve the alarms for all of
        the VCMs.  One or more VCMs may be specified to narrow the scope
        of the alarms that are retrieved.

        VCMs may be specified either as "vcma" or "vcm-a".

        Output is given as {'vcm-a': 'alarms', ...}

        Arguments:
            vcms -- String/list.  The VCM(s) whose alarms you are interested
                    in.

        Returns:
            dict -- A flat dictionary containing the alarms.

        """
        prefix = '/platform/vcm/'
        suffix = '/state/chassis/alarms/***'
        node_list = []

        if vcms is None:
            vcms = self._basic.get_node_values('%s*' % (prefix,))
            for key in vcms.keys():
                node_list.append(key + suffix)
        else:
            if isinstance(vcms, basestring):
                vcms = [vcms]

            if isinstance(vcms, list):
                for index in range(len(vcms)):
                    elm = vcms[index].lower()
                    if elm.find('-') == -1:
                        elm = elm[:-1] + '-' + elm[-1:]
                    node_list.append('%s%s%s' % (prefix, elm, suffix))
            else:
                raise ValueError('"vcms" must be a string or list')

        return_dict = self._basic.get_node_values(node_list)
        for key in return_dict.keys():
            new_key = key.split('/')[prefix.count('/')]
            return_dict[new_key] = return_dict[key]
            del(return_dict[key])

        return return_dict
