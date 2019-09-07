# K2

Библиотека для удобной организации архитектуры небольших программ.  

Уже имеет в себе:  
- Aeon - асинхронный веб сервер  
- Tokenazer - генерация и валидация токенов и сессионных кук  
- Planner - асинхронный планеровщик  
- Stats - агрегатор статистики  
- Logger - управление логированием  

## Установка

Установка производится через утилиту pip:  
```bash
$ pip install git+https://github.com/moff4/k2.git  
```  
или через ручную сборку:  
```bash
$ python3 setup.py build  
$ python3 setup.py install  
```

## Примеры

#### Пример веб-сервиса
```python
from k2.aeon import (
    Aeon,
    Response,
    SiteModule,
)
from k2.aeon.sitemodules import Rederict

class Handler(SiteModule):
    def get(self, request):
        data = '<br>'.join(
            [
                'requested url: %s ? %s' % (request.url, request.args),
            ] + [
                '%s: %s' % (header, value)
                for header, value in request.headers.items()
            ]
        )
        return Response(
            code=200,
            data=data,
        )

server = Aeon(
    port=8080,
    namespace={
        '^/$': Rederict(
            location='/index.html',
        ),
        '^/not_found.html': Response(code=404, data='Not Found'),
        '^/+': Handler(),
    }
)
server.run()
```

#### Пример крон-сервиса  
```python
import time
import asyncio

from k2.planner import Planner

t = 0
def print_time():
    global t
    _t = time.time()
    print('%.2f seconds passed since last call' % (_t - t))
    t = _t

pl = Planner()
pl.add_task(target=print_time, interval={'sec': 3})
pl.run()
asyncio.get_event_loop().run_forever()
```

## Зависимости  
* pygost - Криптографическая библиотека  
