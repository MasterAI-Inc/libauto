###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

import re
import asyncio


class Verification:

    def __init__(self, console):
        self.console = console

    async def init(self):
        pass

    async def connected_cdp(self):
        pass

    async def new_user_session(self, username, user_session):
        pass

    async def got_message(self, msg, send_func):
        if 'origin' in msg and msg['origin'] == 'server':
            if 'verification_text' in msg:
                username = msg['username']
                verification_text = msg['verification_text']
                expire_minutes = msg['expire_minutes']
                coro = self._show_verification_text(username, verification_text, expire_minutes)

            elif 'verification_success' in msg:
                if msg['verification_success']:
                    username = msg['username']
                    coro = self._show_verification_success(username)

                else:
                    reason = msg['reason']
                    coro = self._show_verification_failed(reason)

            else:
                return

            asyncio.create_task(coro)

    async def end_user_session(self, username, user_session):
        pass

    async def disconnected_cdp(self):
        pass

    async def _show_verification_text(self, username, verification_text, expire_minutes):
        text = "Hi {}!\nAuthentication Code:\n{}\n".format(username, verification_text)
        await self.console.big_image('pair_pending')
        await self.console.big_status(text)
        await self.console.write_text(text + "\n\n")
        # TODO Use the `expire_minutes`. E.g. Put a countdown on the screen
        # and auto-close the pairing image when the countdown expires.

    async def _show_verification_success(self, username):
        text = "Congrats {}!\nYou are now paired\nwith this device.\n".format(username)
        await self.console.big_image('pair_success')
        await self.console.big_status(text)
        await self.console.write_text(text + "\n\n")
        await asyncio.sleep(5)
        await self.console.big_clear()

    async def _show_verification_failed(self, reason):
        reason = re.sub(r'\<.*?\>', '', reason)
        text = "Error:\n{}\n\n".format(reason)
        await self.console.big_image('pair_error')
        await self.console.big_status("Error:\nTry again.")
        await self.console.write_text(text + "\n\n")
        await asyncio.sleep(5)
        await self.console.big_clear()

