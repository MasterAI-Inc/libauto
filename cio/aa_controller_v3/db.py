###############################################################################
#
# Copyright (c) 2017-2023 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This module contains a simple sqlite-backed key-value store for persisting
settings of your individual device.
"""

import os
import sqlite3


DEFAULT_DB_PATH = os.environ.get('MAI_LIBAUTO_DEFAULT_DB_PATH', '/var/lib/libauto')


def default_db(same_thread=False):
    """
    Get a new instance of the default KeyValueStore used by this library.

    This file should store things that all users may read. The permissions
    for this file will be such that only the owner may write, but everyone
    may read.
    """
    db_path = os.path.join(DEFAULT_DB_PATH, 'settings.db')
    store = KeyValueStore(db_path, same_thread=same_thread)
    return store


class KeyValueStore:
    """
    This class uses sqlite to persist a simple and flexible key-value store.
    """

    CREATE_TABLE = '''
        CREATE TABLE IF NOT EXISTS key_value_store (
            k BLOB PRIMARY KEY,
            v BLOB
        )
    '''

    def __init__(self, db_file_path, same_thread=False):
        """
        Initialize this key-value store using the sqlite database at `db_file_path`
        as the backing store. If that file does not exist, it will be
        created as an empty store.

        If you are _certain_ that this key-value store will only be used
        by a single thread, you can set `same_thread` equal to True and
        see a little bit of run-time speedup.
        """
        self.db_file_path = db_file_path
        self.db = None
        self.first = True
        if same_thread:
            self.db = self._get_db()
        else:
            _ = self._get_db()   # <-- to handle the self.first case

    def _get_db(self):
        """
        Private method to obtain a database connection.

        If this object was told it would be single-threaded,
        then this method will simply return the single database
        connection which will already be on-hand.

        If this object is in a multi-threaded application, this
        method will open a new database connection every time it
        is invoked.
        """
        if self.db:
            return self.db
        else:
            db = sqlite3.connect(self.db_file_path)
            if self.first:
                db.execute(KeyValueStore.CREATE_TABLE)
                db.commit()
                self.first = False
            return db

    def get(self, key, default_value=None, set_default=False):
        """
        Query the key-value store to obtain the value corresponding to the
        given `key`. If the key does not exist, the `default_value` will
        be retuned.
        """
        query = 'SELECT v FROM key_value_store WHERE k=?'
        db = self._get_db()
        cur = db.execute(query, (key, ))
        rv = cur.fetchall()
        if rv:
            value = rv[0][0]
        else:
            value = default_value
            if set_default:
                self.put(key, value)
        cur.close()
        db.commit()
        return value

    def put(self, key, value):
        """
        Store the given `key`-`value` pair into the database. If the given
        `key` is already in the database, its value will be overwritten with
        the given `value`.
        """
        query = 'INSERT OR REPLACE INTO key_value_store (k, v) VALUES (?, ?)'
        db = self._get_db()
        cur = db.execute(query, (key, value))
        c = cur.rowcount
        cur.close()
        db.commit()
        return c

    def __getitem__(self, key):
        """
        Magic method which invokes the `get()` method for you.
        """
        return self.get(key)

    def __setitem__(self, key, value):
        """
        Magic method which invokes the `put()` method for you.
        """
        return self.put(key, value)

