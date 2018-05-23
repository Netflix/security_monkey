from security_monkey import app
from security_monkey.datastore import SMPluginConfig, db

plugin_registry = {}
abstract_classes = set(['SMPlugin'])


class SMPluginType(type):
    def __init__(cls, name, bases, attrs):
        if cls.__name__ not in abstract_classes and cls.index:
            if not (not getattr(cls, "register", None) or not getattr(cls, "convert_to_json", None)) \
                    and getattr(cls, "build", None):
                app.logger.debug("Registering plugin %s", cls.__name__)
                if cls.__name__ not in plugin_registry.keys():
                    plugin_registry.update({cls.__name__: cls})
                    cls.register()


class SMPlugin(object):
    __metaclass__ = SMPluginType
    index="abstract"

    def __init__(self):
        config = SMPluginConfig.query.filter(SMPluginConfig.classname == self.__class__.__name__).first()
        if config is None:
            self.config = "{}"
        else:
            self.config = config.config
        self.build()

    @classmethod
    def register(cls):
        raise NotImplementedError()

    def convert_to_json(self):
        raise NotImplementedError()

    def build(self):
        raise NotImplementedError()

    def save_config(self, classname):
        plugin_config = SMPluginConfig.query.filter(SMPluginConfig.classname == classname).first()
        if plugin_config is None:
            plugin_config = SMPluginConfig()
            plugin_config.classname = classname
        plugin_config.config = self.convert_to_json()
        db.session.add(plugin_config)
        db.session.commit()
