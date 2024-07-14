from app.database import db
from sqlalchemy.orm import Mapped, mapped_column
from typing import List


User_Roles = [(1, "Admin"), (2, "Poster")]

class Role(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    role_name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    users: Mapped[List["User"]] = db.relationship(back_populates='role')