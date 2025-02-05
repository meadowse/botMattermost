bot_token, ACCESS_TOKEN = "токен бота"
bot_user_id = "id бота"

# параметры подключения к базе:
database = 'твоя база'
host = 'хост твоей базы'
# database='твоя база'
user = 'пользователь базы'
password = 'пароль пользователя базы'
charset = 'кодировка твоей базы'

MATTERMOST_URL = "url твоего мм"
MATTERMOST_PORT = "порт твоего мм"
WEBHOOK_HOST_URL = "url твоего вебхук сервера" # http://localhost или http://0.0.0.0
TEAM_ID = "id команды в мм"
headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

ACCESS_TOKEN_OKO = "вообще хз, что это 😂"
headers_oko = {
    'Authorization': f'Bearer {ACCESS_TOKEN_OKO}',
    'Content-Type': 'application/json'
}

webhook_host_url = "url твоего вебхук сервера"
webhook_host_port = 8579

webhookHostUrl = "http://localhost"
mattermost_host = "http://localhost"
mattermost_port = 8065
confluence_url = "адрес твоей Вики"
