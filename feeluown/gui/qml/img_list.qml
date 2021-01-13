import QtQuick 2.15

ListView {
  width: 300
  height: 300
  flickableDirection: Flickable.AutoFlickDirection
  focus: true
  clip: true

  delegate: Row {
    Text { text: "hello world"; width: 160; height: 30 }
    Image { source: "http://p3.music.126.net/BeIc-sv62xZPpVBS4DjE-g==/109951164607988464.jpg"}
  }
}
