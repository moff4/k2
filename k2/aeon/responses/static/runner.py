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
        try:
            return str(
                eval(
                    '\n'.join(
                        [
                            x.strip()
                            for x in text.split('\n')
                            if x and not x.isspace()
                        ]
                    ),
                    args,
                    {},
                ),
            )
        except Exception:
            await self._logger.exception('Unexpectedly got:')

    async def _run_1_0(self, text, args):
        try:
            exec(
                '\n'.join(
                    [
                        x
                        for x in text.split('\n')
                        if x and not x.isspace()
                    ]
                ),
                args,
                (local := {'result': ''}),
            )
            return str(local['result'])
        except Exception:
            await self._logger.exception('Unexpectedly got:')

    async def run(self, args):
        text = self.text
        k = 0
        for sci in self.scripts_info:
            while sci[0] in text and sci[1] in text:
                pt1 = text[:(i := text.index(sci[0]))]
                pt2 = text[(j := text.index(sci[1])) + len(sci[1]):]
                result = await sci[2](text[i + len(sci[0]):j], args)
                if result is None:
                    await self._logger.error('script #{} ({script[:15]}{"..." if len(script) >= 25 else ""}) failed', k)
                    return False
                text = pt1 + result + pt2
                k += 1
        self.text = text
        return True

    def export(self):
        return self.text
