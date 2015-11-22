# -*- coding: utf-8 -*-

from datetime import datetime
import json
import pickle

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, PickleType, DateTime

from controller_api import ControllerApi


Base = declarative_base()


class PlaylistDb(Base):
    __tablename__ = 'playlist'
    id = Column(Integer, primary_key=True)
    pid = Column('pid', Integer, nullable=False, unique=True)
    _data = Column('data', PickleType, nullable=False)

    @classmethod
    def get_data(cls, pid):
        playlist = ControllerApi.session.query(cls).filter(cls.pid==pid).first()
        if playlist is not None:
            data = pickle.loads(playlist._data)
            return data
        return None
    
    @classmethod
    def update_data(cls, pid, data):
        playlist = ControllerApi.session.query(cls).filter(cls.pid==pid).first()
        playlist._data = pickle.dumps(data)
        ControllerApi.session.commit()

    def update(self, data):
        self._data = pickle.dumps(data)
        ControllerApi.session.commit()

    @classmethod
    def exists(cls, pid):
        if ControllerApi.session.query(cls).filter(cls.pid==pid).count() > 0:
            return True
        return False

    def save(self):
        ControllerApi.session.add(self)
        ControllerApi.session.commit()
    
    @property
    def data(self):
        return pickle.loads(self._data)


class SongDb(Base):
    __tablename__ = 'songs'
    id = Column(Integer, primary_key=True)
    mid = Column('mid', Integer, nullable=False, unique=True)
    _data = Column('data', PickleType, nullable=True)

    @classmethod
    def get_data(cls, mid):
        song = ControllerApi.session.query(cls).filter(cls.mid==mid).first()
        if song is not None:
            data = pickle.loads(song._data)
            if type(data) is bytes:
                data = json.loads(data.decode('utf-8'))
            return data
        return None
    
    @classmethod
    def update_data(cls, mid, data):
        song = ControllerApi.session.query(cls).filter(cls.mid==mid).first()
        song._data = pickle.dumps(data)
        ControllerApi.session.commit()

    def update(self, data):
        self._data = pickle.dumps(data)
        ControllerApi.session.commit()

    @classmethod
    def exists(cls, mid):

        if ControllerApi.session.query(cls).filter(cls.mid==mid).count() > 0:
            return True
        return False

    def save(self):
        if not SongDb.exists(self.mid):
            ControllerApi.session.add(self)
            ControllerApi.session.commit()
        else:
            SongDb.update_data(self.mid, self._data)
    
    @property
    def data(self):
        return pickle.loads(self._data)


class UserDb(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    uid = Column('uid', Integer, nullable=False, unique=True)
    _playlists = Column('playlists', PickleType)
    _cookies = Column('cookies', PickleType)
    _basic_info = Column('basic_info', PickleType, nullable=False)
    last_login = Column('last_login', DateTime)
    username = Column('username', String)
    password = Column('password', String)
    
    @property
    def cookies(self):
        return pickle.loads(self._cookies) if self._cookies else None

    @property
    def playlists(self):
        return pickle.loads(self._playlists) if self._playlists else None

    @property
    def basic_info(self):
        return pickle.loads(self._basic_info) if self._basic_info else None

    def update(self, **kw):
        ControllerApi.session.query(UserDb)\
                     .filter(UserDb.id==self.id).update(kw)
        ControllerApi.session.commit()
    
    def record_login_time(self):
        self.last_login = datetime.now()
        ControllerApi.session.commit()

    @classmethod
    def create_or_update(cls, uid, basic_info):
        user = ControllerApi.session.query(UserDb)\
                .filter(UserDb.uid==uid).first()
        if user is not None:
            user._basic_info=basic_info
        else:
            user = UserDb(uid=uid, _basic_info=basic_info)
            ControllerApi.session.add(user)
        ControllerApi.session.commit()

    @classmethod
    def get_user(cls, uid):
        return ControllerApi.session.query(UserDb)\
                                    .filter(UserDb.uid==uid).first()
    
    @classmethod
    def get_last_login_user(cls):
        return ControllerApi.session.query(UserDb)\
                            .order_by(UserDb.last_login.desc())\
                            .first()

