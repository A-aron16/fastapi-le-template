import typer
from app.database import create_db_and_tables, get_cli_session, drop_all
from app.models import *
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from app.utilities import encrypt_password

cli = typer.Typer()

@cli.command()
def initialize():
    with get_cli_session() as db:
        drop_all() 
        create_db_and_tables() 
        
        bob = UserBase(username='bob', email='bob@mail.com', password=encrypt_password("bobpass"))
        bob_db = User.model_validate(bob)
        db.add(bob_db)

        print("Adding sample albums and tracks...")

        album1 = Album(
            title="Brainrot V1",
            artist= "Triple T",
            image_url="https://weblabs.web.app/api/brainrot/1.webp"
        )

        album2 = Album(
            title= "Brainrot v2",
            artist= "Crocodilo",
            image_url="https://weblabs.web.app/api/brainrot/2.webp"
        )

        track1 = Track(title="Track 1: Rizzard", album=album1)
        track2 = Track(title="Track 2: Ohio Vibes", album=album1)
        track3 = Track(title="Track 1: Mewing Streak", album=album2)
        track4 = Track(title="Track 2: Fanum Tax", album=album2)

        db.add(album1)
        db.add(album2)
        db.add(track1)
        db.add(track2)
        db.add(track3)
        db.add(track4)

        
        db.commit()        
        print("Database Initialized")

@cli.command()
def test():
    print("You're already in the test")


if __name__ == "__main__":
    cli()