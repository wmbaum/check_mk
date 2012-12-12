#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# +------------------------------------------------------------------+
# |             ____ _               _        __  __ _  __           |
# |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
# |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
# |           | |___| | | |  __/ (__|   <    | |  | | . \            |
# |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
# |                                                                  |
# | Copyright Mathias Kettner 2012             mk@mathias-kettner.de |
# +------------------------------------------------------------------+
#
# This file is part of Check_MK.
# The official homepage is at http://mathias-kettner.de/check_mk.
#
# check_mk is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  check_mk is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

# Rules for configuring parameters of checks (services)

register_rulegroup("checkparams", _("Parameters for Inventorized Checks"),
    _("Levels and other parameters for checks found by the Check_MK inventory.\n"
      "Use these rules in order to define parameters like filesystem levels, "
      "levels for CPU load and other things for services that have been found "
      "by the automatic service detection (inventory) of Check_MK."))
group = "checkparams"

subgroup_networking =   _("Networking")
# subgroup_windows =      _("Windows")
subgroup_storage =      _("Storage, Filesystems and Files")
subgroup_os =           _("Operating System Resources")
# subgroup_time =         _("Time synchronization")
subgroup_printing =     _("Printers")
subgroup_environment =  _("Temperature, Humidity, etc.")
subgroup_applications = _("Applications, Processes &amp; Services")
subgroup_virt =         _("Virtualization")
subgroup_hardware =     _("Hardware, BIOS")
subgroup_inventory =    _("Inventory - automatic service detection")

register_rule(group + "/" + subgroup_networking,
    "ping_levels",
    Dictionary(
        title = _("PING and host check parameters"),
        help = _("This rule sets the parameters for the host checks (via <tt>check_icmp</tt>) "
                 "and also for PING checks on ping-only-hosts. For the host checks only the "
                 "critical state is relevant, the warning levels are ignored."),
        elements = [
           ( "rta",
             Tuple(
                 title = _("Round trip average"),
                 elements = [
                     Float(title = _("Warning at"), unit = "ms"),
                     Float(title = _("Critical at"), unit = "ms"),
                 ])),
           ( "loss",
             Tuple(
                 title = _("Packet loss"),
                 help = _("When the percentual number of lost packets is equal or greater then "
                          "the level, then the according state is triggered. The default for critical "
                          "is 100%. That means that the check is only critical if <b>all</b> packets "
                          "are lost."),
                 elements = [
                     Percentage(title = _("Warning at")),
                     Percentage(title = _("Critical at")),
                 ])),

            ( "packets",
              Integer(
                  title = _("Number of packets"),
                  help = _("Number ICMP echo request packets to send to the target host on each "
                           "check execution. All packets are sent directly on check execution. Afterwards "
                           "the check waits for the incoming packets."),
                  minvalue = 1,
                  maxvalue = 20,
               )),

             ( "timeout",
               Integer(
                   title = _("Total timeout of check"),
                   help = _("After this time (in seconds) the check is aborted, regardless "
                            "of how many packets have been received yet."),
                   minvalue = 1,
               )),
        ]),
        match="dict")

register_rule(group + '/' + subgroup_applications,
    varname   = "logwatch_rules",
    title     = _('Logwatch Patterns'),
    valuespec = ListOf(
      Tuple(
          help = _("This defines one logfile pattern rule"),
          show_titles = True,
          orientation = "horizontal",
          elements = [
             DropdownChoice(
               title = _("State"),
               choices = [
                   ('C', _('CRITICAL')),
                   ('W', _('WARNING')),
                   ('O', _('OK')),
                   ('I', _('IGNORE')),
               ],
             ),
             RegExp(
                 title = _("Pattern (Regex)"),
                 size  = 40,
             ),
             TextAscii(
                 title = _("Comment"),
                 size  = 40,
             ),
          ]
      ),
      help = _('<p>You can define one or several patterns (regular expressions) in each logfile pattern rule. '
               'These patterns are applied to the selected logfiles to reclassify the '
               'matching log messages. The first pattern which matches a line will '
               'be used for reclassifying a message. You can use the '
               '<a href="wato.py?mode=pattern_editor">Logfile Pattern Analyzer</a> '
               'to test the rules you defined here.</p>'
               '<p>Select "Ignore" as state to get the matching logs deleted. Other states will keep the '
               'log entries but reclassify the state of them.</p>'),
      add_label = _("Add pattern"),
    ),
    itemtype = 'item',
    itemname = 'logfile',
    itemhelp = _("Put the item names of the logfiles here. For example \"System$\" "
                 "to select the service \"LOG System\"."),
    match = 'list',
)

register_rule(group + '/' + subgroup_inventory,
    varname   = "inventory_services_rules",
    title     = _("Windows Service Inventory"),
    valuespec = Dictionary(
        elements = [
            ('services', ListOfStrings(
                title = _("Services (Regular Expressions)"),
                help  = _('Matching the begining of the service names (regular expression). '
                          'If no service is given, this rule will match all services.'),
                orientation = "horizontal",
            )),
            ('state', DropdownChoice(
                choices = [
                    ('running', _('Running')),
                    ('stopped', _('Stopped')),
                ],
                title = _("Create check if service is in state"),
            )),
            ('start_mode', DropdownChoice(
                choices = [
                    ('auto',     _('Automatic')),
                    ('demand',   _('Manual')),
                    ('disabled', _('Disabled')),
                ],
                title = _("Create check if service is in start mode"),
            )),
        ],
        help = _('<p>This rule can be used to configure the inventory of the windows services check. '
                 'You can configure specific window services to be monitored by the windows check by '
                 'selecting them by name, current state during the inventory or start mode.'),
    ),
    match = 'list',
)

register_rule(group + '/' + subgroup_inventory,
    varname   = "inventory_processes_rules",
    title     = _('Process Inventory'),
    valuespec = Dictionary(
        elements = [
            ('descr', TextAscii(
                title = _('Service Description'),
                help  = _('<p>The service description may contain one or more occurances of %s. If you do this, then the pattern must be a regular '
                          'expression and be prefixed with ~. For each %s in the description, the expression has to contain one "group". A group '
                          'is a subexpression enclosed in brackets, for example (.*) or ([a-zA-Z]+) or (...). When the inventory finds a process '
                          'matching the pattern, it will substitute all such groups with the actual values when creating the check. That way one '
                          'rule can create several checks on a host.</p>'
                          '<p>If the pattern contains more groups thenoccurrances of %s in the service  description then only the first matching '
                          'subexpressions  are used for the  service descriptions. The matched substrings corresponding to the remaining groups '
                          'are copied into the regular expression, nevertheless.</p>'),
            )),
            ('match', Alternative(
                title = _("Process Matching"),
                elements = [
                    TextAscii(
                        title = _("Exact name of the process without argments"),
                        size = 50,
                    ),
                    Transform(
                        RegExp(size = 50),
                        title = _("Regular expression matching command line"),
                        help = _("This regex must match the <i>beginning</i> of the complete "
                                 "command line of the process including arguments"),
                        forth = lambda x: x[1:],   # remove ~
                        back  = lambda x: "~" + x, # prefix ~
                    ),
                    FixedValue(
                        None,
                        totext = "",
                        title = _("Match all processes"),
                    )
                ],
                match = lambda x: (not x and 2) or (x[0] == '~' and 1 or 0),
                default_value = '/usr/sbin/foo',
            )),
            ('user', Alternative(
                title = _('Name of the User'),
                elements = [
                    FixedValue(
                        None,
                        totext = "",
                        title = _("Match all users"),
                    ),
                    TextAscii(
                        title = _('Exact name of the user'),
                    ),
                    FixedValue(
                        False,
                        title = _('Grab user from found processess'),
                        totext = '',
                    ),
                ],
                help = _('<p>The user specification can either be a user name (string). The inventory will then trigger only if that user matches '
                         'the user the process is running as and the resulting check will require that user. Alternatively you can specify '
                         '"grab user". If user is not selected the created check will not check for a specific user.</p>'
                         '<p>Specifying "grab user" makes the created check expect the process to run as the same user as during inventory: the user '
                         'name will be hardcoded into the check. In that case if you put %u into the service description, that will be replaced '
                         'by the actual user name during inventory. You need that if your rule might match for more than one user - your would '
                         'create duplicate services with the same description otherwise.</p>'),
            )),
            ('perfdata', Checkbox(
                title = _('Performance Data'),
                label = _('Collect count of processes, memory and cpu usage'),
            )),
            ('levels', Tuple(
                title = _('Levels'),
                elements = [
                    Integer(
                        title = _("Critical below"),
                        unit = _("processes"),
                        default_value = 1,
                    ),
                    Integer(
                        title = _("Warning below"),
                        unit = _("processes"),
                        default_value = 1,
                    ),
                    Integer(
                        title = _("Warning above"),
                        unit = _("processes"),
                        default_value = 1,
                    ),
                    Integer(
                        title = _("Critical above"),
                        unit = _("processes"),
                        default_value = 1,
                    ),
                ],
            )),
        ],
        optional_keys = [],
    ),
    match = 'list',
)

