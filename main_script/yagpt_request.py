import json
import requests

from config import (
    YANDEX_API_KEY,
    YANDEX_CLOUD_CATALOG,
    YANDEX_GPT_MODEL
)


def analyze_answers(child_data: list[int],
                    parent_data: dict[str: str]):
    system_prompt = (
        'На основе данных об интересах ребёнка подбери '
        'подходящую ему секцию или кружок\n'
        'В ответе должен быть список из пяти лучших '
        'вариантов и обоснование к ним\n'
        '**Не проси учитывать мнение ребёнка**'
    )
    subjects = [
        'творческая деятельность',
        'искусствоведенье',
        'изучение естественных наук',
        'изучение стратегических игр',
        'танцевать',
        'игры с мячом',
        'игра на струнных инструментах',
        'изучение точных наук',
        'изучение технических наук',
        'игра на клавишных инструментах',
        'катание на коньках',
        'игры, развивающие ловкость'
    ]
    user_prompt = (
        f'Возраст ребёнка - {parent_data["age"]}. '
        f'Пол ребёнка - {parent_data["gender"]}. '
        'Для родителя предпочтительно '
        f'направление - {parent_data["priority"]}. '
        f'Бюджет - {parent_data["price"]}. '
        f'В неделю должно быть около {parent_data["schedule"]} занятий. '
        f'Ребёнок находится в {parent_data["city"]}. '
    )
    user_prompt += '\n\n'
    for subject, value in zip(subjects, child_data):
        like = ''
        if value in (0, 3):
            like += 'очень '
        if value in (0, 1):
            like += 'не '
        user_prompt += f'Ребёнку {like}нравится {subject}. '

    body = {
        'modelUri': f'gpt://{YANDEX_CLOUD_CATALOG}/{YANDEX_GPT_MODEL}/latest',
        'completionOptions': {
            'stream': False,
            'temperature': 0.3,
            'maxTokens': '2000',
        },
        'messages': [
            {'role': 'system', 'text': system_prompt},
            {'role': 'user', 'text': user_prompt},
        ],
    }
    url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Api-Key {YANDEX_API_KEY}',
    }
    response = requests.post(url, headers=headers, json=body)

    if response.status_code != 200:
        return 'ERROR'

    response_json = json.loads(response.text)
    answer = response_json['result']['alternatives'][0]['message']['text']
    if len(answer) == 0:
        return 'ERROR'
    return answer
