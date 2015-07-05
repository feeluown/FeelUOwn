var SongTable = {};
var appTable = angular.module('app_table',[]);

appTable.directive('song', function(){
    return {
        link: function($scope, $element){

            setItemMusicId = function(mid, ele){
                ele.attr('id', mid);
            }

            setRowAlternate = function(even, ele){
                // highlight row which is even
                if (even == false) {
                    ele.addClass('alternate');
                }
            }

            setRowAlternate($scope.$even, $element);
            // setItemMusicId($scope.$song.id, $element);
        }
    }
});

SongTable.initData = function($scope){
    $scope.init = function(songs){
        $scope.songs = songs;
    }
}

SongTable.fillSongsTable = function($scope){
    $scope.accessArtistsName = function(artists){
        var name = '';
        for (var i=0; i< artists.length; i++){
            if ( i>0 ){
                name += ', ';
            }
            name += artists[i].name + ' ';
        }
        $scope.artistName = name;
    }

    $scope.accessSongDuration = function(duration){
        var m = parseInt(duration / 60000);
        var s = parseInt(parseInt(duration % 60000)/1000);
        $scope.duration = m.toString() + ':' + s;
    }
}



window.python_log = function(text){
    console.log(text);
    console.log ("hello");
    $('.album').hide();
}

window.fill_playlist = function(playlist_data){
    var imgEle = $('#coverImg');
    var descEle = $('#name');
    var countEle = $('#count');
    var tbodyEle = $('#tracks');

    var playAllBtnEle = $('#play_all');
    playAllBtnEle.attr('pid', playlist_data['id']);

    var img_url = playlist_data.coverImgUrl;

    imgEle.attr('src', img_url);
    descEle.text(playlist_data['name']);

    var tracks = playlist_data.tracks;

    angular.element($('#songs_table')).scope().init(tracks);
    angular.element($('#songs_table')).scope().$apply();

    $('.song').on('dblclick', function(){
        var sid = $(this).attr('id');
        if (sid){
            console.log('play : ', sid);
        }

        // js_python python的接口
        js_python.play(parseInt(sid));
    });
}

window.fill_search = function(songs){

    var tbodyEle = $('#tracks');

    var tracks = songs;
    var total = songs.length;

    for (var i=0; i<total; i++) {
        var trEle = $("<tr class='song' />");
        trEle.attr('id', tracks[i].id);
        if (i%2 != 0){
            trEle.addClass('alternate')
        }

        var tdEle = $("<td />");
        trEle.append(tdEle);

        var starEle = $("<div class='star' />");
        tdEle.append(starEle);

        var tdNameEle = $("<td />");
        tdNameEle.text(tracks[i].name);
        trEle.append(tdNameEle);

        var tdArtistsEle = $("<td />");
        var artists = tracks[i].artists;
        var artistsName = '';
        for (var j=0; j<artists.length; j++){
            // console.log(artists[j].name);
            if (artists[j].name != undefined){
                artistsName += (artists[j].name + ' ');
            }

        }

        tdArtistsEle.text(artistsName);
        trEle.append(tdArtistsEle);

        var tdAlbumEle = $("<td />");
        tdAlbumEle.text(tracks[i].album.name);
        trEle.append(tdAlbumEle);

        var tdDurationEle = $("<td />");
        var duration = tracks[i].duration;
        var m = parseInt(duration / 60000);
        var s = parseInt(parseInt(duration % 60000)/1000);
        duration = m.toString() + ':' + s;
        tdDurationEle.text(duration);
        trEle.append(tdDurationEle);

        tbodyEle.append(trEle);
    }

    $('.song').on('dblclick', function(){
        var sid = $(this).attr('id');
        if (sid){
            console.log('play : ', sid);
        }

        // js_python python的接口
        js_python.play(parseInt(sid));
    });
}

$(function(){
    console.log('common js');
});