checkgroups = []

checkgroups.append((
    subgroup_applications,
    "ad_replication",
    _("Active Directory Replication"),
    Tuple(
        help = _("The number of replication failures"),
        elements = [
           Integer(title = _("Warning at"), unit = _("failures")),
           Integer(title = _("Critical at"), unit = _("failures")),
        ]
      ),
    TextAscii(
        title = _("Replication Partner"),
        help = _("The name of the replication partner (Destination DC Site/Destination DC)."),
    ),
    "first"
))

checkgroups.append((
    subgroup_storage,
    "brocade_fcport",
    _("Brocade FC FibreChannel ports"),
    Dictionary(
        elements = [
            ("bw",
              Alternative(
                  title = _("Throughput levels"),
                  help = _("In few cases you have to set the link speed manually it you want "
                           "to use relative levels"),
                  elements = [
                      Tuple(
                        title = _("Maximum bandwidth in relation to the total traffic"),
                        elements = [
                            Percentage(title = _("Warning at"), unit = _("percent")),
                            Percentage(title = _("Critical at"), unit = _("percent")),
                        ]
                    ),
                    Tuple(
                        title = _("Megabyte bandwidth of the port"),
                        elements = [
                            Integer(title = _("Warning at"), unit = _("MByte/s")),
                            Integer(title = _("Critical at"), unit = _("MByte/s")),
                        ]
                    )
                  ])
            ),
            ("assumed_speed",
                Float(
                    title = _("Assumed link speed"),
                    help = _("If the automatic detection of the link "
                             "speed does not work and you want monitors the relative levels of the "
                             "throughtput you have to set the link speed here."),
                    unit = _("GByte/s")
                )
            ),
            ("rxcrcs",
                Tuple (
                    title = _("CRC errors rate"),
                    elements = [
                        Percentage( title = _("Warning at"), unit = _("percent")),
                        Percentage( title = _("Critical at"), unit = _("percent")),
                    ]
               )
            ),
            ("rxencoutframes",
                Tuple (
                    title = _("Enc-Out frames rate"),
                    elements = [
                        Percentage( title = _("Warning at"), unit = _("percent")),
                        Percentage( title = _("Critical at"), unit = _("percent")),
                    ]
                )
            ),
            ("notxcredits",
                Tuple (
                    title = _("No-TxCredits errors"),
                    elements = [
                        Percentage( title = _("Warning at"), unit = _("percent")),
                        Percentage( title = _("Critical at"), unit = _("percent")),
                    ]
                )
            ),
            ("c3discards",
                Tuple (
                    title = _("C3 discards"),
                    elements = [
                        Percentage( title = _("Warning at"), unit = _("percent")),
                        Percentage( title = _("Critical at"), unit = _("percent")),
                    ]
                )
            ),
            ("average",
                Integer (
                    title = _("Average"),
                    help = _("A number in minutes. If this parameter is set, then "
                           "averaging is turned on and all levels will be applied "
                           "to the averaged values, not the the current ones. Per "
                           "default, averaging is turned off. "),
                   unit = _("minutes"),
                   minvalue = 1,
                )
            ),
            ("phystate",
                Optional(
                    ListChoice(
                        title = _("Allowed states (otherwise check will be critical)"),
                        choices = [ (1, _("noCard") ),
                                    (2, _("noTransceiver") ),
                                    (3, _("laserFault") ),
                                    (4, _("noLight") ),
                                    (5, _("noSync") ),
                                    (6, _("inSync") ),
                                    (7, _("portFault") ),
                                    (8, _("diagFault") ),
                                    (9, _("lockRef") ),
                                  ]
                    ),
                    title = _("Physical state of port") ,
                    negate = True,
                    label = _("ignore physical state"),
                )
            ),
            ("opstate",
                Optional(
                    ListChoice(
                        title = _("Allowed states (otherwise check will be critical)"),
                        choices = [ (0, _("unknown") ),
                                    (1, _("online") ),
                                    (2, _("offline") ),
                                    (3, _("testing") ),
                                    (4, _("faulty") ),
                                  ]
                    ),
                    title = _("Operational state") ,
                    negate = True,
                    label = _("ignore operational state"),
                )
            ),
            ("admstate",
                Optional(
                    ListChoice(
                        title = _("Allowed states (otherwise check will be critical)"),
                        choices = [ (1, _("online") ),
                                    (2, _("offline") ),
                                    (3, _("testing") ),
                                    (4, _("faulty") ),
                                  ]
                    ),
                    title = _("Administrative state") ,
                    negate = True,
                    label = _("ignore administrative state"),
                )
            )
        ]
      ),
    TextAscii(
        title = _("Portname"),
        help = _("The name of the switch port"),
    ),
    "first"
))

checkgroups.append((
    subgroup_storage,
    "fs_mount_options",
    _("Filesystem mount options (Linux/UNIX)"),
    ListOfStrings(
       title = _("Expected mount options"),
       help = _("Specify all expected mount options here. If the list of "
         "actually found options differs from this list, the check will go "
         "warning or critical. Just the option <tt>commit</tt> is being "
         "ignored since it is modified by the power saving algorithms.")),
    TextAscii(
        title = _("Mount point"),
        allow_empty = False),
    "first"))



checkgroups.append((
   subgroup_os,
    "systemtime",
    _("Windows system time offset"),
    Tuple(
        title = _("Time offset"),
        elements = [
           Integer(title = _("Warning at"), unit = _("Seconds")),
           Integer(title = _("Critical at"), unit = _("Seconds")),
        ]
    ),
    None,
    "first"
))

checkgroups.append((
    subgroup_storage,
    "fileinfo",
    _("Size and age of single files"),
    Dictionary(
        elements = [
            ( "minage",
                Tuple(
                    title = _("Minimal age"),
                    elements = [
                      Age(title = _("Warning younger then")),
                      Age(title = _("Critical younger then")),
                    ]
                )
            ),
            ( "maxage",
                Tuple(
                    title = _("Maximal age"),
                    elements = [
                      Age(title = _("Warning older then")),
                      Age(title = _("Critical older then")),
                    ]
                )
            ),
            ("minsize",
                Tuple( 
                    title = _("Minimal size"),
                    elements = [ 
                      Filesize(title = _("Warning lower as")), 
                      Filesize(title = _("Critical lower as")), 
                    ]
                )
            ),
            ("maxsize",
                Tuple( 
                    title = _("Maximal size"),
                    elements = [ 
                      Filesize(title = _("Warning higher as")), 
                      Filesize(title = _("Critical higher as")), 
                    ]
                )
            )

        ]
    ),
    TextAscii(
        title = _("File name"),
        allow_empty = True),
    "first"
))


register_rule(group + '/' + subgroup_storage,
    varname   = "filesystem_groups",
    title     = _('Filesystem grouping patterns'),
    help      = _('Normally the filesystem checks (<tt>df</tt>, <tt>hr_fs</tt> and others) '
                  'will create a single service for each filesystem. '
                  'By defining grouping '
                  'patterns you can handle groups of filesystems like one filesystem. '
                  'For each group you can define one or several patterns containing '
                  '<tt>*</tt> and <tt>?</tt>, for example '
                  '<tt>/spool/tmpspace*</tt>. The filesystems matching one of the patterns '
                  'will be monitored like one big filesystem in a single service.'),
    valuespec = ListOf(
      Tuple(
          show_titles = True,
          orientation = "horizontal",
          elements = [
             TextAscii(
                 title = _("Name of group"),
             ),
             TextAscii(
                 title = _("File pattern (using * and ?)"),
             ),
          ]
      ),
      add_label = _("Add pattern"),
    ),
    match = 'list',
)
register_rule(group + '/' + subgroup_storage,
    varname   = "fileinfo_groups",
    title     = _('Fileinfo grouping patterns'),
    help      = _('The check <tt>fileinfo</tt> monitors the age and size of '
                  'a single file. Each file information that is sent '
                  'by the agent will create one service. By defining grouping '
                  'patterns you can switch to the check <tt>fileinfo.groups</tt>. '
                  'That check monitors a list of files at once. You can set levels '
                  'not only for the total size and the age of the oldest/youngest '
                  'file but also on the count. You can define one or several '
                  'patterns containing <tt>*</tt> and <tt>?</tt>, for example '
                  '<tt>/var/log/apache/*.log</tt>. For files contained in a group '
                  'the inventory will automatically create a group service and '
                  'no single service.'),
    valuespec = ListOf(
      Tuple(
          help = _("This defines one fileinfo grouping pattern"),
          show_titles = True,
          orientation = "horizontal",
          elements = [
             TextAscii(
                 title = _("Name of group"),
             ),
             TextAscii(
                 title = _("Pattern for mount point (using * and ?)"),
             ),
          ]
      ),
      add_label = _("Add pattern"),
    ),
    match = 'list',
)


