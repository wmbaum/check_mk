#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# +------------------------------------------------------------------+
# |             ____ _               _        __  __ _  __           |
# |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
# |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
# |           | |___| | | |  __/ (__|   <    | |  | | . \            |
# |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
# |                                                                  |
# | Copyright Mathias Kettner 2013             mk@mathias-kettner.de |
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


class MKAutomationError(Exception):
    def __init__(self, reason):
        self.reason = reason
    def __str__(self):
        return self.reason

def do_automation(cmd, args):
    try:
        if cmd == "get-configuration":
            read_config_files(with_autochecks=False, with_conf_d=False)
            result = automation_get_configuration()
        elif cmd == "get-check-information":
            result = automation_get_check_information()
        elif cmd == "delete-host":
            read_config_files(with_autochecks=False)
            result = automation_delete_host(args)
        else:
            read_config_files()
            if cmd == "try-inventory":
                result = automation_try_inventory(args)
            elif cmd == "inventory":
                result = automation_inventory(args)
            elif cmd == "get-autochecks":
                result = automation_get_autochecks(args)
            elif cmd == "set-autochecks":
                result = automation_set_autochecks(args)
            elif cmd == "reload":
                result = automation_restart("reload")
            elif cmd == "restart":
                result = automation_restart("restart")
            elif cmd == "scan-parents":
                result = automation_scan_parents(args)
            elif cmd == "diag-host":
                result = automation_diag_host(args)
            elif cmd == "create-snapshot":
                result = automation_create_snapshot(args)
            else:
                raise MKAutomationError("Automation command '%s' is not implemented." % cmd)

    except MKAutomationError, e:
        sys.stderr.write("%s\n" % e)
        if opt_debug:
            raise
        output_profile()
        sys.exit(1)

    except Exception, e:
        if opt_debug:
            raise
        else:
            sys.stderr.write("%s\n" % e)
            output_profile()
            sys.exit(2)

    if opt_debug:
        import pprint
        sys.stdout.write(pprint.pformat(result)+"\n")
    else:
        sys.stdout.write("%r\n" % (result,))
    output_profile()
    sys.exit(0)

# Does inventory for *one* host. Possible values for how:
# "new" - find only new services (like -I)
# "remove" - remove exceeding services
# "fixall" - find new, remove exceeding
# "refresh" - drop all services and reinventorize
def automation_inventory(args):
    global opt_use_cachefile, inventory_max_cachefile_age, check_max_cachefile_age

    # perform full SNMP scan on SNMP devices?
    if args[0] == "@scan":
        with_snmp_scan = True
        args = args[1:]
    else:
        with_snmp_scan = False

    # use cache files if present?
    if args[0] == "@cache":
        opt_use_cachefile = True
        inventory_max_cachefile_age = 1000000000
        check_max_cachefile_age = 1000000000
        args = args[1:]
    else:
        opt_use_cachefile = False
        inventory_max_cachefile_age = -1

    if len(args) < 2:
        raise MKAutomationError("Need two arguments: new|remove|fixall|refresh HOSTNAME")

    how = args[0]
    hostnames = args[1:]

    counts = {}
    failed_hosts = {}
    k = globals().keys()
    if how == "refresh":
        for hostname in hostnames:
            counts.setdefault(hostname, [0, 0, 0, 0]) # added, removed, kept, new
            counts[hostname][1] += remove_autochecks_of(hostname) # checktype could be added here
	reread_autochecks()

    for hostname in hostnames:
        counts.setdefault(hostname, [0, 0, 0, 0]) # added, removed, kept, new

        try:
            # Compute current state of new and existing checks
            table = automation_try_inventory([hostname], leave_no_tcp=True, with_snmp_scan=with_snmp_scan)

            # Create new list of checks
            new_items = []
            for entry in table:
                state_type, ct, checkgroup, item, paramstring = entry[:5]
                if state_type in [ "legacy", "active", "manual", "ignored" ]:
                    continue # this is not an autocheck or ignored and currently not checked

                if state_type == "new":
                    if how in [ "new", "fixall", "refresh" ]:
                        counts[hostname][0] += 1
                        new_items.append((ct, item, paramstring))

                elif state_type == "old":
                    # keep currently existing valid services in any case
                    new_items.append((ct, item, paramstring))
                    counts[hostname][2] += 1

                elif state_type in [ "obsolete", "vanished" ]:
                    # keep item, if we are currently only looking for new services
                    # otherwise fix it: remove ignored and non-longer existing services
                    if how not in [ "fixall", "remove" ]:
                        new_items.append((ct, item, paramstring))
                        counts[hostname][2] += 1
                    else:
                        counts[hostname][1] += 1

            automation_write_autochecks_file(hostname, new_items)
            counts[hostname][3] += len(new_items)

        except Exception, e:
	    if opt_debug:
                raise
            failed_hosts[hostname] = str(e)

    return counts, failed_hosts


