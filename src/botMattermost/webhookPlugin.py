from mmpy_bot import Plugin, listen_webhook, WebHookEvent, ActionEvent
from reminder import set_value_by_id

class webhookPlugin(Plugin):
    @listen_webhook("underApproval")
    @listen_webhook("couldNotGetInTouch")
    async def Cancel(self, event: WebHookEvent):
        """Прослушивает веб-перехватчики «ping» и «pong» и либо обновляет исходный пост,
        либо отправляет сообщение на канал, чтобы указать, что веб-перехватчик работает."""
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

    @listen_webhook("cancel")
    async def cancel(self, event: WebHookEvent):
        """Прослушивает веб-перехватчики «ping» и «pong» и либо обновляет исходный пост,
        либо отправляет сообщение на канал, чтобы указать, что веб-перехватчик работает."""
        if event.context.get("doc_id") is not None:
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