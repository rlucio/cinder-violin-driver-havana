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

import xml.etree.ElementTree as ET

from cinder.volume.drivers.violin.vxg.core.node import XGNode
from cinder.volume.drivers.violin.vxg.core.node import XGNodeDict
from cinder.volume.drivers.violin.vxg.core.error import *


class XGResponse(object):
    """Response from XML gateway"""

    def __init__(self, type, r_code, r_msg, db_rev=0, nodes=[],
                 flat=False, values_only=False):
        self.type = type
        self.r_code = int(r_code)
        self.r_msg = r_msg
        self.db_rev = int(db_rev)
        self.nodes = nodes
        self.flat = flat
        self.values_only = values_only

    def __repr__(self):
        return "<XGResponse type:%s r_code:%d r_msg:%s db_rev:%d nodes:%r>" % \
            (self.type, self.r_code, self.r_msg, self.db_rev, self.nodes)

    @classmethod
    def fromstring(cls, request, xml_str, strip=None):

        """
        Parse XML text contained in string and return as an XGResponse
        object for the given request type.

        Arguments:
            request   - XGRequest object
            xml_str   - string containing XML response to parse

        Returns:
            XGResponse object

        """

        root_el = ET.fromstring(xml_str)

        if root_el.tag != "xg-response":
            raise ParseError("Not xg-response")
        else:
            xg_resp_el = root_el.getchildren()[0]
            if xg_resp_el.tag == "xg-status":
                # parse xg-status
                for child in xg_resp_el.getchildren():
                    if child.tag == "status-msg":
                        r_msg = child.text
                    elif child.tag == "status-code":
                        r_code = child.text
                    else:
                        raise ParseError("Unknown status field.")

                # Handle authentication via Exception
                if r_msg == "Not authenticated":
                    raise AuthenticationError(r_msg)

                return XGResponse("status", int(r_code), r_msg)

            elif xg_resp_el.tag != "%s-response" % (request.type):
                raise ParseError("Response type mismatch.")

            # Parse response

            # TODO(gfreeman):  Refactor to not use find() ... loop through once
            ret_status_el = xg_resp_el.find("return-status")
            if ret_status_el is None:
                raise ParseError("Missing return-status field.")

            try:
                r_code = ret_status_el.find("return-code").text
            except AttributeError:
                raise ParseError("Missing return-code field.")

            try:
                r_msg = ret_status_el.find("return-msg").text
            except AttributeError:
                r_msg = ""

            try:
                db_rev = xg_resp_el.find("db-revision-id").text
                if not db_rev.isdigit():
                    raise ParseError("Non-numeric db-revision-id")
            except AttributeError:
                db_rev = "0"

            try:
                nodes_el = xg_resp_el.find("nodes")
            except AttributeError:
                raise ParseError("Missing nodes element.")

            #
            # Parse the return nodes per parameters in XGRequest
            #
            # If request.flat is True, we return a dict of nodes
            # keyed to node_name. If a returned node had no name
            # it will not be included.
            #
            # If request.flat is False, we return a LIST of nodes
            # that can contain subnodes.
            #
            # If values_only is True, we return node values rather
            # than XGNode objects.
            #

            nodes_d = {}
            nodes_l = []

            if nodes_el is not None:
                for node in nodes_el.getchildren():
                    # parse node
                    if node.tag != "node":
                        raise ParseError("Unexpected subelement '%s'"
                                         % (node.tag,))

                    if request.flat:
                        nodes_d.update(XGNode.parse_el(node, request.flat,
                                       strip=strip))
                    else:
                        nodes_l.append(XGNode.parse_el(node, request.flat,
                                       strip=strip))

            if request.flat:
                nodes = XGNodeDict(nodes_d, request.values_only)
            else:
                nodes = nodes_l

            return XGResponse(request.type, int(r_code), r_msg, db_rev, nodes)

    def as_action_result(self):
        """Return a REST Action's response's code and message. """
        return {'code': self.r_code, 'message': self.r_msg}
