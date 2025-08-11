from PIL import ImageFont
from PIL.Image import Resampling
from kmrbot.painter.pic_painter.color import Color
from kmrbot.painter.pic_painter.pic_generator import PicGenerator
from kmrbot.painter.pic_painter.utils import PainterUtils
from .voice_list_border import VoiceListBorder
from kmrbot.core.bot_base_info import KmrBotBaseInfo
from utils import array_to_string


class VoiceListFont:
    __title_font = \
        ImageFont.truetype(f"{PainterUtils.get_painter_resource_path()}/normal.ttf", 48)
    __sub_title_font = \
        ImageFont.truetype(f"{PainterUtils.get_painter_resource_path()}/normal.ttf", 36)
    __explain_font = \
        ImageFont.truetype(f"{PainterUtils.get_painter_resource_path()}/normal.ttf", 30)
    __each_name_font = \
        ImageFont.truetype(f"{PainterUtils.get_painter_resource_path()}/normal.ttf", 30)
    __each_name_extra_font = \
        ImageFont.truetype(f"{PainterUtils.get_painter_resource_path()}/normal.ttf", 16)
    __each_voice_name_font = \
        ImageFont.truetype(f"{PainterUtils.get_painter_resource_path()}/normal.ttf", 20)
    __emoji_font = \
        ImageFont.truetype(f"{PainterUtils.get_painter_resource_path()}/dynamic/emoji.ttf", 109)
    __designer_bot_name_font = \
        ImageFont.truetype(f"{PainterUtils.get_painter_resource_path()}/normal.ttf", 22)    # 开发者信息 机器人名字字体
    __designer_font = \
        ImageFont.truetype(f"{PainterUtils.get_painter_resource_path()}/normal.ttf", 10)    # 开发者信息字体

    @classmethod
    def title_font(cls):
        return cls.__title_font

    @classmethod
    def sub_title_font(cls):
        return cls.__sub_title_font

    @classmethod
    def explain_font(cls):
        return cls.__explain_font

    @classmethod
    def each_name_font(cls):
        return cls.__each_name_font

    @classmethod
    def each_name_extra_font(cls):
        return cls.__each_name_extra_font

    @classmethod
    def each_voice_name_font(cls):
        return cls.__each_voice_name_font

    @classmethod
    def emoji_font(cls):
        return cls.__emoji_font

    @classmethod
    def designer_bot_name_font(cls):
        return cls.__designer_bot_name_font

    @classmethod
    def designer_font(cls):
        return cls.__designer_font


