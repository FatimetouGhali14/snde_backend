from app import create_app, create_admin_initial

app = create_app()

with app.app_context():
    create_admin_initial()