checkgroups.append((
    subgroup_storage,
    "fileinfo-groups",
    _("Size, age and count of file groups"),
    Dictionary(
        elements = [
            ( "minage_oldest",
                Tuple(
                    title = _("Minimal age of oldest file"),
                    elements = [
                      Age(title = _("Warning younger then")),
                      Age(title = _("Critical younger then")),
                    ]
                )
            ),
            ( "maxage_oldest",
                Tuple(
                    title = _("Maximal age of oldest file"),
                    elements = [
                      Age(title = _("Warning older then")),
                      Age(title = _("Critical older then")),
                    ]
                )
            ),
            ( "minage_newest",
                Tuple(
                    title = _("Minimal age of newest file"),
                    elements = [
                      Age(title = _("Warning younger then")),
                      Age(title = _("Critical younger then")),
                    ]
                )
            ),
            ( "maxage_newest",
                Tuple(
                    title = _("Maximal age of newest file"),
                    elements = [
                      Age(title = _("Warning older then")),
                      Age(title = _("Critical older then")),
                    ]
                )
            ),
            ("minsize",
                Tuple( 
                    title = _("Minimal size"),
                    elements = [ 
                      Filesize(title = _("Warning lower as")), 
                      Filesize(title = _("Critical lower as")), 
                    ]
                )
            ),
            ("maxsize",
                Tuple( 
                    title = _("Maximal size"),
                    elements = [ 
                      Filesize(title = _("Warning higher as")), 
                      Filesize(title = _("Critical higher as")), 
                    ]
                )
            ),
            ("mincount",
                Tuple( 
                    title = _("Minimal file count"),
                    elements = [ 
                      Integer(title = _("Warning lower as")), 
                      Integer(title = _("Critical lower as")), 
                    ]
                )
            ),
            ("maxcount",
                Tuple( 
                    title = _("Maximal file count"),
                    elements = [ 
                      Integer(title = _("Warning higher as")), 
                      Integer(title = _("Critical higher as")), 
                    ]
                )
            ),
        ]
    ),
    TextAscii(
        title = _("Filegroup Name"),
        allow_empty = True),
    "first"
))

checkgroups.append((
    subgroup_storage,
    "netapp_fcprtio",
    _("Netapp FC Port throughput"),
    Dictionary(
        elements = [
            ("read",
                Tuple( 
                    title = _("Read"),
                    elements = [ 
                      Filesize(title = _("Warning lower as")), 
                      Filesize(title = _("Critical lower as")), 
                    ]
                )
            ),
            ("write",
                Tuple( 
                    title = _("Write"),
                    elements = [ 
                      Filesize(title = _("Warning higher as")), 
                      Filesize(title = _("Critical higher as")), 
                    ]
                )
            )

        ]
    ),
    TextAscii(
        title = _("File name"),
        allow_empty = True),
    "first"
))
checkgroups.append((
    subgroup_os,
    "memory_pagefile_win",
    _("Memory and pagefile levels for Windows"),
    Dictionary(
        elements = [
            ( "memory",
               Alternative(
                   title = _("Memory Levels"),
                   elements = [
                       Tuple(
                           title = _("Levels in percent"),
                           elements = [
                               Percentage(title = _("Warning at"), label = _("% usage")),
                               Percentage(title = _("Critical at"), label = _("% usage")),
                           ]
                       ),
                       Tuple(
                           title = _("Absolute levels"),
                           elements = [
                                Filesize(title = _("Warning higher as")), 
                                Filesize(title = _("Critical higher as")), 
                           ]
                        )
                   ])),
            ( "pagefile",
               Alternative(
                   title = _("Pagefile Levels"),
                   elements = [
                       Tuple(
                           title = _("Levels in percent"),
                           elements = [
                               Percentage(title = _("Warning at"), label = _("% usage")),
                               Percentage(title = _("Critical at"), label = _("% usage")),
                           ]
                       ),
                       Tuple(
                           title = _("Absolute levels"),
                           elements = [
                                Filesize(title = _("Warning higher as")), 
                                Filesize(title = _("Critical higher as")), 
                           ]
                        )
                   ])),
        ]),
    None,
    "dict"
))

checkgroups.append((
    subgroup_networking,
    "tcp_conn_stats",
    ("TCP connection stats"),
    Dictionary(
        elements = [
            ( "ESTABLISHED",
              Tuple(
                  title = _("ESTABLISHED"),
                  help = _("connection up and passing data"),
                  elements = [
                      Integer(title = _("Warning at"),  label = _("connections")),
                      Integer(title = _("Critical at"), label = _("connections"))
                  ]
              )
            ),
            ( "SYN_SENT",
              Tuple(
                  title = _("SYN_SENT"),
                  help = _("session has been requested by us; waiting for reply from remote endpoint"),
                  elements = [
                      Integer(title = _("Warning at"),  label = _("connections")),
                      Integer(title = _("Critical at"), label = _("connections"))
                  ]
              )
            ),
            ( "SYN_RECV",
              Tuple(
                  title = _("SYN_RECV"),
                  help = _("session has been requested by a remote endpoint "
                           "for a socket on which we were listening"),
                  elements = [
                      Integer(title = _("Warning at"),  label = _("connections")),
                      Integer(title = _("Critical at"), label = _("connections"))
                  ]
              )
            ),
            ( "LAST_ACK",
              Tuple(
                  title = _("LAST_ACK"),
                  help = _("our socket is closed; remote endpoint has also shut down; "
                           " we are waiting for a final acknowledgement"),
                  elements = [
                      Integer(title = _("Warning at"),  label = _("connections")),
                      Integer(title = _("Critical at"), label = _("connections"))
                  ]
              )
            ),
            ( "CLOSE_WAIT",
              Tuple(
                  title = _("CLOSE_WAIT"),
                  help = _("remote endpoint has shut down; the kernel is waiting "
                           "for the application to close the socket"),
                  elements = [
                      Integer(title = _("Warning at"),  label = _("connections")),
                      Integer(title = _("Critical at"), label = _("connections"))
                  ]
              )
            ),
            ( "TIME_WAIT",
              Tuple(
                  title = _("TIME_WAIT"),
                  help = _("socket is waiting after closing for any packets left on the network"),
                  elements = [
                      Integer(title = _("Warning at"),  label = _("connections")),
                      Integer(title = _("Critical at"), label = _("connections"))
                  ]
              )
            ),
            ( "CLOSED",
              Tuple(
                  title = _("CLOSED"),
                  help = _("socket is not being used"),
                  elements = [
                      Integer(title = _("Warning at"),  label = _("connections")),
                      Integer(title = _("Critical at"), label = _("connections"))
                  ]
              )
            ),
            ( "CLOSING",
              Tuple(
                  title = _("CLOSING"),
                  help = _("our socket is shut down; remote endpoint is shut down; "
                           "not all data has been sent"),
                  elements = [
                      Integer(title = _("Warning at"),  label = _("connections")),
                      Integer(title = _("Critical at"), label = _("connections"))
                  ]
              )
            ),
            ( "FIN_WAIT1",
              Tuple(
                  title = _("FIN_WAIT1"),
                  help = _("our socket has closed; we are in the process of "
                           "tearing down the connection"),
                  elements = [
                      Integer(title = _("Warning at"),  label = _("connections")),
                      Integer(title = _("Critical at"), label = _("connections"))
                  ]
              )
            ),
            ( "FIN_WAIT2",
              Tuple(
                  title = _("FIN_WAIT2"),
                  help = _("the connection has been closed; our socket is waiting "
                           "for the remote endpoint to shutdown"),
                  elements = [
                      Integer(title = _("Warning at"),  label = _("connections")),
                      Integer(title = _("Critical at"), label = _("connections"))
                  ]
              )
            ),
            ( "BOUND",
              Tuple(
                  title = _("BOUND"),
                  help = _("the socket has been created and an address assigned "
                           "to with bind(). The TCP stack is not active yet. "
                           "This state is only reported on Solaris."),
                  elements = [
                      Integer(title = _("Warning at"),  label = _("connections")),
                      Integer(title = _("Critical at"), label = _("connections"))
                  ]
              )
            ),
        ]
    ),
    None,
    "first"
))

