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
from pyexpat.errors import messages
import config
from reminder import send_message_to_channel, getChannelId
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

class SearchPlugin(Plugin):
    @listen_to("[А-Яа-яЁё]*")
    async def officialStatements(self, message: Message):
        # log.info(json.dumps(message.body, indent=4, sort_keys=True, ensure_ascii=False))
        if message.sender_name == 'notify_bot' and message.channel_id == 'xcuskm3u9pbz9c5yqp6o49iuay' and message.body.get('data').get('post').get('reply_count') == 0:
            mustCoordinate = message.text.split('Должен согласовать: *@')[1].strip('*')
            props = {
                "attachments": [
                    {
                        "actions": [
                            {
                                "id": "approve",
                                "name": ":white_check_mark: Согласовать",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/approve",
                                    "context": dict(message=message.body, mustCoordinate=mustCoordinate, )
                                },
                            },
                            {
                                "id": "denied",
                                "name": ":x: Отказать",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/denied",
                                    "context": dict(message=message.body, mustCoordinate=mustCoordinate, )
                                },
                            },
                        ],
                    }
                ]
            }
            self.driver.reply_to(message, '', props=props)

    @listen_webhook("denied")
    async def denied(self, event: WebHookEvent):
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
                    self.driver.respond_to_web(event,
                                               {"update": {"message": f"@{User} ответил Отказом :x:", "props": {}}, }, )
            else:
                self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Отказать\"")
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

    @listen_webhook("approve")
    async def approve(self, event: WebHookEvent):
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
                    self.driver.respond_to_web(event, {"update": {"message": f"@{User} Согласовал :white_check_mark:", "props": {}}, }, )
            else:
                self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Согласовать\"")
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")