def automation_try_inventory(args, leave_no_tcp=False, with_snmp_scan=False):
    global opt_use_cachefile, inventory_max_cachefile_age, check_max_cachefile_age
    if args[0] == '@noscan':
        args = args[1:]
        with_snmp_scan = False
        opt_use_cachefile = True
        check_max_cachefile_age = 1000000000
        inventory_max_cachefile_age = 1000000000
    elif args[0] == '@scan':
        args = args[1:]
        with_snmp_scan = True
        leave_no_tcp = True

    hostname = args[0]

    # hostname might be a cluster. In that case we compute the clustered
    # services of that cluster.
    services = []
    if is_cluster(hostname):
        already_added = set([])
        for node in nodes_of(hostname):
            new_services = automation_try_inventory_node(node, leave_no_tcp=leave_no_tcp, with_snmp_scan=with_snmp_scan)

            for entry in new_services:
                if host_of_clustered_service(node, entry[6]) == hostname:
                    # 1: check, 6: Service description
                    if (entry[1], entry[6]) not in already_added:
                        services.append(entry)
                        already_added.add((entry[1], entry[6])) # make it unique

        # Find manual checks for this cluster
        cluster_checks = get_check_table(hostname)
        for (ct, item), (params, descr, deps) in cluster_checks.items():
            if (ct, descr) not in already_added:
                services.append(("manual", ct, None, item, repr(params), params, descr, 0, "", None))
                already_added.add( (ct, descr) ) # make it unique

    else:
        new_services = automation_try_inventory_node(hostname, leave_no_tcp=leave_no_tcp, with_snmp_scan=with_snmp_scan)
        for entry in new_services:
            host = host_of_clustered_service(hostname, entry[6])
            if host == hostname:
                services.append(entry)
            else:
                services.append(("clustered",) + entry[1:])

    return services



