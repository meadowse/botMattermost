from mmpy_bot import Plugin, listen_webhook, WebHookEvent, ActionEvent
from reminder import set_value_by_id

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
    async def cancel(self, event: WebHookEvent):
        """Прослушивает веб-перехватчики «ping» и «pong» и либо обновляет исходный пост,
        либо отправляет сообщение на канал, чтобы указать, что веб-перехватчик работает."""
        if event.body.get('user_name') == event.context.get("manager_nickname"):
            set_value_by_id('T209', 'F4491', 'Провал', event.context.get("doc_id"))
            set_value_by_id('T209', 'F4529', 'NULL', event.context.get("doc_id"))
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