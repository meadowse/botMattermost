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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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

    @listen_webhook("cancelDocs")
    async def cancelDocs(self, event: WebHookEvent):
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

    @listen_to("Договор")
    async def agreement(self, message: Message):
        # log.info(json.dumps(message.body, indent=4, sort_keys=True, ensure_ascii=False))
        if message.sender_name == 'notify_docs_bot':
            headDepartment = (message.text.split('Рук отдела: @')[1].split()[0], 'a.bukreev', )
            props = {
                "attachments": [
                    {
                        "actions": [
                            {
                                "id": "approveHeadDepartment",
                                "name": ":white_check_mark: Согласовать",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/approveHeadDepartment",
                                    "context": dict(message=message.body, headDepartment=headDepartment, )
                                },
                            },
                            {
                                "id": "deniedHeadDepartment",
                                "name": ":x: Отказать",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/deniedHeadDepartment",
                                    "context": dict(message=message.body, headDepartment=headDepartment, )
                                },
                            },
                        ],
                    }
                ]
            }
            self.driver.reply_to(message, f'Рук отдела @{headDepartment[0]}', props=props)
            pRM = (message.text.split('ПрМ: @')[1].split()[0], 'a.bukreev', )
            props = {
                "attachments": [
                    {
                        "actions": [
                            {
                                "id": "approvePRM",
                                "name": ":white_check_mark: Согласовать",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/approvePRM",
                                    "context": dict(message=message.body, pRM=pRM, )
                                },
                            },
                            {
                                "id": "deniedPRM",
                                "name": ":x: Отказать",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/deniedPRM",
                                    "context": dict(message=message.body, pRM=pRM, )
                                },
                            },
                        ],
                    }
                ]
            }
            self.driver.reply_to(message, f'Прм @{pRM[0]}', props=props)

    @listen_webhook("deniedPRM")
    async def deniedPRM(self, event: WebHookEvent):
        context = event.body.get('context')
        message = Message(context.get('message'))
        try:
            User = event.body.get('user_name')
            if User in context.get("pRM"):
                with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                         password=config.password, charset=config.charset) as con:
                    today = datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d')
                    cur = con.cursor()
                    cur.execute(f"""SELECT ID FROM T3 WHERE F4932 = '{User}'""")
                    iD = cur.fetchone()[0]
                    log.info(iD)
                    idChannel = message.channel_id
                    cur.execute(
                        f"SELECT T213.ID FROM T213 JOIN T212 ON T212.ID = T213.F4573 WHERE F4644 = '{idChannel}'")
                    idAgreement = cur.fetchone()[0]
                    log.info(idAgreement)
                    cur.execute(
                        f"UPDATE T213 SET F5303 = 0, F5307 = {iD}, F5309 = '{today}' WHERE ID = {idAgreement} AND F4567 = 1")
                    con.commit()
                    self.driver.respond_to_web(event,
                                               {"update": {"message": f"@{User} ответил Отказом :x:", "props": {}}, }, )
            else:
                self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Отказать\"")
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

    @listen_webhook("approvePRM")
    async def approvePRM(self, event: WebHookEvent):
        context = event.body.get('context')
        message = Message(context.get('message'))
        try:
            User = event.body.get('user_name')
            if User in context.get("pRM"):
                with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                         password=config.password, charset=config.charset) as con:
                    today = datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d')
                    cur = con.cursor()
                    cur.execute(f"""SELECT ID FROM T3 WHERE F4932 = '{User}'""")
                    iD = cur.fetchone()[0]
                    log.info(iD)
                    idChannel = message.channel_id
                    cur.execute(
                        f"SELECT T213.ID FROM T213 JOIN T212 ON T212.ID = T213.F4573 WHERE F4644 = '{idChannel}'")
                    idAgreement = cur.fetchone()[0]
                    log.info(idAgreement)
                    cur.execute(
                        f"UPDATE T213 SET F5303 = 1, F5307 = {iD}, F5309 = '{today}' WHERE ID = {idAgreement} AND F4567 = 1")
                    con.commit()
                    self.driver.respond_to_web(event, {
                        "update": {"message": f"@{User} Согласовал :white_check_mark:", "props": {}}, }, )
            else:
                self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Согласовать\"")
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

    @listen_webhook("deniedHeadDepartment")
    async def deniedHeadDepartment(self, event: WebHookEvent):
        context = event.body.get('context')
        message = Message(context.get('message'))
        try:
            User = event.body.get('user_name')
            if User in context.get("headDepartment"):
                with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                         password=config.password, charset=config.charset) as con:
                    today = datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d')
                    cur = con.cursor()
                    cur.execute(f"""SELECT ID FROM T3 WHERE F4932 = '{User}'""")
                    iD = cur.fetchone()[0]
                    log.info(iD)
                    idChannel = message.channel_id
                    cur.execute(
                        f"SELECT T213.ID FROM T213 JOIN T212 ON T212.ID = T213.F4573 WHERE F4644 = '{idChannel}'")
                    idAgreement = cur.fetchone()[0]
                    log.info(idAgreement)
                    cur.execute(
                        f"UPDATE T213 SET F5454 = 0, F5453 = {iD}, F5452 = '{today}' WHERE ID = {idAgreement} AND F4567 = 1")
                    con.commit()
                    self.driver.respond_to_web(event,
                                               {"update": {"message": f"@{User} ответил Отказом :x:", "props": {}}, }, )
            else:
                self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Отказать\"")
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

    @listen_webhook("approveHeadDepartment")
    async def approveHeadDepartment(self, event: WebHookEvent):
        context = event.body.get('context')
        message = Message(context.get('message'))
        try:
            User = event.body.get('user_name')
            if User in context.get("headDepartment"):
                with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                         password=config.password, charset=config.charset) as con:
                    today = datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d')
                    cur = con.cursor()
                    cur.execute(f"""SELECT ID FROM T3 WHERE F4932 = '{User}'""")
                    iD = cur.fetchone()[0]
                    log.info(iD)
                    idChannel = message.channel_id
                    cur.execute(
                        f"SELECT T213.ID FROM T213 JOIN T212 ON T212.ID = T213.F4573 WHERE F4644 = '{idChannel}'")
                    idAgreement = cur.fetchone()[0]
                    log.info(idAgreement)
                    cur.execute(
                        f"UPDATE T213 SET F5454 = 1, F5453 = {iD}, F5452 = '{today}' WHERE ID = {idAgreement} AND F4567 = 1")
                    con.commit()
                    self.driver.respond_to_web(event, {
                        "update": {"message": f"@{User} Согласовал :white_check_mark:", "props": {}}, }, )
            else:
                self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Согласовать\"")
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

    @listen_to("[А-Яа-яЁё]*")
    async def officialStatements(self, message: Message):
        # log.info(json.dumps(message.body, indent=4, sort_keys=True, ensure_ascii=False))
        if message.sender_name == 'notify_bot' and message.channel_id == 'odc4nzf6ctnqdqkfsb1jhaiggr' and message.body.get(
                'data').get('post').get('reply_count') == 0:
            mustCoordinate = message.text.split('Должен согласовать: *@')[1].strip('*')
            props = {
                "attachments": [
                    {
                        "actions": [
                            {
                                "id": "approveStatement",
                                "name": ":white_check_mark: Согласовать",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/approveStatement",
                                    "context": dict(message=message.body, mustCoordinate=mustCoordinate, )
                                },
                            },
                            {
                                "id": "deniedStatement",
                                "name": ":x: Отказать",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/deniedStatement",
                                    "context": dict(message=message.body, mustCoordinate=mustCoordinate, )
                                },
                            },
                        ],
                    }
                ]
            }
            self.driver.reply_to(message, '', props=props)

    @listen_webhook("deniedStatement")
    async def deniedStatement(self, event: WebHookEvent):
        context = event.body.get('context')
        message = Message(context.get('message'))
        try:
            User = event.body.get('user_name')
            if User == context.get("mustCoordinate"):
                with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                         password=config.password, charset=config.charset) as con:
                    cur = con.cursor()
                    cur.execute(f"""UPDATE T302 SET F5860 = 'НЕ согласовано' WHERE F5703 = '{message.reply_id}'""")
                    con.commit()
                    self.driver.react_to(message, "x")
                    self.driver.respond_to_web(event,
                                               {"update": {"message": f"@{User} ответил Отказом :x:", "props": {}}, }, )
            else:
                self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Отказать\"")
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

    @listen_webhook("approveStatement")
    async def approveStatement(self, event: WebHookEvent):
        context = event.body.get('context')
        message = Message(context.get('message'))
        try:
            User = event.body.get('user_name')
            if User == context.get("mustCoordinate"):
                with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                         password=config.password, charset=config.charset) as con:
                    cur = con.cursor()
                    cur.execute(f"""UPDATE T302 SET F5860 = 'Согласовано' WHERE F5703 = '{message.reply_id}'""")
                    con.commit()
                    self.driver.react_to(message, "white_check_mark")
                    self.driver.respond_to_web(event, {"update": {"message": f"@{User} Согласовал :white_check_mark:", "props": {}}, }, )
            else:
                self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Согласовать\"")
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

    @listen_to("[А-Яа-яЁё]*")
    async def reconciliationPayments(self, message: Message):
        # log.info(json.dumps(message.body, indent=4, sort_keys=True, ensure_ascii=False))
        if message.sender_name == 'notify_bot' and message.channel_id == 'aicmyxehzjg5tmg7by4p6o9gih' and message.body.get('data').get('post').get('reply_count') == 0:
            generalManagers = ['z.shirinov', ]  # список тех, кто может удалять и менять статус КП
            props = {
                "attachments": [
                    {
                        "actions": [
                            {
                                "id": "toApprove",
                                "name": ":white_check_mark: Согласовать",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/toApprove",
                                    "context": dict(message=message.body, generalManagers=generalManagers, )
                                },
                            },
                            {
                                "id": "deny",
                                "name": ":x: Отказать",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/deny",
                                    "context": dict(message=message.body, generalManagers=generalManagers, )
                                },
                            },
                        ],
                    }
                ]
            }
            self.driver.reply_to(message, '', props=props)

    @listen_webhook("deny")
    async def deny(self, event: WebHookEvent):
        context = event.body.get('context')
        message = Message(context.get('message'))
        try:
            User = event.body.get('user_name')
            if User in context.get("generalManagers"):
                with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                         password=config.password, charset=config.charset) as con:
                    cur = con.cursor()
                    cur.execute(f"""UPDATE T315 SET F5907 = 'НЕ согласовано' WHERE F5909 = '{message.reply_id}'""")
                    con.commit()
                    self.driver.react_to(message, "x")
                    self.driver.respond_to_web(event, {"update": {"message": f"@{User} ответил Отказом :x:", "props": {}}, }, )
            else:
                self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Отказать\"")
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

    @listen_webhook("toApprove")
    async def toApprove(self, event: WebHookEvent):
        context = event.body.get('context')
        message = Message(context.get('message'))
        try:
            User = event.body.get('user_name')
            if User in context.get("generalManagers"):
                with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                         password=config.password, charset=config.charset) as con:
                    cur = con.cursor()
                    cur.execute(f"""UPDATE T315 SET F5907 = 'Согласовано' WHERE F5909 = '{message.reply_id}'""")
                    con.commit()
                    self.driver.react_to(message, "white_check_mark")
                    self.driver.respond_to_web(event, {"update": {"message": f"@{User} Согласовал :white_check_mark:", "props": {}}, }, )
            else:
                self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Согласовать\"")
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

    @listen_to("[А-Яа-яЁё]*")
    async def addButtons(self, message: Message):
        # log.info(json.dumps(message.body, indent=4, sort_keys=True, ensure_ascii=False))
        if message.channel_id == 'kbcyc66jbtbcubs93h43nf19dy' and message.body.get('data').get('post').get('reply_count') == 0:
            managerNicknames = ['a.bukreev', 'a.lavruhin', 'maxulanov', 'b.musaev', 'm.pryamorukov', ]  # список тех, кто может удалять и менять статус КП
            props = {
                "attachments": [
                    {
                        "actions": [
                            {
                                "id": "delete",
                                "name": "❌ Удалить",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/delete",
                                    "context": dict(message=message.body, managerNicknames=managerNicknames, )
                                },
                            },
                            {
                                "id": "reactTo",
                                "name": "⛔ Неквал",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/reactTo",
                                    "context": dict(message=message.body, managerNicknames=managerNicknames, )
                                },
                            },
                            {
                                "id": "createLead",
                                "name": "🚩 Создать Лида",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/createLead",
                                    "context": dict(message=message.body, )
                                },
                            },
                            {
                                "id": "createKP",
                                "name": "💲 Создать КП",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/createKP",
                                    "context": dict(message=message.body, )
                                },
                            },
                            {
                                "id": "toRefuse",
                                "name": "📧Ответить отказом",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/toRefuse",
                                    "context": dict(message=message.body, )
                                }
                            }
                        ],
                    }
                ]
            }
            self.driver.reply_to(message, '', props=props)

    @listen_webhook("toRefuse")
    async def toRefuse(self, event: WebHookEvent):
        # log.info(json.dumps(event.body, indent=4, sort_keys=True, ensure_ascii=False))
        context = event.body.get('context')
        message = Message(context.get('message'))
        User = event.body.get('user_name')
        with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                 password=config.password, charset=config.charset) as con:
            cur = con.cursor()
            cur.execute(f"""SELECT T3.F4932 FROM T5 LEFT JOIN T3 ON T5.ID = T3.F27 LEFT JOIN T309 ON T3.ID = T309.F5681
            WHERE T5.F26 = 'Отдел продаж' AND T3.F5383 = 1 AND F5682 like '%https://post.mosproektkompleks.ru%' AND T3.F4932 = '{User}'""")
            result = cur.fetchone()
            if result is not None:
                self.driver.reply_to(message, f"@{User} у вас нет прав нажимать на кнопку \"Ответить отказом\"")
            else:
                server = smtplib.SMTP(config.smtp_server, config.smtp_port)
                try:
                    listMessage = message.text.split('\n### Отправитель: ')
                    listMessage = listMessage[1].split('\n### Тема: ')
                    # Получатель
                    receiver_email = listMessage[0]
                    listMessage = listMessage[1].split('### Сообщение: \n ')
                    # Тема
                    subject = listMessage[0].strip('\n')
                    # Оригинальное письмо (его текст нужно процитировать)
                    original_message = listMessage[1]
                    # Формируем цитату: каждая строка с ">"
                    quoted_message = "\n".join(["> " + line for line in original_message.splitlines()])
                    cur.execute(f"""SELECT T309.F5683 AS login, T309.F5684 AS password FROM T3
                    LEFT JOIN T309 ON T3.ID = T309.F5681
                    WHERE T3.F4932 = '{User}' AND F5682 like '%https://post.mosproektkompleks.ru%'""")
                    dataUser = cur.fetchone()
                    login = dataUser[0]
                    Password = dataUser[1]
                    sender_email = User + config.postDomen
                    # Текст нового письма
                    new_message_text = f"""     Здравствуйте!

    Благодарим за обращение в «МосПроектКомплекс»! По результатам рассмотрения запроса услуг вынуждены сообщить, что сейчас, к сожалению, мы не сможем помочь вам в данном виде работ.
    Мы высоко ценим ваше внимание к нашей компании и надеемся на возможность сотрудничества в будущем. Будем рады рассмотреть ваши новые запросы и принять участие в решении последующих задач.
    Мы являемся ведущей московской компанией в области инжиниринга коммерческой недвижимости по следующим направлениям:
    Проектирование / Обследование / Экспертиза / Пожарная безопасность / Кадастр / Консалтинг / Легализация самостроя

{quoted_message}"""
                    # Формируем письмо
                    msg = MIMEMultipart()
                    msg["From"] = sender_email
                    msg["To"] = receiver_email
                    msg["Subject"] = subject
                    msg.attach(MIMEText(new_message_text, "plain", "utf-8"))
                    # Отправка
                    server.starttls()
                    server.login(login, Password)
                    server.sendmail(sender_email, receiver_email, msg.as_string())
                    log.info("Письмо успешно отправлено!")
                    self.driver.respond_to_web(event, {"update": {"message": f"@{User} ответил отказом", "props": {}, }, }, )
                except Exception as e:
                    log.info("Ошибка при отправке:", e)
                    self.driver.reply_to(message, f"@{User}, ошибка при отправке: {e}")
                finally:
                    server.quit()

    @listen_webhook("delete")
    async def delete(self, event: WebHookEvent):
        # log.info(json.dumps(event.body, indent=4, sort_keys=True, ensure_ascii=False))
        context = event.body.get('context')
        message = Message(context.get('message'))
        User = event.body.get('user_name')
        if User in context.get('managerNicknames'):
            response = requests.delete(
                f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/posts/{message.reply_id}",
                headers=config.headers)
            if response.status_code == 200:
                log.info('Message sent successfully.')
                log.info(response.json())
            else:
                log.info(f'Failed to send message: {response.status_code}, {response.text}')
        else:
            self.driver.reply_to(message, f"@{User} у вас нет прав нажимать на кнопки")

    @listen_webhook("reactTo")
    async def reactTo(self, event: WebHookEvent):
        # log.info(json.dumps(event.body, indent=4, sort_keys=True, ensure_ascii=False))
        context = event.body.get('context')
        message = Message(context.get('message'))
        User = event.body.get('user_name')
        if User in context.get('managerNicknames'):
            self.driver.react_to(message, "no_entry")
            self.driver.respond_to_web(event, {
                "update": {"message": "", "props": {}, }, }, )
        else:
            self.driver.reply_to(message, f"@{User} у вас нет прав нажимать на кнопки")

    @listen_webhook("createKP")
    async def createKP(self, event: WebHookEvent):
        context = event.body.get('context')
        message = Message(context.get('message'))
        User = event.body.get('user_name')
        ID = event.body.get('user_id')
        num = add_KP(message.reply_id, ID)
        self.driver.respond_to_web(event,
                                   {"update": {"message": f"@{User} создал запись о КП № {num}", "props": {}, }, }, )

    @listen_webhook("createLead")
    async def createLead(self, event: WebHookEvent):
        context = event.body.get('context')
        message = Message(context.get('message'))
        User = event.body.get('user_name')
        ID = event.body.get('user_id')
        num = add_LEAD(message.reply_id, ID)
        self.driver.respond_to_web(event,
                                   {"update": {"message": f"@{User} создал запись о Лиде № {num}", "props": {}, }, }, )

    @listen_to("задач", re.IGNORECASE)
    async def task(self, message: Message):
        if message.body.get('data').get('post').get('reply_count') == 0:
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
                                }
                            },
                            {
                                'id': 'deleteTask',
                                'name': 'Отмена',
                                'integration': {
                                    'url': f'{config.webhook_host_url}:{config.webhook_host_port}/hooks/deleteTask',
                                    'context': message.body,
                                }
                            }
                        ]
                    }
                ]
            }
            self.driver.reply_to(message, '', props=mes_json)

    @listen_webhook("deleteTask")
    async def deleteTask(self, event: WebHookEvent):
        # log.info(json.dumps(event.body, indent=4, sort_keys=True, ensure_ascii=False))
        response = requests.delete(f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/posts/{event.body.get('post_id')}", headers=config.headers)
        if response.status_code == 200:
            log.info('Message sent successfully.')
            log.info(response.json())
        else:
            log.info(f'Failed to send message: {response.status_code}, {response.text}')

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
                    "callback_id": json.dumps(event.body, ensure_ascii=False),
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
                        },
                        {
                            "display_name": "Планируемые времязатраты",
                            "name": "plannedTimeCosts",
                            "type": "text",
                            'subtype': 'number',
                            "optional": True
                        }
                    ],
                    "submit_label": "Cоздать",
                    "state": "somestate"
                }
            }
            # log.info(json.dumps(payload, indent=4, sort_keys=True, ensure_ascii=False))
            response = requests.post(f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/actions/dialogs/open", json=payload)
            log.info({'response': response.json(), 'status': response.status_code})
        else:
            self.driver.reply_to(msg, "Что-то пошло не так")

    @listen_webhook("addTask")
    async def addTask(self, event: WebHookEvent):
        Dict = json.loads(event.body['callback_id'])
        msg_body = Dict.get('context')
        msg = Message(msg_body)
        try:
            idMessage = msg.reply_id
            task = event.body.get('submission').get('task')
            comment = event.body.get('submission').get('comment')
            dateStart = event.body.get('submission').get('dateStart')
            deadline = event.body.get('submission').get('dateEnd')
            directorId = event.body.get('user_id')
            executorId = event.body.get('submission').get('executor')
            plannedTimeCosts = event.body.get('submission').get('plannedTimeCosts')
            if plannedTimeCosts == '':
                plannedTimeCosts = None
            with (firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                      password=config.password, charset=config.charset) as con):
                cur = con.cursor()
                sql = f"SELECT ID FROM T212 WHERE F4644 = '{event.body.get('channel_id')}'"
                cur.execute(sql)
                contractId = cur.fetchone()
                if contractId is not None:
                    contractId = contractId[0]
                sql = f"SELECT ID, F4932 FROM T3 WHERE F16 = '{directorId}'"
                cur.execute(sql)
                directorData = cur.fetchone()
                directorId = directorData[0]
                director = directorData[1]
                sql = f"SELECT ID, F4932 FROM T3 WHERE F16 = '{executorId}'"
                cur.execute(sql)
                executorData = cur.fetchone()
                executorId = executorData[0]
                executor = executorData[1]
                cur.execute(f'SELECT GEN_ID(GEN_T218, 1) FROM RDB$DATABASE')
                ID = cur.fetchonemap().get('GEN_ID', None)
                values = {
                    'id': ID, 'F4691': contractId, 'F4695': task, 'F4698': comment, 'F4970': dateStart,
                    'F5569': dateStart, 'F4696': deadline, 'F4693': directorId,  # должно быть ID пользователя
                    'F4694': executorId, 'F4697': 0, 'F5451': idMessage, 'F5872': 'Новая', 'F5889': plannedTimeCosts}
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
                sql = f"INSERT INTO T218 ({', '.join(values.keys())}) VALUES ({', '.join(sql_values)})"
                cur.execute(sql)
                con.commit()
                message = f'**Добавлена :hammer_and_wrench: Задача :hammer_and_wrench: by @{director}**\n'
                message += f'Дата добавления: *{dateStart}*\n'
                message += f'Постановщик: *@{director}*\n'
                message += f'Исполнитель: *@{executor}*\n'
                message += f'Задача: :hammer: *{task}*\n'
                message += f'Deadline: :calendar: *{deadline}*\n'
                message += f'Комментарий: :speech_balloon: *{comment}*\n' if comment is not None and comment != '' else ''
                message += f'Планируемые времязатраты: :clock3: *{plannedTimeCosts}ч.*\n' if plannedTimeCosts is not None and plannedTimeCosts != '0' else ''
                message += 'Статус: :new: *Новая* :new:\n:large_yellow_circle: *Задача ожидает исполнения...*'
                data = {'channel_id': Dict.get('channel_id'), 'message': message, 'root_id': msg.reply_id}
                self.driver.respond_to_web(event, {"update": {"message": '', "props": {}}, }, )
                response = requests.post(f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/posts", json=data,
                                         headers=config.headers_notify_tasks_bot)
                if response.status_code == 201:
                    log.info('Message sent successfully.')
                    log.info(response.json())
                else:
                    log.info(f'Failed to send message: {response.status_code}, {response.text}')
                    self.driver.reply_to(msg, f'Failed to send message: {response.status_code}, {response.text}')
        except Exception as ex:
            self.driver.reply_to(msg, f"Ошибка при создании задачи: {ex}")

    # @listen_webhook("complete")
    # async def complete(self, event: WebHookEvent):
    #     # log.info(event.body)
    #     Context = event.body.get('context')
    #     msg = Message(Context)
    #     try:
    #         taskId = Context.get('taskId')
    #         today = datetime.datetime.strftime(datetime.date.today(), '%d.%m.%y')
    #         with (firebirdsql.connect(host=config.host, database=config.database, user=config.user,
    #                                   password=config.password,
    #                                   charset=config.charset) as con):
    #             cur = con.cursor()
    #             sql = f"""UPDATE T218 SET F4697 = 1, F4708 = '{today}' WHERE ID = {taskId}"""
    #             cur.execute(sql)
    #             con.commit()
    #         messageId = Context.get('messageId')
    #         if messageId is not None:
    #             channelId = getChannelId(messageId)
    #             message = dict(data=dict(post=dict(channel_id=channelId, root_id=messageId)))
    #             message = Message(message)
    #             self.driver.reply_to(message, f"@{Context.get('executor')} выполнил задачу")
    #         self.driver.respond_to_web(event, {
    #             "update": {"message": f"{Context.get('message')}\nзадача выполнена", "props": {}}, }, )
    #     except Exception as ex:
    #         self.driver.reply_to(msg, f"Ошибка при выполнении задачи: {ex}")
    #     log.info(f"Веб-хук complete выполнен: {datetime.datetime.now()}")


