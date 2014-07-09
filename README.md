cinder-violin-driver-havana
===========================

6000 Series All-Flash Array Volume Driver V1.0.0 for OpenStack Cinder
Havana Release.

This repository contains the latest open-source release of Violin
Memory's python drivers and client communication libraries for use
with Openstack Cinder's block storage services.

It is maintained externally for 3rd party developers, testers, and
users and may be periodically updated in the future.


Overview
--------
The Volume Driver package for OpenStack Havana from Violin Memory adds
block-storage service support for Violin V6000 series All-Flash
Arrays. The package is implemented as a storage "plug-in" using the
standard Cinder storage driver API, and facilitates the creation,
attachment, and management of volumes (LUNs) between a Flash Array and
different host servers.

All Cinder volume features required for the OpenStack Havana release
are supported, including volume, snapshot, and clone operations. The
1.0.0 driver package release can be used with any OpenStack Havana
deployment for all 6000 Series arrays running V6.3.0.4 or V6.3.1 using
FibreChannel HBAs.

The released software is available as an installable tarball and a
RHEL6.5 RPM. Software and support for existing Violin Memory customers
is available from the Violin Memory Support portal at
www.violinmemory.com/support.


Setup
-----

1. Download a zip file of this repository (using the "Download ZIP"
   button to the right).  Unzip the file on the machine(s) running
   Cinder's volume service (cinder-volume).

2. Recursively copy the cinder directory to the same directory as your
   cinder code installation.

    Examples:

    For devstack: 'cp -r cinder /opt/stack/cinder'

    For ubuntu: 'cp -r cinder /usr/local/lib/python2.7/dist-packages/cinder'

3. Follow your system documentation to enable FibreChannel or iSCSI
   and configure your HBAs.

4. Configure cinder to use one of the violin drivers (see below).

5. Restart cinder-volume.

Basic Configuration with iSCSI
------------------------------

You will need to alter your cinder configuation, typically in
/etc/cinder/cinder.conf.

The following list shows all of the available options and their
default values:

    # IP address or hostname of the v6000 master VIP (string
    # value)
    gateway_vip=

    # IP address or hostname of mg-a (string value)
    gateway_mga=

    # IP address or hostname of mg-b (string value)
    gateway_mgb=

    # User name for connecting to the Memory Gateway (string
    # value)
    gateway_user=admin

    # User name for connecting to the Memory Gateway (string
    # value)
    gateway_password=

    # [iSCSI only] IP port to use for iSCSI targets (integer value)
    gateway_iscsi_port=3260

    # [iSCSI only] prefix for iscsi volumes (string value)
    gateway_iscsi_target_prefix=iqn.2004-02.com.vmem:

    # Use igroups to manage targets and initiators (bool value)
    use_igroups=False

    # Use thin luns instead of thick luns (bool value)
    use_thin_luns=False

A typical configuration file section for using the Violin driver might
look like this:

    volume_driver=cinder.volume.drivers.violin.violin.ViolinDriver
    gateway_vip=1.2.3.4
    gateway_mga=1.2.3.5
    gateway_mgb=1.2.3.6

Note: if you add the configuration option 'verbose=True' and/or
'debug=True' to cinder.conf, you will receive helpful logging from the
Violin driver in /var/log/cinder/cinder-volume.log.

Basic Configuration with FibreChannel
-------------------------------------
You will need to alter your cinder configuation, typically in
/etc/cinder/cinder.conf.

The following list shows all of the available options and their
default values:

    # IP address or hostname of the v6000 master VIP (string
    # value)
    gateway_vip=

    # IP address or hostname of mg-a (string value)
    gateway_mga=

    # IP address or hostname of mg-b (string value)
    gateway_mgb=

    # User name for connecting to the Memory Gateway (string
    # value)
    gateway_user=admin

    # User name for connecting to the Memory Gateway (string
    # value)
    gateway_password=

    # Use igroups to manage targets and initiators (bool value)
    use_igroups=False

    # Use thin luns instead of thick luns (bool value)
    use_thin_luns=False

A typical configuration file section for using the Violin driver might
look like this:

    volume_driver=cinder.volume.drivers.violin.violin_fc.ViolinFCDriver
    gateway_vip=1.2.3.4
    gateway_mga=1.2.3.5
    gateway_mgb=1.2.3.6

Note: if you add the configuration option 'verbose=True' and/or
'debug=True' to cinder.conf, you will receive helpful logging from the
Violin driver in /var/log/cinder/cinder-volume.log.

Additional Configuration for Multibackend
-----------------------------------------
*Multibackend is currently only available for the FCP driver.*

This setup is specifically for users who want to use multiple storage
drivers on their cinder-volume nodes.  In this case *each* driver
instance must have a different configuration section with a unique
name and configuration.  The driver section names must then be added
to the default configuration section using the enabled_backends key.

For example, to add a multi-backend configuration section for the
violin FCP driver, you might do the following:

    [violin-1]
    volume_backend_name=VMEM_FCP
    volume_driver=cinder.volume.drivers.violin.violin_fc.ViolinFCDriver
    gateway_vip=1.2.3.4
    gateway_mga=1.2.3.5
    gateway_mgb=1.2.3.6

    [DEFAULT]
    enabled_backends=violin-1

Further information can be found in the Openstack Cloud Administrator
Guide at
http://docs.openstack.org/admin-guide-cloud/content/multi_backend.html.

Questions?
----------

For questions or support regarding the driver or its support
libraries, please contact opensource@vmem.com.