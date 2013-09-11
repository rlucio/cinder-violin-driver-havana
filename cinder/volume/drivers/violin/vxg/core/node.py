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

import datetime

import xml.etree.ElementTree as ET

from cinder.volume.drivers.violin.vxg.core.error import *

# List of TMS types that are integers
int_types = ["uint8", "int8", "uint16", "int16",
             "uint32", "int32", "uint64", "int64"]
float_types = ['float32', 'float64']


def _parse_attrs_el(attribs_el):

    #print "Parsing;\n%s" % (ET.tostring(attribs_el))

    if attribs_el.tag != "attribs":
        return {}

    ret_attrs = {}

    for attrib_el in attribs_el.getchildren():
        #print "Parsing;\n%s" % (ET.tostring(attrib_el))
        # get attribute-id, type and value
        try:
            attr_id = attrib_el.find("attribute-id").text
            attr_type = attrib_el.find("type").text
            attr_value = attrib_el.find("value").text
        except AttributeError:
            raise ParseError("Missing element in <attrib>.")

        ret_attrs[attr_id] = XGNodeAttr(attr_id, attr_type, attr_value)

    #print "Returning: %r" % (ret_attrs)
    return ret_attrs


class XGNodeAttr(object):
    """Tall Maple Node Attributes"""

    def __init__(self, id, type, value):
        self.id = id
        self.type = type
        self.value = value

    def __repr__(self):
        return ('<XGNodeAttr id:%s type:%s value:%s>'
                % (self.id, self.type, self.value))


