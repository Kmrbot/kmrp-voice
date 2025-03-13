import yaml
import yaml.scanner
from pathlib import Path
from nonebot.log import logger

from protocol_adapter.adapter_type import AdapterMessageEvent
from protocol_adapter.protocol_adapter import ProtocolAdapter
from utils import get_config_path


def get_voice_yaml_data():
    try:
        # 每次都重新加载 即可以动态重载 性能消耗可忽略
        with open(get_config_path().joinpath("voice/voice_list.yaml"), "r", encoding="utf8") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError:
        logger.error("get_voice_yaml_data fail ! File not found !")
        data = None
    except yaml.scanner.ScannerError:
        logger.error("get_voice_yaml_data fail ! Scanner Error !")
        data = None
    return data


def is_voice_command(event: AdapterMessageEvent) -> bool:
    text_data = ProtocolAdapter.get_text(event)
    if len(text_data) == 0:
        return False
    text_split_data = text_data[0].strip().split(' ')
    if len(text_split_data) == 0:
        return False
    # XXX help这种也是不行的
    if len(text_split_data) > 1 and text_split_data[1] == "help":
        return False
    for info in get_voice_yaml_data()["data"]:
        if info["prefix_name"] == text_split_data[0]:
            return True
    return False


def is_voice_help_command(event: AdapterMessageEvent) -> bool:
    text_data = ProtocolAdapter.get_text(event)
    if len(text_data) == 0:
        return False
    text_split_data = text_data[0].strip().split(' ')
    if len(text_split_data) == 0:
        return False
    prefix = voice_help_get_prefix(text_split_data)
    if prefix is None:
        return False
    for info in get_voice_yaml_data()["data"]:
        if info["prefix_name"] == prefix:
            return True
    return False


def voice_help_get_prefix(text_split_data) -> str | None:
    if len(text_split_data) == 0:
        return None
    # 看是不是help结尾 两种格式 XXX help 和 XXX_help
    if len(text_split_data) == 1 and \
            len(text_split_data[0]) > 5 \
            and text_split_data[0][len(text_split_data[0]) - 5:] == "_help":
        return text_split_data[0][:len(text_split_data[0]) - 5]
    elif len(text_split_data) >= 2 and text_split_data[1] == "help":
        return text_split_data[0]
    return None


def get_voice_info_by_prefix(prefix: str):
    yaml_data = get_voice_yaml_data()
    if yaml_data is None:
        return None
    for info in yaml_data["data"]:
        if info["prefix_name"] == prefix:
            return info
    return None
