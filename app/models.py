from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from pydantic import EmailStr
from pwdlib import PasswordHash

class UserBase(SQLModel,):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password: str

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    comments: List["Comment"] = Relationship(back_populates="user")

    def check_password(self, plaintext_password:str):
        return PasswordHash.recommended().verify(password=plaintext_password, hash=self.password)
    
class Album(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    artist: str
    image_url: str

    tracks: List["Track"] = Relationship(back_populates="album")

class Track(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    likes: int = Field(default = 0)
    dislikes: int = Field(default= 0)

    album_id: Optional[int] = Field(default=None, foreign_key="album.id")
    album: Optional[Album] = Relationship(back_populates="tracks")

    comments: List["Comment"] = Relationship(back_populates="track")

class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str

    # LINK: Foreign Key to Track
    track_id: Optional[int] = Field(default=None, foreign_key="track.id")
    track: Optional[Track] = Relationship(back_populates="comments")
    
    # LINK: Foreign Key to User
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="comments")