checkgroups.append((
    subgroup_applications,
    "msx_queues",
    _("MS Exchange message queues"),
    Tuple(
        help = _("The length of the queues"),
        elements = [
            Integer(title = _("Warning at queue length")),
            Integer(title = _("Critical at queue length"))
        ]),
        OptionalDropdownChoice(
            title = _("Explicit Queue Names"),
            help = _("You can enter a number of explicit queues names that "
                     "rule should or should not apply here. Builtin queues:<br>"
                     "Active Remote Delivery<br>Active Mailbox Delivery<br>"
                     "Retry Remote Delivery<br>Poison Queue Length<br>"),
           choices = [
              ( "Active Remote Delivery",  "Active Remote Delivery" ),
              ( "Retry Remote Delivery",   "Retry Remote Delivery" ),
              ( "Active Mailbox Delivery", "Active Mailbox Delivery" ),
              ( "Poison Queue Length",     "Poison Queue Length" ),
              ],
           otherlabel = _("specify manually ->"),
           explicit = TextAscii(allow_empty = False)),
    "first")
)

checkgroups.append((
    subgroup_storage,
    "filesystem",
    _("Filesystems (used space and growth)"),
    Dictionary(
        elements = [
            ( "levels",
              Tuple(
                  title = _("Levels for the used space"),
                  elements = [
                      Percentage(title = _("Warning at"),  label = _("% usage"), allow_int = True),
                      Percentage(title = _("Critical at"), label = _("% usage"), allow_int = True)])),
            (  "magic",
               Float(
                  title = _("Magic factor (automatic level adaptation for large filesystems)"),
                  minvalue = 0.1,
                  maxvalue = 1.0)),
            (  "magic_normsize",
               Integer(
                   title = _("Reference size for magic factor"),
                   minvalue = 1,
                   label = _("GB"))),
            ( "levels_low",
              Tuple(
                  title = _("Minimum levels if using magic factor"),
                  help = _("The filesystem levels will never fall below these values, when using "
                           "the magic factor and the filesystem is very small."),
                  elements = [
                      Percentage(title = _("Warning at"),  label = _("usage"), allow_int = True),
                      Percentage(title = _("Critical at"), label = _("usage"), allow_int = True)])),
            (  "trend_range",
               Optional(
                   Integer(
                       title = _("Range for filesystem trend computation"),
                       minvalue = 1,
                       label= _("hours")),
                   title = _("Trend computation"),
                   label = _("Enable trend computation"))),
            (  "trend_mb",
               Tuple(
                   title = _("Levels on trends in MB per range"),
                   elements = [
                       Integer(title = _("Warning at"), label = _("MB / range")),
                       Integer(title = _("Critical at"), label = _("MB / range"))
                   ])),
            (  "trend_perc",
               Tuple(
                   title = _("Levels for the percentual growth"),
                   elements = [
                       Percentage(title = _("Warning at"), label = _("% / range")),
                       Percentage(title = _("Critical at"), label = _("% / range"))
                   ])),
            (  "trend_timeleft",
               Tuple(
                   title = _("Levels on the time left until the filesystem gets full"),
                   elements = [
                       Integer(title = _("Warning at"), label = _("days left")),
                       Integer(title = _("Critical at"), label = _("days left"))
                   ])),
            ( "trend_perfdata",
              Checkbox(
                  title = _("Trend performance data"),
                  label = _("Enable performance data from trends"))),


        ]),
    TextAscii(
        title = _("Mount point"),
        help = _("For Linux/UNIX systems, specify the mount point, for Windows systems "
                 "the drive letter uppercase followed by a colon, e.g. <tt>C:</tt>"),
        allow_empty = False),
    "dict")
)

checkgroups.append((
    subgroup_networking,
    "if",
    _("Network interfaces and switch ports"),
    Dictionary(
        elements = [
            ( "errors",
              Tuple(
                  title = _("Levels for error rates"),
                  help = _("These levels make the check go warning or critical whenever the "
                           "<b>percentual error rate</b> of the monitored interface reaches "
                           "the given bounds. The error rate is computed by dividing number of "
                           "errors by the total number of packets (successful plus errors)."),
                  elements = [
                      Percentage(title = _("Warning at"), label = _("errors")),
                      Percentage(title = _("Critical at"), label = _("errors"))
                  ])),

             ( "speed",
               OptionalDropdownChoice(
                   title = _("Operating speed"),
                   help = _("If you use this parameter then the check goes warning if the "
                            "interface is not operating at the expected speed (e.g. it "
                            "is working with 100MBit/s instead of 1GBit/s.<b>Note:</b> "
                            "some interfaces do not provide speed information. In such cases "
                            "this setting is used as the assumed speed when it comes to "
                            "traffic monitoring (see below)."),
                  choices = [
                     ( None,       "ignore speed" ),
                     ( 10000000,   "10 MBit/s" ),
                     ( 100000000,  "100 MBit/s" ),
                     ( 1000000000, "1 GBit/s" ) ],
                  otherlabel = _("specify manually ->"),
                  explicit = \
                      Integer(title = _("Other speed in bits per second"),
                              label = _("Bits per second")))
             ),
             ( "state",
                Optional(
                    ListChoice(
                        title = _("Allowed states:"),
                        choices = _if_portstate_choices),
                    title = _("Operational State"),
                    help = _("Activating the monitoring of the operational state (opstate), "
                             "the check will get warning or critical of the current state "
                             "of the interface does not match the expected state or states."),
                    label = _("Ignore the operational state"),
                    none_label = _("ignore"),
                    negate = True)
             ),
             ( "unit",
               RadioChoice(
                   title = _("Measurement unit"), 
                   help = _("Here you can specifiy the measurement unit of the network interface"),
                   default_value = "byte",
                   choices = [
                       ( "bit",  _("Bits") ),
                       ( "byte", _("Bytes") ),],
               )),
             ( "traffic",
               Alternative(
                   title = _("Used bandwidth (traffic)"),
                   help = _("Settings levels on the used bandwidth is optional. If you do set "
                            "levels you might also consider using an averaging."),
                   elements = [
                       Tuple(
                           title = _("Percentual levels (in relation to port speed)"),
                           elements = [
                               Percentage(title = _("Warning at"), label = _("% of port speed")),
                               Percentage(title = _("Critical at"), label = _("% of port speed")),
                           ]
                       ),
                       Tuple(
                           title = _("Absolute levels in bits or bytes per second"),
                           help = _("Depending on the measurement unit (defaults to byte) the absolute levels are set in bit or byte"),
                           elements = [
                               Integer(title = _("Warning at"), label = _("bits / bytes per second")),
                               Integer(title = _("Critical at"), label = _("bits / bytes per second")),
                           ]
                        )
                   ])
               ),

               ( "average",
                 Integer(
                     title = _("Average values"),
                     help = _("By activating the computation of averages, the levels on "
                              "errors and traffic are applied to the averaged value. That "
                              "way you can make the check react only on long-time changes, "
                              "not on one-minute events."),
                     label = _("minutes"),
                     minvalue = 1,
                 )
               ),


           ]),
    TextAscii(
        title = _("port specification"),
        allow_empty = False),
    "dict",
    ))


checkgroups.append((
    subgroup_os,
    "memory",
    _("Main memory usage (Linux / UNIX)"),
    Alternative(
        help = _("The levels for memory usage on Linux and UNIX systems take into account the "
               "currently used memory (RAM or SWAP) by all processes and sets this in relation "
               "to the total RAM of the system. This means that the memory usage can exceed 100%. "
               "A usage of 200% means that the total size of all processes is twice as large as "
               "the main memory, so <b>at least</b> the half of it is currently swapped out."),
        elements = [
            Tuple(
                title = _("Specify levels in percentage of total RAM"),
                elements = [
                  Percentage(title = _("Warning at a usage of"), label = _("% of RAM"), max_value = None),
                  Percentage(title = _("Critical at a usage of"), label = _("% of RAM"), max_value = None)]),
            Tuple(
                title = _("Specify levels in absolute usage values"),
                elements = [
                  Integer(title = _("Warning at"), unit = _("MB")),
                  Integer(title = _("Critical at"), unit = _("MB"))]),
            ]),
    None, None))

