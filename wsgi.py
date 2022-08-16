from app import create_app
from app.spotify import scheduler_check_and_execute

app = create_app()


@app.cli.command()
def run_scheduler():
    scheduler_check_and_execute()


if __name__ == '__main__':
    app.run()