class XGNode(object):
    """Representation of Tall Maple Node"""

    def __init__(self, name='', type='string', value='', node_id='',
                 nodes=[], flags=None, subop=None, attrs=[]):
        self.type = type
        self.nodes = nodes     # Child nodes of this node (in tree form)
        self.node_id = node_id
        # TODO(gfreeman): If attrs is list, process into dict by attr id
        self.attrs = attrs

        name_flags = []
        name_subop = None
        if name.endswith('/***'):
            name_flags = ['subtree', 'include-self']
            name_subop = 'iterate'
        elif name.endswith('/**'):
            name_flags = ['subtree']
            name_subop = 'iterate'
        elif name.endswith('/*'):
            name_subop = 'iterate'
        self.name = name.rstrip('/*')

        if type == "bool":
            if isinstance(value, bool):
                self.value = value
            elif str(value).lower() == 'true':
                self.value = True
            elif str(value).lower() == 'false':
                self.value = False
            else:
                raise TypeError('Unknown boolean value {0}.'.format(value))
        elif type in int_types:
            try:
                self.value = int(value)
            except ValueError:
                raise TypeError('Non integer value %s ' % (value,) +
                                'provided for type %s.' % (type,))
        elif type in float_types:
            try:
                self.value = float(value)
            except ValueError:
                raise TypeError('Non float value %s ' % (value,) +
                                'provided for type %s.' % (type,))
        elif type == 'date':
            if hasattr(value, 'strftime') and callable(value.strftime):
                self.value = value.strftime('%Y/%m/%d')
            else:
                self.value = str(value)
        elif type == 'time_sec':
            if hasattr(value, 'strftime') and callable(value.strftime):
                self.value = value.strftime('%H:%M:%S')
            else:
                self.value = str(value)
        elif type == 'duration_sec':
            try:
                # Handle ints and strings that are actually an int
                self.value = int(value)
            except ValueError:
                # Handle 1w2d3h4m5s type strings
                remainder = value.lower()
                timedelta_params = {}
                for key in ['weeks', 'days', 'hours', 'minutes', 'seconds']:
                    field = key[0]
                    elms = remainder.split(key[0])
                    if len(elms) == 1:
                        pass
                    elif len(elms) == 2:
                        timedelta_params[key] = int(elms[0])
                        remainder = elms[1]
                    else:
                        raise ValueError('Improperly formatted duration: ' +
                                         value)
                if remainder:
                    raise ValueError('Improperly formatted duration: ' +
                                     value)
                delta = datetime.timedelta(**timedelta_params)
                self.value = delta.seconds + delta.days * 86400
        else:
            self.value = value

        self.flags = flags
        if len(name_flags) > 0:
            if self.flags is None or len(self.flags) == 0:
                self.flags = name_flags
            else:
                # Add new flags, but no dupes
                self.flags.extend(name_flags)
                self.flags = list(set(self.flags))

        self.subop = subop
        if name_subop is not None:
            if self.subop is not None:
                if self.subop != name_subop:
                    raise Exception('Not sure how to resolve differing ' +
                                    'subops: %s and %s' %
                                    (self.subop, name_subop))
            else:
                self.subop = name_subop

    def as_element_tree(self, theType):
        node = ET.Element('node')
        if self.subop is not None:
            handler = ET.SubElement(node, 'subop')
            handler.text = self.subop
        if self.flags is not None and len(self.flags) > 0:
            flags = ET.SubElement(node, 'flags')
            for f in self.flags:
                flag = ET.SubElement(flags, 'flag')
                flag.text = f
        handler = ET.SubElement(node, 'name')
        handler.text = self.name
        if theType != 'query':
            handler = ET.SubElement(node, 'type')
            handler.text = self.type
            handler = ET.SubElement(node, 'value')
            if self.type == 'bool':
                handler.text = str(self.value).lower()
            else:
                handler.text = str(self.value)
        return node

    def __repr__(self):
        return ('<XGNode name:%s ' % (self.name,) +
                'type:%s ' % (self.type,) +
                'value:%r ' % (self.value,) +
                'flags:%r ' % (self.flags,) +
                'subop:%s ' % (self.subop,) +
                'attrs:%r ' % (self.attrs,) +
                'node_id:%s ' % (self.node_id,) +
                'nodes:%r>' % (self.nodes,))

    @classmethod
    def parse_el(cls, node_el, flat=False, strip=None):
        """
        Parse an Element Tree element into a XGNode object.

        Returns the XGNode object.
        """

        #print "DEBUG: parsing:\n%s" % (ET.tostring(node_el))

        # These are treated as static variables and when we recurse they
        # overwrite each other
        node_id = ""
        node_name = ""
        node_value = None
        node_type = "unknown"
        node_list = []
        node_attrs = []
        node_dict = {}

        if node_el.tag != "node":
            raise ParseError("Not a node element.")

        # Loop through children and parse elements
        # Python 2.7 has an iter() method but we want compatibility to 2.5
        for sub_el in node_el.getchildren():

            if sub_el.tag == "node-id":
                node_id = sub_el.text
            elif sub_el.tag == "binding":
                for b_sub_el in sub_el.getchildren():
                    if b_sub_el.tag == "name":
                        node_name = b_sub_el.text
                    elif b_sub_el.tag == "value":
                        node_value = b_sub_el.text
                    elif b_sub_el.tag == "type":
                        node_type = b_sub_el.text
                    elif b_sub_el.tag == "attribs":
                        node_attrs = _parse_attrs_el(b_sub_el)
                    else:
                        raise ParseError("Unexpected sub-element " +
                                         "'%s' in binding element." %
                                         (b_sub_el.tag,))

            elif sub_el.tag == "node":
                # Recursively parse sub node
                if flat:
                    node_dict.update(cls.parse_el(sub_el, flat=flat,
                                                  strip=strip))
                else:
                    node_list.append(cls.parse_el(sub_el, flat=flat,
                                                  strip=strip))
            elif sub_el.tag == "name":
                node_name = sub_el.text
            elif sub_el.tag == "value":
                node_value = sub_el.text
            elif sub_el.tag == "type":
                node_type = sub_el.text
            elif sub_el.tag == "attribs":
                node_attrs = _parse_attrs_el(sub_el)
            else:
                raise ParseError("Unexpected subelement " +
                                 "'%s' found while parsing node element."
                                 % (sub_el.tag,))

        # Strip the prefix if one is specified and present
        if strip is not None:
            if strip[-1] != '/':
                strip += '/'
            if node_name.startswith(strip):
                node_name = node_name[len(strip):]

        if flat:
            if node_name == "":
                return node_dict

            # Return a dict containing XGNodes keyed to node name.
            # Nodes without names will not be returned.
            node = XGNode(name=node_name, type=node_type,
                          value=node_value, node_id=node_id,
                          nodes=[], attrs=node_attrs)

            node_dict[node_name] = node

            return node_dict

        else:
            # Return a single node object that contains any subnodes as
            # objects in the parent node's nodes element.

            return XGNode(name=node_name, type=node_type,
                          value=node_value, node_id=node_id,
                          nodes=node_list, attrs=node_attrs)

    @classmethod
    def as_node_list(cls, name, the_type, value):
        """
        Returns a list of XGNode objects.

        Parameters:
            name     -- The node name.  This should be in the format:  blah/{0}
            the_type -- The node type.
            value    -- The node value, can be any of the following:
                            None
                            string
                            list of strings

        Returns:
            A list of XGNodes

        """
        ret_val = []

        if value is None:
            pass
        elif isinstance(value, basestring):
            ret_val.append(cls(name.format(value), the_type, value))
        elif isinstance(value, list):
            for one_value in value:
                ret_val.append(cls(name.format(one_value),
                                   the_type, one_value))
        else:
            raise ValueError('Field "{0}" must be a string or list'.format(
                             name.split('/')[0]))

        return ret_val


