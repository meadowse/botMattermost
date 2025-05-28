import datetime
import json
from mmpy_bot import Plugin, listen_webhook, WebHookEvent, ActionEvent, listen_to, Message
from reminder import set_value_by_id, getChannelId
import re
from dataclasses import dataclass, asdict
from typing import Optional
import config
import requests
import firebirdsql
from mmpy_bot.plugins.base import log

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

class webhookPlugin(Plugin):
    @listen_webhook("underApproval")
    @listen_webhook("couldNotGetInTouch")
    async def Cancel(self, event: WebHookEvent):
        """Прослушивает веб-перехватчики «ping» и «pong» и либо обновляет исходный пост,
        либо отправляет сообщение на канал, чтобы указать, что веб-перехватчик работает."""
        if event.body.get('user_name') in event.context.get("managerNicknames"):
            if isinstance(event, ActionEvent):
                self.driver.respond_to_web(
                    event,
                    {
                        "update": {"message": event.context.get("message") + "\n@" + event.body.get(
                            'user_name') + " ответил " + event.context.get("text"), "props": {}},
                    },
                )
            else:
                self.driver.create_post(
                    event.body["channel_id"],
                    f"Webhook {event.webhook_id} сработал!"
                )
        else:
            self.driver.create_post(
                event.body["channel_id"],
                f"@{event.body.get('user_name')} у тебя нет прав нажимать {event.context.get('text')}"
            )

    @listen_webhook("cancel")
    async def cancel(self, event: WebHookEvent):
        """Прослушивает веб-перехватчики «ping» и «pong» и либо обновляет исходный пост,
        либо отправляет сообщение на канал, чтобы указать, что веб-перехватчик работает."""
        if event.body.get('user_name') in event.context.get("managerNicknames"):
            set_value_by_id('T213', 'F4570', 'Аннулирован', event.context.get("doc_id"))
            set_value_by_id('T213', 'F4666', 'NULL', event.context.get("doc_id"))
            if isinstance(event, ActionEvent):
                self.driver.respond_to_web(
                    event,
                    {
                        "update": {"message": event.context.get(
                            "message") + "\n@" + event.body.get(
                            'user_name') + " ответил " + event.context.get("text"),
                                   "props": {}},
                    },
                )
            else:
                self.driver.create_post(
                    event.body["channel_id"],
                    f"Webhook {event.webhook_id} сработал!"
                )
        else:
            self.driver.create_post(
                event.body["channel_id"],
                f"@{event.body.get('user_name')} у тебя нет прав нажимать {event.context.get('text')}"
            )

    @listen_webhook("failure")
    async def failure(self, event: WebHookEvent):
        """Прослушивает веб-перехватчики «ping» и «pong» и либо обновляет исходный пост,
        либо отправляет сообщение на канал, чтобы указать, что веб-перехватчик работает."""
        if event.body.get('user_name') == event.context.get("manager_nickname"):
            set_value_by_id('T209', 'F4491', 'Провал', event.context.get("kp_id"))
            set_value_by_id('T209', 'F4529', 'NULL', event.context.get("kp_id"))
            if isinstance(event, ActionEvent):
                self.driver.respond_to_web(
                    event,
                    {
                        "update": {"message": event.context.get(
                            "message") + "\n@" + event.body.get(
                            'user_name') + " ответил " + event.context.get("text"),
                                   "props": {}},
                    },
                )
            else:
                self.driver.create_post(
                    event.body["channel_id"],
                    f"Webhook {event.webhook_id} сработал!"
                )
        else:
            self.driver.create_post(
                event.body["channel_id"],
                f"@{event.body.get('user_name')} у тебя нет прав нажимать {event.context.get('text')}"
            )

    @listen_webhook("delete")
    async def delete(self, event: WebHookEvent):
        """Прослушивает веб-перехватчики «ping» и «pong» и либо обновляет исходный пост,
        либо отправляет сообщение на канал, чтобы указать, что веб-перехватчик работает."""
        if event.body.get('user_name') in event.context.get("managerNicknames"):
            if isinstance(event, ActionEvent):
                self.driver.respond_to_web(
                    event,
                    {
                        "update": {"message": '', "props": {}},
                    },
                )
            else:
                self.driver.create_post(
                    event.body["channel_id"],
                    f"Webhook {event.webhook_id} сработал!"
                )
        else:
            self.driver.create_post(
                event.body["channel_id"],
                f"@{event.body.get('user_name')} у тебя нет прав нажимать {event.context.get('text')}"
            )

    @listen_webhook("nonStandard")
    async def nonStandard(self, event: WebHookEvent):
        """Прослушивает веб-перехватчики «ping» и «pong» и либо обновляет исходный пост,
        либо отправляет сообщение на канал, чтобы указать, что веб-перехватчик работает."""
        if event.body.get('user_name') in event.context.get("managerNicknames"):
            if isinstance(event, ActionEvent):
                print(event)
                # self.driver.reply_to(message, '', props={
                #     "attachments": [
                #         {
                #             "text": f"⛔Неквал от {event.body.get('user_name')}",
                #         }
                #     ]
                # })
                # self.driver.respond_to_web(
                #     event,
                #     {
                #         "update": {"message": event.context.get("message") + "\n@" + event.body.get(
                #             'user_name') + " ответил " + event.context.get("text"), "props": {}},
                #     },
                # )
            else:
                self.driver.create_post(
                    event.body["channel_id"],
                    f"Webhook {event.webhook_id} сработал!"
                )
        else:
            self.driver.create_post(
                event.body["channel_id"],
                f"@{event.body.get('user_name')} у тебя нет прав нажимать {event.context.get('text')}"
            )

    # @listen_to("^(.)*$", re.IGNORECASE)
    # async def hello(self, message: Message, status):
    #     managerNicknames = ['a.bukreev', 'a.lavruhin', 'm.ulanov', 's.volkov',
    #                         'b.musaev', ]  # список тех, кто может удалять и менять статус КП
    #     props = {
    #         "attachments": [
    #             {
    #                 "actions": [
    #                     {
    #                         "id": "delete",
    #                         "name": "❌Удалить",
    #                         "integration": {
    #                             "url": f"{config.webhook_host_url}:{config.webhookHostUrl}/"
    #                                    "hooks/delete",
    #                             "context": dict(
    #                                 text="❌Удалить",
    #                                 managerNicknames=managerNicknames,
    #                             )
    #                         },
    #                     },
    #                     {
    #                         "id": "nonStandard",
    #                         "name": "⛔Неквал",
    #                         "integration": {
    #                             "url": f"{config.webhook_host_url}:{config.webhookHostUrl}/"
    #                                    "hooks/nonStandard",
    #                             "context": dict(
    #                                 text="⛔Неквал",
    #                                 # message=message,
    #                                 managerNicknames=managerNicknames,
    #                             )
    #                         },
    #                     },
    #                     {
    #                         "id": "createLead",
    #                         "name": "🚩Создать Лида",
    #                         "integration": {
    #                             "url": f"{config.webhook_host_url}:{config.webhookHostUrl}/"
    #                                    "hooks/createLead",
    #                             "context": dict(
    #                                 text="🚩Создать Лида",
    #                                 # message=message,
    #                                 managerNicknames=managerNicknames,
    #                             )
    #                         },
    #                     },
    #                     {
    #                         "id": "createKP",
    #                         "name": "💲Создать КП",
    #                         "integration": {
    #                             "url": f"{config.webhook_host_url}:{config.webhookHostUrl}/"
    #                                    "hooks/createKP",
    #                             "context": dict(
    #                                 text="💲Создать КП",
    #                                 # message=message,
    #                                 managerNicknames=managerNicknames,
    #                             )
    #                         },
    #                     },
    #                 ],
    #             }
    #         ]
    #     }
    #     self.driver.reply_to(message, '', props=props)

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
                                "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/createTask",
                                "context": message.body,
                            },
                        }
                    ]
                }
            ]
        }
        self.driver.reply_to(message, '', props=mes_json)

    @listen_webhook("createTask")
    async def createTask(self, event: WebHookEvent):
        # log.info(event.request_id)
        # log.info(event.webhook_id)
        # log.info(event.body)
        msg_body = event.body.get('context')
        msg = Message(msg_body)
        # log.info(msg.body)
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
        # log.info(json.dumps(event.body.get('context'), indent=4, sort_keys=True, ensure_ascii=False))
        if isinstance(event, ActionEvent):
            payload = {
                "trigger_id": event.body['trigger_id'],
                "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/addTask",
                "dialog": {
                    "callback_id": json.dumps(event.body, indent=4, sort_keys=True, ensure_ascii=False),
                    "title": "Добавление задачи",
                    'introduction_text': f"Постановщик задачи: {event.body['user_name']}",
                    "elements": [
                        {
                            "display_name": "Задача",
                            "placeholder": "Задача",
                            "name": "task",
                            "type": "text",
                            'default': msg.text
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
            requests.post(f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/actions/dialogs/open",
                          json=payload)
        else:
            self.driver.reply_to(msg, "Что-то пошло не так")

    @listen_webhook("addTask")
    async def addTask(self, event: WebHookEvent):
        # log.info(event.body)
        Dict = json.loads(event.body['callback_id'])
        # log.info(Dict)
        msg_body = Dict.get('context')
        msg = Message(msg_body)
        # log.info(json.dumps(msg.body, indent=4, sort_keys=True, ensure_ascii=False))
        try:
            idMessage = msg.reply_id
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
            with (firebirdsql.connect(host=config.host, database=config.database, user=config.user, password=config.password,
                                      charset=config.charset) as con):
                cur = con.cursor()
                sql = f"""SELECT ID FROM T212 WHERE F4644 = '{event.body.get('channel_id')}'"""
                cur.execute(sql)
                contractId = cur.fetchone()
                # log.info(contractId)
                if contractId is not None:
                    contractId = contractId[0]
                sql = f"""SELECT ID FROM T3 WHERE F16 = '{directorId}'"""
                cur.execute(sql)
                directorId = cur.fetchone()[0]
                # log.info(directorId)
                sql = f"""SELECT ID FROM T3 WHERE F16 = '{executorId}'"""
                cur.execute(sql)
                executorId = cur.fetchone()[0]
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
                data = {'id': Dict.get('post_id'), 'message': f'Задача успешно создана в МПК24'}
                response = requests.put(f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/posts/{Dict.get('post_id')}",
                                        json=data, headers=config.headers)
                if response.status_code == 200:
                    log.info('Message sent successfully.')
                    log.info(response.json())
                else:
                    log.info(f'Failed to send message: {response.status_code}, {response.text}')
                # log.info(json.dumps(Dict, indent=4, sort_keys=True, ensure_ascii=False))
        except Exception as ex:
            self.driver.reply_to(msg, f"Ошибка при создании задачи: {ex}")
        log.info(f"Веб-хук addTask выполнен: {datetime.datetime.now()}")

    @listen_webhook("complete")
    async def complete(self, event: WebHookEvent):
        Context = event.body.get('context')
        msg = Message(Context)
        try:
            taskId = Context.get('taskId')
            with (firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                      password=config.password,
                                      charset=config.charset) as con):
                cur = con.cursor()
                sql = f"""UPDATE T218 SET F4697 = 1 WHERE ID = {taskId}"""
                cur.execute(sql)
                con.commit()
            messageId = Context.get('messageId')
            if messageId is not None:
                channelId = getChannelId(messageId)
                message = dict(data=dict(post=dict(channel_id=channelId, id=messageId)))
                message = Message(message)
                self.driver.reply_to(message, f"@{Context.get('executor')} выполнил задачу")
            self.driver.respond_to_web(event, {"update": {"message": 'задача выполнена', "props": {}},},)
        except Exception as ex:
            self.driver.reply_to(msg, f"Ошибка при выполнении задачи: {ex}")
        log.info(f"Веб-хук complete выполнен: {datetime.datetime.now()}")