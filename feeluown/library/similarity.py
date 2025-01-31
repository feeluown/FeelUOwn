from .models import SongModel

FULL_SCORE = 10


def get_standby_origin_similarity(origin, standby):

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

    score = FULL_SCORE
    unsure_score = 0
    if origin.artists_name != standby.artists_name:
        score -= 3
    if origin.title != standby.title:
        score -= 2
    # Only compare album_name when it is not empty.
    if origin.album_name:
        if origin.album_name != standby.album_name:
            score -= 2
    else:
        score -= 1
        unsure_score += 2

    if isinstance(origin, SongModel):
        origin_duration = origin.duration
    else:
        origin_duration = duration_ms_to_duration(origin.duration_ms)
    if isinstance(standby, SongModel):
        standby_duration = standby.duration
    else:
        standby_duration = duration_ms_to_duration(standby.duration_ms)
    # Only compare duration when it is not empty.
    if origin_duration:
        if abs(origin_duration - standby_duration) / max(origin_duration, 1) > 0.1:
            score -= 3
    else:
        score -= 1
        unsure_score += 3

    # Debug code for score function
    # print(f"{score}\t('{standby.title}', "
    #       f"'{standby.artists_name}', "
    #       f"'{standby.album_name}', "
    #       f"'{standby.duration_ms}')")
    return ((score - unsure_score) / (FULL_SCORE - unsure_score)) * FULL_SCORE
