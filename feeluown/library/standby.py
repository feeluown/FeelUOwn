from .models import SongModel

STANDBY_DEFAULT_MIN_SCORE = 0.5
STANDBY_FULL_SCORE = 1


def get_standby_score(origin, standby):

    # TODO: move this function to utils module
    def duration_ms_to_duration(ms):
        if not ms:  # ms is empty
            return 0
        parts = ms.split(':')
        assert len(parts) in (2, 3), f'invalid duration format: {ms}'
        if len(parts) == 3:
            h, m, s = parts
        else:
            m, s = parts
            h = 0
        return int(h) * 3600 + int(m) * 60 + int(s)

    def get_duration(s):
        return s.duration if isinstance(s, SongModel) else \
            duration_ms_to_duration(s.duration_ms)

    origin_duration = get_duration(origin)

    score = 0
    if not (origin.album_name and origin_duration):
        score_dis = [4, 4, 1, 1]
    else:
        score_dis = [3, 2, 2, 3]

    if origin.artists_name == standby.artists_name:
        score += score_dis[0]
    if origin.title == standby.title:
        score += score_dis[1]
    # Only compare album_name when it is not empty.
    if origin.album_name and origin.album_name == standby.album_name:
        score += score_dis[2]
    standby_duration = get_duration(standby)
    if origin_duration and \
            abs(origin_duration - standby_duration) / max(origin_duration, 1) < 0.1:
        score += score_dis[3]

    # Debug code for score function
    # print(f"{score}\t('{standby.title}', "
    #       f"'{standby.artists_name}', "
    #       f"'{standby.album_name}', "
    #       f"'{standby.duration_ms}')")
    return score / 10
