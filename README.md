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

Пример веб-сервиса
```python
from k2.aeon import Aeon, Response, SiteModule
Aeon(
    port=8080,
    namespace={
        '/': type(
            'cgi',
            (SiteModule,),
            {
                'get': lambda request: Response(
                    code=200,
                    data='<br>'.join(
                        [
                            'requested url: %s ? %s' % (request.url, request.args),
                        ] + [
                            '%s: %s' % (header, value)
                            for header, value in request.headers.items()
                        ]
                    )
                )
            }
        ),
    }
).run()
```

## Зависимости  
* pygost - Криптографическая библиотека  