checkgroups.append((
    subgroup_printing,
    "printer_supply",
    _("Printer cardridge levels"),
    Tuple(
          help = _("Levels for printer cardridges."),
          elements = [
              Float(title = _("Warning remaining")),
              Float(title = _("Critical remaining"))]
    ),
    TextAscii(
        title = _("cardridge specification"),
        allow_empty = True
    ),
    None,
    ))

checkgroups.append((
    subgroup_os,
    "cpu_load",
    _("CPU load (not utilization!)"),
    Tuple(
          help = _("The CPU load of a system is the number of processes currently being "
                   "in the state <u>running</u>, i.e. either they occupy a CPU or wait "
                   "for one. The <u>load average</u> is the averaged CPU load over the last 1, "
                   "5 or 15 minutes. The following levels will be applied on the average "
                   "load. On Linux system the 15-minute average load is used when applying "
                   "those levels."),
          elements = [
              Integer(title = _("Warning at a load of")),
              Integer(title = _("Critical at a load of"))]),
    None, None))

checkgroups.append((
    subgroup_os,
    "cpu_utilization",
    _("CPU utilization (percentual)"),
    Optional(
        Tuple(
              elements = [
                  Percentage(title = _("Warning at a utilization of"), label = "%"),
                  Percentage(title = _("Critical at a utilization of"), label = "%")]),
        label = _("Alert on too high CPU utilization"),
        help = _("The CPU utilization sums up the percentages of CPU time that is used "
                 "for user processes and kernel routines over all available cores within "
                 "the last check interval. The possible range is from 0% to 100%")),
    None, None))

checkgroups.append((
    subgroup_os,
    "cpu_iowait",
    _("CPU utilization (disk wait)"),
    Optional(
        Tuple(
              elements = [
                  Percentage(title = _("Warning at a disk wait of"), label = "%"),
                  Percentage(title = _("Critical at a disk wait of"), label = "%")]),
        label = _("Alert on too high disk wait (IO wait)"),
        help = _("The CPU utilization sums up the percentages of CPU time that is used "
                 "for user processes, kernel routines (system), disk wait (sometimes also "
                 "called IO wait) or nothing (idle). "
                 "Currently you can only set warning/critical levels to the disk wait. This "
                 "is the total percentage of time all CPUs have nothing else to do then waiting "
                 "for data coming from or going to disk. If you have a significant disk wait "
                 "the the bottleneck of your server is IO. Please note that depending on the "
                 "applications being run this might or might not be totally normal.")),
    None, None))

checkgroups.append((
    subgroup_environment,
    "akcp_humidity",
    _("AKCP Humidity Levels"),
    Tuple(
          help = _("This Rulset sets the threshold limits for humidity sensors attached to " 
                   "AKCP Sensor Probe "),
          elements = [
              Integer(title = _("Critical if moisture lower than")),
              Integer(title = _("Warning if moisture lower than")),
              Integer(title = _("Warning if moisture higher than")),
              Integer(title = _("Critical if moisture higher than")),
              ]),
    TextAscii(
        title = _("Service descriptions"),
        allow_empty = False),
     None))

checkgroups.append((
    subgroup_applications,
    "oracle_logswitches",
    _("Oracle Logswitches"),
    Tuple(
          help = _("This check monitors the number of log switches of an ORACLE " 
                   "database instance in the last 60 minutes. You can set levels for upper and lower bounds."),
          elements = [
              Integer(title = _("Critical if fewer than"), unit=_("log switches")),
              Integer(title = _("Warning if fewer than"), unit=_("log switches")),
              Integer(title = _("Warning if more than"), unit=_("log switches")),
              Integer(title = _("Critical if more than"), unit=_("log switches")),
              ]),
    TextAscii(
        title = _("Service descriptions"),
        allow_empty = False),
     None))


checkgroups.append((
    subgroup_applications,
    "mssql_backup",
    _("MSSQL Backups"),
    Optional(
        Tuple(
            elements = [
              Integer(title = _("Warning if more than"), unit = _("seconds")),
              Integer(title = _("Critical if more than"), unit = _("seconds"))
            ]
        ),
        title = _("Specify time since last successful backup"),
        help = _("The levels for memory usage on Linux and UNIX systems take into account the "
               "currently used memory (RAM or SWAP) by all processes and sets this in relation "
               "to the total RAM of the system. This means that the memory usage can exceed 100%. "
               "A usage of 200% means that the total size of all processes is twice as large as "
               "the main memory, so <b>at least</b> the half of it is currently swapped out."),
    ),
    TextAscii(
        title = _("Service descriptions"),
        allow_empty = False),
     None))

checkgroups.append((
    subgroup_applications,
    "mssql_counters_locks",
    _("MSSQL Locks"),
    Dictionary(
         help = _("This check monitors locking related information of MSSQL tablespaces."),
         elements = [
             ("lock_requests/sec",
               Tuple(
                   title = _("Lock Requests / sec"),
                   help = _("Number of new locks and lock conversions per second requested from the lock manager."),
                   elements = [
                       Float(title = _("Warning at"),  unit = _("requests/sec")),
                       Float(title = _("Critical at"), unit = _("requests/sec")),
                    ],
               ),
            ),
            ( "lock_timeouts/sec",
               Tuple(
                   title = _("Lock Timeouts / sec"),
                   help = _("Number of lock requests per second that timed out, including requests for NOWAIT locks."),
                   elements = [
                       Float(title = _("Warning at"),  unit = _("timeouts/sec")),
                       Float(title = _("Critical at"), unit = _("timeouts/sec")),
                    ],
               ),
            ),
            ( "number_of_deadlocks/sec",
               Tuple(
                   title = _("Number of Deadlocks / sec"),
                   help = _("Number of lock requests per second that resulted in a deadlock."),
                   elements = [
                       Float(title = _("Warning at"),  unit = _("deadlocks/sec")),
                       Float(title = _("Critical at"), unit = _("deadlocks/sec")),
                    ],
               ),
            ),
            ( "lock_waits/sec",
               Tuple(
                   title = _("Lock Waits / sec"),
                   help = _("Number of lock requests per second that required the caller to wait."),
                   elements = [
                       Float(title = _("Warning at"),  unit = _("waits/sec")),
                       Float(title = _("Critical at"), unit = _("waits/sec")),
                    ],
               ),
            ),
         ]
    ),
    TextAscii(
        title = _("Service descriptions"),
        allow_empty = False
    ),
    None))


checkgroups.append((
    subgroup_applications,
    "mysql_sessions",
    _("MySQL Sessions & Connections"),
    Dictionary(
         help = _("This check monitors the current number of active sessions to the MySQL "
                  "database server as well as the connection rate."),
         elements = [
             ( "total", 
               Tuple(
                   title = _("Number of current sessions"),
                   elements = [
                       Integer(title = _("Warning at"),  unit = _("sessions"), default_value = 100), 
                       Integer(title = _("Critical at"), unit = _("sessions"), default_value = 200),
                    ],
               ),
            ),
            ( "running",
               Tuple(
                   title = _("Number of currently running sessions"),
                   help = _("Levels for the number of sessions that are currently active"),
                   elements = [
                       Integer(title = _("Warning at"),  unit = _("sessions"), default_value = 10), 
                       Integer(title = _("Critical at"), unit = _("sessions"), default_value = 20),
                    ],
               ),
            ),
            ( "connections",
               Tuple(
                   title = _("Number of new connections per second"),
                   elements = [
                       Integer(title = _("Warning at"),  unit = _("connection/sec"), default_value = 20), 
                       Integer(title = _("Critical at"), unit = _("connection/sec"), default_value = 40),
                    ],
               ),
            ),
         ]
    ),
    None,
    None))

