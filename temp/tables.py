from sqlalchemy import Column, ForeignKey, Integer, String, Table, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DB_URL = "sqlite:///./pdfs.db"  # SQLite database URL, can be changed to PostgreSQL or others
engine = create_engine(DB_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
pdfs_tags = Table(
    "pdfs_tags", Base.metadata, Column("pdf_id", Integer, ForeignKey("pdfs.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True)
    )  # build a many-to-many relationship table


class PDF(Base):
    __tablename__ = "pdfs"

    id = Column(Integer, primary_key=True)  # unique identifier for each PDF
    name = Column(String, nullable=False)  # name of the PDF
    path = Column(String, unique=True, nullable=False)  # file path of the PDF

    # build a relationship with `Tag` through `pdfs_tags`
    tags = relationship("Tag", secondary=pdfs_tags, back_populates="pdfs")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)  # unique identifier for each tag
    name = Column(String, unique=True, nullable=False)  # name of the tag

    # build a relationship with `PDF` through `pdfs_tags`
    pdfs = relationship("PDF", secondary=pdfs_tags, back_populates="tags")
