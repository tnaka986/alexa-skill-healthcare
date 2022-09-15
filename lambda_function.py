import os
import requests 
import urllib3

from urllib3.exceptions import InsecureRequestWarning
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import get_slot_value, is_intent_name, is_request_type
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

sb = SkillBuilder()

# POSTリクエスト時に発生するWARNINGを無視する
urllib3.disable_warnings(InsecureRequestWarning)
# Alexaから受けた質問が何回目かをカウントする（Conditionインテントが呼ばれた回数）
question_counter = 0
# Alexa経由で発話された健康データを保管
health_data={}

# Alexaスキルを起動したときに呼び出される関数
@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    # ローバル変数を読み込む
    global question_counter
    # 質問カウンタを1に初期化
    question_counter = 1
            
    # 1回目の質問
    speech_text = "今日の気分はどうですか？"

    handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard("健康管理アプリ", speech_text)).set_should_end_session(
        False)
    return handler_input.response_builder.response

# Alexaの質問に回答したときに呼び出される関数（自由テキストのため何を発話してもこのインテントが起動）
@sb.request_handler(can_handle_func=is_intent_name("Condition"))
def health_telling_intent_handler(handler_input):
    # ローバル変数を読み込む
    global question_counter
    global health_data
    
    # 回答した発話を読み込む
    user_condition = get_slot_value(handler_input=handler_input, slot_name="utterance")
    print(user_condition)
    
    # 1回目の質問に回答したとき
    if question_counter == 1:
        # 気分の状態を変数に保管
        health_data['condition'] = user_condition
        # 次の質問をAlexaに発話させる
        speech_text = "ストレス値はどうですか？"
        handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard("健康管理アプリ", speech_text)).set_should_end_session(False)
        # 質問カウンタをインクリメント
        question_counter += 1

    # 2回目の質問に回答したとき
    elif question_counter == 2:
        # ストレスの状態を変数に保管
        health_data['stress'] = user_condition
        # 次の質問をAlexaに発話させる
        speech_text = "睡眠はどうですか？"
        handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard("健康管理アプリ", speech_text)).set_should_end_session(False)
        # 質問カウンタをインクリメント
        question_counter += 1
    
    # 3回目の質問に回答したとき    
    elif question_counter == 3:
        # 睡眠の状態を変数に保管
        health_data['sleep'] = user_condition
        # 登録用にデータを加工/ヘッダーを作成
        json_data = {'health':health_data}
        headers = { 'accept': 'application/json' }
        print(json_data)
        # POSTメソッドで健康データを送信
        response = requests.post(os.getenv('POST_URL'), headers=headers, json=json_data, verify=False)
        print(response)
        # 会話を終了する
        speech_text = "健康状態を登録しました。"
        handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard("健康管理アプリ", speech_text)).set_should_end_session(True)
        # 質問カウンタをインクリメント
        question_counter += 1
        
    else:
        speech_text = "登録に失敗しました。最初からやり直してください。"
        print(question_counter)
        handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard("健康管理アプリ", speech_text)).set_should_end_session(True)
        # 質問カウンタを0に初期化
        question_counter = 0
        
    return handler_input.response_builder.response

@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    # type: (HandlerInput) -> Response

    return handler_input.response_builder.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    # type: (HandlerInput, Exception) -> Response
    print(exception)

    speech = "すみません、わかりませんでした。もう一度言ってください。"
    handler_input.response_builder.speak(speech).ask(speech)
    return handler_input.response_builder.response


lambda_handler = sb.lambda_handler()