def automation_try_inventory_node(hostname, leave_no_tcp=False, with_snmp_scan=False):
    global opt_use_cachefile, opt_no_tcp, opt_dont_submit

    try:
        ipaddress = lookup_ipaddress(hostname)
    except:
        raise MKAutomationError("Cannot lookup IP address of host %s" % hostname)

    found_services = []

    dual_host = is_snmp_host(hostname) and is_tcp_host(hostname)

    # if we are using cache files, then we restrict us to existing
    # check types. SNMP scan is only done without the --cache option
    snmp_error = None
    if is_snmp_host(hostname):
        try:
            if not with_snmp_scan:
                existing_checks = set([ cn for (cn, item) in get_check_table(hostname) ])
                for cn in inventorable_checktypes("snmp"):
                    if cn in existing_checks:
                        found_services += make_inventory(cn, [hostname], True, True)
            else:
                if not in_binary_hostlist(hostname, snmp_without_sys_descr):
                    sys_descr = get_single_oid(hostname, ipaddress, ".1.3.6.1.2.1.1.1.0")
                    if sys_descr == None:
                        raise MKSNMPError("Cannot get system description via SNMP. "
                                          "SNMP agent is not responding. Probably wrong "
                                          "community or wrong SNMP version. IP address is %s" %
                                           ipaddress)

                found_services = do_snmp_scan([hostname], True, True)

        except Exception, e:
            if not dual_host:
                raise
            snmp_error = str(e)

    tcp_error = None

    # Honor piggy_back data, even if host is not declared as TCP host
    if is_tcp_host(hostname) or \
           get_piggyback_info(hostname) or get_piggyback_info(ipaddress):
        try:
            for cn in inventorable_checktypes("tcp"):
                found_services += make_inventory(cn, [hostname], True, True)
        except Exception, e:
            if not dual_host:
                raise
            tcp_error = str(e)

    # raise MKAutomationError("%s/%s/%s" % (dual_host, snmp_error, tcp_error))
    if dual_host and snmp_error and tcp_error:
        raise MKAutomationError("Error using TCP (%s)\nand SNMP (%s)" %
                (tcp_error, snmp_error))

    found = {}
    for hn, ct, item, paramstring, state_type in found_services:
       found[(ct, item)] = ( state_type, paramstring )

    # Check if already in autochecks (but not found anymore)
    for hn, ct, item, params in autochecks:
        if hn == hostname and (ct, item) not in found:
            found[(ct, item)] = ( 'vanished', repr(params) ) # This is not the real paramstring!

    # Find manual checks
    existing = get_check_table(hostname)
    for (ct, item), (params, descr, deps) in existing.items():
        if (ct, item) not in found:
            found[(ct, item)] = ('manual', repr(params) )

    # Add legacy checks and active checks with artificial type 'legacy'
    legchecks = host_extra_conf(hostname, legacy_checks)
    for cmd, descr, perf in legchecks:
        found[('legacy', descr)] = ( 'legacy', 'None' )

    # Add custom checks and active checks with artificial type 'custom'
    custchecks = host_extra_conf(hostname, custom_checks)
    for entry in custchecks:
        found[('custom', entry['service_description'])] = ( 'custom', 'None' )

    # Similar for 'active_checks', but here we have parameters
    for acttype, rules in active_checks.items():
        act_info = active_check_info[acttype]
        entries = host_extra_conf(hostname, rules)
        for params in entries:
            descr = act_info["service_description"](params)
            found[(acttype, descr)] = ( 'active', repr(params) )

    # Collect current status information about all existing checks
    table = []
    for (ct, item), (state_type, paramstring) in found.items():
        params = None
        if state_type not in [ 'legacy', 'active', 'custom' ]:
            # apply check_parameters
            try:
                if type(paramstring) == str:
                    params = eval(paramstring)
                else:
                    params = paramstring
            except:
                raise MKAutomationError("Invalid check parameter string '%s'" % paramstring)

            descr = service_description(ct, item)
            global g_service_description
            g_service_description = descr
            infotype = ct.split('.')[0]

            # Sorry. The whole caching stuff is the most horrible hack in
            # whole Check_MK. Nobody dares to clean it up, YET. But that
            # day is getting nearer...
            old_opt_use_cachefile = opt_use_cachefile
            opt_use_cachefile = True
	    if not leave_no_tcp:
	        opt_no_tcp = True
            opt_dont_submit = True

            try:
                exitcode = None
                perfdata = []
                info = get_host_info(hostname, ipaddress, infotype)
            # Handle cases where agent does not output data
            except MKAgentError, e:
                exitcode = 3
                output = "Error getting data from agent"
                if str(e):
                    output += ": %s" % e
                tcp_error = output

            except MKSNMPError, e:
                exitcode = 3
                output = "Error getting data from agent for %s via SNMP" % infotype
                if str(e):
                    output += ": %s" % e
                snmp_error = output

            except Exception, e:
                exitcode = 3
                output = "Error getting data for %s: %s" % (infotype, e)
                if check_uses_snmp(ct):
                    snmp_error = output
                else:
                    tcp_error = output

            opt_use_cachefile = old_opt_use_cachefile

            if exitcode == None:
                check_function = check_info[ct]["check_function"]
                if state_type != 'manual':
                    params = compute_check_parameters(hostname, ct, item, params)

                try:
                    result = check_function(item, params, info)
                except MKCounterWrapped, e:
                    result = (None, "WAITING - Counter based check, cannot be done offline")
                except Exception, e:
                    result = (3, "UNKNOWN - invalid output from agent or error in check implementation")
                if len(result) == 2:
                    result = (result[0], result[1], [])
                exitcode, output, perfdata = result
        else:
            descr = item
            exitcode = None
            output = "WAITING - %s check, cannot be done offline" % state_type.title()
            perfdata = []

        if state_type == "active":
            params = eval(paramstring)

        if state_type in [ "legacy", "active", "custom" ]:
            checkgroup = None
            if service_ignored(hostname, None, descr):
                state_type = "ignored"
        else:
            checkgroup = check_info[ct]["group"]

        table.append((state_type, ct, checkgroup, item, paramstring, params, descr, exitcode, output, perfdata))

    if not table and (tcp_error or snmp_error):
        error = ""
        if snmp_error:
            error = "Error getting data via SNMP: %s" % snmp_error
        if tcp_error:
            if error:
                error += ", "
            error += "Error getting data from Check_MK agent: %s" % tcp_error
        raise MKAutomationError(error)

    return table

