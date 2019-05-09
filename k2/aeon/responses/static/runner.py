#!/usr/bin/env python3


class ScriptRunner:

    def __init__(self, text, logger):
        self.text = text if isinstance(text, str) else text.decode()
        self._logger = logger
        self.scripts_info = [
            ('<!--#@', '#@-->', self._run_1_0),
            ('<!--#', '#-->', self._run_1_1),
            ('/*#', '#*/', self._run_1_1),
        ]

    async def _run_1_1(self, text, args):
        text = '\n'.join(
            [
                x.strip()
                for x in text.split('\n')
                if x and not x.isspace()
            ]
        )
        try:
            return str(eval(text, args, {}))
        except Exception as e:
            await self._logger.exception(f'Unexpectedly got: {e}')

    async def _run_1_0(self, text, args):
        text = '\n'.join(
            [
                x
                for x in text.split('\n')
                if x and not x.isspace()
            ]
        )
        local = {'result': ''}
        try:
            exec(text, args, local)
            return str(local['result'])
        except Exception as e:
            await self._logger.exception(f'Unexpectedly got: {e}')

    async def run(self, args):
        text = self.text
        k = 0
        for sci in self.scripts_info:
            while sci[0] in text and sci[1] in text:
                i = text.index(sci[0])
                j = text.index(sci[1])
                pt1 = text[:i]
                pt2 = text[j + len(sci[1]):]
                script = text[i + len(sci[0]):j]
                result = await sci[2](script, args)
                if result is None:
                    await self._logger.error(f'script #{k} ({script[:15]}{"..." if len(script) >= 25 else ""}) failed')
                    return False
                text = pt1 + result + pt2
                k += 1
        self.text = text
        return True

    def export(self):
        return self.text
