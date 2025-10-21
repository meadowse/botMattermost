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
    @listen_to("Статус: :new: \*Новая\* :new:")
    async def newTask(self, message: Message):
        if message.channel_id == 'xcuskm3u9pbz9c5yqp6o49iuay':
            mes_json = {
                'attachments': [
                    {
                        "actions": [
                            {
                                "id": "takeWork",
                                "name": "Взять в работу :molot:",
                                "integration": {
                                    "url": f"{config.webhook_host_url}:{config.webhook_host_port}/hooks/takeWork",
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

    @listen_to("Статус: :molot: \*В работе\* :molot:")
    async def workTask(self, message: Message):
        if message.channel_id == 'xcuskm3u9pbz9c5yqp6o49iuay':
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
    async def completedTask(self, message: Message):
        if message.channel_id == 'xcuskm3u9pbz9c5yqp6o49iuay':
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
                        cur.execute(f"UPDATE T218 SET F5872 = 'Отмененная', F4697 = 0 WHERE F5451 = '{message.reply_id}'")
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
                        else:
                            log.info(f'Failed to send message: {response.status_code}, {response.text}')
                            self.driver.reply_to(message,
                                                 f'Failed to send message: {response.status_code}, {response.text}')
                        deleteButtons(self, message)
                    else:
                        self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Отменить :x:\"")
                else:
                    self.driver.reply_to(message, 'В базе не сохранён messageId')
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

    @listen_webhook("takeWork")
    async def takeWork(self, event: WebHookEvent):
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
                        if status == 'Новая':
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
                            else:
                                log.info(f'Failed to send message: {response.status_code}, {response.text}')
                                self.driver.reply_to(message,
                                                     f'Failed to send message: {response.status_code}, {response.text}')
                        else:
                            self.driver.reply_to(message, 'Не подходящий статус у задачи')
                        deleteButtons(self, message)
                    else:
                        self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Отменить :x:\"")
                else:
                    self.driver.reply_to(message, 'В базе не сохранён messageId')
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

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
                            else:
                                log.info(f'Failed to send message: {response.status_code}, {response.text}')
                                self.driver.reply_to(message,
                                                     f'Failed to send message: {response.status_code}, {response.text}')
                        else:
                            self.driver.reply_to(message, 'Не подходящий статус у задачи')
                        deleteButtons(self, message)
                    else:
                        self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Отменить :x:\"")
                else:
                    self.driver.reply_to(message, 'В базе не сохранён messageId')
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

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
                            else:
                                log.info(f'Failed to send message: {response.status_code}, {response.text}')
                                self.driver.reply_to(message,
                                                     f'Failed to send message: {response.status_code}, {response.text}')
                        else:
                            self.driver.reply_to(message, 'Не подходящий статус у задачи')
                        deleteButtons(self, message)
                    else:
                        self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Отменить :x:\"")
                else:
                    self.driver.reply_to(message, 'В базе не сохранён messageId')
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

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
                            else:
                                log.info(f'Failed to send message: {response.status_code}, {response.text}')
                                self.driver.reply_to(message,
                                                     f'Failed to send message: {response.status_code}, {response.text}')
                        else:
                            self.driver.reply_to(message, 'Не подходящий статус у задачи')
                        deleteButtons(self, message)
                    else:
                        self.driver.reply_to(message, f"@{User} у тебя нет прав нажимать \"Отменить :x:\"")
                else:
                    self.driver.reply_to(message, 'В базе не сохранён messageId')
        except Exception as error:
            log.info(json.dumps(error, indent=4, sort_keys=True, ensure_ascii=False))
            self.driver.reply_to(message, f"что-то пошло не так: {error}")

def deleteButtons(self, message):
    response = requests.get(f"{config.MATTERMOST_URL}:{config.MATTERMOST_PORT}/api/v4/posts/{message.reply_id}/thread",
                            headers=config.headers_notify_tasks_bot)
    if response.status_code == 200:
        log.info('Message sent successfully.')
        responseJson = response.json()
        log.info(json.dumps(responseJson, indent=4, sort_keys=True, ensure_ascii=False))
        messages = responseJson.get('order')
        for message in messages:
            if responseJson.get('posts').get(message).get('props') not in [
                {"from_bot": "true"}, {"disable_group_highlight": True}, {"disable_group_highlight": False}]:
                data = {'id': message}
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

def editMessage(replyId, cur):
    cur.execute(f"""SELECT ID AS id,
    F4695 AS task,
    F4698 AS comment,
    F5569 AS dateStart,
    F4696 AS deadline,
    F4697 AS done,
    F4708 AS today,
    F4693 AS directorId,
    F4694 AS executorId,
    F5872 AS status,
    F5889 AS plannedTimeCosts FROM T218 WHERE F5451 = '{replyId}'""")
    taskData = cur.fetchone()
    columns = ('id', 'task', 'comment', 'dateStart', 'deadline', 'done', 'today', 'directorId', 'executorId', 'status',
               'plannedTimeCosts')
    jsonResult = {col: value for col, value in zip(columns, taskData)}
    sql = f"SELECT F4932 FROM T3 WHERE ID = {jsonResult.get('directorId')}"
    cur.execute(sql)
    director = cur.fetchone()[0]
    sql = f"SELECT F4932 FROM T3 WHERE ID = {jsonResult.get('executorId')}"
    cur.execute(sql)
    executor = cur.fetchone()[0]
    done = jsonResult.get('done')
    message = f"**{'Изменена' if done != 1 else 'Завершена'} :hammer_and_wrench: Задача :hammer_and_wrench: by @{director}**\n"
    message += f"Дата добавления: *{jsonResult.get('dateStart')}*\n"
    message += f"Постановщик: *@{director}*\n"
    message += f"Исполнитель: *@{executor}*\n"
    message += f"Задача: :hammer: *{jsonResult.get('task')}*\n"
    message += f"Deadline: :calendar: *{jsonResult.get('deadline')}*\n"
    comment = jsonResult.get('comment')
    if comment != '':
        message += f"Комментарий: :speech_balloon: *{comment}*\n"
    plannedTimeCosts = jsonResult.get('plannedTimeCosts')
    if plannedTimeCosts is not None:
        message += f"Планируемые времязатраты: :clock3: *{jsonResult.get('plannedTimeCosts')}ч.*\n"
    sql = f"SELECT SUM(F5882) FROM T320 WHERE F5862 = {jsonResult.get('id')}"
    cur.execute(sql)
    currentTimeCosts = cur.fetchone()[0]
    if currentTimeCosts is not None:
        message += f"Текущие времязатраты: :clock3: *{currentTimeCosts}ч.*\n"
    statusEmoji = ''
    status = jsonResult.get('status')
    match status:
        case 'Новая':
            statusEmoji = ':new:'
        case 'В работе':
            statusEmoji = ':molot:'
        case 'Выполненная':
            statusEmoji = ':white_check_mark:'
        case 'Завершенная':
            statusEmoji = ':thumbsup:'
        case 'Отмененная':
            statusEmoji = ':x:'
    message += f"Статус: {statusEmoji} *{status}* {statusEmoji}\n"
    if status != 'Отмененная':
        message += ":large_yellow_circle: *Задача ожидает завершения...*" if done != 1 else f":large_green_circle: *Задача завершена {jsonResult.get('today')}*"
    return message