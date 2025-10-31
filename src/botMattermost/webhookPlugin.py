import datetime
import json
from mmpy_bot import Plugin, listen_webhook, WebHookEvent, ActionEvent, listen_to, Message
from functions import set_value_by_id, add_KP, add_LEAD, editMessage
import re
import config
import requests
import firebirdsql
from mmpy_bot.plugins.base import log
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class webhookPlugin(Plugin):
    @listen_to("Просьба связаться с Заказчиком и узнать когда оплатят/подпишут")
    async def docsButtons(self, message: Message):
        try:
            managerNickname = message.text.split('@')[1].split()[0]
            with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                     password=config.password, charset=config.charset) as con:
                cur = con.cursor()
                cur.execute(f"""SELECT T213.ID AS docId,
                projectManager.F4932 AS projectManager
                FROM T213
                LEFT JOIN T212 ON T213.F4573 = T212.ID
                LEFT JOIN T3 AS projectManager ON T212.F4950 = projectManager.ID
                WHERE T212.F4644 = '{message.channel_id}'""")
                data = cur.fetchone()
                if data is not None:
                    docId = data[0]
                    projectManager = data[1]
                else:
                    docId = None
                    projectManager = None
            managerNicknames = (managerNickname, projectManager)
            props = {
                "attachments": [
                    {
                        "actions": [
                            {
                                "id": "underApproval",
                                "name": ":memo: На согласовании",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/underApproval",
                                    "context": dict(message=message.body, managerNicknames=managerNicknames,
                                                    text=':memo: На согласовании')
                                },
                            },
                            {
                                "id": "couldNotGetInTouch",
                                "name": ":shrug: Не удалось связаться",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/couldNotGetInTouch",
                                    "context": dict(message=message.body, managerNicknames=managerNicknames,
                                                    text=':shrug: Не удалось связаться')
                                },
                            },
                            {
                                "id": "cancelDocs",
                                "name": ":x: Аннулировать",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/cancelDocs",
                                    "context": dict(message=message.body, docId=docId,
                                                    managerNicknames=managerNicknames, )
                                },
                            },
                        ],
                    }
                ]
            }
            self.driver.reply_to(message, '', props=props)
        except Exception as error:
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")

    @listen_webhook("underApproval")
    @listen_webhook("couldNotGetInTouch")
    async def Cancel(self, event: WebHookEvent):
        eventBody = event.body
        context = eventBody.get('context')
        User = eventBody.get('user_name')
        if User in context.get("managerNicknames"):
            self.driver.respond_to_web(event, {"update": {"message": f'@{User} ответил {context.get("text")}',
                                                          "props": {}}, }, )
        else:
            message = Message(context.get('message'))
            self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать {context.get('text')}")

    @listen_webhook("cancelDocs")
    async def cancelDocs(self, event: WebHookEvent):
        eventBody = event.body
        context = eventBody.get('context')
        User = eventBody.get('user_name')
        if User in context.get("managerNicknames"):
            set_value_by_id('T213', 'F4570', 'Аннулирован', context.get("docId"))
            set_value_by_id('T213', 'F4666', 'NULL', context.get("docId"))
            self.driver.respond_to_web(event, {"update": {"message": f'@{User} ответил {context.get("text")}',
                                                          "props": {}}, }, )
        else:
            message = Message(context.get('message'))
            self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать :x: Аннулировать")

    @listen_to("Просьба связаться с Заказчиком и получить обратную связь по нашему КП")
    async def kpButtons(self, message: Message):
        try:
            managerNickname = message.text.split('@')[1].split()[0]
            with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                     password=config.password, charset=config.charset) as con:
                cur = con.cursor()
                cur.execute(f"SELECT ID AS kpId FROM T209 WHERE F4505 = '{message.reply_id}'")
                data = cur.fetchall()
                if data is not None:
                    kpId = data[0]
                else:
                    kpId = None
            props = {
                "attachments": [
                    {
                        "actions": [
                            {
                                "id": "underApproval",
                                "name": ":memo: На согласовании",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/"
                                           f"hooks/underApproval",
                                    "context": dict(text=":memo: На согласовании", message=message.body,
                                                    managerNicknames=(managerNickname,), )
                                },
                            },
                            {
                                "id": "couldNotGetInTouch",
                                "name": ":shrug: Не удалось связаться",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/"
                                           "hooks/couldNotGetInTouch",
                                    "context": dict(text=":shrug: Не удалось связаться", message=message.body,
                                                    managerNicknames=(managerNickname,), )
                                },
                            },
                            {
                                "id": "failure",
                                "name": ":x: Провал",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/failure",
                                    "context": dict(message=message.body, kpId=kpId,
                                                    managerNicknames=(managerNickname,), )
                                },
                            },
                        ],
                    }
                ]
            }
            self.driver.reply_to(message, '', props=props)
        except Exception as error:
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")

    @listen_webhook("failure")
    async def failure(self, event: WebHookEvent):
        eventBody = event.body
        context = eventBody.get('context')
        User = eventBody.get('user_name')
        if User in context.get("managerNicknames"):
            set_value_by_id('T209', 'F4491', 'Провал', context.get("kpId"))
            set_value_by_id('T209', 'F4529', 'NULL', context.get("kpId"))
            self.driver.respond_to_web(event, {"update": {"message": f'@{User} ответил {context.get("text")}',
                                                          "props": {}}, }, )
        else:
            message = Message(context.get('message'))
            self.driver.reply_to(message, f'@{User} у тебя нет прав нажимать :x: Провал')

    @listen_to("Договор")
    async def agreement(self, message: Message):
        # log.info(json.dumps(message.body, indent=4, sort_keys=True, ensure_ascii=False))
        try:
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
        except Exception as error:
            log.info(error)
            self.driver.reply_to(message, f'@b.musaev, что-то пошло не так {error}')

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
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")

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
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")

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
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")

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
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")

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
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")

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
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")

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
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")

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
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")

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
                                "id": "deleteMessage",
                                "name": "❌ Удалить",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/deleteMessage",
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
                    self.driver.reply_to(message, f"@b.musaev, @{User}, ошибка при отправке: {e}")
                finally:
                    server.quit()

    @listen_webhook("deleteMessage")
    async def deleteMessage(self, event: WebHookEvent):
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
                log.info(json.dumps(response.json(), indent=4, sort_keys=True, ensure_ascii=False))
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
        if message.body.get('data').get('post').get('reply_count') == 0 and message.sender_name != 'notify_tasks_bot':
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
        self.driver.respond_to_web(event, {"update": {"message": '', "props": {}}, }, )

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
                sql = f"SELECT ID AS contractId FROM T212 WHERE F4644 = '{event.body.get('channel_id')}'"
                cur.execute(sql)
                contractId = cur.fetchone()
                if contractId is not None:
                    contractId = contractId[0]
                    projectId = None
                else:
                    sql = f"SELECT ID AS projectId FROM T323 WHERE F5895 = '{event.body.get('channel_id')}'"
                    cur.execute(sql)
                    projectId = cur.fetchone()
                    if projectId is not None:
                        projectId = projectId[0]
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
                    'F4694': executorId, 'F4697': 0, 'F5451': idMessage, 'F5872': 'Новая', 'F5889': plannedTimeCosts,
                    'F5900': projectId}
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
                    log.info(json.dumps(response.json(), indent=4, sort_keys=True, ensure_ascii=False))
                else:
                    log.info(f'Failed to send message: {response.status_code}, {response.text}')
                    self.driver.reply_to(msg, f'Failed to send message: {response.status_code}, {response.text}')
        except Exception as ex:
            self.driver.reply_to(msg, f"@b.musaev, Ошибка при создании задачи: {ex}")

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

    @listen_to("Статус: :new: \*Новая\* :new:")
    @listen_to("Статус: \*:new: Новая\* :new:")
    async def newTask(self, message: Message):
            mes_json = {
                'attachments': [
                    {
                        "actions": [
                            {
                                "id": "takeWork",
                                "name": "Взять в работу :molot:",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/takeWork",
                                    "context": {'message': message.body, 'direct': False},
                                }
                            },
                            {
                                'id': 'cancelTask',
                                'name': 'Отменить :x:',
                                'integration': {
                                    'url': f'{config.webhook_host_url}:{config.webhook_host_port}/hooks/cancelTask',
                                    'context': message.body,
                                }
                            }
                        ]
                    }
                ]
            }
            deleteButtons(self, message)
            self.driver.reply_to(message, '', props=mes_json)

    @listen_to("Статус: :molot: \*В работе\* :molot:")
    @listen_to("Статус: \*:molot: В работе\* :molot:")
    async def workTask(self, message: Message):
            mes_json = {
                'attachments': [
                    {
                        "actions": [
                            {
                                "id": "done",
                                "name": "Выполнено :white_check_mark:",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/done",
                                    "context": message.body,
                                }
                            },
                            {
                                'id': 'cancelTask',
                                'name': 'Отменить :x:',
                                'integration': {
                                    'url': f'{config.webhook_host_url}:{config.webhook_host_port}/hooks/cancelTask',
                                    'context': message.body,
                                }
                            }
                        ]
                    }
                ]
            }
            deleteButtons(self, message)
            self.driver.reply_to(message, '', props=mes_json)

    @listen_to("Статус: :white_check_mark: \*Выполненная\* :white_check_mark:")
    @listen_to("Статус: \*:white_check_mark: Выполненная\* :white_check_mark:")
    async def completedTask(self, message: Message):
            mes_json = {
                'attachments': [
                    {
                        "actions": [
                            {
                                "id": "acceptJob",
                                "name": "Принять работу :+1:",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/acceptJob",
                                    "context": message.body,
                                }
                            },
                            {
                                "id": "getBackWork",
                                "name": "Вернуть в работу :leftwards_arrow_with_hook:",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/getBackWork",
                                    "context": message.body,
                                }
                            },
                            {
                                'id': 'cancelTask',
                                'name': 'Отменить :x:',
                                'integration': {
                                    'url': f'{config.webhook_host_url}:{config.webhook_host_port}/hooks/cancelTask',
                                    'context': message.body,
                                }
                            }
                        ]
                    }
                ]
            }
            deleteButtons(self, message)
            self.driver.reply_to(message, '', props=mes_json)

    @listen_webhook("cancelTask")
    async def cancelTask(self, event: WebHookEvent):
        Data = event.body
        context = Data.get('context')
        message = Message(context)
        try:
            User = event.body.get('user_name')
            with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                     password=config.password, charset=config.charset) as con:
                cur = con.cursor()
                cur.execute(f"SELECT F4693 AS directorId FROM T218 WHERE F5451 = '{message.reply_id}'")
                director = cur.fetchone()
                if director is not None:
                    directorId = director[0]
                    cur.execute(f'SELECT F4932 FROM T3 WHERE ID = {directorId}')
                    director = cur.fetchone()[0]
                    if director == User:
                        cur.execute(f"SELECT F5872 AS status FROM T218 WHERE F5451 = '{message.reply_id}'")
                        status = cur.fetchone()[0]
                        if status != 'Завершенная':
                            today = datetime.date.today().strftime('%Y-%m-%d')
                            cur.execute(
                                f"UPDATE T218 SET F5872 = 'Отмененная', F4697 = 1, F4708 = '{today}' WHERE F5451 = '{message.reply_id}'")
                            con.commit()
                            textMessage = editMessage(message.reply_id, cur)
                            data = {'channel_id': Data.get('channel_id'), 'message': textMessage,
                                    'root_id': message.reply_id}
                            response = requests.post(f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/posts",
                                                     json=data,
                                                     headers=config.headers_notify_tasks_bot)
                            if response.status_code == 201:
                                log.info('Message sent successfully.')
                                log.info(json.dumps(response.json(), indent=4, sort_keys=True, ensure_ascii=False))
                                deleteButtons(self, message)
                            else:
                                log.info(f'Failed to send message: {response.status_code}, {response.text}')
                                self.driver.reply_to(message,
                                                     f'Failed to send message: {response.status_code}, {response.text}')
                        else:
                            self.driver.reply_to(message, f'Не подходящий статус у задачи {status}')
                    else:
                        self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Отменить :x:\"")
                else:
                    self.driver.reply_to(message, 'В базе не сохранён messageId')
        except Exception as error:
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")

    @listen_webhook("takeWork")
    async def takeWork(self, event: WebHookEvent):
        Data = event.body
        context = Data.get('context')
        message = Message(context.get('message'))
        try:
            User = event.body.get('user_name')
            with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                     password=config.password, charset=config.charset) as con:
                cur = con.cursor()
                cur.execute(f"SELECT F4694 AS executorId FROM T218 WHERE F5451 = '{message.reply_id}'")
                executor = cur.fetchone()
                if executor is not None:
                    executorId = executor[0]
                    cur.execute(f'SELECT F4932 FROM T3 WHERE ID = {executorId}')
                    executor = cur.fetchone()[0]
                    if executor == User:
                        cur.execute(f"SELECT F5872 AS status FROM T218 WHERE F5451 = '{message.reply_id}'")
                        status = cur.fetchone()[0]
                        if status == 'Новая':
                            cur.execute(
                                f"UPDATE T218 SET F5872 = 'В работе', F4697 = 0 WHERE F5451 = '{message.reply_id}'")
                            con.commit()
                            textMessage = editMessage(message.reply_id, cur)
                            data = {'channel_id': message.channel_id, 'message': textMessage,
                                    'root_id': message.reply_id}
                            response = requests.post(f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/posts",
                                                     json=data,
                                                     headers=config.headers_notify_tasks_bot)
                            if response.status_code == 201:
                                log.info('Message sent successfully.')
                                log.info(json.dumps(response.json(), indent=4, sort_keys=True, ensure_ascii=False))
                                deleteButtons(self, message)
                            else:
                                log.info(f'Failed to send message: {response.status_code}, {response.text}')
                                self.driver.reply_to(message,
                                                     f'Failed to send message: {response.status_code}, {response.text}', direct=context.get('direct'))
                        else:
                            self.driver.reply_to(message, f'Не подходящий статус у задачи {status}', direct=context.get('direct'))
                    else:
                        self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Взять в работу :molot:\"", direct=context.get('direct'))
                else:
                    self.driver.reply_to(message, 'В базе не сохранён messageId', direct=context.get('direct'))
        except Exception as error:
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}", direct=context.get('direct'))

    @listen_webhook("done")
    async def done(self, event: WebHookEvent):
        Data = event.body
        context = Data.get('context')
        message = Message(context)
        try:
            User = event.body.get('user_name')
            with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                     password=config.password, charset=config.charset) as con:
                cur = con.cursor()
                cur.execute(f"SELECT F4694 AS executorId FROM T218 WHERE F5451 = '{message.reply_id}'")
                executor = cur.fetchone()
                if executor is not None:
                    executorId = executor[0]
                    cur.execute(f'SELECT F4932 FROM T3 WHERE ID = {executorId}')
                    executor = cur.fetchone()[0]
                    if executor == User:
                        cur.execute(f"SELECT F5872 AS status FROM T218 WHERE F5451 = '{message.reply_id}'")
                        status = cur.fetchone()[0]
                        if status == 'В работе':
                            cur.execute(
                                f"UPDATE T218 SET F5872 = 'Выполненная', F4697 = 0 WHERE F5451 = '{message.reply_id}'")
                            con.commit()
                            textMessage = editMessage(message.reply_id, cur)
                            data = {'channel_id': Data.get('channel_id'), 'message': textMessage,
                                    'root_id': message.reply_id}
                            response = requests.post(f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/posts",
                                                     json=data,
                                                     headers=config.headers_notify_tasks_bot)
                            if response.status_code == 201:
                                log.info('Message sent successfully.')
                                log.info(json.dumps(response.json(), indent=4, sort_keys=True, ensure_ascii=False))
                                deleteButtons(self, message)
                            else:
                                log.info(f'Failed to send message: {response.status_code}, {response.text}')
                                self.driver.reply_to(message,
                                                     f'Failed to send message: {response.status_code}, {response.text}')
                        else:
                            self.driver.reply_to(message, f'Не подходящий статус у задачи {status}')
                    else:
                        self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Выполнено :white_check_mark:\"")
                else:
                    self.driver.reply_to(message, 'В базе не сохранён messageId')
        except Exception as error:
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")

    @listen_webhook("acceptJob")
    async def acceptJob(self, event: WebHookEvent):
        Data = event.body
        context = Data.get('context')
        message = Message(context)
        try:
            User = event.body.get('user_name')
            with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                     password=config.password, charset=config.charset) as con:
                cur = con.cursor()
                cur.execute(f"SELECT F4693 AS directorId FROM T218 WHERE F5451 = '{message.reply_id}'")
                director = cur.fetchone()
                if director is not None:
                    directorId = director[0]
                    cur.execute(f'SELECT F4932 FROM T3 WHERE ID = {directorId}')
                    director = cur.fetchone()[0]
                    if director == User:
                        cur.execute(f"SELECT F5872 AS status FROM T218 WHERE F5451 = '{message.reply_id}'")
                        status = cur.fetchone()[0]
                        if status == 'Выполненная':
                            today = datetime.date.today().strftime('%Y-%m-%d')
                            cur.execute(
                                f"UPDATE T218 SET F5872 = 'Завершенная', F4697 = 1, F4708 = '{today}' WHERE F5451 = '{message.reply_id}'")
                            con.commit()
                            textMessage = editMessage(message.reply_id, cur)
                            data = {'channel_id': Data.get('channel_id'), 'message': textMessage,
                                    'root_id': message.reply_id}
                            response = requests.post(f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/posts",
                                                     json=data,
                                                     headers=config.headers_notify_tasks_bot)
                            if response.status_code == 201:
                                log.info('Message sent successfully.')
                                log.info(json.dumps(response.json(), indent=4, sort_keys=True, ensure_ascii=False))
                                deleteButtons(self, message)
                            else:
                                log.info(f'Failed to send message: {response.status_code}, {response.text}')
                                self.driver.reply_to(message,
                                                     f'Failed to send message: {response.status_code}, {response.text}')
                        else:
                            self.driver.reply_to(message, f'Не подходящий статус у задачи {status}')
                    else:
                        self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Отменить :x:\"")
                else:
                    self.driver.reply_to(message, 'В базе не сохранён messageId')
        except Exception as error:
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")

    @listen_webhook("getBackWork")
    async def getBackWork(self, event: WebHookEvent):
        Data = event.body
        context = Data.get('context')
        message = Message(context)
        try:
            User = event.body.get('user_name')
            with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                     password=config.password, charset=config.charset) as con:
                cur = con.cursor()
                cur.execute(f"SELECT F4693 AS directorId FROM T218 WHERE F5451 = '{message.reply_id}'")
                director = cur.fetchone()
                if director is not None:
                    directorId = director[0]
                    cur.execute(f'SELECT F4932 FROM T3 WHERE ID = {directorId}')
                    director = cur.fetchone()[0]
                    if director == User:
                        cur.execute(f"SELECT F5872 AS status FROM T218 WHERE F5451 = '{message.reply_id}'")
                        status = cur.fetchone()[0]
                        if status == 'Выполненная':
                            cur.execute(
                                f"UPDATE T218 SET F5872 = 'В работе', F4697 = 0 WHERE F5451 = '{message.reply_id}'")
                            con.commit()
                            textMessage = editMessage(message.reply_id, cur)
                            data = {'channel_id': Data.get('channel_id'), 'message': textMessage,
                                    'root_id': message.reply_id}
                            response = requests.post(f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/posts",
                                                     json=data,
                                                     headers=config.headers_notify_tasks_bot)
                            if response.status_code == 201:
                                log.info('Message sent successfully.')
                                log.info(json.dumps(response.json(), indent=4, sort_keys=True, ensure_ascii=False))
                                deleteButtons(self, message)
                            else:
                                log.info(f'Failed to send message: {response.status_code}, {response.text}')
                                self.driver.reply_to(message,
                                                     f'Failed to send message: {response.status_code}, {response.text}')
                        else:
                            self.driver.reply_to(message, f'Не подходящий статус у задачи {status}')
                    else:
                        self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Отменить :x:\"")
                else:
                    self.driver.reply_to(message, 'В базе не сохранён messageId')
        except Exception as error:
            log.info(error)
            self.driver.reply_to(message, f"@b.musaev, что-то пошло не так: {error}")