checkgroups.append((
    subgroup_applications,
    "mysql_innodb_io",
    _("MySQL InnoDB Throughput"),
    Dictionary(
        elements = [
            ( "read",
              Tuple(
                  title = _("Read throughput"),
                  elements = [
                      Float(title = _("warning at"), unit = _("MB/s")),
                      Float(title = _("critical at"), unit = _("MB/s"))
                  ])),
            ( "write",
              Tuple(
                  title = _("Write throughput"),
                  elements = [
                      Float(title = _("warning at"), unit = _("MB/s")),
                      Float(title = _("critical at"), unit = _("MB/s"))
                  ])),
            ( "average",
              Integer(
                  title = _("Average"),
                  help = _("When averaging is set, then an floating average value "
                           "of the disk throughput is computed and the levels for read "
                           "and write will be applied to the average instead of the current "
                           "value."),
                 unit = "min"))
        ]),
    None,
    "dict"))

checkgroups.append((
    subgroup_applications,
    "dbsize",
    _("Size of MySQL/PostgresQL databases"),
    Optional(
        Tuple(
            elements = [
                Integer(title = _("warning at"), unit = _("MB")),
                Integer(title = _("critical at"), unit = _("MB")),
            ]),
        help = _("The check will trigger a warning or critical state if the size of the "
                 "database exceeds these levels."),
        title = _("Impose limits on the size of the database"),
    ),
    TextAscii(
        title = _("Name of the database"),
    ),
    "first"))

checkgroups.append((
    subgroup_applications,
    "postgres_sessions",
    _("PostgreSQL Sessions"),
    Dictionary(
         help = _("This check monitors the current number of active and idle sessions on PostgreSQL"),
         elements = [
             ( "total", 
               Tuple(
                   title = _("Number of current sessions"),
                   elements = [
                       Integer(title = _("Warning at"),  unit = _("sessions"), default_value = 100), 
                       Integer(title = _("Critical at"), unit = _("sessions"), default_value = 200),
                    ],
               ),
            ),
            ( "running",
               Tuple(
                   title = _("Number of currently running sessions"),
                   help = _("Levels for the number of sessions that are currently active"),
                   elements = [
                       Integer(title = _("Warning at"),  unit = _("sessions"), default_value = 10), 
                       Integer(title = _("Critical at"), unit = _("sessions"), default_value = 20),
                    ],
               ),
            ),
         ]
    ),
    None,
    None))


checkgroups.append((
    subgroup_applications,
    "oracle_sessions",
    _("Oracle Sessions"),
    Tuple(
         title = _("Number of active sessions"),
         help = _("This check monitors the current number of active sessions on Oracle"),
         elements = [
             Integer(title = _("Warning at"),  unit = _("sessions"), default_value = 100), 
             Integer(title = _("Critical at"), unit = _("sessions"), default_value = 200),
          ],
     ),
      None, None))

checkgroups.append((
    subgroup_applications,
    "postgres_stat_database",
    _("PostgreSQL Database Statistics"),
    Dictionary(
        help = _("This check monitors how often database objects in a PostgreSQL Database are accessed"),
        elements = [ 
            ( "blocks_read",
                Tuple(
                   title = _("Blocks read"),
                   elements = [
                      Float(title = "warning at", unit = _("blocks/s")),
                      Float(title = "critical at", unit = _("blocks/s")),
                   ],
                ),
            ),
            ( "xact_commit", 
                Tuple(
                   title = _("Commits"),
                   elements = [
                      Float(title = "warning at", unit = _("/s")),
                      Float(title = "critical at", unit = _("/s")),
                   ],
                ),
            ),
            ( "tup_fetched", 
                Tuple(
                   title = _("Fetches"),
                   elements = [
                      Float(title = "warning at", unit = _("/s")),
                      Float(title = "critical at", unit = _("/s")),
                   ],
                ),
            ),    
            ( "tup_deleted", 
                Tuple(
                   title = _("Deletes"),
                   elements = [
                      Float(title = "warning at", unit = _("/s")),
                      Float(title = "critical at", unit = _("/s")),
                   ],
                ),
            ),
            ( "tup_updated", 
                Tuple(
                   title = _("Updates"),
                   elements = [
                      Float(title = "warning at", unit = _("/s")),
                      Float(title = "critical at", unit = _("/s")),
                   ],
                ),
            ),
            ( "tup_inserted", 
                Tuple(
                   title = _("Inserts"),
                   elements = [
                      Float(title = "warning at", unit = _("/s")),
                      Float(title = "critical at", unit = _("/s")),
                   ],
                ),
            ),
        ],
    ),
    TextAscii(
        title = _("Database name"),
        allow_empty = False),
    None))

checkgroups.append((
    subgroup_applications,
    "win_dhcp_pools",
    _("Windows DHCP Pool"),
    Tuple(
          help = _("The count of remaining entries in the DHCP pool represents "
                   "the number of IP addresses left which can be assigned in the network"),
          elements = [
              Percentage(title = _("Warning if pool usage higher than")),
              Percentage(title = _("Critical if pool usage higher than")),
              ]),
    TextAscii(
        title = _("Service descriptions"),
        allow_empty = False),
     None))

checkgroups.append((
    subgroup_os,
    "threads",
    _("Number of threads"),
    Tuple(
          help = _("These levels check the number of currently existing threads on the system. Each process has at "
                   "least one thread."),
          elements = [
              Integer(title = _("Warning at"), unit = _("threads"), default_value = 1000),
              Integer(title = _("Critical at"), unit = _("threads"), default_value = 2000)]),
    None, None))

checkgroups.append((
    subgroup_applications,
    "vms_procs",
    _("Number of processes on OpenVMS"),
    Optional(
        Tuple(
              elements = [
                  Integer(title = _("Warning at"), unit = _("processes"), default_value = 100), 
                  Integer(title = _("Critical at"), unit = _("processes"), default_value = 200)]),
        title = _("Impose levels on number of processes"),
    ),
    None, None))

checkgroups.append((
    subgroup_os,
    "vm_counter",
    _("Number of kernel events per second"),
    Tuple(
          help = _("This ruleset applies to several similar checks measing various kernel "
                   "events like context switches, process creations and major page faults. "
                   "Please create separate rules for each type of kernel counter you "
                   "want to set levels for."),
          show_titles = False,
          elements = [
              Optional(
                 Float(label = _("events per second")),
                 title = _("Set warning level:"),
                 sameline = True),
              Optional(
                 Float(label = _("events per second")),
                 title = _("Set critical level:"),
                 sameline = True)]),

    DropdownChoice(
        title = _("kernel counter"),
        choices = [ (x,x) for x in [
           "Context Switches",
           "Process Creations",
           "Major Page Faults" ]]),
    "first"))

checkgroups.append((
    subgroup_storage,
    "disk_io",
    _("Levels on disk IO (throughput)"),
    Dictionary(
        elements = [
            ( "read",
              Tuple(
                  title = _("Read throughput"),
                  elements = [
                      Float(title = "warning at", unit = _("MB/s")),
                      Float(title = "critical at", unit = _("MB/s"))
                  ])),
            ( "write",
              Tuple(
                  title = _("Write throughput"),
                  elements = [
                      Float(title = "warning at", unit = _("MB/s")),
                      Float(title = "critical at", unit = _("MB/s"))
                  ])),
            ( "average",
              Integer(
                  title = _("Average"),
                  help = _("When averaging is set, then an floating average value "
                           "of the disk throughput is computed and the levels for read "
                           "and write will be applied to the average instead of the current "
                           "value."),
                 unit = "min")),
            ( "latency", 
              Tuple(
                  title = _("IO Latency"),
                  elements = [
                      Float(title = "warning at",  unit = _("ms"), default_value = 80.0),
                      Float(title = "critical at", unit = _("ms"), default_value = 160.0),
             ])),
            ( "latency_perfdata",
              Checkbox(
                  title = _("Performance Data for Latency"),
                  label = _("Collect performance data for disk latency"),
                  help = _("Note: enabling performance data for the latency might "
                           "cause incompatibilities with existing historical data "
                           "if you are running PNP4Nagios in SINGLE mode.")),
            ),
            ( "read_ql", 
              Tuple(
                  title = _("Read Queue-Length"),
                  elements = [
                      Float(title = "warning at",  default_value = 80.0),
                      Float(title = "critical at", default_value = 90.0),
             ])),
            ( "write_ql", 
              Tuple(
                  title = _("Write Queue-Length"),
                  elements = [
                      Float(title = "warning at",  default_value = 80.0),
                      Float(title = "critical at", default_value = 90.0),
             ])),
            ( "ql_perfdata",
              Checkbox(
                  title = _("Performance Data for Queue Length"),
                  label = _("Collect performance data for disk latency"),
                  help = _("Note: enabling performance data for the latency might "
                           "cause incompatibilities with existing historical data "
                           "if you are running PNP4Nagios in SINGLE mode.")),
            ),
        ]),
    OptionalDropdownChoice(
        choices = [ ( "SUMMARY",  _("Summary of all disks") ),
                    ( "read",     _("Summary of disk input (read)") ),
                    ( "write",    _("Summary of disk output (write)") ),
                  ],
        otherlabel = _("On explicit devices ->"),
        explicit = TextAscii(allow_empty = False),
        title = _("Device"),
        help = _("For a summarized throughput of all disks, specify <tt>SUMMARY</tt>, for a "
                 "sum of read or write throughput write <tt>read</tt> or <tt>write</tt> resp. "
                 "A per-disk IO is specified by the drive letter and a colon on Windows "
                 "(e.g. <tt>C:</tt>) or by the device name on Linux/UNIX (e.g. <tt>/dev/sda</tt>).")),
    "first"))


