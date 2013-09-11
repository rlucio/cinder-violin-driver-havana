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

from cinder.volume.drivers.violin.vxg.varray import format as FORMAT
from cinder.volume.drivers.violin.vxg.varray import vcm as VCM


CLASS_NAMES = 'VArray'

"""
Adding new classes to this module:

All new classes should be added at the bottom of this file (you can't inherit
from a class that hasn't been defined yet).  Keep the most up-to-date class
named "VArray".  When adding a new VArray class, rename the current VArray
to "VArray_x", where x is +1 of the highest named class in this file.  This
will typically be +1 of whatever class the old "VArray" class is inheriting
from).

Here's an example snippit of old code before updating:

class VArray(VArray_5):
    def __init__(self, session):
        super(VArray, self).__init__(session)
        ...

Here's what this would change to (two updates):

class VArray_6(VArray_5):
    def __init__(self, session):
        super(VArray_6, self).__init__(session)
        ...

"""


class VArray(object):
    versions = '5.1.0'

    def __init__(self, session):
        self.basic = session
        self.format = FORMAT.Format(self.basic)
        self.vcm = VCM.VCM(self.basic)
        self.close = self.basic.close

    def __del__(self):
        try:
            self.basic.close()
        except Exception:
            pass

    @property
    def debug(self):
        return self.basic.debug

    @debug.setter
    def debug(self, value):
        self.basic.debug = value

    def __repr__(self):
        return '<%s host:%s user:%s proto:%s>' % (self.__class__.__name__,
                                                  self.basic.host,
                                                  self.basic.user,
                                                  self.basic.proto)
