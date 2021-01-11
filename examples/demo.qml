import QtQuick 2.15


ListView {
  width: 500
  height: 600
  flickableDirection: Flickable.AutoFlickDirection
  focus: true
  clip: true
  delegate: Row {
    Text { text: user + '：' + content; width: 160; height: 30 }
  }
}
