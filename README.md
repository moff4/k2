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
import k2.aeon
server = k2.aeon.Aeon(port=8080)
server.add_site_module(
    key='/',
    target=type(
        'cgi',
        (),
        {
            'get': lambda req: k2.aeon.Response(code=200, data='requested url: %s' % req.url)
        }
    )
)
server.run()
```

## Зависимости  
* pygost - Криптографическая библиотека  
