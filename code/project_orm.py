import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import column,String,Integer,Float,ForeignKey,DateTime, Column
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(50), unique=True)
    name = Column(String(50))
    password = Column(String(64))
    group = Column(Integer, default=1)
    created_at = Column(DateTime,default=datetime.utcnow, nullable=False )

    def __repr__(self) -> str:
        return f"{self.id}|{self.name}|{self.group}"
    
if __name__ == "__main__":
    engine = create_engine('sqlite:///database.db')
    Base.metadata.create_all(engine)    