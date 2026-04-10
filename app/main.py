import uvicorn
from fastapi import FastAPI, Request, status, Form
from fastapi.responses import RedirectResponse
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from app.config import get_settings
from app.dependencies import IsUserLoggedIn, SessionDep, AuthDep
from fastapi.templating import Jinja2Templates
from app.utilities import get_flashed_messages
from jinja2 import Environment, FileSystemLoader
from sqlmodel import select
from app.models import User, Album, Track, Comment
from app.utilities import flash, create_access_token
from fastapi.staticfiles import StaticFiles


app = FastAPI(middleware=[
    Middleware(SessionMiddleware, secret_key=get_settings().secret_key)
]
)
template_env = Environment(loader = FileSystemLoader("app/templates",), )
template_env.globals['get_flashed_messages'] = get_flashed_messages
templates = Jinja2Templates(env=template_env)
static_files = StaticFiles(directory="app/static")

app.mount("/static", static_files, name="static")


@app.get('/', response_class=RedirectResponse)
async def index_view(
  request: Request,
  user_logged_in: IsUserLoggedIn,
):
  if user_logged_in:
    return RedirectResponse(url=request.url_for('home_view'), status_code=status.HTTP_303_SEE_OTHER)
  return RedirectResponse(url=request.url_for('login_view'), status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login")
async def login_view(
  user_logged_in: IsUserLoggedIn,
  request: Request,
):
  if user_logged_in:
    return RedirectResponse(url=request.url_for('home_view'), status_code=status.HTTP_303_SEE_OTHER)
  return templates.TemplateResponse(
          request=request, 
          name="login.html",
      )

@app.post('/login')
def login_action(
  request: Request,
  db: SessionDep,
  username: str = Form(),
  password: str = Form(),
):
  
  user = db.exec(select(User).where(User.username == username)).one_or_none()
  if user and user.check_password(password):
    response = RedirectResponse(url=request.url_for("index_view"), status_code=status.HTTP_303_SEE_OTHER)
    access_token = create_access_token(data={"sub": f"{user.id}"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=False,
        samesite="lax",
        secure=True,
    )    
    return response
  else:
    flash(request, 'Invalid username or password')
    return RedirectResponse(url=request.url_for('login_view'), status_code=status.HTTP_303_SEE_OTHER)


# 1. THE DASHBOARD (No ID here!)
@app.get('/app')
def home_view(request: Request, db: SessionDep, user: AuthDep):
    albums = db.exec(select(Album)).all()
    return templates.TemplateResponse(
          request=request, name="index.html",
          # Notice we pass None for the active album and track
          context={"albums": albums, "active_album": None, "active_track": None, "current_user": user}
      )

# 2. VIEWING AN ALBUM (This one uses the ID!)
@app.get("/album/{id}")
def view_album(request: Request, id: int, db: SessionDep, user: AuthDep):
    albums = db.exec(select(Album)).all()
    active_album = db.get(Album, id)  # <--- This is where db.get belongs!
    return templates.TemplateResponse(
        request=request, name="index.html", 
        context={"albums": albums, "active_album": active_album, "active_track": None, "current_user": user}
    )

# 3. VIEWING A TRACK (This one uses the ID too!)
@app.get("/track/{id}")
def view_track(request: Request, id: int, db: SessionDep, user: AuthDep):
    albums = db.exec(select(Album)).all()
    active_track = db.get(Track, id)
    return templates.TemplateResponse(
        request=request, name="index.html", 
        context={"albums": albums, "active_album": active_track.album, "active_track": active_track, "current_user": user}
    )

@app.post("/track/{id}/comment")
def add_comment(request: Request, id: int, db: SessionDep, user: AuthDep, text: str = Form(...)):
    new_comment = Comment(text=text, track_id=id, user_id=user.id)
    db.add(new_comment)
    db.commit()
    flash(request, "Comment added successfully!")
    return RedirectResponse(url=f"/track/{id}", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/track/{id}/react")
def react_to_track(request: Request, id: int, db: SessionDep, user: AuthDep, action: str = Form(...)):
    track = db.get(Track, id)
    if action == "like":
        track.likes += 1
    elif action == "dislike":
        track.dislikes += 1
        
    db.add(track)
    db.commit()
    return RedirectResponse(url=f"/track/{id}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/comment/{id}/delete")
def delete_comment(request: Request, id: int, db: SessionDep, user: AuthDep):
    comment = db.get(Comment, id)
    
    # Security: Verify the comment exists and belongs to the user trying to delete it
    if comment and comment.user_id == user.id:
        track_id = comment.track_id # Save track_id so we know where to redirect back to
        db.delete(comment)
        db.commit()
        flash(request, "Comment deleted!")
        return RedirectResponse(url=f"/track/{track_id}", status_code=status.HTTP_303_SEE_OTHER)
    else:
        flash(request, "You can only delete your own comments!")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

@app.get('/logout')
async def logout(request: Request):
  response = RedirectResponse(url=request.url_for("login_view"), status_code=status.HTTP_303_SEE_OTHER)
  response.delete_cookie(
      key="access_token", 
      httponly=True,
      samesite="none",
      secure=True
  )
  flash(request, 'logged out')
  return response