# Set the new list of autochecks. This list is specified by a
# table of (checktype, item). No parameters are specified. Those
# are either (1) kept from existing autochecks or (2) computed
# from a new inventory. Note: we must never convert check parameters
# from python source code to actual values.
def automation_set_autochecks(args):
    hostname = args[0]
    new_items = eval(sys.stdin.read())
    do_cleanup_autochecks()

    # A Cluster does not have an autochecks file
    # All of its services are located in the nodes instead
    # So we cycle through all nodes remove all clustered service
    # and add the ones we've got from stdin
    if is_cluster(hostname):
        for node in nodes_of(hostname):
            new_autochecks = []
            existing = automation_parse_autochecks_file(node)
            for ct, item, params, paramstring in existing:
                descr = service_description(ct, item)
                if hostname != host_of_clustered_service(node, descr):
                    new_autochecks.append((ct, item, paramstring))
            for (ct, item), paramstring in new_items.items():
                new_autochecks.append((ct, item, paramstring))
            # write new autochecks file for that host
            automation_write_autochecks_file(node, new_autochecks)
    else:
        existing = automation_parse_autochecks_file(hostname)
        # write new autochecks file, but take paramstrings from existing ones
        # for those checks which are kept
        new_autochecks = []
        for ct, item, params, paramstring in existing:
            if (ct, item) in new_items:
                new_autochecks.append((ct, item, paramstring))
                del new_items[(ct, item)]

        for (ct, item), paramstring in new_items.items():
            new_autochecks.append((ct, item, paramstring))

        # write new autochecks file for that host
        automation_write_autochecks_file(hostname, new_autochecks)


def automation_get_autochecks(args):
    hostname = args[0]
    do_cleanup_autochecks()
    return automation_parse_autochecks_file(hostname)

def automation_write_autochecks_file(hostname, table):
    if not os.path.exists(autochecksdir):
        os.makedirs(autochecksdir)
    path = "%s/%s.mk" % (autochecksdir, hostname)
    f = file(path, "w")
    f.write("# Autochecks for host %s, created by Check_MK automation\n[\n" % hostname)
    for ct, item, paramstring in table:
        f.write("  (%r, %r, %r, %s),\n" % (hostname, ct, item, paramstring))
    f.write("]\n")
    if inventory_check_autotrigger and inventory_check_interval:
        schedule_inventory_check(hostname)

def schedule_inventory_check(hostname):
    try:
        import socket
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(livestatus_unix_socket)
        now = int(time.time())
        command = "SCHEDULE_FORCED_SVC_CHECK;%s;Check_MK inventory;%d" % (hostname, now)
        s.send("COMMAND [%d] %s\n" % (now, command))
    except Exception, e:
        if opt_debug:
            raise


