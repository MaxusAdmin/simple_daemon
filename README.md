# Simple Daemon - уж очень простой daemon #

**Назначение:** Данный модуль был разработан для более эффективной интеграции прикладных программ в ОС в качестве 
"сервисов" системы systemd. Сервис (в рамках данного модуля) - это такая программа, 
которая работает по принципу "While True: pass".

**Каждый сервис должен:**
* уметь обрабатывать сигналы (SIGINT, SIGTERM).
* иметь подсистему логирования (как минимум 2 уровня логирования: debug, info).
* иметь два режима обработки прерываний (агрессивный и пассивный).

**Описание возможностей:**
1. **Обработка сигналов прерывания.** Когда используется цикл работы программы типа - "While True: pass", то нужно
   иметь возможно корректно прерывать работы данного цикла. Прервать работу можно агрессивно (когда нужно чтобы
   программа не завершала какие-либо действия и просто закончила свою работу) и пассивно (когда нужно выполнить
   какие-либо действия без прерывания а после прервать закончить свою работу (break)).

   Класс SimpleDaemon имеет параметр interrupt_mode, который определяет режим прерываний (True - агрессивный,
   False - пассивный).

   При агрессивном режиме работы будет возбуждаться исключение SimpleDaemonExit.
   При пассивном режиме работы переменная interrupted == True и исключение не возбуждается.
2. **Подсистема логирования. Подсистема логирования базируется но модуле logging.**
   Наименование приложения - SimpleDaemon.name_app
   Основное метсо журнала событий (log - файла, можно переопределить) - SimpleDaemon.log_path
   Основное наименованиа журнала событий (log - файла, можно переопределить) - - SimpleDaemon.log_name
   Формат сообщений (можно переопределить) - SimpleDaemon.log_format
   Вывод сообщений в stdout (можно переопределить, default: False) - SimpleDaemon.stream_handlers

   HandlerS:
         - FileHandler:
            Основное метсо журнала событий (log - файла, можно переопределить) - SimpleDaemon.log_path
            Основное наименованиа журнала событий (log - файла, можно переопределить) - - SimpleDaemon.log_name
         - Stream(Stdout)
            Вывод сообщений в stdout (можно переопределить, default: False) - SimpleDaemon.stream
         - Syslog(Systemd)
            Вывод сообщений в /dev/log (можно переопределить, default: False) - SimpleDaemon.syslog
            Примечаение:
            Фильтрация событий journalctl
                1. journalctl -f (real time)
                2. journalctl _PID=$PID (filter on PID)
                3. journalctl _UID=$ID (filter on user $ID)
                4. journalctl -F _UID (Вывести на консоль список пользователей, о которых имеются записи в логах, можно
                   так:)

   Ротация журнала событий:
     Максимальный размер журнала в мегабайт (можно переопределить, default: 1mb) - SimpleDaemon.max_size_byte_log
     Максимальное кол-во файлов ротации (можно переопределить, default: 2) - SimpleDaemon.max_count_file_rotation

   Уровни логирования класса SimpleDaemon:
    - info: int 20
    - debug: int 10

   Доступные уровни логирования для разработчика - наследуются от модуля logg
  
 **Алгоритм работы:**
1. Инициализация подсистемы логирования __get_logger()
2. Инициализация обработчиков сигналов прерывания __signal_handler()
3. Возвращение объекта класса SimpleDaemon
4. Ожидание прерывания
    1. Возбуждение исключения SimpleDaemonExit, при interrupt_mode == True
    2. Изменение переменной interrupted == True, при interrupt_mode == False
    
## Примеры использования: ##
**Для пассивного режима прерывания:**
```python
from time import sleep as sp
from simple_daemon import SimpleDaemon

with SimpleDaemon('MyDaemon') as sdh:
    while True:
        if sdh.interrupted: 
            break
        sp(60)
    
        if sdh.interrupted:
            break
```
tail -f /tmp/simple_daemon.log

    2018-11-27 13:47:59,971 - MyDaemon - INFO - PID: 9215
    2018-11-27 13:47:59,972 - MyDaemon - DEBUG - Set signal handler: 2
    2018-11-27 13:47:59,972 - MyDaemon - DEBUG - Set signal handler: 15
    2018-11-27 13:47:59,972 - MyDaemon - INFO - Mode: PASSIVE

kill -15 $PID

    2018-11-27 13:50:07,032 - MyDaemon - INFO - interrupted == True
    2018-11-27 13:50:07,032 - MyDaemon - INFO - Received 2 signal.
    
**Для агрессивного режима прерывания:**
```python
    from time import sleep as sp
    from simple_daemon import SimpleDaemon

    try:
        with SimpleDaemon('MyDaemon', interrupted_mode=True) as sdh:
            while True:
                sp(60)
    except Exception as e:
        pass
```
stdout
    
    SimpleDaemon Exit
   
tail -f /var/log/simple_daemon.log
    
    2018-11-27 13:57:16,124 - MyDaemon - INFO - PID: 9450
    2018-11-27 13:57:16,125 - MyDaemon - DEBUG - Set signal handler: 2
    2018-11-27 13:57:16,125 - MyDaemon - DEBUG - Set signal handler: 15
    2018-11-27 13:57:16,125 - MyDaemon - INFO - Mode: AGGRESSIVE

kill -15 $PID

    2018-11-27 13:57:39,517 - MyDaemon - INFO - Received 2 signal.
    2018-11-27 13:57:39,517 - MyDaemon - INFO - Graceful Interrupt...


