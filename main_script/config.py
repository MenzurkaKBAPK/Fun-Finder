import environ
import os


env = environ.Env(
    DEBUG=(bool, False)
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

TELEGRAM_TOKEN = env('TELEGRAM_TOKEN')
YANDEX_CLOUD_CATALOG = env('YANDEX_CLOUD_CATALOG')
YANDEX_API_KEY = env('YANDEX_API_KEY')
YANDEX_GPT_MODEL = env('YANDEX_GPT_MODEL')
DATABASE = env('DATABASE')
