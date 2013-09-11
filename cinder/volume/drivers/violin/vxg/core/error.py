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


class XGError(Exception):
    """Generic VXG Error"""
    pass


class ParseError(XGError):
    """Error parsing XML request/response"""
    pass


class TypeError(XGError):
    """Node type mismatch"""
    pass


class AuthenticationError(XGError):
    """Login authentication error"""
    pass


class UnsupportedProtocol(XGError):
    """Unsupported network protocol"""
    pass


class NetworkError(XGError):
    """Network error"""
    pass
