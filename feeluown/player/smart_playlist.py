import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from feeluown.consts import DATA_DIR
from feeluown.utils.dispatch import Signal

logger = logging.getLogger(__name__)


class SmartSort(str, Enum):
    play_count_desc = 'play_count_desc'
    last_played_desc = 'last_played_desc'
    date_added_desc = 'date_added_desc'
    title_asc = 'title_asc'


@dataclass
class SmartRule:
    sort_by: str = SmartSort.play_count_desc.value
    time_range_days: Optional[int] = None
    limit: int = 50
    sources: Optional[List[str]] = None
    min_play_count: int = 1
    max_play_count: Optional[int] = None

    def to_dict(self):
        return {
            'sort_by': self.sort_by,
            'time_range_days': self.time_range_days,
            'limit': self.limit,
            'sources': self.sources,
            'min_play_count': self.min_play_count,
            'max_play_count': self.max_play_count,
        }

    @classmethod
    def from_dict(cls, data):
        data = dict(data or {})
        sort_by = data.get('sort_by', SmartSort.play_count_desc.value)
        # Validate sort_by against known values.
        valid = {e.value for e in SmartSort}
        if sort_by not in valid:
            logger.warning(
                'Unknown smart sort_by:%s, fallback to play_count_desc',
                sort_by)
            sort_by = SmartSort.play_count_desc.value
        limit = data.get('limit', 50)
        try:
            limit = max(1, min(int(limit), 500))
        except (TypeError, ValueError):
            limit = 50
        min_play_count = data.get('min_play_count', 1)
        try:
            min_play_count = max(1, int(min_play_count))
        except (TypeError, ValueError):
            min_play_count = 1
        max_play_count = data.get('max_play_count')
        if max_play_count is not None:
            try:
                max_play_count = int(max_play_count)
            except (TypeError, ValueError):
                max_play_count = None
        time_range_days = data.get('time_range_days')
        if time_range_days is not None:
            try:
                time_range_days = int(time_range_days)
            except (TypeError, ValueError):
                time_range_days = None
        sources = data.get('sources')
        if sources is not None:
            sources = [str(s) for s in sources]
        return cls(
            sort_by=sort_by,
            time_range_days=time_range_days,
            limit=limit,
            sources=sources,
            min_play_count=min_play_count,
            max_play_count=max_play_count,
        )


def _song_title(model):
    for attr in ('title', 'title_display'):
        try:
            value = getattr(model, attr, '')
        except Exception:
            value = ''
        if value:
            return str(value)
    return str(model)


@dataclass
class SmartPlaylist:
    id: str
    name: str
    description: str = ''
    rule: SmartRule = field(default_factory=SmartRule)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'rule': self.rule.to_dict(),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=str(data.get('id')),
            name=str(data.get('name', data.get('id'))),
            description=str(data.get('description', '')),
            rule=SmartRule.from_dict(data.get('rule', {})),
        )


def builtin_playlists():
    """Return builtin smart playlists."""
    return [
        SmartPlaylist(
            id='recent-7d',
            name='Recently Played (7 days)',
            description='Songs played in the last 7 days, most recent first.',
            rule=SmartRule(
                sort_by=SmartSort.last_played_desc.value,
                time_range_days=7,
                limit=50,
                min_play_count=1,
            ),
        ),
        SmartPlaylist(
            id='most-played',
            name='Most Played (Top 50)',
            description='Top 50 most played songs of all time.',
            rule=SmartRule(
                sort_by=SmartSort.play_count_desc.value,
                time_range_days=None,
                limit=50,
                min_play_count=1,
            ),
        ),
        SmartPlaylist(
            id='new-discoveries',
            name='New Discoveries',
            description='Recently first-played songs with no more than 2 plays.',
            rule=SmartRule(
                sort_by=SmartSort.date_added_desc.value,
                time_range_days=None,
                limit=50,
                min_play_count=1,
                max_play_count=2,
            ),
        ),
    ]


def default_filepath():
    return os.path.join(DATA_DIR, 'smart_playlists.json')


