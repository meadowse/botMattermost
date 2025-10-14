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
    @listen_to("Договор")
    async def agreement(self, message: Message):
        # log.info(json.dumps(message.body, indent=4, sort_keys=True, ensure_ascii=False))
        if message.sender_name == 'notify_docs_bot':
            headDepartment = message.text.split('Рук отдела: @')[1].split()[0]
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
            self.driver.reply_to(message, f'Рук отдела @{headDepartment}', props=props)
            pRM = message.text.split('ПрМ: @')[1].split()[0]
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
            self.driver.reply_to(message, f'Прм @{pRM}', props=props)

    @listen_webhook("deniedPRM")
    async def deniedPRM(self, event: WebHookEvent):
        context = event.body.get('context')
        message = Message(context.get('message'))
        try:
            User = event.body.get('user_name')
            if User == context.get("pRM"):
                with firebirdsql.connect(host=config.host, database=config.database, user=config.user,
                                         password=config.password, charset=config.charset) as con:
                    today = datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d')
                    cur = con.cursor()
                    cur.execute(f"""SELECT ID FROM T3 WHERE F4932 = '{User}'""")
                    iD = cur.fetchone()[0]
                    log.info(iD)
                    idChannel = message.channel_id
                    cur.execute(f"SELECT T213.ID FROM T213 JOIN T212 ON T212.ID = T213.F4573 WHERE F4644 = '{idChannel}'")
                    idAgreement = cur.fetchone()[0]
                    log.info(idAgreement)
                    cur.execute(f"UPDATE T213 SET F5303 = 0, F5307 = {iD}, F5309 = '{today}' WHERE ID = {idAgreement} AND F4567 = 1")
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
            if User == context.get("pRM"):
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
                    cur.execute(f"UPDATE T213 SET F5303 = 1, F5307 = {iD}, F5309 = '{today}' WHERE ID = {idAgreement} AND F4567 = 1")
                    con.commit()
                    self.driver.respond_to_web(event, {"update": {"message": f"@{User} Согласовал :white_check_mark:", "props": {}}, }, )
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
            if User == context.get("headDepartment"):
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
            if User == context.get("headDepartment"):
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