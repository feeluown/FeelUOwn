# -*- coding=utf8 -*-
__author__ = 'cosven'


class DataModel(object):
    def user(self):
        user_model = {
            'uid': int,
            'username': unicode,
            'avatar': unicode
        }
        return user_model

    def music(self):
        music_model = {
            'id': int,
            'name': unicode,
            'artists': list,
            'album': dict,
            'duration': unicode,
            'mp3Url': unicode
        }
        return music_model

    def playlist(self):
        playlist_model = {
            'id': int,
            'name': unicode
        }
        return playlist_model

    def search_result(self):
        """
        from search result: data['result']['songs']
        """
        search_list = {
            'id': int,
            'name': unicode,
            'artists': list,
            'album': dict
        }
        return search_list


    def set_datamodel_from_data(self, data, datamodel):
        """
        before generating model, the data should be validated
        requirement: the datastructure of model is similar with standard
        :param data: dict, input data
        :param type: string, the target model type
        """
        # temperarily: no validation check
        for key in datamodel:
            datamodel[key] = data[key]
        return datamodel

    def validate(self, data, model_type):
        """
        compare data with the standard model, to validate the data basicllay.
        1. check those keys which data must contain
        :param data: dict type,
        :param model: dict type, standard data model. base on the doc
        :return: if validated: true
        """
        return True

