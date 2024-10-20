import flask

import params


def NewInstance() -> flask.Flask:
    app = flask.Flask("frontend.server")
    app.config.from_object(params.GetParams().frontend_params)

    assert app.config["SECRET_KEY"] is not None

    @app.route("/")
    def home():
        assert False
        return "Hello world!"

    return app