def automation_parse_autochecks_file(hostname):
    def split_python_tuple(line):
        quote = None
        bracklev = 0
        backslash = False
        for i, c in enumerate(line):
            if backslash:
                backslash = False
                continue
            elif c == '\\':
                backslash = True
            elif c == quote:
                quote = None # end of quoted string
            elif c in [ '"', "'" ]:
                quote = c # begin of quoted string
            elif quote:
                continue
            elif c in [ '(', '{', '[' ]:
                bracklev += 1
            elif c in [ ')', '}', ']' ]:
                bracklev -= 1
            elif bracklev > 0:
                continue
            elif c == ',':
                value = line[0:i]
                rest = line[i+1:]
                return value.strip(), rest
        return line.strip(), None

    path = "%s/%s.mk" % (autochecksdir, hostname)
    if not os.path.exists(path):
        return []
    lineno = 0

    table = []
    for line in file(path):
        lineno += 1
        try:
            line = line.strip()
            if not line.startswith("("):
                continue

            # drop everything after potential '#' (from older versions)
	    i = line.rfind('#')
	    if i > 0: # make sure # is not contained in string
		rest = line[i:]
		if '"' not in rest and "'" not in rest:
		    line = line[:i].strip()

            if line.endswith(","):
                line = line[:-1]
            line = line[1:-1] # drop brackets

            hostnamestring, line = split_python_tuple(line) # should be hostname
            checktypestring, line = split_python_tuple(line)
            itemstring, line = split_python_tuple(line)
            paramstring, line = split_python_tuple(line)
            table.append((eval(checktypestring), eval(itemstring), eval(paramstring), paramstring))
        except:
            if opt_debug:
                raise
            raise MKAutomationError("Invalid line %d in autochecks file %s" % (lineno, path))
    return table

def automation_delete_host(args):
    hostname = args[0]
    for path in [
        "%s/%s"    % (precompiled_hostchecks_dir, hostname),
        "%s/%s.py" % (precompiled_hostchecks_dir, hostname),
        "%s/%s.mk" % (autochecksdir, hostname),
        "%s/%s"    % (logwatch_dir, hostname),
        "%s/%s"    % (counters_directory, hostname),
        "%s/%s"    % (tcp_cache_dir, hostname),
        "%s/%s.*"  % (tcp_cache_dir, hostname)]:
        os.system("rm -rf '%s'" % path)

def automation_restart(job="restart"):
    # make sure, Nagios does not inherit any open
    # filedescriptors. This really happens, e.g. if
    # check_mk is called by WATO via Apache. Nagios inherits
    # the open file where Apache is listening for incoming
    # HTTP connections. Really.
    if monitoring_core == "nagios":
        objects_file = nagios_objects_file
        for fd in range(3, 256):
            try:
                os.close(fd)
            except:
                pass
    else:
        objects_file = var_dir + "/core/config"
        job = "reload" # force reload for CMC

    # os.closerange(3, 256) --> not available in older Python versions

    class null_file:
        def write(self, stuff):
           pass
        def flush(self):
           pass

    # Deactivate stdout by introducing fake file without filedescriptor
    old_stdout = sys.stdout
    sys.stdout = null_file()

    try:
        backup_path = None
        if not lock_objects_file():
            raise MKAutomationError("Cannot activate changes. "
                  "Another activation process is currently in progresss")

        if os.path.exists(objects_file):
            backup_path = objects_file + ".save"
            os.rename(objects_file, backup_path)
        else:
            backup_path = None

        try:
            if monitoring_core == "nagios":
                create_nagios_config(file(objects_file, "w"))
            else:
                do_create_cmc_config(opt_cmc_relfilename)

        except Exception, e:
	    if backup_path:
		os.rename(backup_path, objects_file)
            if opt_debug:
                raise
	    raise MKAutomationError("Error creating configuration: %s" % e)

        if do_check_nagiosconfig():
            if backup_path:
                os.remove(backup_path)
            if monitoring_core != "cmc":
                do_precompile_hostchecks()
            if job == 'restart':
                do_restart_core(False)
            elif job == 'reload':
                do_restart_core(True)
        else:
            if backup_path:
                os.rename(backup_path, objects_file)
            else:
                os.remove(objects_file)
            raise MKAutomationError("Configuration for monitoring core is invalid. Rolling back.")

    except Exception, e:
        if backup_path and os.path.exists(backup_path):
            os.remove(backup_path)
        if opt_debug:
            raise
        raise MKAutomationError(str(e))

    sys.stdout = old_stdout

def automation_get_configuration():
    # We read the list of variable names from stdin since
    # that could be too much for the command line
    variable_names = eval(sys.stdin.read())
    result = {}
    for varname in variable_names:
        if varname in globals():
            result[varname] = globals()[varname]
    return result

