from feeluown.ai.tools.library import library_search, library_tools
from feeluown.ai.tools.artifacts import play_artifact_song, artifact_tools
from feeluown.ai.tools.playback import (
    playback_adjust_volume,
    playback_get_state,
    playback_next_track,
    playback_pause,
    playback_previous_track,
    playback_resume,
    playback_set_volume,
    playback_stop,
    playback_toggle,
    playback_tools,
)
from feeluown.ai.tools.ai_radio import (
    ai_radio_activate,
    ai_radio_deactivate,
    ai_radio_get_state,
    ai_radio_update_preferences,
    ai_radio_tools,
)
from feeluown.ai.tools.fm_candidates import (
    fm_candidates_append,
    fm_candidates_get_state,
    fm_candidates_remove,
    fm_candidates_tools,
)
from feeluown.ai.tools.suggestions import (
    create_song_suggestions_artifact,
    play_song_suggestion,
    suggestion_tools,
)


copilot_tools = [
    *suggestion_tools,
    *library_tools,
    *artifact_tools,
    *playback_tools,
    *ai_radio_tools,
    *fm_candidates_tools,
]


__all__ = [
    "ai_radio_activate",
    "ai_radio_deactivate",
    "ai_radio_get_state",
    "ai_radio_tools",
    "ai_radio_update_preferences",
    "copilot_tools",
    "create_song_suggestions_artifact",
    "fm_candidates_append",
    "fm_candidates_get_state",
    "fm_candidates_remove",
    "fm_candidates_tools",
    "library_search",
    "library_tools",
    "artifact_tools",
    "play_song_suggestion",
    "play_artifact_song",
    "playback_adjust_volume",
    "playback_get_state",
    "playback_next_track",
    "playback_pause",
    "playback_previous_track",
    "playback_resume",
    "playback_set_volume",
    "playback_stop",
    "playback_toggle",
    "playback_tools",
    "suggestion_tools",
]
