class SingletonMeta(type):
    """
    Metaclass for implementing Singleton pattern.
    Any class using this as a metaclass will be a Singleton.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