def automation_get_check_information():
    manuals = all_manuals()
    checks = {}
    for check_type, check in check_info.items():
        manfile = manuals.get(check_type)
        if manfile:
            title = file(manfile).readline().strip().split(":", 1)[1].strip()
        else:
            title = check_type
        checks[check_type] = { "title" : title }
        if check["group"]:
            checks[check_type]["group"] = check["group"]
        checks[check_type]["service_description"] = check.get("service_description","%s")
        checks[check_type]["snmp"] = check_uses_snmp(check_type)
    return checks

def automation_scan_parents(args):
    settings = {
        "timeout"     : int(args[0]),
        "probes"      : int(args[1]),
        "max_ttl"     : int(args[2]),
        "ping_probes" : int(args[3]),
    }
    hostnames = args[4:]
    traceroute_prog = find_bin_in_path('traceroute')
    if not traceroute_prog:
        raise MKAutomationError("Cannot find binary <tt>traceroute</tt> in search path.")

    try:
        gateways = scan_parents_of(hostnames, silent=True, settings=settings)
        return gateways
    except Exception, e:
        raise MKAutomationError(str(e))

def automation_diag_host(args):
    hostname, test, ipaddress, snmp_community = args[:4]
    agent_port, snmp_timeout, snmp_retries = map(int, args[4:7])
    cmd = args[7]

    if not ipaddress:
        try:
            ipaddress = lookup_ipaddress(hostname)
        except:
            raise MKGeneralException("Cannot resolve hostname %s into IP address" % hostname)

    try:
        if test == 'ping':
            import subprocess
            p = subprocess.Popen('ping -A -i 0.2 -c 2 -W 5 %s 2>&1' % ipaddress, shell = True, stdout = subprocess.PIPE)
            response = p.stdout.read()
            return (p.wait(), response)

        elif test == 'agent':
            if not cmd:
                cmd = get_datasource_program(hostname, ipaddress)

            if cmd:
                return 0, get_agent_info_program(cmd)
            else:
                return 0, get_agent_info_tcp(hostname, ipaddress, agent_port or None)

        elif test.startswith('snmp'):
            if snmp_community:
                explicit_snmp_communities[hostname] = snmp_community

            # override timing settings if provided
            if snmp_timeout or snmp_retries:
                timing = {}
                if snmp_timeout:
                    timing['timeout'] = snmp_timeout
                if snmp_retries:
                    timing['retries'] = snmp_retries
                snmp_timing.insert(0, (timing, [], [hostname]))

            # SNMP versions
            global bulkwalk_hosts, snmpv2c_hosts
            if test == 'snmpv2':
                bulkwalk_hosts = [hostname]

            elif test == 'snmpv2_nobulk':
                bulkwalk_hosts = []
                snmpv2c_hosts  = [hostname]
            elif test == 'snmpv1':
                bulkwalk_hosts = []
                snmpv2c_hosts  = []

            else:
                return 1, "SNMP command not implemented"

            data = get_snmp_table(hostname, ipaddress, ('.1.3.6.1.2.1.1', ['1.0', '4.0', '5.0', '6.0']))
            if data:
                return 0, 'sysDescr:\t%s\nsysContact:\t%s\nsysName:\t%s\nsysLocation:\t%s\n' % tuple(data[0])
            else:
                return 1, 'Got empty SNMP response'

        else:
            return 1, "Command not implemented"

    except Exception, e:
        return 1, str(e)

