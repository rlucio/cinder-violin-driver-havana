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

from xml.dom import minidom
import xml.etree.ElementTree as ET

from cinder.volume.drivers.violin.vxg.core.node import XGNode
from cinder.volume.drivers.violin.vxg.core.error import *


class XGRequest(object):
    """Request to XML gateway"""

    def __init__(self, type="query", nodes=[], action=None, event=None,
                 flat=False, values_only=False):

        if type not in ["query", "set", "action", "event"]:
            raise TypeError("Unknown request type %s." % (type))

        self.type = type
        self.nodes = nodes

        if values_only and not flat:
            raise TypeError("values_only requires flat = True")

        self.flat = flat
        self.values_only = values_only

        if type == "action" and action is None:
            raise TypeError("Missing action name for action request.")

        if type != "action" and action is not None:
            raise TypeError("Action name specified for non-action request.")

        self.action = action

        if type == "event" and event is None:
            raise TypeError("Missing event name for event request.")

        if type != "event" and event is not None:
            raise TypeError("Event name specified for non-event request.")

        self.event = event

    def __repr__(self):
        return ('<XGRequest type:%s action:%s nodes:%r>'
                % (self.type, self.action, self.nodes))

    def to_xml(self, pretty_print=True):
        """
        Return an XML document describing this XGRequest.

        Arguments:
            pretty_print    -- Get a properly formatted XML doc as opposed
                               to a single-line string with XML tags (bool)

        Returns:
            This request object as an XML string.

        """
        root = ET.Element('xg-request')
        req = ET.SubElement(root, '%s-request' % (self.type,))
        if self.action is not None:
            action = ET.SubElement(req, 'action-name')
            action.text = self.action
        if self.event is not None:
            event = ET.SubElement(req, 'event-name')
            event.text = self.event
        if len(self.nodes) > 0:
            nodes = ET.SubElement(req, 'nodes')
            for n in self.nodes:
                nodes.append(n.as_element_tree(self.type))

        if pretty_print:
            return self._pretty_print(root)
        else:
            return ET.tostring(root)

    def _pretty_print(self, node):
        """
        Return a properly formatted XML document with newlines and spaces.

        Arguments:
            node    -- An instance of xml.etree.Element

        Returns:
            A properly formatted XML document.

        """
        reparsed = minidom.parseString(ET.tostring(node))
        return self._tighten_xml(reparsed.toprettyxml('  ', "\n", 'UTF-8'))

    def _tighten_xml(self, xml):
        """
        Tighten the value and close tags to the opening tag in an XML document.

        The XML gateway will not be able to process a document that is
        formatted like so:

            <tag>
              tagValue
            </tag>

        Unfortunately, this is how toprettyxml() outputs the XML.  So the
        purpose of this function is to turn the above into this:

            <tag>tagValue</tag>

        Arguments:
            xml     -- XML output from the toprettyxml() function

        Returns:
            A properly formatted XML document.

        """
        newxml = []
        prevLeadingSpaces = 0
        leadingSpaces = 0
        ascended = False

        for line in xml.split('\n'):
            leadingSpaces = len(line) - len(line.lstrip())
            if leadingSpaces > prevLeadingSpaces:
                # Increase in indent, just append
                newxml.append(line)
                ascended = True
            elif leadingSpaces < prevLeadingSpaces:
                if ascended:
                    # Single close tag, merge lines
                    value = newxml.pop().lstrip()
                    newxml[-1] += value + line.lstrip()
                else:
                    # Multiple closing tags, so just append
                    newxml.append(line)
                ascended = False
            else:
                # Same indent, just append
                newxml.append(line)
            prevLeadingSpaces = leadingSpaces

        return '\n'.join(newxml)


class XGQuery(XGRequest):
    def __init__(self, nodes=[], flat=False, values_only=False):
        super(XGQuery, self).__init__('query', nodes,
                                      flat=flat, values_only=values_only)


class XGAction(XGRequest):
    def __init__(self, action, nodes=[], flat=False, values_only=False):
        super(XGAction, self).__init__('action', nodes, action,
                                       flat=flat, values_only=values_only)


class XGEvent(XGRequest):
    def __init__(self, *args, **kwargs):
        raise Exception("Not yet implemented.")


class XGSet(XGRequest):
    def __init__(self, *args, **kwargs):
        raise Exception("Not yet implemented.")
