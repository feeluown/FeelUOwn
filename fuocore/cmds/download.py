from .base import AbstractHandler


class DownloadHandler(AbstractHandler):
    cmds = 'download'

    def handle(self, cmd):
        # TODO: Download progress; Download multi songs; Download http:// song
        s = ' '.join(cmd.args)
        if s.startswith('fuo://'):
            song = self.model_parser.parse_line(s)
            if song is not None:
                save_path = song.save()
                return f'Downloaded on {save_path}'