"""Keep a record of 3Gem's clients"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cache import cache_get, cache_invalidate, cache_set
from database import get_db
from dependencies import get_current_user, require_global_role
from models import Client, User
from schemas import ClientCreate, ClientOut

router = APIRouter(prefix="/api/clients", tags=["Clients"])

CLIENTS_CACHE_KEY = "clients:all"


@router.get("", response_model=list[ClientOut])
def list_clients(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Every client, alphabetically sorted."""
    cached = cache_get(CLIENTS_CACHE_KEY)
    if cached is not None:
        return cached

    clients = db.query(Client).order_by(Client.name).all()
    payload = [ClientOut.model_validate(c).model_dump() for c in clients]
    cache_set(CLIENTS_CACHE_KEY, payload, ttl_seconds=300)
    return payload


@router.post("", response_model=ClientOut, status_code=201)
def create_client(
    payload: ClientCreate,
    user: User = Depends(require_global_role("pm")),
    db: Session = Depends(get_db),
):
    """Add a client. Names are unique, so a duplicate is a 409 rather than a second row."""
    name = payload.name.strip()
    if not name:
        raise HTTPException(422, "Client name cannot be empty")
    if db.query(Client).filter(Client.name == name).first():
        raise HTTPException(409, f"Client '{name}' already exists")

    client = Client(name=name)
    db.add(client)
    db.commit()
    db.refresh(client)
    cache_invalidate(CLIENTS_CACHE_KEY)
    return client