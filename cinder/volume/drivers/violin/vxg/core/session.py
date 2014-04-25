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

import urllib
import urllib2

from cinder.volume.drivers.violin.vxg.core.node import XGNode
from cinder.volume.drivers.violin.vxg.core.error import *
from cinder.volume.drivers.violin.vxg.core.request import XGAction
from cinder.volume.drivers.violin.vxg.core.request import XGEvent
from cinder.volume.drivers.violin.vxg.core.request import XGQuery
from cinder.volume.drivers.violin.vxg.core.request import XGRequest
from cinder.volume.drivers.violin.vxg.core.request import XGSet
from cinder.volume.drivers.violin.vxg.core.response import XGResponse


# TODO(gfreeman)
#
# - Figure out flat vs. tree and dict vs. list for node data
#
class XGSession(object):
    """
    XML Gateway session object

    The XGSession is used to send and receive XML based messages
    to a Violin Memory Gateway or Memory Array. In addition to
    sending requests and receiving responses, it also manages
    authentication by logging in at initialization and retaining
    the authentication cookie returned.

    """

    def __init__(self, host, user="admin", password="", debug=False,
                 proto="https", autologin=True):

        """
        Create new XGSession instance.

        Arguments:
            host      -- Name or IP address of host to connect to.
            user      -- Username to login with.
            password  -- Password for user
            debug     -- Enable/disable debugging to stdout (bool)
            proto     -- Either 'http' or 'https'
            autologin -- Should auto-login or not (bool)

        """

        self.host = host
        self.user = user
        self.password = password
        self.debug = debug
        self.proto = proto

        self.request_url = "%s://%s/admin/launch?script=xg" % \
            (self.proto, self.host)

        if proto not in ("http", "https"):
            raise UnsupportedProtocol("Protocol %s not supported." % (proto))

        self.http_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())

        if autologin:
            self.login()

    def __repr__(self):
        return "<XGSession host:%s user:%s password:%s>" % \
            (self.host, self.user, self.password)

    def login(self):
        """
        Login to host and save authentication cookie.

        """

        # Note: login_url and login_data are closely tied to the web GUI
        #       implementation. It is important that these change if the
        #       GUI login screen changes.

        login_url = '%s://%s/admin/launch' % (self.proto, self.host) + \
                    '?script=rh&template=login&action=login'

        login_data = urllib.urlencode({
            'd_user_id': 'user_id',
            't_user_id': 'string',
            'c_user_id': 'string',
            'e_user_id': 'true',
            'f_user_id': self.user,
            'f_password': self.password,
            'Login': 'Login',
        })

        # Handle various login responses.  A valid login must contain all
        # of the following searched for parameters.
        valid_responses = [['template=dashboard', "HTTP-EQUIV='Refresh'"],
                           ['template=index', 'HTTP-EQUIV="Refresh"']]

        try:
            resp = self.http_opener.open(login_url, login_data).read()
            for valid_response_list in valid_responses:
                checks = [x in resp for x in valid_response_list]
                if all(checks):
                    if self.debug:
                        print("Successfully logged in using %s protocol." %
                              (self.proto,))
                    return True
            else:
                if self.debug:
                    print("Failed to login using %s protocol." % (self.proto))
                    print(resp)
                raise AuthenticationError("Could not login")

        except urllib2.HTTPError as e:
            raise NetworkError("urllib2.HTTPError - %s" % (e))

        except urllib2.URLError as e:
            raise NetworkError("urllib2.URLError - %s" % (e))

        return False

    def close(self):
        """
        Close the connection to the given Violin Memory appliance.

        """
        url = '%s://%s' % (self.proto, self.host) +\
            '/admin/launch?script=rh&template=logout&action=logout'

        try:
            resp = self.http_opener.open(url)
            pg = resp.read()
            if False and self.debug:
                print("Logout page: %s" % (pg,))
            if 'You have been successfully logged out.' in pg:
                return True
            else:
                print("Logout failed somehow...")

        except urllib2.HTTPError as e:
            raise NetworkError("urllib2.HTTPError - %s" % (e))

        except urllib2.URLError as e:
            raise NetworkError("urllib2.URLError - %s" % (e))

        return False

    def send_request(self, request, strip=None):
        """
        Sends an XGRequest to the host and parses output into a XGResponse
        object

        Arguments:
            request  -- An XGRequest object

        """

        data = request.to_xml()

        if self.debug:
            print("sending:\n%s" % (data))
        try:
            urlresp = self.http_opener.open(self.request_url, data)

            urlresp_str = urlresp.read()
            if self.debug:
                print("received:\n%s" % (urlresp_str))

            return XGResponse.fromstring(request, urlresp_str, strip)

        except urllib2.HTTPError as e:
            raise NetworkError("urllib2.HTTPError - %s" % (e))

        except urllib2.URLError as e:
            raise NetworkError("urllib2.URLError - %s" % (e))

    def save_config(self):
        """
        Save the configuration on the remote system. Equivalent to
        a "conf t" "wr mem".

        Returns:
            Action result as a dict.

        """

        # TODO(gfreeman) Think about different return methods?  Maybe
        #        handle via exception?

        return self.perform_action('/mgmtd/db/save')

    def get_nodes(self, node_names, nostate=False, noconfig=False):
        """
        Retrieve a "flat" list of XGNode objects based on node_names.
        If you wish to perform some iteration over a representational
        hierarchy, use get_node_tree() instead.

        This takes similar arguments to get_node_values() but returns
        all the node infomation received from the gateway in terms of
        XGNode objects.

        Arguments:
            node_names  -- String or list of node names or patterns (see
                           below) that will be queried.
            nostate     -- Set to True to not return state nodes.
            noconfig    -- Set to True to not return config nodes.

        Returns:
            list()      -- A flat (non-hierarchical) dict-like object with
                           keys as the node name and values of XGNode objects.

        Node name syntax:

        get_nodes() uses the same primitive pattern syntax used
        for TMS XML GET requests, namely:

        If a node name name ends with ..
            /*    perform a shallow iteration (no subtree option).
            /**   perform a subtree iteration.
            /***  perform a subtree iteration and include node itself

        """

        return self._get_nodes(node_names, nostate, noconfig, flat=True)

    def _get_nodes(self, node_names, nostate=False, noconfig=False,
                   flat=False, values_only=False, strip=None):

        query_flags = []
        if nostate:
            query_flags.append("no-state")
        if noconfig:
            query_flags.append("no-config")

        # Convert basestring to list, so we can accept either now
        if isinstance(node_names, basestring):
            node_names = [node_names]

        nodes = []
        for n in node_names:
            nodes.append(XGNode(n, flags=query_flags))

        req = XGQuery(nodes, flat, values_only)
        resp = self.send_request(req, strip)

        # TODO(gfreeman): If we have send_request return empty nodes
        #       dict rather than None for error we can eliminate this
        #       conditional.
        return resp.nodes

    def get_node_values(self, node_names, nostate=False, noconfig=False,
                        strip=None):
        """
        Retrieve values of one or more nodes, returning as a flat dict.
        If you wish to perform some iteration over a representational
        hierarchy, use get_node_tree_values() instead.

        This is a convenience function for users who do not want to
        worry about node binding types or attributes and want to avoid
        the complexity of creating XGNodes and XGRequest objects
        themselves.

        Arguments:
            node_names  -- String or list of node names or patterns (see
                           below) that will be queried.
            nostate     -- Set to True to not return state nodes.
            noconfig    -- Set to True to not return config nodes.
            strip       -- String to remove from the beginning of each key

        Returns:
            dict()      -- A flat (non-hierarchical) dict-like object with
                           keys being the node name and values being the
                           node value.

        """

        return self._get_nodes(node_names, nostate=nostate,
                               noconfig=noconfig, flat=True,
                               values_only=True, strip=strip)

    def perform_action(self, name, nodes=[]):
        """
        Performs the action specified and returns the result.

        Arguments:
            name  -- The node name (string)
            nodes -- The relevant nodes (list)

        Returns:
            A dict of the return code and message.

        """
        # Input validation
        if not isinstance(name, basestring):
            raise ValueError('Expecting name to be of type string')
        elif not isinstance(nodes, list):
            raise ValueError('Expecting nodes to be of type list')
        else:
            for x in nodes:
                if not isinstance(x, XGNode):
                    raise ValueError('Invalid node: {0}'.format(x.__class__))

        # Perform the action given
        req = XGAction(name, nodes)
        resp = self.send_request(req)
        return resp.as_action_result()

    def perform_set(self, nodes=[]):
        """
        Performs a 'set' using the nodes specified and returns the result.

        Arguments:
            nodes -- The relevant nodes (list or XGNodeDict)

        Returns:
            A dict of the return code and message.

        """
        # Input validation
        try:
            # Works for XGNodeDict input
            set_nodes = nodes.get_updates()
        except (AttributeError, TypeError):
            # Assume list instead
            set_nodes = nodes
        if not isinstance(set_nodes, list):
            raise ValueError('Expecting nodes to be of type list')
        else:
            for x in set_nodes:
                if not isinstance(x, XGNode):
                    raise ValueError('Invalid node: {0}'.format(x.__class__))

        req = XGSet(set_nodes)
        resp = self.send_request(req)
        try:
            # Works for XGNodeDict input, clear the tracked modifications
            nodes.clear_updates()
        except (AttributeError, TypeError):
            pass
        return resp.as_action_result()

    def get_node_tree(self, node_names, nostate=False, noconfig=False):
        raise Exception("Not yet implemented.")

    def get_node_tree_values(self, node_names, nostate=False, noconfig=False):
        raise Exception("Not yet implemented.")

    def set_nodes_values(self, node_dict):
        """Sets nodes per dict with node name -> value mappings"""

        # Requires nodes to have type defined in lookup array
        raise Exception("Not yet implemented.")
