import json
import requests
from mmpy_bot import Plugin, listen_to, listen_webhook, WebHookEvent, \
    ActionEvent, Message
import re
from dataclasses import dataclass, asdict
from typing import Optional
import click
from pathlib import Path
import schedule
from mmpy_bot.plugins.base import log
import firebirdsql
import mattermostautodriver
import datetime
import asyncio
from config import confluence_url, host, database, user, password, charset, webhookHostUrl, headers, \
    webhook_host_port, mattermost_host, mattermost_port, webhook_host_url, MATTERMOST_URL, MATTERMOST_PORT, headers
from reminder import send_message_to_channel


@dataclass
class Field:
    title: str
    value: str
    short: bool = True

@dataclass
class Section:
    title: Optional[str] = None
    text: Optional[str] = None
    fields: Optional[list[Field]] = None
    def asdict(self):
        res = {}
        if self.fields:
            res['fields'] = [asdict(field) for field in self.fields]
        if self.title:
            res['title'] = str(self.title)
        if self.text:
            res['text'] = str(self.text)
        return res

class SearchPlugin(Plugin):
    @listen_to("задач", re.IGNORECASE)
    async def hello(self, message: Message):
        # log.info(message.body)
        mes_json = {
            'attachments': [
                {
                    "actions": [
                        {
                            "id": "createTask",
                            "name": "Создать задачу",
                            "integration": {
                                "url": f"{webhookHostUrl}:{webhook_host_port}/hooks/createTask",
                                "context": dict(reply_id=message.reply_id, message=message.text),
                            },
                        }
                    ]
                }
            ]
        }
        data = {'id': message.id, 'message': message.text, 'props': mes_json}
        response = requests.put(f"{MATTERMOST_URL}:{MATTERMOST_PORT}/api/v4/posts/{message.id}",
                                json=data, headers=headers)
        if response.status_code == 200:
            log.info('Message sent successfully.')
            log.info(response.json())
        else:
            log.info(f'Failed to send message: {response.status_code}, {response.text}')

    @listen_webhook("createTask")
    async def createTask(self, event: WebHookEvent):
        # log.info(event.body['user_id'])
        msg_body = event.body['context']['reply_id']
        msg = Message(msg_body)
        today = datetime.datetime.strftime(datetime.date.today(), '%d.%m.%y')
        # log.info(event.body['channel_id'])
        # with firebirdsql.connect(host=host, database=database, user=user, password=password, charset=charset) as con:
        #     cur = con.cursor()
        #     try:
        #         sql = f"""SELECT
        #         F4601 AS number,
        #         T214.F4600 AS typeWork
        #         FROM T212
        #         JOIN T214 ON T212.ID = T214.F4606 AND T212.F4644 = 'ae4smat5obr1dx4ahmky5kjpce'"""
        #         # {event.body['channel_id']}
        #         cur.execute(sql)
        #         result = cur.fetchall()
        #         columns = ('value', 'text')
        #         json_result = [
        #             {col: value for col, value in zip(columns, row)}
        #             for row in result
        #         ]
        #         log.info(json_result)
        #     except Exception as ex:
        #         log.info(f"НЕ удалось получить работы договора {ex}")
        if isinstance(event, ActionEvent):
            payload = {
                "trigger_id": event.body['trigger_id'],
                "url": f"{webhookHostUrl}:{webhook_host_port}/hooks/addTask",
                "dialog": {
                    "callback_id": f'{msg_body}',
                    "title": "Добавление задачи",
                    'introduction_text': f"Постановщик задачи: {event.body['user_name']}",
                    "elements": [
                        {
                            "display_name": "Задача",
                            "placeholder": "Задача",
                            "name": "task",
                            "type": "text",
                            'default': event.body['context']['message']
                        },
                        {
                            "display_name": "Исполнитель",
                            "name": "executor",
                            "type": "select",
                            "data_source": "users"
                            # , 'default': event.body['user_id']
                        },
                        {
                            "display_name": "Комментарий",
                            "placeholder": "Комментарий",
                            "name": "comment",
                            "type": "text",
                            "optional": True
                        },
                        {
                            "display_name": "Дата начала",
                            "name": "dateStart",
                            "type": "text",
                            'default': today,
                            'help_text': 'Формат даты: ДД.ММ.ГГ'
                        },
                        {
                            "display_name": "Дедлайн",
                            "name": "dateEnd",
                            "type": "text",
                            'default': today,
                            'help_text': 'Формат даты: ДД.ММ.ГГ'
                        }
                        # {
                        #     "display_name": "Вид работы",
                        #     "name": "typeWork",
                        #     "type": "select",
                        #     'options': List
                        #     # , 'default': event.body['user_name']
                        # }
                    ],
                    "submit_label": "Cоздать",
                    "state": "somestate"
                }
            }
            requests.post(f"{MATTERMOST_URL}:{MATTERMOST_PORT}/api/v4/actions/dialogs/open",
                          json=payload)
        else:
            self.driver.reply_to(msg, "Что-то пошло не так")

    @listen_webhook("addTask")
    async def addTask(self, event: WebHookEvent):
        msg_body = dict(data=dict(post=dict(channel_id=event.body['channel_id'], root_id=event.body['callback_id'])))
        msg = Message(msg_body)
        try:
            log.info(event.body)
            idMessage = event.body['callback_id']
            # log.info(idMessage)
            task = event.body.get('submission').get('task')
            # log.info(task)
            comment = event.body.get('submission').get('comment')
            # log.info(comment)
            dateStart = event.body.get('submission').get('dateStart')
            # log.info(dateStart)
            deadline = event.body.get('submission').get('dateEnd')
            # log.info(deadline)
            directorId = event.body.get('user_id')
            # log.info(directorId)
            executorId = event.body.get('submission').get('executor')
            # log.info(executorId)
            with (firebirdsql.connect(host=host, database=database, user=user, password=password, charset=charset) as con):
                cur = con.cursor()
                sql = f"""SELECT ID FROM T212 WHERE F4644 = '{event.body.get('channel_id')}'"""
                cur.execute(sql)
                contractId = cur.fetchall()[0][0]
                # log.info(contractId)
                sql = f"""SELECT ID FROM T3 WHERE F16 = '{directorId}'"""
                cur.execute(sql)
                directorId = cur.fetchall()[0][0]
                # log.info(directorId)
                sql = f"""SELECT ID FROM T3 WHERE F16 = '{executorId}'"""
                cur.execute(sql)
                executorId = cur.fetchall()[0][0]
                # log.info(executorId)
                cur.execute(f'SELECT GEN_ID(GEN_T218, 1) FROM RDB$DATABASE')
                ID = cur.fetchonemap().get('GEN_ID', None)
                values = {
                    'id': ID,
                    'F4691': contractId,
                    'F4695': task,
                    'F4698': comment,
                    'F4970': dateStart,
                    'F5569': dateStart,
                    'F4696': deadline,
                    'F4693': directorId,  # должно быть ID пользователя
                    'F4694': executorId,
                    'F4697': 0,
                    'F5451': idMessage
                }
                sql_values = []
                for key, value in values.items():
                    if value is None:
                        sql_values.append('NULL')
                    elif isinstance(value, (int, float)):
                        sql_values.append(str(value))
                    elif isinstance(value, str):
                        sql_values.append(f"'{value}'")
                    else:
                        raise ValueError(f"Unsupported type for value: {value}")
                sql = f"""INSERT INTO T218 ({', '.join(values.keys())}) VALUES ({', '.join(sql_values)})"""
                cur.execute(sql)
                con.commit()
                data = {'id': idMessage, 'message': f'{task}\nЗадача успешно создана в МПК24'}
                response = requests.put(f"{MATTERMOST_URL}:{MATTERMOST_PORT}/api/v4/posts/{idMessage}",
                              json=data, headers=headers)
                if response.status_code == 200:
                    log.info('Message sent successfully.')
                    log.info(response.json())
                else:
                    log.info(f'Failed to send message: {response.status_code}, {response.text}')
        except Exception as ex:
            self.driver.reply_to(msg, f"Ошибка при создании задачи: {ex}")
        log.info(f"Веб-хук addTask выполнен: {datetime.datetime.now()}")