class VoiceListPainter:

    @classmethod
    def generate_voice_list_pic(cls, prefix_name: str, voice_data, event_type, type_id):
        width = 1460
        height = 10000
        pic = PicGenerator(width, height)
        pic = pic.draw_rectangle(0, 0, width, height, Color.WHITE)

        # 绘制标题
        pic = cls.__paint_title(pic, prefix_name)

        # 绘制语法部分
        pic = cls.__paint_syntax(pic, prefix_name)

        # 绘制列表
        pic = cls.__paint_voice_data(pic, voice_data, event_type, type_id)

        # 绘制开发者信息
        pic = cls.__paint_designer_info(pic)

        pic.crop()

        return pic.bytes_io()

    @classmethod
    def __paint_title(cls, pic: PicGenerator, prefix_name: str):
        pic.set_pos(VoiceListBorder.BORDER_DEFAULT_LR, pic.y + VoiceListBorder.BORDER_TITLE_TOP_U)
        pic.paint_center_text(pic.x, ["voice", " - ", prefix_name],
                              VoiceListFont.title_font(),
                              [Color.DEEPSKYBLUE, Color.BLACK, Color.CRIMSON],
                              right_limit=pic.width - VoiceListBorder.BORDER_DEFAULT_LR)
        return pic

    @classmethod
    def __paint_syntax(cls, pic: PicGenerator, prefix_name: str):
        pic.set_pos(VoiceListBorder.BORDER_SYNTAX_TITLE_L, pic.y + VoiceListBorder.BORDER_SYNTAX_TITLE_U)

        pic.paint_auto_line_text(pic.x,
                                 [PicGenerator.AutoLineTextData(text="语法：\n", color=Color.BLACK)],
                                 VoiceListFont.title_font())
        pic.set_pos(VoiceListBorder.BORDER_SYNTAX_EXPLAIN_L, pic.y)
        pic.paint_auto_line_text(pic.x,
                                 [PicGenerator.AutoLineTextData(text=f"{prefix_name} [UserName] [VoiceName]\n", color=Color.BLACK),
                                  PicGenerator.AutoLineTextData(text="UserName: 用户名（多个均可触发）\n", color=Color.BLACK),
                                  PicGenerator.AutoLineTextData(text="VoiceName: 音频名（部分有模糊匹配）\n", color=Color.BLACK),
                                  PicGenerator.AutoLineTextData(text="用户名和音频名均可以省略，省略时则随机返回一个音频内容。\n", color=Color.RED),
                                  PicGenerator.AutoLineTextData(text="私密音频仅可在当前群组/私聊内生效。该种音频会以", color=Color.RED),
                                  PicGenerator.AutoLineTextData(text="紫色", color=Color.FUCHSIA),
                                  PicGenerator.AutoLineTextData(text="列出。\n", color=Color.RED)],
                                 VoiceListFont.explain_font())
        return pic

    @classmethod
    def __paint_voice_data(cls, pic: PicGenerator, voice_data, event_type, type_id):
        pic.set_pos(VoiceListBorder.BORDER_SYNTAX_TITLE_L, pic.y + VoiceListBorder.BORDER_NAME_LIST_TITLE_U)
        pic.paint_auto_line_text(pic.x,
                                 [PicGenerator.AutoLineTextData(text="命令内容：\n", color=Color.BLACK)],
                                 VoiceListFont.title_font())
        if len(voice_data) == 0:
            return pic

        paint_count = 0  # 已绘制的数量 超过一半就换到右面去
        offset_index = 0
        max_y = pic.y

        voice_count = 0
        voice_name_voice_exist = {}    # name -> count 用来过滤掉某些群组下某个name下无任何语音可以展示的情况
        for each_data in voice_data["voice_data"]:
            for each_voice in each_data["voices"]:
                if len(each_voice.get("black_list", [])) != 0 and len(list(filter(
                        lambda x: (x.get("type", "") == event_type and x.get("type_id", 0) == type_id),
                        each_voice["black_list"]))) != 0:
                    # 在黑名单内
                    continue
                if len(each_voice.get("white_list", [])) != 0 and len(list(filter(
                        lambda x: (x.get("type", "") == event_type and x.get("type_id", 0) == type_id),
                        each_voice["white_list"]))) == 0:
                    # 不在白名单内
                    continue
                voice_count += 1
                voice_name_voice_exist[str(each_data["name"])] = True
        cur_name = None  # 切换了ame则新建一个标题
        # index_total表示一共有多少行 根据行数来决定什么时候切换列
        # name_count个标题（name名），以及name_count*0.3个标题额外内容（name名称集合）
        # 按比例来计算可以更好模拟换行操作
        offset_index_total = voice_count + len(voice_data["voice_data"]) * 1.3
        # print(f"voice_count{voice_count} len{len(voice_data['data'])} offset_index_total{offset_index_total}")
        paint_start_y = pic.y
        for each_data in voice_data["voice_data"]:
            if cur_name != each_data["name"]:
                cur_name = each_data["name"]
                if voice_name_voice_exist.get(str(cur_name)) is None:
                    continue
                pic.set_pos(VoiceListBorder.BORDER_NAME_LIST_SUB_TITLE_L[offset_index], pic.y)
                start_x = pic.x
                right_limit = VoiceListBorder.BORDER_NAME_LIST_SUB_TITLE_L[offset_index + 1] if \
                    offset_index < (len(VoiceListBorder.BORDER_NAME_LIST_SUB_TITLE_L) - 1) else pic.width
                pic.paint_auto_line_text(
                    start_x,
                    [PicGenerator.AutoLineTextData(text=cur_name[0] + "\n", color=Color.RED)],
                    VoiceListFont.sub_title_font(),
                    right_limit=right_limit,
                    row_length=int(pic.row_space / 2))
                pic.paint_auto_line_text(
                    start_x,
                    [PicGenerator.AutoLineTextData(text="[" + array_to_string(cur_name) + "]\n", color=Color.RED)],
                    VoiceListFont.each_name_extra_font(),
                    right_limit=right_limit,
                    row_length=int(pic.row_space / 2))
                paint_count += 1.3
                for each_voice in each_data["voices"]:
                    voice_name_color = Color.BLACK
                    if len(each_voice.get("black_list", [])) != 0 and len(list(filter(
                            lambda x: (x.get("type", "") == event_type and x.get("type_id", 0) == type_id),
                            each_voice["black_list"]))) != 0:
                        continue
                    if len(each_voice.get("white_list", [])) != 0:
                        # 带白名单的则换一种颜色来打印
                        if len(list(filter(
                                lambda x: (x.get("type", "") == event_type and x.get("type_id", 0) == type_id),
                                each_voice["white_list"]))) == 0:
                            continue
                        else:
                            voice_name_color = Color.FUCHSIA
                    pic.set_pos(VoiceListBorder.BORDER_NAME_LIST_SUB_TITLE_L[offset_index] +
                                VoiceListBorder.BORDER_NAME_LIST_CONTENT_EXTRA_L,
                                pic.y)
                    pic.paint_auto_line_text(
                        pic.x,
                        [PicGenerator.AutoLineTextData(text=f"·{each_voice['show_name']}\n", color=voice_name_color)],
                        VoiceListFont.explain_font(),
                        row_length=int(pic.row_space / 2))
                    # 记录最大y高度
                    if max_y < pic.y:
                        max_y = pic.y
                    paint_count += 1
                    # 计算是否需要换列
                    new_offset_index = int(paint_count / offset_index_total *
                                           len(VoiceListBorder.BORDER_NAME_LIST_SUB_TITLE_L))
                    if offset_index != new_offset_index:
                        # 说明是新的一列 把y拉到start的位置
                        pic.set_pos(pic.x, paint_start_y)
                        offset_index = new_offset_index
        pic.set_pos(VoiceListBorder.BORDER_DEFAULT_LR, max_y)
        return pic

    @classmethod
    def __paint_designer_info(cls, pic: PicGenerator):
        pic.set_pos(0, pic.y + VoiceListBorder.BORDER_DESIGNER_UP)
        origin_row_space = pic.row_space

        pic.set_row_space(8)
        pic.draw_text_right(VoiceListBorder.BORDER_DESIGNER_RD,
                            ["K", "m", "r", "Bot", KmrBotBaseInfo.get_version()],
                            VoiceListFont.designer_bot_name_font(),
                            [Color.DEEPSKYBLUE, Color.FUCHSIA, Color.CRIMSON, Color.BLACK, Color.RED, Color.GRAY])
        pic.draw_text_right(VoiceListBorder.BORDER_DESIGNER_RD,
                            f"Author : {KmrBotBaseInfo.get_author_name()}", VoiceListFont.designer_font(),
                            Color.DYNAMIC_DESIGNER_AUTHOR_NAME)
        pic.draw_text_right(VoiceListBorder.BORDER_DESIGNER_RD,
                            f"{KmrBotBaseInfo.get_author_url()}", VoiceListFont.designer_font(), Color.LINK)
        pic.set_row_space(origin_row_space)
        pic.move_pos(0, VoiceListBorder.BORDER_DESIGNER_RD - 8)   # -8是剪掉间隔 draw_text_right会自动加一个间距

        # pic.draw_text("Komori...Komori...AA", DynamicFont.dynamic_watermark_font(), Color.DYNAMIC_LD_TEXT,
        #               (DynamicBorder.BORDER_LD_WATERMARK_TEXT_LD,
        #                pic.y - DynamicFont.dynamic_watermark_font().size - DynamicBorder.BORDER_LD_WATERMARK_TEXT_LD))

        return pic
