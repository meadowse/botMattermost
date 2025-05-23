from mmpy_bot import Bot, ExamplePlugin, Settings, WebHookExample
from plugin import SearchPlugin
from webhookPlugin import webhookPlugin
from config import MATTERMOST_URL, MATTERMOST_PORT, ACCESS_TOKEN, WEBHOOK_HOST_URL

bot = Bot(
    # Either specify your settings here or use environment variables to override them.
    # See docker-compose.yml for an example you can use for local development.
    settings=Settings(
        MATTERMOST_URL = MATTERMOST_URL,
        MATTERMOST_PORT = MATTERMOST_PORT,
        BOT_TOKEN = ACCESS_TOKEN,
        SSL_VERIFY = True,
        WEBHOOK_HOST_ENABLED = True,
        WEBHOOK_HOST_URL = WEBHOOK_HOST_URL,
        # WEBHOOK_HOST_PORT = 8579,
        # LOG_LEVEL = logging.DEBUG,
    ),
    plugins=[ExamplePlugin(), WebHookExample(), webhookPlugin(),
             # SearchPlugin(),
             ],  # Add your own plugins here.
)
bot.run()