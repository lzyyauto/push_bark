# klippy status push to Bark
#
# Copyright (C) 2022 lzyyauto <lzyyauto@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

from __future__ import annotations

import logging
import socket
# Annotation imports
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import requests
from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from confighelper import ConfigHelper

    from .klippy_apis import KlippyAPI
    DBComp = database.MoonrakerDatabase


class PushBark:

    def __init__(self, config: ConfigHelper) -> None:
        self.server = config.get_server()
        self.last_print_stats: Dict[str, Any] = {}

        self.msgtype: str = config.get('msg_type')

        if self.msgtype == "bark":
            self.baseurl: str = config.get('base_url')
            self.baseurl = self.baseurl.replace(" ", "")

            self.barkid: str = config.get('bark_id')
            self.barkid = self.barkid.replace(" ", "")
        else:
            self.server.add_warning(
                f"[Push_Bark] Unsupported message types {self.msgtype}"
                "\n\nIf you want to get rid of this warning, please restart MoonRaker."
            )
            logging.error("Unsupported message types")
            return

        db: DBComp = self.server.load_component(config, "database")
        db_path = db.get_database_path()
        self.gc_path: str = db.get_item("moonraker", "file_manager.gcode_path",
                                        "").result()
        self.print_name: str = db.get_item("fluidd",
                                           "uiSettings.general.instanceName",
                                           "").result()
        if self.print_name is None:
            self.print_name = db.get_item("mainsail",
                                          "uiSettings.general.instanceName",
                                          "").result()
        if self.print_name is None:
            self.print_name = self.server.get_host_info()['hostname']

        self.last_print_stats: Dict[str, Any] = {}
        self.server.register_event_handler("server:klippy_started",
                                           self._handle_started)
        self.server.register_event_handler("server:klippy_shutdown",
                                           self._handle_shutdown)
        self.server.register_event_handler("server:status_update",
                                           self._status_update)

    async def _handle_started(self, state: str) -> None:
        if state != "ready":
            return
        kapis: KlippyAPI = self.server.lookup_component('klippy_apis')
        sub: Dict[str, Optional[List[str]]] = {"print_stats": None}
        try:
            result = await kapis.subscribe_objects(sub)
        except self.server.error as e:
            logging.info(f"Error subscribing to print_stats")
        self.last_print_stats = result.get("print_stats", {})
        if "state" in self.last_print_stats:
            state = self.last_print_stats["state"]
            logging.info(f"Job state initialized: {state}")

    async def _handle_shutdown(self, state: str) -> None:
        logging.info(f"Shutdown: {state}")

    async def _status_update(self, data: Dict[str, Any]) -> None:
        # print(data)
        if "webhooks" in data:
            webhooks = data['webhooks']
            state = webhooks['state']
            state_message = webhooks['state_message']
            logging.info(f"Status: {state}")
            logging.info(f"Info: {state_message}")
            if state == "shutdown":
                # 报错停机
                self._pushState(state=state, text=state_message)
        elif "print_stats" in data:
            print_stats = data['print_stats']

            if "state" in print_stats:
                new_ps = dict(self.last_print_stats)
                new_ps.update(print_stats)
                state = print_stats['state']
                filename = new_ps['filename']
                if state == "printing":
                    # 开始打印
                    self._pushState(state=state,
                                    text='开始打印',
                                    filename=filename)
                elif state == "complete":
                    # 打印完成
                    self._pushState(state=state,
                                    text='打印完成',
                                    filename=filename)
                elif state == "error":
                    # 错误
                    self._pushState(state=state, text=new_ps['message'])
                elif state == "paused":
                    # 暂停
                    self._pushState(state=state, text='暂停', filename=filename)
                elif state == "standby":
                    # 取消
                    self._pushState(state=state, text='取消', filename=filename)
                else:
                    logging.info(f"状态：{state}")
                    print(data)
            self.last_print_stats.update(print_stats)

    def _pushState(self, state: str, text: str = None, filename: str = None):
        logging.info(f'state: {state},text: {text}')
        # 构建消息标题和内容
        title = f"[{self.print_name}] 状态更新："
        message = ""

        # 根据不同的状态设置消息的标题和内容
        if state == "shutdown":
            title += "停机"
            message = text
        elif state == "printing":
            title += "开始打印"
            message = f"文件名：{filename}"
        elif state == "complete":
            title += "打印完成"
            message = f"文件名：{filename}"
        elif state == "error":
            title += "发生错误"
            message = text
        elif state == "paused":
            title += "打印暂停"
            message = f"文件名：{filename}"
        elif state == "standby":
            title += "取消打印"
            message = f"文件名：{filename}"
        else:
            logging.error("未知状态")
            return

        # 对标题和消息进行URL编码
        title = requests.utils.quote(title)
        message = requests.utils.quote(message)

        # 构建完整的Bark请求URL
        request_url = f"{self.baseurl}/{self.barkid}/{title}/{message}"

        # 发送GET请求到Bark
        response = requests.get(request_url)
        if response.status_code == 200:
            logging.info("消息成功推送到Bark")
        else:
            logging.error("推送到Bark失败")

        def _extract_ip(self):
            st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                st.connect(('10.255.255.255', 1))
                IP = st.getsockname()[0]
            except Exception:
                IP = '127.0.0.1'
            finally:
                st.close()
            return IP


def load_component(config: ConfigHelper) -> PushBark:
    return PushBark(config)