def automation_create_snapshot(args):
    try:
        import tarfile, time, cStringIO, shutil, subprocess, thread, traceback, threading
        the_data = sys.stdin.read()
        data = eval(the_data)

        snapshot_name = data["snapshot_name"]
        snapshot_dir  = var_dir + "/wato/snapshots"
        work_dir       = snapshot_dir + "/workdir"
        if not os.path.exists(work_dir):
            os.makedirs(work_dir)

        # Open / initialize files
        filename_target = "%s/%s"        % (snapshot_dir, snapshot_name)
        filename_work   = "%s/%s.work"   % (work_dir, snapshot_name)
        filename_status = "%s/%s.status" % (work_dir, snapshot_name)
        filename_pid    = "%s/%s.pid"    % (work_dir, snapshot_name)
        filename_subtar = ""
        current_domain  = ""

        file(filename_target, "w").close()
        file(filename_status, "w").close()

        lock_status_file = threading.Lock()
        def update_status_file(domain = None, infotext = None):
            lock_status_file.acquire()
            if os.path.exists(filename_status):
                if domain:
                    statusinfo[domain] = infotext
                statusfile = file(filename_status, "w")
                statusfile.write("comment:%s\n" % data.get("comment"," ").encode("utf-8"))
                status_list = list(statusinfo.items())
                status_list.sort()
                for status in status_list:
                    statusfile.write("%s:%s\n" % status)
            lock_status_file.release()

        # Set initial status info
        statusinfo = {}
        for name in data.get("domains", {}).keys():
            statusinfo[name] = "TODO"
        update_status_file()

        if not data.get("wait"):
            try:
                pid = os.fork()
                if pid > 0:
                    # Exit parent process
                    return
                # Decouple from parent environment
                os.chdir("/")
                os.umask(0)
                os.setsid()
                for fd in range(0, 256):
                    try:
                        os.close(fd)
                    except OSError:
                        pass
            except OSError, e:
                raise MKAutomationError(str(e))

        # Save pid of working process.
        file(filename_pid, "w").write("%d" % os.getpid())
        tar_in_progress = tarfile.open(filename_work, "w")

        def cleanup():
            for filename in [filename_work, filename_status,
                             filename_pid, filename_subtar]:
                if filename and os.path.exists(filename):
                    os.unlink(filename)

        def check_should_abort():
            if not os.path.exists(filename_target):
                cleanup()
                sys.exit(0)

        def get_basic_tarinfo(name):
            tarinfo = tarfile.TarInfo(name)
            tarinfo.mtime = time.time()
            tarinfo.uid   = 0
            tarinfo.gid   = 0
            tarinfo.mode  = 0644
            tarinfo.type  = tarfile.REGTYPE
            return tarinfo

        def update_subtar_size(seconds):
            while current_domain != None:
                try:
                    if current_domain:
                        if os.path.exists(filename_subtar):
                            update_status_file(current_domain, "Processing / Size: %d" % os.stat(filename_subtar).st_size)
                except:
                    pass
                time.sleep(0.1)

        # Add comment to tar file
        if data.get("comment"):
            tarinfo       = get_basic_tarinfo("comment")
            tarinfo.size  = len(data.get("comment").encode("utf-8"))
            tar_in_progress.addfile(tarinfo, cStringIO.StringIO(data.get("comment").encode("utf-8")))

        if data.get("created_by"):
            tarinfo       = get_basic_tarinfo("created_by")
            tarinfo.size  = len(data.get("created_by"))
            tar_in_progress.addfile(tarinfo, cStringIO.StringIO(data.get("created_by")))

        # Add snapshot type
        snapshot_type = data.get("type")
        tarinfo       = get_basic_tarinfo("type")
        tarinfo.size  = len(snapshot_type)
        tar_in_progress.addfile(tarinfo, cStringIO.StringIO(snapshot_type))

        # Close tar in progress, all other files are included via command line tar
        tar_in_progress.close()

        # Process domains (sorted)
        subtar_update_thread = thread.start_new_thread(update_subtar_size, (1,))
        domains = map(lambda x: x, data.get("domains").items())
        domains.sort()

        for name, info in domains:
            current_domain = name # Set name for update size thread
            paths  = info["paths"]
            prefix = info.get("prefix","")
            check_should_abort()

            paths = map(lambda x: x[1] == "" and "." or x[1], paths)

            # Create tar.gz subtar
            filename_subtar = "%s.tar.gz" % name
            command = "cd %s ; tar czf %s --ignore-failed-read --force-local -C %s %s" %  (work_dir, filename_subtar, prefix, " ".join(paths))
            proc = subprocess.Popen(command, shell=True)
            proc.wait()

            subtar_size   = os.stat("%s/%s" % (work_dir, filename_subtar)).st_size

            # Append tar.gz subtar to snapshot
            command = "cd %s ; tar --append --file=%s %s ; rm %s" % (work_dir, filename_work, filename_subtar, filename_subtar)
            proc = subprocess.Popen(command, shell=True)
            proc.wait()

            current_domain = ""
            update_status_file(name, "Finished / Size: %d" % subtar_size)

        current_domain = None

        shutil.move(filename_work, filename_target)
        cleanup()

    except Exception, e:
        raise MKAutomationError(str(e))


