from mmpy_bot import Plugin, listen_webhook, WebHookEvent, ActionEvent, listen_to, Message
from reminder import set_value_by_id
import re
from dataclasses import dataclass, asdict
from typing import Optional

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
        if event.body.get('user_name') == event.context.get("manager_nickname"):
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
        if event.body.get('user_name') == event.context.get("manager_nickname"):
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
    async def nonStandard(self, event: WebHookEvent, message: Message):
        """Прослушивает веб-перехватчики «ping» и «pong» и либо обновляет исходный пост,
        либо отправляет сообщение на канал, чтобы указать, что веб-перехватчик работает."""
        if event.body.get('user_name') in event.context.get("managerNicknames"):
            if isinstance(event, ActionEvent):
                self.driver.reply_to(message, '', props={
                    "attachments": [
                        {
                            "text": f"⛔Неквал от {event.body.get('user_name')}",
                        }
                    ]
                })
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

    # @listen_to("^((?!Найди).)*$", re.IGNORECASE)
    # async def hello(self, message: Message, status):
    #     blocks = [
    #         Section(
    #             title=f'Приветствую!',
    #             text=f'Я осуществляю поиск по базе знаний [wiki]({confluence_url}). Поиск осуществляется только по публичным страницам.\nЧтобы начать поиск используйте слово **Найди** и ваш запрос, пример: **Найди цели и планы**',
    #             fields=list(filter(None, [
    #                 Field(
    #                     title='Поиск осуществляется с предустановленными настройками:',
    #                     value='', short=False),
    #                 Field(title='Пространства', value='QA, DEV'),
    #                 Field(title='Период', value='Последний год'),
    #                 Field(title='Содержимое', value='Страница'),
    #             ]
    #                                )
    #                         )
    #         )
    #     ]
    #     mes_json = {'attachments': [block.asdict() for block in blocks]}
    #     self.driver.respond_to_web(message, '', props=mes_json)