# Defines SQLAlchemy models and db connection

from sqlalchemy import Column, String, Float, Date, create_engine, UniqueConstraint, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from .config import SQLALCHEMY_DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Users(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="student")
    created_at = Column(DateTime, default=datetime.utcnow)
    submissions = relationship("Submissions", back_populates="user")

class Assignments(Base):
    __tablename__ = "assignments"
    assignment_id = Column(String, primary_key=True)
    description = Column(String)
    due_date = Column(Date)
    autograder = Column(String)
    submissions = relationship("Submissions", back_populates="assignment")

class Autograders(Base):
    __tablename__ = "autograders"
    name = Column(String, primary_key=True)
    outputs = Column(Text)
    grade_weights = Column(Text)

class Tests(Base):
    __tablename__ = "tests"
    test_id = Column(String, primary_key=True)
    assignment_id = Column(String, ForeignKey('assignments.assignment_id'))
    input_data = Column(Text)
    assignment = relationship("Assignments")

class Submissions(Base):
    __tablename__ = "submissions"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    assignment_id = Column(String, ForeignKey('assignments.assignment_id'), nullable=False)
    submission_time = Column(DateTime, default=datetime.utcnow)
    grade = Column(Float)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'assignment_id', name='unique_user_assignment'),
    )
    
    user = relationship("Users", back_populates="submissions")
    assignment = relationship("Assignments", back_populates="submissions")
    
    def __init__(self, user_id, assignment_id, submission_time, grade):
        self.id = f"{user_id}_{assignment_id}"
        self.user_id = user_id
        self.assignment_id = assignment_id
        self.submission_time = submission_time
        self.grade = grade

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)