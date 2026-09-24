from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan quyidagilarni o'qiymiz
BOT_TOKEN = env.str("BOT_TOKEN", default=None)  # Bot token
# Django imports bot helpers while loading URLs, including during health checks
# and tests.  A missing optional Telegram configuration must not prevent the
# whole web application from starting; webhook handling already rejects calls
# when no bot has been configured.
ADMINS = env.list("ADMINS", default=[])  # adminlar ro'yxati
