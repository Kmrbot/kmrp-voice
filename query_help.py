from typing import Union
from protocol_adapter.protocol_adapter import ProtocolAdapter
from protocol_adapter.adapter_type import AdapterGroupMessageEvent, AdapterPrivateMessageEvent, AdapterMessage
from nonebot import on_message
from utils.permission import white_list_handle
from .voice_config import get_voice_info_by_prefix, is_voice_help_command, voice_help_get_prefix
from .painter.voice_list_painter import VoiceListPainter


query_help = on_message(priority=5, rule=is_voice_help_command)
query_help.__doc__ = """voice"""
query_help.__help_type__ = None

query_help.handle()(white_list_handle("voice"))


last_query_time_data = {}


@query_help.handle()
async def _(
        event: Union[AdapterGroupMessageEvent, AdapterPrivateMessageEvent],
):
    # 语音筛选条件
    prefix = voice_help_get_prefix(ProtocolAdapter.get_text(event)[0].strip().split(' '))
    if prefix is None:
        await query_help.finish()

    msg_type = ProtocolAdapter.get_msg_type(event)
    msg_type_id = ProtocolAdapter.get_msg_type_id(event)
    pic = ProtocolAdapter.MS.image(VoiceListPainter.generate_voice_list_pic(
        prefix,
        get_voice_info_by_prefix(prefix), msg_type, msg_type_id))
    await query_help.finish(pic)