class SmartPlaylistManager:
    """Manage rule-based smart playlists.

    This manager follows the FM-style lifecycle (activate/deactivate) but the
    fetch function is a local rule evaluation over play history instead of
    a provider API call.
    """

    def __init__(self, app, filepath=None):
        self._app = app
        self._filepath = filepath
        self._playlists: Dict[str, SmartPlaylist] = {}
        self._active_id: Optional[str] = None
        self.playlists_changed = Signal()
        self.active_changed = Signal()

    @property
    def filepath(self):
        return self._filepath or default_filepath()

    @property
    def active_id(self):
        return self._active_id

    def list_all(self):
        return list(self._playlists.values())

    def get(self, id):
        return self._playlists.get(str(id))

    def load(self):
        """Load playlists from file, seeding builtins on first run."""
        path = self.filepath
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                logger.exception('Load smart playlists failed: %s', path)
                data = {}
            items = data.get('playlists', []) if isinstance(data, dict) else []
            playlists = []
            for item in items:
                try:
                    playlists.append(SmartPlaylist.from_dict(item))
                except Exception:
                    logger.exception('Invalid smart playlist item: %s', item)
            if playlists:
                self._playlists = {p.id: p for p in playlists}
                self.playlists_changed.emit()
                return
            logger.warning('No valid smart playlists in %s, seeding builtins', path)
        for playlist in builtin_playlists():
            self._playlists[playlist.id] = playlist
        self.save()
        self.playlists_changed.emit()

    def save(self):
        path = self.filepath
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = {
                'version': 1,
                'playlists': [p.to_dict() for p in self._playlists.values()],
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            logger.exception('Save smart playlists failed: %s', path)

    def create(self, id, name, rule, description=''):
        key = str(id)
        if key in self._playlists:
            raise ValueError(f'Smart playlist {key} already exists')
        playlist = SmartPlaylist(id=key, name=name, description=description, rule=rule)
        self._playlists[key] = playlist
        self.save()
        self.playlists_changed.emit()
        return playlist

    def remove(self, id):
        key = str(id)
        if key in self._playlists:
            self._playlists.pop(key)
            if self._active_id == key:
                self._active_id = None
                self.active_changed.emit()
            self.save()
            self.playlists_changed.emit()
            return True
        return False

    def update_rule(self, id, rule):
        playlist = self.get(id)
        if playlist is None:
            return None
        playlist.rule = rule
        self.save()
        self.playlists_changed.emit()
        return playlist

    def set_active(self, id):
        key = str(id) if id is not None else None
        if key is not None and key not in self._playlists:
            return False
        if self._active_id != key:
            self._active_id = key
            self.active_changed.emit()
        return True

    def evaluate(self, rule):
        """Evaluate a rule against play history and return song models."""
        recently_played = self._app.recently_played
        counts = recently_played.get_play_counts(rule.time_range_days)
        last_map = recently_played.get_last_played_map(rule.time_range_days)
        first_map = recently_played.get_first_seen_map()
        models_map = recently_played.get_models_map()

        candidates = []
        for uri, model in models_map.items():
            if rule.sources is not None:
                if getattr(model, 'source', None) not in rule.sources:
                    continue
            if rule.time_range_days is not None and uri not in last_map:
                continue
            count = counts.get(uri, 0)
            if count < rule.min_play_count:
                continue
            if rule.max_play_count is not None and count > rule.max_play_count:
                continue
            candidates.append(uri)

        sort_by = rule.sort_by
        if sort_by == SmartSort.play_count_desc.value:
            candidates.sort(key=lambda u: (-counts.get(u, 0), -last_map.get(u, 0)))
        elif sort_by == SmartSort.last_played_desc.value:
            candidates.sort(key=lambda u: -last_map.get(u, 0))
        elif sort_by == SmartSort.date_added_desc.value:
            candidates.sort(key=lambda u: -first_map.get(u, 0))
        elif sort_by == SmartSort.title_asc.value:
            candidates.sort(key=lambda u: _song_title(models_map[u]).lower())
        else:
            candidates.sort(key=lambda u: (-counts.get(u, 0), -last_map.get(u, 0)))
        return [models_map[uri] for uri in candidates[:rule.limit]]

    def evaluate_playlist(self, id):
        playlist = self.get(id)
        if playlist is None:
            return []
        return self.evaluate(playlist.rule)

    def activate(self, id, replace=True):
        """Replace the current queue with smart playlist results.

        V1 only tracks the active id and replaces the queue; it does not
        auto-play or live-update the queue on every play event.
        """
        playlist = self.get(id)
        if playlist is None:
            return []
        songs = self.evaluate(playlist.rule)
        if replace:
            self._app.playlist.set_models(songs)
        self.set_active(id)
        return songs

    def deactivate(self):
        self.set_active(None)