def add_LEAD(message_id, user_db_id):
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    current_year = datetime.datetime.now().year
    message_link = config.MATTERMOST_URL + '/mosproektkompleks/pl/' + message_id
    with firebirdsql.connect(host=config.host, database=config.database, user=config.user, password=config.password, charset=config.charset) as con:
        cur = con.cursor()
        Sql = f"""SELECT ID FROM T3 WHERE F16 = '{user_db_id}'"""
        cur.execute(Sql)
        userData = cur.fetchone()
        userId = userData[0]
        sql_count_of_lead = f"""
        SELECT COUNT(*) 
        FROM T208 
        WHERE T208.F4452 = {current_year};
        """
        cur.execute(sql_count_of_lead)
        count_of_lead = cur.fetchall()[0][0]
        print(count_of_lead)
        lead_num = str(current_year) + '-' + str(int(count_of_lead) + 1) + 'Л'
        path_of_lead = 'N:\\1. Лиды\\'+str(current_year)+'\\'+lead_num
        print(lead_num)
        print(path_of_lead)
        cur.execute(f'SELECT GEN_ID(GEN_T208, 1) FROM RDB$DATABASE')
        ID = cur.fetchonemap().get('GEN_ID', None)
        values = {
            'id': ID,
            'F4452': current_year, #год добавления КП
            'F4442': current_date, #дата добавления КП
            'F4443': current_time, #время добавления КП
            'F4450': lead_num,
            'F4458': message_link,
            'F4446': userId,
            'F5006': path_of_lead,
            'F4477': 'напоминать Исп.',
            'F4964': message_id,
            }
        sql = f"""
        INSERT INTO T208 (
        {', '.join(values.keys())}
        ) VALUES (
        {', '.join(f"'{value}'" for value in values.values())}
        )
        """
        cur.execute(sql)
        con.commit()
        con.close()
        return lead_num


