# app/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .config import settings

security = HTTPBasic()

def basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    if (
        credentials.username != settings.basic_auth_user
        or credentials.password != settings.basic_auth_pass
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True