register_rule(
    group + '/' + subgroup_storage,
    "diskstat_inventory",
    ListChoice(
        title = _("Inventory mode for Disk IO check"),
        help = _("This rule controls which and how many checks will be created "
                 "for monitoring individual physical and logical disks."),
        choices = [ 
           ( "summary",  _("Create a summary over all physical disks") ),
           ( "legacy",   _("Create a summary for all read, one for write") ),
           ( "physical", _("Create a separate check for each physical disk") ),
           ( "lvm",      _("Create a separate check for each LVM volume (Linux)") ),
           ( "vxvm",     _("Creata a separate check for each VxVM volume (Linux)") ),
        ],
        default_value = [ 'summary' ],
    ),
    match="first")


checkgroups.append((
    subgroup_applications,
    "mailqueue_length",
    _("Number of mails in outgoing mail queue"),
    Tuple(
          help = _("These levels are applied to the number of Email that are "
                   "currently in the outgoing mail queue."),
          elements = [
              Integer(title = _("Warning at"), label = _("mails")),
              Integer(title = _("Critical at"), label = _("mails"))]),
    None, None))

checkgroups.append((
    subgroup_os,
    "uptime",
    _("Display the system's uptime as a check"),
    None,
    None, None))

checkgroups.append((
    subgroup_storage,
    "zpool_status",
    _("ZFS storage pool status"),
    None,
    None, None))

checkgroups.append((
    subgroup_virt,
    "vm_state",
    _("Overall state of a virtual machine"),
    None,
    None, None))

checkgroups.append((
    subgroup_hardware,
    "hw_errors",
    _("Simple checks for BIOS/Hardware errors"),
    None,
    None, None))

checkgroups.append((
    subgroup_applications,
    "omd_status",
    _("OMD site status"),
    None,
    TextAscii(
        title = _("Name of the OMD site"),
        help = _("The name of the OMD site to check the status for")),
    "first"))

checkgroups.append((
    subgroup_storage,
    "network_fs",
    _("Network filesystem - overall status (e.g. NFS)"),
    None,
    TextAscii(
        title = _("Name of the mount point"),
        help = _("For NFS enter the name of the mount point.")),
    "first"))

checkgroups.append((
     subgroup_storage,
    "multipath",
    _("Multipathing - health of a multipath LUN"),
    Integer(
        title = _("Expected number of active paths")),
    TextAscii(
        title = _("Name of the MP LUN"),
        help = _("For Linux multipathing this is either the UUID (e.g. "
                 "60a9800043346937686f456f59386741), or the configured "
                 "alias.")),
    "first"))

checkgroups.append((
     subgroup_storage,
    "hpux_multipath",
    _("Multipathing on HPUX - state of paths of a LUN"),
    Tuple(
        title = _("Expected path situation"),
        elements = [
            Integer(title = _("Number of active paths")),
            Integer(title = _("Number of standby paths")),
            Integer(title = _("Number of failed paths")),
            Integer(title = _("Number of unopen paths")),
        ]),
    TextAscii(
        title = _("WWID of the LUN")),
    "first"))


checkgroups.append((
    subgroup_applications,
    "services",
    _("Windows Services"),
    Dictionary(
        elements = [
            ( "states", 
              ListOf(
                Tuple(
                    orientation = "horizontal",
                    elements = [
                        DropdownChoice(
                            title = _("Expected state"),
                            default_value = "running",
                            choices = [
                                ( None, _("ignore the state") ),
                                ( "running", _("running") ),
                                ( "stopped", _("stopped") )]),
                        DropdownChoice(
                            title = _("Start type"),
                            default_value = "auto",
                            choices = [
                                ( None, _("ignore the start type") ),
                                ( "demand", _("demand") ),
                                ( "disabled", _("disabled") ),
                                ( "auto", _("auto") ),
                                ( "unknown", _("unknown (old agent)") ),
                            ]),
                        MonitoringState(
                            title = _("Resulting state"),
                        ),
                    ],
                    default_value = ( "running", "auto", 0)),
                title = _("Services states"),
                help = _("You can specify a separate monitoring state for each possible "
                         "combination of service state and start type. If you do not use " 
                         "this parameter, then only running/auto will be assumed to be OK."),
            )),
        ( "else",
           MonitoringState(
               title = _("State if no entry matches"),
               default_value = 2,
           ),
        ),]
    ),
    TextAscii(
        title = _("Name of the service"),
        help = _("Please Please note, that the agent replaces spaces in "
         "the service names with underscores. If you are unsure about the "
         "correct spelling of the name then please look at the output of "
         "the agent (cmk -d HOSTNAME). The service names  are in the first "
         "column of the section &lt;&lt;&lt;services&gt;&gt;&gt;. Please "
         "do not mix up the service name with the display name of the service."
         "The latter one is just being displayed as a further information."),
        allow_empty = False),
    "first"))

checkgroups.append((
    subgroup_storage,
    "raid",
    _("RAID: overall state"),
    None,
    TextAscii(
        title = _("Name of the device"),
        help = _("For Linux MD specify the device name without the "
                 "<tt>/dev/</tt>, e.g. <tt>md0</tt>, for hardware raids "
                 "please refer to the manual of the actual check being used.")),
    "first"))

checkgroups.append((
    subgroup_storage,
    "raid_disk",
    _("RAID: state of a single disk"),
    TextAscii(
        title = _("Target state"),
        help = _("State the disk is expected to be in. Typical good states "
            "are online, host spare, OK and the like. The exact way of how "
            "to specify a state depends on the check and hard type being used. "
            "Please take examples from inventorized checks for reference.")),
    TextAscii(
        title = _("Number or ID of the disk"),
        help = _("How the disks are named depends on the type of hardware being "
                 "used. Please look at already inventorized checks for examples.")),
    "first"))

checkgroups.append((
    subgroup_environment,
    "room_temperature",
    _("Room temperature (external thermal sensors)"),
    Tuple(
        help = _("Temperature levels for external thermometers that are used "
                 "for monitoring the temperature of a datacenter. An example "
                 "is the webthem from W&amp;T."),
        elements = [
            Integer(title = _("warning at"), unit = u"°C", default_value = 26),
            Integer(title = _("critical at"), unit = u"°C", default_value = 30),
        ]),
    TextAscii(
        title = _("Sensor ID"),
        help = _("The identificator of the themal sensor.")),
    "first"))

checkgroups.append((
    subgroup_environment,
    "eaton_enviroment",
    _("Temperature and Humidity for Eaton UPS"),
    Dictionary(
        elements = [
            ( "temp",
              Tuple(
                  title = _("Temerature"),
                  elements = [
                      Integer(title = _("warning at"), unit = u"°C", default_value = 26),
                      Integer(title = _("critical at"), unit = u"°C", default_value = 30),
                  ])),
            ( "remote_temp",
              Tuple(
                  title = _("Remote Temerature"),
                  elements = [
                      Integer(title = _("warning at"), unit = u"°C", default_value = 26),
                      Integer(title = _("critical at"), unit = u"°C", default_value = 30),
                  ])),
            ( "humidity",
              Tuple(
                  title = _("Humidity"),
                  elements = [
                      Integer(title = _("warning at"), unit = u"%", default_value = 60),
                      Integer(title = _("critical at"), unit = u"%", default_value = 75),
                  ])),
            ]),
            None,
    "first"))


