var SongTable = {};
var appTable = angular.module('app_table',[]);

appTable.directive('song', function($compile){
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

searchArtist = function(self){
    var artistId = parseInt($(self).attr('id'));
    console.log(artistId);
}

searchAlbum = function(self){
    var albumId = parseInt($(self).attr('id'));
    console.log(albumId);
}

window.python_log = function(text){
    console.log(text);
    console.log ("hello");
    $('.album').hide();
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

$(function(){
    console.log('common js');
});