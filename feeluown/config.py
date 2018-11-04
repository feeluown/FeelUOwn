class Config:
    """配置模块

    用户可以在 rc 文件中配置各个选项的值
    """
    COLLECTIONS_DIR = []

    def __getattr__(self, name):
        if name not in self.__dict__:
            return None
        return object.__getattribute__(self, name)


config = Config()
