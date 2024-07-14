from app.database import db
from sqlalchemy.orm import Mapped, mapped_column

class Comment(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.Integer, nullable=False)
    username: Mapped[str] = mapped_column(db.String(255), nullable=False)
    comment_body: Mapped[str] = mapped_column(db.String(1050), nullable=False)

    def __str__(self):
        return f"{self.username} left a comment"
    
    def __repr__(self):
        return f"<Comment {self.id}|{self.user_id}"
               