import eventlet
eventlet.monkey_patch()

from app import create_app

app = create_app('production')

if __name__ == "__main__":
    app.run()
