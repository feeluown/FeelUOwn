var SongTable = {};
var appTable = angular.module('app_table',[]);

appTable.directive('song', function(){
    return {
        link: function($scope, $element){

            setRowAlternate = function(even, ele){
                // highlight row which is even
                if (even == false) {
                    ele.addClass('alternate');
                }
            }

            setRowAlternate($scope.$even, $element);
        }
    }
});

appTable.directive('mvbtn', function(){
    return {
        link: function($scope, $element, $attributes){
            if (parseInt($attributes.id) == 0){
                $element.hide();
            }
        }
    }
});

SongTable.initData = function($scope){
   $scope.init_search = function(songs){
        $scope.songs = songs;
   }

   $scope.init_playlist = function(playlist_data){
        $scope.songs = playlist_data.tracks;
        $scope.name = playlist_data.name;
        $scope.count = playlist_data.tracks.length;
        $scope.coverImgUrl = playlist_data.coverImgUrl;
   }

   $scope.init_artist = function(artist_detail){
        $scope.songs = artist_detail.hotSongs;
        $scope.name = artist_detail.name;
        $scope.count = artist_detail.hotSongs.length;
        $scope.coverImgUrl = artist_detail.picUrl;
   }

   $scope.init_album = function(album_detail){
        $scope.songs = album_detail.songs;
        $scope.name = album_detail.name;
        $scope.count = album_detail.songs.length;
        $scope.coverImgUrl = album_detail.picUrl;
   }
}

SongTable.fillSongsTable = function($scope){
    $scope.accessArtists = function(artists){
        var name = '';
        for (var i=0; i< artists.length; i++){
            if ( i>0 ){
                name += ', ';
            }
            name += artists[i].name + ' ';
        }
        $scope.artistName = name;

        $scope.artistId = artists[0].id;
    }

    $scope.accessSongDuration = function(duration){
        var m = parseInt(duration / 60000);
        var s = parseInt(parseInt(duration % 60000)/1000);
        $scope.duration = m.toString() + ':' + s;
    }
}

SongTable.bind_music_play = function(){
    $('.song').on('dblclick', function(){
        var sid = $(this).attr('id');
        if (sid){
            console.log('play : ', sid);
        }

        // js_python python的接口
        js_python.play(parseInt(sid));
    });

    $('.mv_flag').on('click', function(self){
        var mvid = parseInt($(this).attr('id'));
        if (mvid !=0 ){
            js_python.play_mv(mvid);
        }
    });

    $('#play_all').on('click', function(){
        var songs = {};
        songs.tracks = window.songs;
        var songsStr = JSON.stringify(songs);
        js_python.play_songs(songsStr);
    });
}

SongTable.tmpSaveSongsInfo = function(songs){
    window.songs = songs.slice(0);
}

window.searchArtist = function(self){
    var artistId = parseInt($(self).attr('id'));
    js_python.search_artist(artistId);
}

window.searchAlbum = function(self){
    var albumId = parseInt($(self).attr('id'));
    js_python.search_album(albumId);
}

window.python_log = function(text){
    console.log(text);
    console.log ("hello");
    $('.album').hide();
}

window.fill_album = function(album_detail){
    angular.element($('#songs_table')).scope().init_album(album_detail);
    angular.element($('#songs_table')).scope().$apply();

    SongTable.tmpSaveSongsInfo(album_detail.songs);
    SongTable.bind_music_play();
}

window.fill_artist = function(artist_detail){
    angular.element($('#songs_table')).scope().init_artist(artist_detail);
    angular.element($('#songs_table')).scope().$apply();

    SongTable.tmpSaveSongsInfo(artist_detail.hotSongs);
    SongTable.bind_music_play();
}

window.fill_playlist = function(playlist_data){
    angular.element($('#songs_table')).scope().init_playlist(playlist_data);
    angular.element($('#songs_table')).scope().$apply();

    SongTable.tmpSaveSongsInfo(playlist_data.tracks);
    SongTable.bind_music_play();
}

window.fill_search = function(songs){
    var tracks = songs;
    var total = songs.length;

    angular.element($('#songs_table')).scope().init_search(tracks);
    angular.element($('#songs_table')).scope().$apply();

    SongTable.bind_music_play();
    SongTable.tmpSaveSongsInfo(tracks);
}

window.play_mv = function(url){
    $('#video_mv').find('#mv_src').attr('src', url);
}


$(function(){

});