$(document).ready(function(){
    $('#play_all').on('click', function(){
        var playAllBtnEle = $('#play_all');
        var pid = playAllBtnEle.attr('pid');
        pid = parseInt(pid);
        js_python.play_playlist(pid);
    });
});