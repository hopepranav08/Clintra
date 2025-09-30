from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Table, JSON, Boolean, Text
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import hashlib
import secrets

Base = declarative_base()

team_members = Table('team_members', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('team_id', Integer, ForeignKey('teams.id'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100))
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    teams = relationship("Team", secondary=team_members, back_populates="members")
    activities = relationship("Activity", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    members = relationship("User", secondary=team_members, back_populates="teams")

class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    activity_type = Column(String(50), nullable=False)
    query = Column(String(200))
    result_summary = Column(Text)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="activities")

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id'))
    role = Column(String(20))  # 'user' or 'assistant'
    content = Column(Text)
    mode = Column(String(20))  # 'literature', 'hypothesis', 'download', 'graph'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    session = relationship("ChatSession", back_populates="messages")

class Workspace(Base):
    __tablename__ = 'workspaces'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    creator = relationship("User", backref="created_workspaces")

class WorkspaceMember(Base):
    __tablename__ = 'workspace_members'
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(String(20), default='member')  # 'owner', 'admin', 'member'
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    workspace = relationship("Workspace", backref="members")
    user = relationship("User", backref="workspace_memberships")

class SharedSearch(Base):
    __tablename__ = 'shared_searches'
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'))
    shared_by = Column(Integer, ForeignKey('users.id'))
    query = Column(String(500), nullable=False)
    results = Column(JSON)
    filters = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    workspace = relationship("Workspace", backref="shared_searches")
    sharer = relationship("User", backref="shared_searches")

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, index=True)
    shared_search_id = Column(Integer, ForeignKey('shared_searches.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    shared_search = relationship("SharedSearch", backref="comments")
    user = relationship("User", backref="comments")