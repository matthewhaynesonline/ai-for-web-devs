import click

from app.database import db
from app.models import User, Chat


def register_cli_commands(app) -> None:
    @app.cli.command("db_seed")
    def db_seed():
        users_exist = app.chat_manager._exists(User)
        chats_exist = app.chat_manager._exists(Chat)

        if users_exist or chats_exist:
            click.echo("Database already seeded. Skipping seeding.")
            return

        try:
            user = User(username="test_user")
            app.chat_manager._save_to_db(user)
            output = f"Created user: {user}"
            click.echo(output)
            app.logger_service.log(output)

            chat = app.chat_manager.create_chat_and_add_user(
                title="test_chat", user=user
            )
            output = f"Created chat: {chat}"
            click.echo(output)
            app.logger_service.log(output)

            output = "Database seeded."
            click.echo(output)
            app.logger_service.log(output)
        except Exception as e:
            db.session.rollback()
            raise e

    @app.cli.command("clear_logs")
    def clear_logs():
        app.logger_service.clear_log_file()
        click.echo("Log files cleared")
