import pexpect
import time
import hashlib
import base64


def change_password(system_user, new_password):

    p = pexpect.spawn('sudo', ['passwd', system_user], timeout=5)

    for i in range(2):
        p.expect('new.*password.*:')
        time.sleep(0.5)
        p.sendline(new_password)

    p.expect('.*success')


def token_to_password(token):
    # The goal here is to take the token (which is already secret; it is used
    # for authentication with the AutoAuto servers), and use it to seed a default
    # password to use on this AutoAuto device. This will ensure that every
    # AutoAuto device has a strong, unique password, which is extremely important!
    # (Reason it's important: We really don't want AutoAuto devices used in an
    # IoT botnet... we assume you agree. See [this story](http://goo.gl/sbq4it).)
    #
    # The password will be deterministically computed from the token by this
    # function. We will write down this default password and send it with the
    # physical device (similar to what wifi routers do). We don't want that
    # written-down password to expose too much info about the device, so we'll
    # use a one-way hash to compute it (i.e. so that you can't use the password
    # to derive the original token; the token must be kept completely secret!)

    m = hashlib.sha256()
    m.update('AutoAuto is awesome.'.encode('utf-8')) # Salt value, to invalidate rainbow tables.
    m.update(token.encode('utf-8'))
    hash_bytes = m.digest()
    hash_base64 = base64.b64encode(hash_bytes)
    return hash_base64[:12].decode('utf-8')   # 12 characters is plenty safe, we think.

