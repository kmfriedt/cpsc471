from flask import Flask
from flask_bcrypt import Bcrypt
from flaskext.mysql import MySQL
from config import Config

bcrypt = Bcrypt()
mysql = MySQL()

app = Flask(__name__)


def create_app(config_class=Config):
    app.config.from_object(Config)
    app.config["JSON_SORT_KEYS"] = False  # prevents jsonify from reordering json

    mysql.init_app(app)
    bcrypt.init_app(app)

    from api.authentication.routes import authentication
    from api.main.routes import main
    from api.schedule.routes import schedule
    from api.stats.routes import stats
    from api.teams.routes import teams

    #register each folder to have it's own root URL path
    app.register_blueprint(authentication, url_prefix="/authentication")
    app.register_blueprint(main)
    app.register_blueprint(schedule, url_prefix="/schedule")
    app.register_blueprint(stats, url_prefix="/stats")
    app.register_blueprint(teams, url_prefix="/teams")

    return app
