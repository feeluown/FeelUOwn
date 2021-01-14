import QtQuick 2.15
import QtQuick.Controls 2.15
import Qt.labs.qmlmodels 1.0

TableView {
  flickableDirection: Flickable.AutoFlickDirection
  focus: true

  model: TableModel {
    TableModelColumn { display: "title" }
    TableModelColumn { display: "artists_name" }
    TableModelColumn { display: "album_name" }

    rows: [
      {
        "title": "野孩子",
        "artists_name": "杨千嬅",
        "album_name": "前花生防"
      },
      {
        "title": "野孩子",
        "artists_name": "杨千嬅",
        "album_name": "前花生防"
      },
      {
        "title": "野孩子",
        "artists_name": "杨千嬅",
        "album_name": "前花生防"
      }
    ]
  }

  delegate: Button {
    id: btn
    text: model.display
    contentItem: Text {
      text: btn.text
      horizontalAlignment: Text.AlignHCenter
    }
    // border bottom
    background: Rectangle {
      anchors.bottom: parent.bottom
      height: 1
      color: palette.mid
    }

  }
}
