import os
import requests


class Plex:

    default_config = {
        "url": "",  # Plex服务器URL
        "token": "",  # Plex Token，可F12在请求中抓取
        "quark_root_path": "",  # 夸克根目录在Plex中的路径；假设夸克目录/media/tv在plex中对应的路径为/quark/media/tv，则为/quark
    }
    default_task_config = {
        "enable": True,  # 任务级开关：转存后是否刷新 Plex 媒体库
    }
    is_active = False
    _libraries = None  # 缓存库信息

    def __init__(self, **kwargs):
        if kwargs:
            for key, value in self.default_config.items():
                if key in kwargs:
                    setattr(self, key, kwargs[key])
                else:
                    print(f"{self.__class__.__name__} 模块缺少必要参数: {key}")
            if self.url and self.token and self.quark_root_path:
                if self.get_info():
                    self.is_active = True

    def run(self, task, **kwargs):
        task_config = task.get("addition", {}).get("plex", self.default_task_config)
        if not task_config.get("enable", True):
            return
        if task.get("savepath"):
            # 检查是否已缓存库信息
            if self._libraries is None:
                self._libraries = self._get_libraries()
            # 拼接完整路径
            full_path = os.path.normpath(
                os.path.join(self.quark_root_path, task["savepath"].lstrip("/"))
            ).replace("\\", "/")
            self.refresh(full_path)

    def get_info(self):
        """获取Plex服务器信息"""
        headers = {"Accept": "application/json", "X-Plex-Token": self.token}
        try:
            response = requests.get(f"{self.url}/", headers=headers)
            if response.status_code == 200:
                info = response.json()["MediaContainer"]
                print(
                    f"Plex媒体库: {info.get('friendlyName','')} v{info.get('version','')}"
                )
                return True
            else:
                print(f"Plex媒体库: 连接失败❌ 状态码：{response.status_code}")
        except Exception as e:
            print(f"获取Plex媒体库信息出错: {e}")
        return False

    def refresh(self, folder_path):
        """刷新指定文件夹"""
        if not folder_path:
            return False
        headers = {"Accept": "application/json", "X-Plex-Token": self.token}
        try:
            for library in self._libraries:
                for location in library.get("Location", []):
                    if (
                        os.path.commonpath([folder_path, location["path"]])
                        == location["path"]
                    ):
                        refresh_url = f"{self.url}/library/sections/{library['key']}/refresh?path={folder_path}"
                        refresh_response = requests.get(refresh_url, headers=headers)
                        if refresh_response.status_code == 200:
                            print(
                                f"🎞️ 刷新Plex媒体库：{library['title']} [{folder_path}] 成功✅"
                            )
                            return True
                        else:
                            print(
                                f"🎞️ 刷新Plex媒体库：刷新请求失败❌ 状态码：{refresh_response.status_code}"
                            )
            print(f"🎞️ 刷新Plex媒体库：{folder_path} 未找到匹配的媒体库❌")
        except Exception as e:
            print(f"刷新Plex媒体库出错: {e}")
        return False

    def _get_libraries(self):
        """获取Plex媒体库信息"""
        url = f"{self.url}/library/sections"
        headers = {"Accept": "application/json", "X-Plex-Token": self.token}
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                libraries = response.json()["MediaContainer"].get("Directory", [])
                return libraries
            else:
                print(f"🎞️ 获取Plex媒体库信息失败❌ 状态码：{response.status_code}")
        except Exception as e:
            print(f"获取Plex媒体库信息出错: {e}")
        return []
