from api import create_app

app = create_app()

# imports and start the app so that app is modular
if __name__ == '__main__':
    app.run(debug=True)
