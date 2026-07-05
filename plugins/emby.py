import requests


class Emby:

    default_config = {
        "url": "",  # Emby服务器地址
        "token": "",  # Emby服务器token
    }
    default_task_config = {
        "enable": True,  # 任务级开关：转存后是否刷新 Emby 媒体库
    }
    is_active = False

    def __init__(self, **kwargs):
        self.plugin_name = self.__class__.__name__.lower()
        if kwargs:
            for key, _ in self.default_config.items():
                if key in kwargs:
                    setattr(self, key, kwargs[key])
                else:
                    print(f"{self.plugin_name} 模块缺少必要参数: {key}")
            if self.url and self.token:
                if self.get_info():
                    self.is_active = True

    def run(self, task, **kwargs):
        task_config = task.get("addition", {}).get(
            self.plugin_name, self.default_task_config
        )
        if not task_config.get("enable", True):
            print(f"🎞️ Emby刷新: 已禁用，跳过")
            return
        self.scan_library()

    def get_info(self):
        url = f"{self.url}/emby/System/Info"
        headers = {"X-Emby-Token": self.token}
        querystring = {}
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            if "application/json" in response.headers["Content-Type"]:
                response = response.json()
                print(
                    f"Emby媒体库: {response.get('ServerName','')} v{response.get('Version','')}"
                )
                return True
            else:
                print(f"Emby媒体库: 连接失败❌ {response.text}")
        except Exception as e:
            print(f"获取Emby媒体库信息出错: {e}")
        return False

    def scan_library(self):
        """触发 Emby 全量扫描媒体库"""
        url = f"{self.url}/emby/Library/Refresh"
        headers = {"X-Emby-Token": self.token}
        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 204:
                print(f"🎞️ Emby刷新: 媒体库扫描已触发✅")
                return True
            else:
                print(f"🎞️ Emby刷新: 失败❌ 状态码:{response.status_code}")
        except Exception as e:
            print(f"🎞️ Emby刷新出错: {e}")
        return False
