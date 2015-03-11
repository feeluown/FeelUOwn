# -*- coding=utf8 -*-
__author__ = 'cosven'


class DataModel(object):
    def user(self):
        user_model = {
            'uid': str,
            'username': str,
            'avatar': str
        }
        return user_model

    def music(self):
        music_model = {
            'mid': str,
            'title': str,
            'artist': str,
            'album': str,
            'duration': str,
            'mp3url': str
        }
        return music_model

    def playlist(self):
        playlist_model = {
            'plid': str,
            'name': str,
            'category': str
        }

    def generate_model_from_data(self, data, model_type):
        """
        before generating model, the data should be validated
        :param data: dict, input data
        :param type: string, the target model type
        """
        model = {}
        return model

    def validate(self, data, model_type):
        """
        compare data with the standard model, to validate the data basicllay.
        1. check those keys which data must contain
        :param data: dict type,
        :param model: dict type, standard data model. base on the doc
        :return: if validated: true
        """
        return True

