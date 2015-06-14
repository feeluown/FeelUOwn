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

    var img_url = playlist_data.coverImgUrl;

    imgEle.attr('src', img_url);
    descEle.text(playlist_data['name']);

    var tracks = playlist_data.tracks;
    var total = tracks.length;

    countEle.text(total);
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


$(document).ready(function(){

});