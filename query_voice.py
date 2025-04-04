import random
import re
import time
from typing import Union
from utils import get_config_path
from protocol_adapter.protocol_adapter import ProtocolAdapter
from protocol_adapter.adapter_type import AdapterGroupMessageEvent, AdapterPrivateMessageEvent, AdapterMessage
from nonebot import on_message
from nonebot.matcher import Matcher
from nonebot.log import logger
from utils.permission import white_list_handle
from .voice_config import get_voice_yaml_data, is_voice_command


query_voice = on_message(priority=5, rule=is_voice_command)
query_voice.__doc__ = """voice"""
query_voice.__help_type__ = None

query_voice.handle()(white_list_handle("voice"))


last_query_time_data = {}


@query_voice.handle()
async def _(
        matcher: Matcher,
        event: Union[AdapterPrivateMessageEvent, AdapterGroupMessageEvent],
):
    msg_type = ProtocolAdapter.get_msg_type(event)
    msg_type_id = ProtocolAdapter.get_msg_type_id(event)
    user_id = ProtocolAdapter.get_user_id(event)
    # 如果不是纯文本消息则略过
    if ProtocolAdapter.get_msg_len(event) != 1:
        await query_voice.finish()

    # voice阻止后续事件执行
    matcher.stop_propagation()
    voices_data = get_voice_yaml_data()
    if voices_data is None:
        logger.error("query_voice voices_data is None.")
        await query_voice.finish("无法获取voice列表")

    # 语音筛选条件
    voice_conditions = ProtocolAdapter.get_text(event)[0].strip().split(' ')

    # 超级用户跳过所有限流
    if ProtocolAdapter.get_user_id(event) not in voices_data["super_user"]:
        # 限流 一个人有时间限制 一个群也有时间限制
        if last_query_time_data.get(msg_type) is None:
            last_query_time_data[msg_type] = {}
        if last_query_time_data.get("private") is None:
            last_query_time_data["private"] = {}

        left_time = voices_data["query_interval"] - \
            (int(time.time()) - last_query_time_data["private"].get(user_id, 0))
        if left_time > 0:
            # 针对个人的
            await query_voice.finish(ProtocolAdapter.MS.reply(event) +
                                     ProtocolAdapter.MS.text(f"个人请求过于频繁：请{round(left_time, 2)}秒后再试"))
        if msg_type == "group":
            left_time = voices_data["query_interval"] - \
                (int(time.time()) - last_query_time_data[msg_type].get(msg_type_id, 0))
            if left_time > 0:
                # 针对群的
                await query_voice.finish(ProtocolAdapter.MS.reply(event) +
                                         ProtocolAdapter.MS.text(f"群组/频道请求过于频繁：请{round(left_time, 2)}秒后再试"))

    voices_list = []
    total_voices_list = []
    for each_data in voices_data["data"]:
        if len(voice_conditions) >= 1 and each_data["prefix_name"] != voice_conditions[0]:
            continue
        # 把这个下面的语音全都拿出来，然后规则放成map，符合所有规则的才留下
        for user_voice_data in each_data["voice_data"]:
            # 展开每个语音
            for each_voice in user_voice_data["voices"]:
                if each_voice.get("white_list") is not None:
                    if len(list(filter(
                            lambda x: (x.get("type", "") == msg_type and x.get("type_id", 0) == msg_type_id),
                            each_voice["white_list"]))) == 0:
                        # 有白名单但是不符合白名单规则
                        continue
                if each_voice.get("black_list") is not None:
                    if len(list(filter(
                            lambda x: (x.get("type", "") == msg_type and x.get("type_id", 0) == msg_type_id),
                            each_voice["black_list"]))) != 0:
                        # 有黑名单且符合规则
                        continue
                # 规则放进来
                total_voices_list.append({
                    "rules": [user_voice_data["name"], each_voice['voice_name']],
                    "voice": each_voice,
                })

    for i in range(len(total_voices_list)):
        is_valid = True
        # 判断所有规则
        # 数组则判断是否conditions都存在，字符串则判断conditions是否可以正则匹配
        if len(voice_conditions) > 1:
            # voice_conditions长度是1表示只有一个命令，那就全部视为有效
            cur_condition_valid = False
            for rule in total_voices_list[i]["rules"]:
                for condition_index in range(1, len(voice_conditions)):
                    if type(rule) == list and voice_conditions[condition_index] in rule:
                        cur_condition_valid = True
                        break
                    if type(rule) == str and re.match(f"^{rule}$", voice_conditions[condition_index]) is not None:
                        cur_condition_valid = True
                        break
                if cur_condition_valid:
                    break
            # 这条规则在所有rule中都没通过
            if not cur_condition_valid:
                is_valid = False
        if is_valid:
            voices_list.append(total_voices_list[i]["voice"])

    if len(voices_list) == 0:
        await query_voice.finish(ProtocolAdapter.MS.reply(event) +
                                 ProtocolAdapter.MS.text("未找到对应音频！"))

    if user_id not in voices_data["super_user"]:
        # 非超级用户 写入对应的CD时间
        last_query_time_data[msg_type][msg_type_id] = time.time()
        last_query_time_data["private"][user_id] = time.time()

    # 随机取一首
    dst_voice_dirs = voices_list[random.randint(0, len(voices_list) - 1)]["dirs"]
    dst_voice_dir = dst_voice_dirs[random.randint(0, len(dst_voice_dirs) - 1)]

    file_path_origin = get_config_path().joinpath(f"voice/{voice_conditions[0]}/{dst_voice_dir}")
    msg = ProtocolAdapter.MS.voice(file_path_origin)
    await query_voice.finish(msg)
