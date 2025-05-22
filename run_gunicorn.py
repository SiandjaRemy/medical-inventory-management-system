import os
import django
from gunicorn.app.base import BaseApplication

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InventoryManagement.settings')
django.setup()

class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

if __name__ == '__main__':
    from InventoryManagement.wsgi import application
    StandaloneApplication(application, {
        'bind': '%s:%s' % ('0.0.0.0', '5000'),
        'workers': 1,
    }).run()