checkgroups.append((
    subgroup_environment,
    "pdu_gude",
    _("Levels for Gude PDU Devices"),
    Dictionary(
        elements = [
            ( "kWh",
              Tuple(
                  title = _("Total accumulated Active Energy of Power Channel"),
                  elements = [
                      Integer(title = _("warning at"), unit = _("kW") ),
                      Integer(title = _("critical at"), unit = _("kW")),
                  ])),
            ( "W",
              Tuple(
                  title = _("Active Power"),
                  elements = [
                      Integer(title = _("warning at"), unit = _("W") ),
                      Integer(title = _("critical at"), unit = _("W") ),
                  ])),
            ( "A",
              Tuple(
                  title = _("Current on Power Channel"),
                  elements = [
                      Integer(title = _("warning at"), unit = _("A") ),
                      Integer(title = _("critical at"), unit = _("A")),
                  ])),
            ( "V",
              Tuple(
                  title = _("Voltage on Power Channel"),
                  elements = [
                      Integer(title = _("warning lower"), unit = _("V") ),
                      Integer(title = _("critical lower"), unit = _("V") ),
                  ])),
            ( "VA",
              Tuple(
                  title = _("Line Mean Apparent Power"),
                  elements = [
                      Integer(title = _("warning at"), unit = _("VA") ),
                      Integer(title = _("critical at"), unit = _("VA")),
                  ])),
            ]),
    TextAscii(
        title = _("Phase Number"),
        help = _("The Number of the power Phase.")),
    "first"))


checkgroups.append((
    subgroup_environment,
    "temperature_auto",
    _("Temperature sensors with builtin levels"),
    None,
    TextAscii(
        title = _("Sensor ID"),
        help = _("The identificator of the themal sensor.")),
    "first"))

checkgroups.append((
   subgroup_os,
    "ntp_time",
    _("State of NTP time synchronisation"),
    Tuple(
        elements = [
            Integer(
                title = _("Max. allowed stratum"),
                default_value = 10,
                help = _("The stratum (\"distance\" to the reference clock) at which the check gets critical."),
            ),
            Float(
                title = _("Warning at"),
                unit = _("Miliseconds"),
                default_value = 200.0,
                help = _("The offset in ms at which a warning state is triggered."),
            ),
            Float(
                title = _("Critical at"),
                unit = _("Miliseconds"),
                default_value = 500.0,
                help = _("The offset in ms at which a critical state is triggered."),
            ),
        ]
    ),
    None,
    "first"
))

checkgroups.append((
   subgroup_os,
    "apc_symentra",
    _("Levels for APC Symentra Check"),
    Tuple(
        elements = [
            Integer(
                title = _("Max. Crit Capacity"),
                help = _("The battery capacity in percent at and below which a critical state is be triggered"),
            ),
            Integer(
                title = _("Max. Battery Temperature"),
                help = _("The critical temperature of the battery"),
            ),
            Integer(
                title = _("Max. Current Power"),
                help = _("The critical battery current in Ampere"),
            ),
            Integer(
                title = _("Max. Voltage"),
                help = _("The output voltage at and below which a critical state is triggered."),
            ),
        ]
    ),
    None,
    "first"
))

syslog_facilities = [
    (0, "kern"),
    (1, "user"),
    (2, "mail"),
    (3, "daemon"),
    (4, "auth"),
    (5, "syslog"),
    (6, "lpr"),
    (7, "news"),
    (8, "uucp"),
    (9, "cron"),
    (10, "authpriv"),
    (11, "ftp"),
    (16, "local0"),
    (17, "local1"),
    (18, "local2"),
    (19, "local3"),
    (20, "local4"),
    (21, "local5"),
    (22, "local6"),
    (23, "local7"),
]

checkgroups.append((
    subgroup_applications,
    "logwatch_ec",
    _('Logwatch Event Console Forwarding'),
    Dictionary(
        elements = [
            ('method', Alternative(
                title = _("Forwarding Method"),
                elements = [
                    FixedValue(
                        None,
                        totext = "",
                        title = _("Send events to local event console in same OMD site"),
                    ),
                    TextAscii(
                        title = _("Send events to local event console into pipe"),
                        allow_empty = False,
                    ),
                    Tuple(
                        title = _("Send events to remote syslog host"),
                        elements = [
                            DropdownChoice(
                                choices = [
                                    ('udp', _('UDP')),
                                    ('tcp', _('TCP')),
                                ],
                                title = _("Protocol"),
                            ),
                            TextAscii(
                                title = _("Address"),
                                allow_empty = False,
                            ),
                            Integer(
                                title = _("Port"),
                                allow_empty = False,
                                default_value = 514,
                                minvalue = 1,
                                maxvalue = 65535,
                                size = 6,
                            ),
                        ]
                    ),
                ],
            )),
            ('facility', DropdownChoice(
                title = _("Syslog facility for forwarded messages"),
                help = _("When forwarding messages and no facility can be extracted from the "
                         "message this facility is used."),
                choices = syslog_facilities,
                default_value = 17, # local1
            )),
        ],
        optional_keys = [],
    ),
    None,
    'first'
))

# Create rules for check parameters of inventorized checks
for subgroup, checkgroup, title, valuespec, itemspec, matchtype in checkgroups:
    register_check_parameters(subgroup, checkgroup, title, valuespec, itemspec, matchtype)

checkgroups = []

register_rule(
    group + "/" + subgroup_networking,
    "if_disable_if64_hosts",
    title = _("Hosts forced to use <tt>if</tt> instead of <tt>if64</tt>"),
    help = _("A couple of switches with broken firmware report that they "
             "support 64 bit counters but do not output any actual data "
             "in those counters. Listing those hosts in this rule forces "
             "them to use the interface check with 32 bit counters instead."))


# Create Rules for static checks
register_rulegroup("static", _("Manual Checks"),
    _("Statically configured Check_MK checks that do not rely on the inventory"))


# wmic_process does not support inventory at the moment
checkgroups.append((
    subgroup_applications,
    "wmic_process",
    _("Memory and CPU of processes on Windows"),
    Tuple(
        elements = [
            TextAscii(
                title = _("Name of the process"),
                allow_empty = False,
            ),
            Integer(title = _("Memory warning at"), unit = "MB"),
            Integer(title = _("Memory critical at"), unit = "MB"),
            Integer(title = _("Pagefile warning at"), unit = "MB"),
            Integer(title = _("Pagefile critical at"), unit = "MB"), 
            Percentage(title = _("CPU usage warning at")),
            Percentage(title = _("CPU usage critical at")),
        ],
    ),
    TextAscii(
        title = _("Process name for usage in the Nagios service description"),
        allow_empty = False),
    "first"))

# Add checks that have parameters but are only configured as manual checks
checkgroups.append((
    subgroup_applications,
    "ps",
    _("State and count of processes"),
    Tuple(
        elements = [
            Alternative(
                title = _("Name of the process"),
                elements = [
                    TextAscii(
                        title = _("Exact name of the process without argments"),
                        size = 50,
                    ),
                    Transform(
                        RegExp(size = 50),
                        title = _("Regular expression matching command line"),
                        help = _("This regex must match the <i>beginning</i> of the complete "
                                 "command line of the process including arguments"),
                        forth = lambda x: x[1:],   # remove ~
                        back  = lambda x: "~" + x, # prefix ~
                    ),
                    FixedValue(
                        None,
                        totext = "",
                        title = _("Match all processes"),
                    )
                ],
                match = lambda x: (not x and 2) or (x[0] == '~' and 1 or 0)
                ),
            TextAscii(
                title = _("Name of operating system user"),
                help = _("Leave this empty, if the user does not matter"),
                none_is_empty = True,
            ),
            Integer(
                title = _("Minimum number of matched process for WARNING state"),
                default_value = 1,
            ),
            Integer(
                title = _("Minimum number of matched process for OK state"),
                default_value = 1,
            ),
            Integer(
                title = _("Maximum number of matched process for OK state"),
                default_value = 1,
            ),
            Integer(
                title = _("Maximum number of matched process for WARNING state"),
                default_value = 1,
            ),
        ]),
    TextAscii(
        title = _("Name of service"),
        help = _("This name will be used in the description of the service"),
        allow_empty = False,
        regex = "^[a-zA-Z_0-9 _.-]*$",
        regex_error = _("Please use only a-z, A-Z, 0-9, space, underscore, "
                        "dot and hyphon for your service description"),
    ),
    "first"))


for subgroup, checkgroup, title, valuespec, itemspec, matchtype in checkgroups:
    register_check_parameters(subgroup, checkgroup, title, valuespec, itemspec, matchtype, False)

