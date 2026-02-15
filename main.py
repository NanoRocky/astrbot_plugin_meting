import asyncio
import os
import shutil
import tempfile

import aiohttp

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Record
from astrbot.api.star import Context, Star, register


def setup_ffmpeg_path():
    """自动检测并设置 FFmpeg 路径

    Returns:
        bool: 是否成功找到 FFmpeg
    """
    ffmpeg_exe = shutil.which("ffmpeg")
    if ffmpeg_exe:
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        os.environ["FFMPEG_PATH"] = ffmpeg_exe
        os.environ["PATH"] = os.pathsep.join([os.environ.get("PATH", ""), ffmpeg_dir])
        logger.info(f"找到 FFmpeg: {ffmpeg_exe}")
        return True

    logger.warning("未找到 FFmpeg，请确保已安装 FFmpeg")
    return False


SOURCE_MAP = {
    "qq": "tencent",
    "qq音乐": "tencent",
    "网易云": "netease",
    "网易": "netease",
    "酷狗": "kugou",
    "酷我": "kuwo",
}

SOURCE_DISPLAY = {
    "tencent": "QQ音乐",
    "netease": "网易云",
    "kugou": "酷狗",
    "kuwo": "酷我",
}


@register("astrbot_plugin_meting", "初叶🍂竹叶-Furry控", "基于 MetingAPI 的点歌插件", "1.0.2")
class MetingPlugin(Star):
    """MetingAPI 点歌插件

    支持多音源搜索和播放，自动分段发送长歌曲
    """

    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config
        self.session_sources = {}
        self.last_search_results = {}
        setup_ffmpeg_path()

    async def initialize(self):
        """插件初始化"""
        logger.info("MetingAPI 点歌插件已初始化")
        setup_ffmpeg_path()

    def get_api_url(self) -> str:
        """获取 API 地址

        Returns:
            str: API 地址，如果未配置则返回空字符串
        """
        if self.config and self.config.get("api_url"):
            return self.config["api_url"]
        return ""

    def get_default_source(self) -> str:
        """获取默认音源

        Returns:
            str: 默认音源，默认为 netease
        """
        if self.config and self.config.get("default_source"):
            return self.config["default_source"]
        return "netease"

    def get_search_result_count(self) -> int:
        """获取搜索结果显示数量

        Returns:
            int: 搜索结果显示数量，范围 5-30，默认 10
        """
        if self.config and self.config.get("search_result_count"):
            count = self.config["search_result_count"]
            if isinstance(count, int) and 5 <= count <= 30:
                return count
        return 10

    def get_session_source(self, session_id: str) -> str:
        """获取会话音源

        Args:
            session_id: 会话 ID

        Returns:
            str: 会话音源，如果未设置则返回默认音源
        """
        return self.session_sources.get(session_id, self.get_default_source())

    def set_session_source(self, session_id: str, source: str):
        """设置会话音源

        Args:
            session_id: 会话 ID
            source: 音源
        """
        self.session_sources[session_id] = source

    @filter.command("切换QQ音乐")
    async def switch_tencent(self, event: AstrMessageEvent):
        """切换当前会话的音源为QQ音乐"""
        session_id = event.unified_msg_origin
        self.set_session_source(session_id, "tencent")
        yield event.plain_result("已切换音源为QQ音乐")

    @filter.command("切换网易云")
    async def switch_netease(self, event: AstrMessageEvent):
        """切换当前会话的音源为网易云"""
        session_id = event.unified_msg_origin
        self.set_session_source(session_id, "netease")
        yield event.plain_result("已切换音源为网易云")

    @filter.command("切换酷狗")
    async def switch_kugou(self, event: AstrMessageEvent):
        """切换当前会话的音源为酷狗"""
        session_id = event.unified_msg_origin
        self.set_session_source(session_id, "kugou")
        yield event.plain_result("已切换音源为酷狗")

    @filter.command("切换酷我")
    async def switch_kuwo(self, event: AstrMessageEvent):
        """切换当前会话的音源为酷我"""
        session_id = event.unified_msg_origin
        self.set_session_source(session_id, "kuwo")
        yield event.plain_result("已切换音源为酷我")

    @filter.command("点歌")
    async def search_song(self, event: AstrMessageEvent):
        """搜索歌曲，使用当前会话的音源

        Args:
            event: 消息事件
        """
        keyword = event.message_str.replace("点歌", "").strip()
        if not keyword:
            yield event.plain_result("请输入要搜索的歌曲名称，例如：点歌一期一会")
            return

        api_url = self.get_api_url()
        if not api_url:
            yield event.plain_result("请先在插件配置中设置 MetingAPI 地址")
            return

        session_id = event.unified_msg_origin
        source = self.get_session_source(session_id)

        try:
            async with aiohttp.ClientSession() as session:
                params = {"server": source, "type": "search", "id": keyword}
                async with session.get(f"{api_url}/api", params=params) as resp:
                    if resp.status != 200:
                        yield event.plain_result(
                            f"搜索失败，API 返回状态码: {resp.status}"
                        )
                        return

                    try:
                        data = await resp.json()
                    except Exception as e:
                        logger.error(f"解析 JSON 响应失败: {e}")
                        logger.error(f"响应内容: {await resp.text()}")
                        yield event.plain_result(f"解析响应失败: {e}")
                        return

            if not data or len(data) == 0:
                yield event.plain_result(f"未找到歌曲: {keyword}")
                return

            result_count = self.get_search_result_count()
            results = data[:result_count]
            self.last_search_results[session_id] = results

            message = f"搜索结果（音源: {SOURCE_DISPLAY.get(source, source)}）:\n"
            for idx, song in enumerate(results, 1):
                name = song.get("title", "未知")
                artist = song.get("author", "未知歌手")
                message += f"{idx}. {name} - {artist}\n"

            message += '\n发送"点歌1"播放第一首歌曲'
            yield event.plain_result(message)

        except aiohttp.ClientError as e:
            logger.error(f"搜索歌曲时网络错误: {e}")
            yield event.plain_result("搜索歌曲时网络错误，请检查 API 地址或网络连接")
        except Exception as e:
            logger.error(f"搜索歌曲时发生错误: {e}")
            yield event.plain_result(f"搜索歌曲时发生错误: {e}")

    @filter.regex(r"点歌(\d+)")
    async def play_song_by_number(self, event: AstrMessageEvent):
        """播放指定序号的歌曲，以语音形式发送

        Args:
            event: 消息事件
        """
        import re

        match = re.match(r"点歌(\d+)", event.get_message_str().strip())
        if not match:
            return

        index = int(match.group(1))
        session_id = event.unified_msg_origin

        if (
            session_id not in self.last_search_results
            or not self.last_search_results[session_id]
        ):
            yield event.plain_result('请先使用"点歌"命令搜索歌曲')
            return

        results = self.last_search_results[session_id]
        if index < 1 or index > len(results):
            yield event.plain_result(
                f"序号超出范围，请输入 1-{len(results)} 之间的序号"
            )
            return

        song = results[index - 1]
        song_url = song.get("url")

        if not song_url:
            yield event.plain_result("获取歌曲播放地址失败")
            return

        segment_duration = 120

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(song_url) as resp:
                    if resp.status != 200:
                        yield event.plain_result(f"下载歌曲失败，状态码: {resp.status}")
                        return

                    content_type = resp.headers.get("Content-Type", "")
                    if "audio" not in content_type.lower():
                        logger.error(
                            f"返回的不是音频文件，Content-Type: {content_type}"
                        )
                        yield event.plain_result("返回的不是音频文件")
                        return

                    temp_dir = tempfile.gettempdir()
                    temp_file = os.path.join(
                        temp_dir, f"meting_song_{event.get_sender_id()}.mp3"
                    )

                    with open(temp_file, "wb") as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            f.write(chunk)

                    file_size = os.path.getsize(temp_file)
                    if file_size == 0:
                        yield event.plain_result("下载的歌曲文件为空")
                        return

                    yield event.plain_result("正在分段录制歌曲...")

                    setup_ffmpeg_path()

                    ffmpeg_path = os.environ.get("FFMPEG_PATH")
                    if not ffmpeg_path:
                        yield event.plain_result("未找到 FFmpeg，请确保已安装 FFmpeg")
                        return

                    try:
                        from pydub import AudioSegment

                        AudioSegment.converter = ffmpeg_path
                    except ImportError:
                        yield event.plain_result(
                            "缺少 pydub 依赖，请安装: pip install pydub"
                        )
                        return

                    try:
                        audio = AudioSegment.from_file(temp_file)
                        total_duration = len(audio)
                        segment_ms = segment_duration * 1000

                        segments = []
                        for start in range(0, total_duration, segment_ms):
                            end = min(start + segment_ms, total_duration)
                            segment = audio[start:end]
                            segments.append(segment)

                        base_name = os.path.splitext(os.path.basename(temp_file))[0]

                        for idx, segment in enumerate(segments, 1):
                            segment_file = os.path.join(
                                temp_dir, f"{base_name}_segment_{idx}.wav"
                            )
                            segment.export(segment_file, format="wav")

                            try:
                                record = Record.fromFileSystem(segment_file)
                                yield event.chain_result([record])
                                await asyncio.sleep(1)
                            except Exception as e:
                                logger.error(f"发送语音片段 {idx} 时发生错误: {e}")
                                yield event.plain_result(
                                    f"发送语音片段 {idx} 时发生错误: {e}"
                                )
                            finally:
                                if os.path.exists(segment_file):
                                    os.remove(segment_file)

                        yield event.plain_result("歌曲播放完成")

                    except Exception as e:
                        logger.error(f"分割音频时发生错误: {e}")
                        yield event.plain_result(f"分割音频时发生错误: {e}")

                    os.remove(temp_file)

        except aiohttp.ClientError as e:
            logger.error(f"下载歌曲时网络错误: {e}")
            yield event.plain_result("下载歌曲时网络错误")
        except Exception as e:
            logger.error(f"分段发送歌曲时发生错误: {e}")
            yield event.plain_result(f"分段发送歌曲时发生错误: {e}")

    async def terminate(self):
        """插件终止时清理资源"""
        if hasattr(self, "session") and self.session:
            await self.session.close()
