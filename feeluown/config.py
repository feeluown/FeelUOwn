class Config:
    COLLECTIONS_DIR = []

    def __getattr__(self, name):
        if name not in self.__dict__:
            return None
        return object.__getattribute__(self, name)


config = Config()
