###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

import os
import base64
import hashlib
import asyncio

from notebook.auth import passwd as jupyter_passwd_hasher

from auto.services.scripts import SCRIPTS_DIRECTORY, run_script


async def change_system_password(system_user, new_password):
    loop = asyncio.get_running_loop()
    output = await loop.run_in_executor(None, _change_system_password, system_user, new_password)
    return 'success' in output.lower()


def _change_system_password(system_user, new_password):
    path = os.path.join(SCRIPTS_DIRECTORY, 'set_password')
    return run_script(path, new_password, system_user)


def derive_system_password(token):
    return _hashed_token(token, 'AutoAuto privileged system password salt value!', 12)


def derive_jupyter_password(token):
    jupyter_password = _hashed_token(token, 'AutoAuto Jupyter server password salt value!', 24)
    return jupyter_passwd_hasher(jupyter_password)


def derive_labs_auth_code(token):
    return _hashed_token(token, 'AutoAuto Lab single device authentication code!', 24)


def _hashed_token(token, salt, length):
    # The `token` is the "DEVICE_TOKEN" that this device uses to authenticate
    # with the Labs servers. It is stored in a permission-locked file that
    # only `root` can access. The `token` is unique to this device; it is set
    # _once_ when the device is first configured, and it should remain secret
    # for all of eternity.
    #
    # This function takes that `token`, and uses it to generate other secrets.
    # Namely, it is used to generate two other secrets:
    #
    #   1. It will be used to generate the default password for the privileged
    #      system user on this device (e.g. used by the owner of the device to
    #      `ssh` into the device). It is important that every device has a
    #      strong & unique default system password [1], thus using the `token`
    #      to generate it is a good solution.
    #
    #   2. It will be used to generate the password used to access this device's
    #      Jupyter server. It is important that the Jupyter server is locked-down
    #      (for obvious reasons), so once again, we'll use the `token` to create
    #      a strong & unique password to protect the Jupyter server running on this
    #      device.
    #
    # Note that the passwords generated here are one-way hashes of the `token`,
    # thus these passwords will not reveal any information about the original
    # token, which is highly important.
    #
    # It is also important that the two uses above result in _different_ passwords.
    # To achieve this we will salt each differently (using the `salt` parameter
    # passed here). They should be _different_ because each grants a different
    # level of access to the device (the first is a _privileged_ system user, while
    # the second is an _unprivileged_ Jupyter server).
    #
    # The password generated by the first usage above will be written-down and
    # sent with the physical device to its owner. It is the responsibility of the
    # owner to (1) keep it secret, and (2) change it (using `passwd`) for the highest
    # amount of security. (Note: This is similar to what WiFi routers do with
    # their devices.)
    #
    # The password generated by the second usage above will not be written-down.
    # Instead it will be used to generate a link to the Jupyter server from the
    # owner's AutoAuto Labs account. Again, it is the owner's responsibility to not
    # share that link.
    #
    # [1] The reason it's important to have strong & unique default passwords
    #     is because we really don't want AutoAuto devices used in an IoT botnet...
    #     we assume you agree :) For example, see [this story](http://goo.gl/sbq4it).

    m = hashlib.sha256()
    m.update(salt.encode('utf-8'))
    m.update(token.encode('utf-8'))
    hash_bytes = m.digest()
    hash_base64 = base64.b64encode(hash_bytes)
    password = hash_base64[:length].decode('utf-8')
    password = password.replace('/', '_').replace('+', '_')  # '/' and '+' are confusing for users to see in a password; this replacement is easier on the eyes and only decreases the level of security by a miniscule amount (the password length is plenty long, and we're just giving up 1 character from an alphabet of 64.)
    return password