class XGNodeDict(object):
    """
    Object that acts like a mapping (dict), containing XGNodes.

    The keys for this mapping are the XGNode names, while the values are the
    XGNode's value attribute.

    Updates to the XGNodeDict's values are tracked internally.

    Unlike traditional python mapping objects, you cannot add new elements to
    an XGNodeDict by assigning a value to a non-existent key.  Instead, new
    values can be added via the "add_node" function.

    """
    def __init__(self, data={}, values_only=False):
        # How to report values
        self.__values_only = values_only

        # Internal variable to track user modifications
        self.__updates = set()

        # Set the data as appropriate
        self.__data = {}
        if isinstance(data, dict):
            self.__data = data
        elif isinstance(data, list):
            for x in data:
                self.__data[x.name] = x
        else:
            raise ValueError('Invalid "data" type: {0}'.format(data.__class__))

    def __delitem__(self, key):
        """Deletes the specified element. """
        # Implements:  del(xgd['foo'])
        if key not in self.__data:
            raise KeyError(key)
        else:
            del(self.__data[key])
            self.__updates.discard(key)

    def __iter__(self):
        """Returns an iterator for the keys in this mapping. """
        return self.__data.iterkeys()

    def __getitem__(self, key):
        """
        Returns the node value for the given key.

        If "values_only" is True, then the value returned is the XGNode.value
        property.  This is how the XGNodeDict behaves when returning data from
        the get_node_values() basic function.

        If "values_only" is False, then the value returned is the entire XGNode
        itself.  This is how the XGNodeDict behaves when returning data from
        the get_nodes() basic function.

        """
        # Implements: xgd['foo']
        if key not in self.__data:
            raise KeyError(key)
        else:
            if self.__values_only:
                return self.__data[key].value
            else:
                return self.__data[key]

    def __setitem__(self, key, value):
        """
        Sets the node value for the given key.

        If "values_only" is True, then the value should not be an XGNode
        object.  If "value_only" is False, then the value should be an
        XGNode object.

        Traditional mapping behavior is that this can be used to both update
        an existing value and to create an additional value.  As the values
        of this mapping are objects, we do not behave like a regular dict does,
        and instead will throw a KeyError exception if the key specified does
        not already exist.

        If you need to add an item to a XGNodeDict object, use the "add_node"
        function instead.

        """
        # Implements: xgd['foo'] = 'value'
        if key not in self.__data:
            raise KeyError(key)
        else:
            if self.__values_only:
                if isinstance(value, XGNode):
                    raise ValueError('Expecting non-XGNode value')
                self.__data[key].value = value
                self.__updates.add(key)
            else:
                if not isinstance(value, XGNode):
                    raise ValueError('Expecting XGNode, got {0}'.format(
                                     value.__class__))
                elif key != value.name:
                    raise ValueError('Key and node name do not match')
                elif self.__data[key].type != value.type:
                    raise ValueError('Type mismatch between original and ' +
                                     'desired values')
                else:
                    self.__data[key] = value
                    self.__updates.add(key)

    def __contains__(self, key):
        """Returns boolean specifying if the key is in this mapping. """
        # Implements: 'foo' in xgd
        return key in self.__data

    def __nonzero__(self):
        """Returns boolean specifying if this mapping is empty or not. """
        # Implements: if xgd:
        return self.__data != {}

    def __len__(self):
        """Returns the number of nodes in this XGNodeDict. """
        # Implements: len(xgd)
        return len(self.__data)

    def add_node(self, node):
        """
        Adds an XGNode to this XGNodeDict.

        If the node already exists, then a KeyError will be raised.  If the
        node passed in is not an XGNode instance, then a ValueError Exception
        will be raised.

        """
        if not isinstance(node, XGNode):
            raise ValueError('node must be an XGNode instance')
        else:
            if node.name in self.__data:
                raise KeyError(node.name)
            else:
                self.__data[node.name] = node
                self.__updates.add(node.name)

    def clear(self):
        """Resets this mapping's data and base. """
        self.__data = {}
        self.__updates.clear()

    def keys(self):
        """Returns the XGNodeDict keys. """
        return self.__data.keys()

    def has_key(self, key):
        """Return boolean value saying if the key is found or not. """
        return key in self.__data

    def get(self, key, default=None):
        """
        Returns the value for the given key node, else 'default'.

        If "values_only" is True, then the value returned is the XGNode.value
        property.  This is how the XGNodeDict behaves when returning data from
        the get_node_values() basic function.

        If "values_only" is False, then the value returned is the entire XGNode
        itself.  This is how the XGNodeDict behaves when returning data from
        the get_nodes() basic function.

        """
        if key not in self.__data:
            return default
        else:
            if self.__values_only:
                return self.__data[key].value
            else:
                return self.__data[key]

    def setdefault(self, key, default=None):
        """
        If key is contained, return it's value, else return 'default'.

        Traditional mapping behavior specifies that if "key" is not present,
        then the value is instead added to the dict.  As the values of this
        mapping are objects, we do not behave like a regular dict does, and
        will instead throw a KeyError exception if the key being requested
        does not exist.

        """
        return self.get(key, default)

    def iterkeys(self):
        """Returns an iterator for the keys in this mapping. """
        return self.__data.iterkeys()

    def pop(self, key):
        """
        Delete the given key from this mapping and return it.

        If "values_only" is True, then the value returned is the XGNode.value
        property.  This is how the XGNodeDict behaves when returning data from
        the get_node_values() basic function.

        If "values_only" is False, then the value returned is the entire XGNode
        itself.  This is how the XGNodeDict behaves when returning data from
        the get_nodes() basic function.

        """
        if key not in self.__data:
            raise KeyError(key)
        else:
            popped_item = self.__data.pop(key)
            self.__updates.discard(key)
            if self.__values_only:
                return popped_item.value
            else:
                return popped_item

    def values(self):
        """
        Returns the node values.

        If "values_only" is True, then the value returned is the XGNode.value
        property.  This is how the XGNodeDict behaves when returning data from
        the get_node_values() basic function.

        If "values_only" is False, then the value returned is the entire XGNode
        itself.  This is how the XGNodeDict behaves when returning data from
        the get_nodes() basic function.

        """
        if self.__values_only:
            return [x.value for x in self.__data.values()]
        else:
            return self.__data.values()

    def itervalues(self):
        """Returns an iterator for the node values. """
        return iter(self.values())

    def items(self):
        """
        Returns a list of (key, value) tuples for this mapping.

        If "values_only" is True, then the value returned is the XGNode.value
        property.  This is how the XGNodeDict behaves when returning data from
        the get_node_values() basic function.

        If "values_only" is False, then the value returned is the entire XGNode
        itself.  This is how the XGNodeDict behaves when returning data from
        the get_nodes() basic function.

        In either case, the key is the XGNode.name property.

        """
        if self.__values_only:
            return [(key, self.__data[key].value)
                    for key in self.__data.keys()]
        else:
            return self.__data.items()

    def iteritems(self):
        """Returns an iterator for the list of (key, value) tuples. """
        return iter(self.items())