def add_KP(message_id, user_db_id):
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    current_year = datetime.datetime.now().year
    message_link = config.MATTERMOST_URL + '/mosproektkompleks/pl/' + message_id
    with firebirdsql.connect(host=config.host, database=config.database, user=config.user, password=config.password,
                             charset=config.charset) as con:
        cur = con.cursor()
        Sql = f"""SELECT ID, F4887SRC, F4887DEST FROM T3 WHERE F16 = '{user_db_id}'"""
        cur.execute(Sql)
        userData = cur.fetchone()
        userId = userData[0]
        src = userData[1]
        dest = userData[2]
        sql_count_of_kp = f"""
        SELECT COUNT(*) 
        FROM T209 
        WHERE T209.F4500 = {current_year};
        """
        cur.execute(sql_count_of_kp)
        count_of_kp = cur.fetchall()[0][0]
        print(count_of_kp)
        kp_num = str(current_year) + '-' + str(int(count_of_kp) + 1) + 'КП'
        path_of_kp = 'N:\\2. КП\\' + str(current_year) + '\\' + kp_num
        print(kp_num)
        print(path_of_kp)
        cur.execute(f'SELECT GEN_ID(GEN_T209, 1) FROM RDB$DATABASE')
        Id = cur.fetchonemap().get('GEN_ID', None)
        values = {
            'id': Id,
            'F4490': Id,
            'F4500': current_year,  # год добавления КП
            'F4511': current_date,  # дата добавления КП
            'F4485': current_date,  # дата КП
            'F4480': kp_num,
            'F4491': 'В процессе подготовки',
            'F4505': message_link,
            'F4496': userId,
            'F4527': path_of_kp,
            'F4528': 'напоминать Исп.',
            'F4512': message_id,
            'F4483': 'выполнение работ по ... (далее Объект(ы))',  # предмет работ
            'F4484': 0,  # цена работ
            'F4488': 0,  # срок работ
            'F4503': 1,
            'F4888SRC': src,
            'F4888DEST': dest,
        }
        sql = f"""
        INSERT INTO T209 (
        {', '.join(values.keys())}
        ) VALUES (
        {', '.join(f"'{value}'" for value in values.values())}
        )
        """
        cur.execute(sql)
        con.commit()
        con.close()
        return kp_num