def deleteButtons(self, message):
    response = requests.get(f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/posts/{message.reply_id}/thread",
                            headers=config.headers_notify_tasks_bot)
    if response.status_code == 200:
        log.info('Message sent successfully.')
        responseJson = response.json()
        log.info(json.dumps(responseJson, indent=4, sort_keys=True, ensure_ascii=False))
        messages = responseJson.get('order')
        for message in messages:
            messageData = responseJson.get('posts').get(message)
            if messageData.get('props') not in [
                {"from_bot": "true"}, {"disable_group_highlight": True}, {"disable_group_highlight": False}]:
                data = {'id': message, 'message': messageData.get('message')}
                response = requests.put(
                    f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/posts/{message}",
                    json=data, headers=config.headers_notify_tasks_bot)
                if response.status_code == 200:
                    log.info('Message sent successfully.')
                    log.info(
                        json.dumps(response.json(), indent=4, sort_keys=True, ensure_ascii=False))
                else:
                    log.info(f'Failed to update message: {response.status_code}, {response.text}')
                    self.driver.reply_to(message,
                                         f'Failed to update message: {response.status_code}, {response.text}')
    else:
        log.info(f'Failed get data message: {response.status_code}, {response.text}')
        self.driver.reply_to(message,
                             f'Failed get data message: {response.status_code}, {response.text}')