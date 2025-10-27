import json
from mmpy_bot import Plugin, listen_to, listen_webhook, WebHookEvent, Message
from mmpy_bot.plugins.base import log
import firebirdsql
import config
from functions import set_value_by_id


class SearchPlugin(Plugin):
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
                    WHERE T213.F4928 = '{message.reply_id}'""")
                data = cur.fetchone()
                docId = data[0]
                projectManager = data[1]
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
                                                    managerNicknames=managerNicknames,
                                                    text=':x: Аннулировать')
                                },
                            },
                        ],
                    }
                ]
            }
            self.driver.reply_to(message, '', props=props)
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

    @listen_webhook("underApproval")
    @listen_webhook("couldNotGetInTouch")
    async def Cancel(self, event: WebHookEvent):
        eventBody = event.body
        context = eventBody.get('context')
        User = eventBody.get('user_name')
        if User in context.get("managerNicknames"):
            self.driver.respond_to_web(event, {"update": {
                "message": f'{context.get("message")}\n@{User} ответил {context.get("text")}', "props": {}}, }, )
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
            self.driver.respond_to_web(event, {"update": {
                "message": f'{context.get("message")}\n@{User} ответил {context.get("text")}', "props": {}}, }, )
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
                kpId = cur.fetchone()[0]
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
                                    "context": dict(text=":x: Провал", message=message.body, kpId=kpId,
                                                    managerNicknames=(managerNickname,), )
                                },
                            },
                        ],
                    }
                ]
            }
            self.driver.reply_to(message, '', props=props)
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

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
            self.driver.reply_to(message, f'@{User} у тебя нет прав нажимать {context.get("text")}')