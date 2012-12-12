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

import config, defaults
from lib import *
import time
from valuespec import *

# Datastructures and functions needed before plugins can be loaded
loaded_with_language = False

# Load all login plugins
def load_plugins():
    global loaded_with_language
    if loaded_with_language == current_language:
        return

    # declare & initialize global vars
    global multisite_user_connectors ; multisite_user_connectors = []

    load_web_plugins("userdb", globals())

    # This must be set after plugin loading to make broken plugins raise
    # exceptions all the time and not only the first time (when the plugins
    # are loaded).
    loaded_with_language = current_language


def list_user_connectors():
    return [ (c['id'], c['title']) for c in multisite_user_connectors ]

def connector_enabled(connector_id):
    return connector_id in config.user_connectors

def enabled_connectors():
    connectors = []
    for connector in multisite_user_connectors:
        if connector['id'] in config.user_connectors:
            connectors.append(connector)
    return connectors

def get_connector_id(connector_id):
    if connector_id is None:
        connector_id = 'htpasswd'
    return connector_id

# Returns the connector dictionary of the given id
def get_connector(connector_id):
    connector_id = get_connector_id(connector_id)
    for connector in enabled_connectors():
        if connector['id'] == connector_id:
            return connector
    return {}

# Returns a list of locked attributes
def locked_attributes(connector_id):
    connector = get_connector(connector_id)
    return connector.get('locked_attributes', lambda: [])()

# Returns a list of multisite attributes
def multisite_attributes(connector_id):
    connector = get_connector(connector_id)
    return connector.get('multisite_attributes', lambda: [])()

# Returns a list of non contact attributes
def non_contact_attributes(connector_id):
    connector = get_connector(connector_id)
    return connector.get('non_contact_attributes', lambda: [])()

# This is a function needed in WATO and the htpasswd module. This should
# really be modularized one day. Till this day this is a good place ...
def encrypt_password(password, salt = None):
    import md5crypt
    if not salt:
        salt = "%06d" % (1000000 * (time.time() % 1.0))
    return md5crypt.md5crypt(password, salt, '$1$')

def new_user_template(connector_id):
    new_user = {
        'serial':        0,
        'connector':     connector_id,
    }

    # Apply the default user profile
    new_user.update(config.default_user_profile)
    return new_user

def create_non_existing_user(connector_id, username):
    import wato
    users = wato.load_users()
    if username in users:
        return # User exists. Nothing to do...

    users[username] = new_user_template(connector_id)
    wato.save_users(users)

    # Call the sync function for this new user
    hook_sync(connector_id = connector_id, only_username = username)

def user_locked(username):
    import wato
    users = wato.load_users()
    return users[username].get('locked', False)

#   .----------------------------------------------------------------------.
#   |                     _   _             _                              |
#   |                    | | | | ___   ___ | | _____                       |
#   |                    | |_| |/ _ \ / _ \| |/ / __|                      |
#   |                    |  _  | (_) | (_) |   <\__ \                      |
#   |                    |_| |_|\___/ \___/|_|\_\___/                      |
#   |                                                                      |
#   +----------------------------------------------------------------------+

# This hook is called to validate the login credentials provided by a user
def hook_login(username, password):
    for connector in enabled_connectors():
        handler = connector.get('login', None)
        if not handler:
            continue

        result = handler(username, password)
        # None  -> User unknown, means continue with other connectors
        # True  -> success
        # False -> failed
        if result == True:
            # Check wether or not the user exists (and maybe create it)
            create_non_existing_user(connector['id'], username)

            # Now, after successfull login (and optional user account
            # creation), check wether or not the user is locked.
            # In e.g. htpasswd connector this is checked by validating the
            # password against the hash in the htpasswd file prefixed with
            # a "!". But when using other conectors it might be neccessary
            # to validate the user "locked" attribute.
            lock_handler = connector.get('locked', None)
            if lock_handler:
                result = not lock_handler(username) # returns True if locked

            return result

        elif result == False:
            return result

# Hook function can be registered here to be executed to synchronize all users.
# Is called on:
#   a) before rendering the user management page in WATO
#   b) a user is created during login (only for this user)
def hook_sync(connector_id = None, add_to_changelog = False, only_username = None):
    if connector_id:
        connectors = [ get_connector(connector_id) ]
    else:
        connectors = enabled_connectors()

    for connector in connectors:
        handler = connector.get('sync', None)
        if handler:
            try:
                handler(add_to_changelog, only_username)
            except MKLDAPException, e:
                if config.debug:
                    import traceback
                    html.show_error(
                        "<h3>" + _("Error executing sync hook") + "</h3>"
                        "<pre>%s</pre>" % (traceback.format_exc())
                    )
                else:
                    html.show_error(
                        "<h3>" + _("Error executing sync hook") + "</h3>"
                        "<pre>%s</pre>" % (e)
                    )
            except:
                import traceback
                html.show_error(
                    "<h3>" + _("Error executing sync hook") + "</h3>"
                    "<pre>%s</pre>" % (traceback.format_exc())
                )

# Hook function can be registered here to be executed during saving of the
# new user construct
def hook_save(users):
    for connector in enabled_connectors():
        handler = connector.get('save', None)
        if not handler:
            continue
        try:
            handler(users)
        except:
            if config.debug:
                import traceback
                html.show_error(
                    "<h3>" + _("Error executing sync hook") + "</h3>"
                    "<pre>%s</pre>" % (traceback.format_exc())
                )
            else:
                raise

# This function registers general stuff, which is independet of the single
# connectors to each page load. It is exectued AFTER all other page hooks.
def general_page_hook():
    # Working around the problem that the auth.php file needed for multisite based
    # authorization of external addons might not exist when setting up a new installation
    # We assume: Each user must visit this login page before using the multisite based
    #            authorization. So we can easily create the file here if it is missing.
    # This is a good place to replace old api based files in the future.
    auth_php = defaults.var_dir + '/wato/auth/auth.php'
    if not os.path.exists(auth_php) or os.path.getsize(auth_php) == 0:
        import wato
        wato.create_auth_file(wato.load_users())

    # Create initial auth.serials file, same issue as auth.php above
    serials_file = '%s/auth.serials' % os.path.dirname(defaults.htpasswd_file)
    if not os.path.exists(serials_file):
        import wato
        wato.save_users(wato.load_users())

# Hook function can be registered here to execute actions on a "regular" base without
# user triggered action. This hook is called on each page load.
# Catch all exceptions and log them to apache error log. Let exceptions raise trough
# when debug mode is enabled.
def hook_page():
    for connector in enabled_connectors():
        handler = connector.get('page', None)
        if not handler:
            continue
        try:
            handler()
        except:
            if config.debug:
                raise
            else:
                import traceback
                html.log('Exception (%s, page handler): %s' % 
                            (connector['id'], traceback.format_exc()))

    general_page_hook()
