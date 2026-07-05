import requests


class Emby:

    default_config = {
        "url": "",  # Emby服务器地址
        "token": "",  # Emby服务器token
    }
    default_task_config = {
        "enable": True,     # 任务级开关：转存后是否刷新 Emby
        "mode": "full",     # 刷新模式：full=全库扫描, item=单剧刷新
        "media_id": "",     # mode=item 时指定媒体ID，为空则尝试自动匹配任务名
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

        if task_config.get("mode") == "item":
            # 单剧刷新
            media_id = task_config.get("media_id", "")
            if media_id and media_id != "0":
                self.refresh_item(media_id)
            else:
                # 自动匹配任务名
                if match_id := self.search(task["taskname"]):
                    self.refresh_item(match_id)
                    task_config["media_id"] = match_id
                    task.setdefault("addition", {})[self.plugin_name] = task_config
                else:
                    print(f"🎞️ Emby刷新: 未匹配到《{task['taskname']}》，跳过（可切为 mode=full 全库扫描）")
        else:
            # 全库扫描
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
        """全库扫描"""
        url = f"{self.url}/emby/Library/Refresh"
        headers = {"X-Emby-Token": self.token}
        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 204:
                print(f"🎞️ Emby刷新(全库): 扫描已触发✅")
                return True
            else:
                print(f"🎞️ Emby刷新(全库): 失败❌ 状态码:{response.status_code}")
        except Exception as e:
            print(f"🎞️ Emby刷新(全库)出错: {e}")
        return False

    def refresh_item(self, emby_id):
        """刷新单部剧集"""
        if not emby_id:
            return False
        url = f"{self.url}/emby/Items/{emby_id}/Refresh"
        headers = {"X-Emby-Token": self.token}
        querystring = {
            "Recursive": "true",
            "MetadataRefreshMode": "FullRefresh",
            "ImageRefreshMode": "FullRefresh",
            "ReplaceAllMetadata": "false",
            "ReplaceAllImages": "false",
        }
        try:
            response = requests.post(url, headers=headers, params=querystring)
            if response.text == "":
                print(f"🎞️ Emby刷新(单剧): 成功✅")
                return True
            else:
                print(f"🎞️ Emby刷新(单剧): {response.text}❌")
        except Exception as e:
            print(f"🎞️ Emby刷新(单剧)出错: {e}")
        return False

    def search(self, media_name):
        """按名称搜索媒体库"""
        if not media_name:
            return ""
        url = f"{self.url}/emby/Items"
        headers = {"X-Emby-Token": self.token}
        querystring = {
            "IncludeItemTypes": "Series",
            "StartIndex": 0,
            "SortBy": "SortName",
            "SortOrder": "Ascending",
            "ImageTypeLimit": 0,
            "Recursive": "true",
            "SearchTerm": media_name,
            "Limit": 10,
            "IncludeSearchTypes": "false",
        }
        try:
            response = requests.get(url, headers=headers, params=querystring)
            if "application/json" in response.headers["Content-Type"]:
                response = response.json()
                if response.get("Items"):
                    for item in response["Items"]:
                        if item["IsFolder"]:
                            print(
                                f"🎞️ 《{item['Name']}》匹配到Emby媒体库ID：{item['Id']}"
                            )
                            return item["Id"]
            else:
                print(f"🎞️ 搜索Emby媒体库：{response.text}❌")
        except Exception as e:
            print(f"搜索Emby媒体库出错: {e}")
        return ""
