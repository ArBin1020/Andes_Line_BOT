from apis import app
from const import *


if __name__ == '__main__':
    app.run('0.0.0.0', port=FLASK_PORT, debug=True)