#     @listen_to("^((?!Найди).)*$", re.IGNORECASE)
#     async def hello(self, message: Message, status):
#         blocks = [
#             Section(
#                 title=f'Приветствую!',
#                 text=f'Я осуществляю поиск по базе знаний [wiki]({confluence_url}). Поиск осуществляется только по публичным страницам.\nЧтобы начать поиск используйте слово **Найди** и ваш запрос, пример: **Найди цели и планы**',
#                 fields=list(filter(None, [
#                     Field(
#                         title='Поиск осуществляется с предустановленными настройками:',
#                         value='', short=False),
#                     Field(title='Пространства', value='QA, DEV'),
#                     Field(title='Период', value='Последний год'),
#                     Field(title='Содержимое', value='Страница'),
#                 ]
#                                    )
#                             )
#             )
#         ]
#         mes_json = {'attachments': [block.asdict() for block in blocks]}
#         self.driver.reply_to(message, '', props=mes_json)
#
#     def search_by_label(self, submission):
#         sql = 'select'
#         if submission.get('speedLimit') != '' and submission.get('speedLimit') is not None:
#             sql += f" first {submission.get('speedLimit')}"
#
#         sql += f" * from T4 where f7 like '%{submission.get('search')}%'"
#
#         if submission.get('where') != '' and submission.get('where') is not None and submission.get('someId') != '' and submission.get('someId') is not None:
#             sql += f" and id {submission.get('where')} {submission.get('someId')}"
#
#         if submission.get('orderAll') != '' and submission.get('orderAll') is not None:
#             sql += f" order by {submission.get('orderAll')}"
#
#         if submission.get('orderBy') != '' and submission.get('orderBy') is not None:
#             sql += f" {submission.get('orderBy')}"
#         json_result = ''
#         with firebirdsql.connect(
#             host=host,
#             database=database,
#             user=user,
#             password=password,
#             charset=charset
#         ) as con:
#             cur = con.cursor()
#             cur.execute(sql)
#             result = cur.fetchall()
#             columns = ('id', 'post')
#             json_result = [
#                 {col: value for col, value in zip(columns, row)}
#                 for row in result
#             ]
#             submission.update({"search_results": json_result})
#         return submission
#
#     @listen_to("Найди (.*)", re.IGNORECASE)
#     async def search(self, message: Message, text_to_search):
#         log.info(f'Запрошен поиск "{text_to_search}"')
#         search = {}
#         search.update({'search': text_to_search})
#         search = self.search_by_label(search)
#         self.print_search_result(message, search)
#
#     def print_search_result(self, message: Message, search):
#         total_count = len(search.get('search_results'))
#
#         if total_count > 0:
#             blocks = [
#                 Section(text=f"Вот **ТОП-{max(total_count, 5)}** того что я нашел по запросу \"***{search.get('search')}***\":")
#             ]
#             message_json = {
#                 'attachments': [block.asdict() for block in blocks]}
#             self.driver.reply_to(message, '', props=message_json)
#
#             for result in search.get('search_results')[0:5]:
#                 title = result.get('id')
#                 excerpt = result.get('post').replace("@@@hl@@@", "**").replace(
#                     "@@@endhl@@@", "**")
#                 blocks = [
#                     Section(title=f'{title}',
#                             text=f'{excerpt}'
#                             )
#                 ]
#                 mes_json = {
#                     'attachments': [block.asdict() for block in blocks]}
#                 self.driver.reply_to(message, '', props=mes_json)
#
#             if total_count > 5:
#                 self.driver.reply_to(
#                     message,
#                     "",
#                     props={
#                         "attachments": [
#                             {
#                                 "pretext": None,
#                                 "text": f"Всего найдено **{total_count}** записей. Вывести остальные {total_count - 5} результатов поиска?",
#                                 "actions": [
#                                     {
#                                         "id": "yes",
#                                         "name": "Да",
#                                         "integration": {
#                                             "url": f"{webhookHostUrl}:{webhook_host_port}/hooks/yes",
#                                             "context": dict(
#                                                 channel_id=message.channel_id,
#                                                 reply_id=message.reply_id,
#                                                 search_response=search.get('search_results'))
#                                         },
#                                     },
#                                     {
#                                         "id": "advanced",
#                                         "name": "Расширенный поиск",
#                                         "integration": {
#                                             "url": f"{webhookHostUrl}:{webhook_host_port}"
#                                                    "/hooks/advanced",
#                                             "context": dict(
#                                                 channel_id=message.channel_id,
#                                                 reply_id=message.reply_id,
#                                                 search_text=search.get('search'))
#                                         },
#                                     },
#                                 ],
#                             }
#                         ]
#                     },
#                 )
#             else:
#                 blocks = [
#                     Section(
#                         text=f'Всего найдено **{total_count}** записей.'
#                     )
#                 ]
#                 message_json = {
#                     'attachments': [block.asdict() for block in blocks]}
#                 self.driver.reply_to(message, '', props=message_json)
#
#         else:
#             blocks = [
#                 Section(
#                     text=f"По запросу \"***{search.get('search')}***\" ничего не найдено."
#                 )
#             ]
#             message_json = {
#                 'attachments': [block.asdict() for block in blocks]}
#             self.driver.reply_to(message, '', props=message_json)
#
#     @listen_webhook("yes")
#     async def yes(self, event: WebHookEvent):
#         msg_body = dict(data=dict(
#             post=dict(channel_id=event.body['context']['channel_id'],
#                       root_id=event.body['context']['reply_id'])))
#         msg = Message(msg_body)
#         for result in event.body['context']['search_response'][5:]:
#             title = result.get('id')
#             excerpt = result.get('post').replace("@@@hl@@@", "**").replace(
#                 "@@@endhl@@@", "**")
#             blocks = [
#                 Section(title=f'{title}',
#                         text=f'{excerpt}'
#                         )
#             ]
#             mes_json = {
#                 'attachments': [block.asdict() for block in blocks]}
#             self.driver.reply_to(msg, '', props=mes_json)
#
#     @listen_webhook("advanced")
#     async def advanced_search_form(self, event: WebHookEvent):
#         msg_body = dict(data=dict(
#             post=dict(channel_id=event.body['context']['channel_id'], root_id=event.body['context']['reply_id'])))
#         search_text = event.body['context']['search_text']
#         msg = Message(msg_body)
#         if isinstance(event, ActionEvent):
#             payload = {
#                 "trigger_id": event.body['trigger_id'],
#                 "url": f"{webhookHostUrl}:{webhook_host_port}/hooks/adv_search",
#                 "dialog": {
#                     "callback_id": f'{msg_body}',
#                     "title": "Расширенный поиск",
#                     "elements": [
#                         {
#                             "display_name": "Строка поиска",
#                             "placeholder": "Искать указанную должность",
#                             "default": f'{search_text}',
#                             "name": "search",
#                             "type": "text",
#                             "optional": False
#                         },
#                         {
#                             "display_name": "Сортировать по полю:",
#                             "name": "orderAll",
#                             "type": "select",
#                             "optional": True,
#                             "options": [{"text": "должности",
#                                          "value": "f7"},
#                                         {"text": "id",
#                                          "value": "id"}],
#                             "default": "id"
#                         },
#                         {
#                             "display_name": "Сортировать по:",
#                             "name": "orderBy",
#                             "type": "select",
#                             "optional": True,
#                             "options": [{"text": "убыванию",
#                                          "value": "desc"},
#                                         {"text": "возрастанию",
#                                          "value": "asc"}],
#                             "default": "asc"
#                         },
#                         {
#                             "display_name": "Кол-во выводимых записей",
#                             "name": "speedLimit",
#                             "type": "text",
#                             "subtype": "number",
#                             "optional": True,
#                             "help_text": "Оставьте пустым, чтобы вывести все записи."
#                         },
#                         {
#                             "display_name": "Дополнительный фильтр по полю id:",
#                             "name": "where",
#                             "type": "select",
#                             "optional": True,
#                             "options": [{"text": "больше",
#                                          "value": ">"},
#                                         {"text": "меньше",
#                                          "value": "<"},
#                                         {"text": "равно",
#                                          "value": "="},]
#                         },
#                         {
#                             "display_name": "",
#                             "name": "someId",
#                             "help_text": "Целевое значение фильтра",
#                             "type": "text",
#                             "subtype": "number",
#                             "optional": True
#                         }
#                     ],
#                     "submit_label": "Искать",
#                     "state": "somestate"
#                 }
#             }
#             requests.post(f"{mattermost_host}:{mattermost_port}/api/v4/actions/dialogs/open",
#                           json=payload)
#
#         else:
#             self.driver.reply_to(msg, "Что-то пошло не так")
#
#     @listen_webhook("adv_search")
#     async def form_listener(self, event: WebHookEvent):
#         search_query = self.search_by_label(event.body['submission'])
#         msg_body = event.body['callback_id']
#         msg = Message(json.loads(msg_body.replace("'", "\"")))
#         log.info(f"Запрошен поиск (расширенный) \"{search_query.get('search')}\"")
#         self.print_search_result(msg, search_query)
#
#     @listen_to("проснись")
#     async def wake_up(self, message: Message):
#         self.driver.reply_to(message, "Я проснулся!")
#
#     @listen_to('привет', re.IGNORECASE)
#     def hi(self, message: Message):
#         self.driver.reply_to(message, 'Я могу понять "привет" или "ПРИВЕТ!')
#
#     @listen_to('Дай мне (.*)')
#     async def give_me(self, message, something):
#         self.driver.reply_to(message, 'Вот %s' % something)
#
#     @listen_to("эй", needs_mention=True)
#     async def hey(self, message: Message):
#         self.driver.reply_to(message, "Привет! Ты упомянул меня?")
#
#     @listen_to("эй", direct_only=True)
#     async def hey(self, message: Message):
#         self.driver.reply_to(message, "Привет! Это приватный разговор.")
#
#     @listen_to(
#         "^admin$", direct_only=True, allowed_users=["admin", "root"],
#         category="admin"
#     )
#     async def users_access(self, message: Message):
#         """Сработает, только если имя пользователя отправителя "admin" или "root"."""
#         self.driver.reply_to(message, "Доступ разрешен!")
#
#     @listen_to("^poke$", allowed_channels=["off-topic", "town-square"], category="admin")
#     async def poke(self, message: Message):
#         """Сработает только в том случае, если сообщение было отправлено в формате "#staff" или "#town-square"."""
#         self.driver.reply_to(message, "Доступ разрешен!")
#
#     @listen_to(
#         "^ответь в (.*)$", re.IGNORECASE, needs_mention=True,
#         category="schedule", human_description="ответь в TIMESTAMP",
#     )
#     def schedule_once(self, message: Message, trigger_time: str):
#         """Планирует отправку ответа в заданное время.
#
#         Аргументы:
#         - triger_time (строка): отметка времени в формате %d-%m-%Y_%H:%M:%S,
#             например, 20-02-2021_20:22:01. Ответ будет отправлен в это время.
#         """
#         try:
#             time = datetime.strptime(trigger_time, "%d-%m-%Y_%H:%M:%S")
#             self.driver.reply_to(message,
#                                  f"Запланированное сообщение в {trigger_time}!")
#             schedule.once(time).do(
#                 self.driver.reply_to, message, "Это запланированное сообщение!"
#             )
#         except ValueError as e:
#             self.driver.reply_to(message, str(e))
#
#     @listen_to("hello_click", needs_mention=True, category="click")
#     @click.command(help="Пример команды click с различными аргументами.")
#     @click.argument("POSITIONAL_ARG", type=str)
#     @click.option("--keyword-arg", type=float, default=5.0, help="A keyword arg.")
#     @click.option("-f", "--flag", is_flag=True, help="Можно переключать.")
#     def hello_click(self, message: Message, positional_arg: str, keyword_arg: float, flag: bool):
#         """Функция щелчка, задокументированная с помощью docstring"""
#         response = (
#             "Получены следующие аргументы:\n"
#             f"- positional_arg: {positional_arg}\n"
#             f"- keyword_arg: {keyword_arg}\n"
#             f"- flag: {flag}\n"
#         )
#         self.driver.reply_to(message, response)
#
#     @listen_to("^hello_file$", re.IGNORECASE, needs_mention=True)
#     async def hello_file(self, message: Message):
#         """Отвечает загрузкой текстового файла."""
#         file = Path("/tmp/hello.txt")
#         file.write_text("Привет из этого файла!")
#         self.driver.reply_to(message, "Вот и всё", file_paths=[file])
#
#     # def on_start(self):
#     #     """Уведомляет какой-либо канал о том, что бот сейчас запущен."""
#     #     self.driver.create_post(channel_id="ag9ei9zx3fnw9p694ww5xi6sxe",
#     #                             message="Бот только что начал работать!")
#     #
#     # def on_stop(self):
#     #     """Уведомляет какой-либо канал о завершении работы бота."""
#     #     self.driver.create_post(channel_id="ag9ei9zx3fnw9p694ww5xi6sxe",
#     #                             message="Я сейчас вернусь!")
#
#     @listen_webhook("ping")
#     async def ping_listener(self, event: WebHookEvent):
#         """Прослушивает запросы post к '<server_url>/hooks/ping' и отправляет сообщение в
# канале, указанном в теле запроса."""
#         self.driver.create_post(
#             event.body["channel_id"], f"Webhook {event.webhook_id} сработало!"
#         )
#         self.driver.respond_to_web(
#             event,
#             {
#                 # Здесь вы можете добавить любые данные, которые можно сериализовать в JSON
#                 "message": "привет!",
#             },
#         )
#
#     @listen_to(
#         "^запланировать каждые ([0-9]+)$",
#         re.IGNORECASE,
#         needs_mention=True,
#         category="schedule",
#     )
#     def schedule_every(self, message: Message, seconds: int):
#         """Планирует отправку ответа каждые x секунд. Для остановки используйте команду `cancel jobs`.
#
#         Аргументы:
#         - секунды (целое число): количество секунд между каждым ответом.
#         """
#         schedule.every(int(seconds)).seconds.do(
#             self.driver.reply_to, message,
#             f"Запланированное сообщение каждые {seconds} секунд!"
#         )
#
#     @listen_to('отменить задания', re.IGNORECASE, needs_mention=True,
#                category="schedule")
#     def cancel_jobs(self, message: Message):
#         """Отменяет все запланированные задания, включая повторяющиеся и разовые события."""
#         schedule.clear()
#         self.driver.reply_to(message, 'Все задания отменены')
#
#     @listen_to("^занято|задания$", re.IGNORECASE, needs_mention=True, category="admin")
#     async def busy_reply(self, message: Message):
#         """Показывает количество занятых рабочих потоков."""
#         busy = self.driver.threadpool.get_busy_workers()
#         self.driver.reply_to(
#             message,
#             f"Количество занятых рабочих потоков: {busy}",
#         )
#
#     @listen_to("^hello_channel$", needs_mention=True)
#     async def hello_channel(self, message: Message):
#         """Отвечает публикацией в канале, а не ответом."""
#         self.driver.create_post(channel_id=message.channel_id, message="привет, канал!")
#
#
#     # Требуются права администратора
#     @listen_to("^hello_ephemeral$", needs_mention=True)
#     async def hello_ephemeral(self, message: Message):
#         """Пытается ответить временным сообщением, если у бота есть права администратора системы."""
#         try:
#             self.driver.reply_to(message, "привет отправителю!", ephemeral=True)
#         except mattermostautodriver.exceptions.NotEnoughPermissions:
#             self.driver.reply_to(
#                 message, "У меня нет разрешения на создание эфемерных постов!"
#             )
#
#     @listen_to("^hello_react$", re.IGNORECASE, needs_mention=True)
#     async def hello_react(self, message: Message):
#         """Реагирует поднятием большого пальца вверх."""
#         self.driver.react_to(message, "+1")
#
#     @listen_to("^!hello_webhook$", re.IGNORECASE, category="webhook")
#     async def hello_webhook(self, message: Message):
#         """Веб-хук, который передает привет."""
#         self.driver.client.call_webhook(
#             "ritynzgku3d4dckduu4kbfquxo",
#             options={
#                 "username": "webhook_test",
#                 # Требуются соответствующие разрешения для работы с webhook
#                 "channel": "off-topic",
#                 "text": "Привет?",
#                 "attachments": [
#                     {
#                         "fallback": "Резервный текст",
#                         "title": "Заглавие",
#                         "author_name": "meadowsebot",
#                         "text": "Текст приложения здесь...",
#                         "color": "#59afe1",
#                     }
#                 ],
#             },
#         )
#
#     @listen_to("^!info$")
#     async def info(self, message: Message):
#         """Отвечает информацией о пользователе запрашивающего пользователя."""
#         user_email = self.driver.get_user_info(message.user_id)["email"]
#         reply = (
#             f"TEAM-ID: {message.team_id}\nUSERNAME: {message.sender_name}\n"
#             f"EMAIL: {user_email}\nUSER-ID: {message.user_id}\n"
#             f"IS-DIRECT: {message.is_direct_message}\nMENTIONS: {message.mentions}\n"
#             f"MESSAGE: {message.text}"
#         )
#         self.driver.reply_to(message, reply)
#
#     @listen_to("^свист$", re.IGNORECASE, needs_mention=True)
#     async def ping_reply(self, message: Message):
#         """Пинг-понг."""
#         self.driver.reply_to(message, "пинг-понг")
#
#     @listen_to("^жди ([0-9]+)$", needs_mention=True)
#     async def sleep_reply(self, message: Message, seconds: str):
#         """Засыпает на указанное количество секунд.
#
#         Аргументы:
#             - секунды: количество секунд для сна.
#         """
#         self.driver.reply_to(message,
#                              f"Хорошо, я буду ждать {seconds} секунд.")
#         await asyncio.sleep(int(seconds))
#         self.driver.reply_to(message, "Сделано!")
#
    @listen_webhook("ping")
    @listen_webhook("pong")
    async def action_listener(self, event: WebHookEvent):
        """Прослушивает веб-перехватчики «ping» и «pong» и либо обновляет исходный пост,
        либо отправляет сообщение на канал, чтобы указать, что веб-перехватчик работает."""
        if isinstance(event, ActionEvent):
            self.driver.respond_to_web(
                event,
                {
                    "update": {"message": event.context["text"], "props": {}},
                    "ephemeral_text": "Вы обновили этот пост!",
                },
            )
        else:
            self.driver.create_post(
                event.body["channel_id"], f"Webhook {event.webhook_id} сработал!"
            )

    @listen_to("!button", direct_only=False)
    async def webhook_button(self, message: Message):
        """Создает кнопку, которая запускает веб-переход в зависимости от выбранного параметра."""
        self.driver.reply_to(
            message,
            "",
            props={
                "attachments": [
                    {
                        "pretext": None,
                        "text": "Выбирите сами..",
                        "actions": [
                            {
                                "id": "sendPing",
                                "name": "Ping",
                                "integration": {
                                    "url": f"{webhookHostUrl}:{webhook_host_port}/"
                                           "hooks/ping",
                                    "context": {
                                        "text": "ping webhook работает! :tada:",
                                    },
                                },
                            },
                            {
                                "id": "sendPong",
                                "name": "Pong",
                                "integration": {
                                    "url": f"{webhookHostUrl}:{webhook_host_port}/"
                                           "hooks/pong",
                                    "context": {
                                        "text": "pong webhook работает! :tada:",
                                    },
                                },
                            },
                        ],
                    }
                ]
            },
        )