from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class Intervento(Base):
    __tablename__ = 'interventi'

    id = Column(Integer, primary_key=True)
    nome_cliente = Column(String, nullable=False)
    durata_ore = Column(Float, nullable=False)
    data = Column(Date, default=datetime.date.today)
    note = Column(String)
    risolto = Column(Boolean, default=False)
    urgenza = Column(Boolean, default=False)
    costo_totale = Column(Float)
    signature = Column(String)

# 🔧 Setup DB engine + session
engine = create_engine('sqlite:///interventi.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
