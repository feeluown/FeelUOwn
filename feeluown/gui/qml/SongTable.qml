import QtQuick 2.15
import QtQuick.Controls 2.15
import Qt.labs.qmlmodels 1.0

TableView {
  property string songs

  width: parent.width
  flickableDirection: Flickable.AutoFlickDirection
  focus: true

  FontMetrics {
    id: fontMetrics
  }

  model: TableModel {
    TableModelColumn { }
    TableModelColumn { display: "title" }
    TableModelColumn { display: "artists_name" }
    TableModelColumn { display: "album_name" }
    TableModelColumn { display: "duration_ms" }
    rows: JSON.parse(songs)
  }

  function columnWidth(pWidth, column, fontHeight){
    var ratios = [0.1, 0.3, 0.2, 0.3, 0.1]
    return pWidth * ratios[column]
  }

  delegate: Button {
    id: btn
    implicitWidth: columnWidth(parent.width, column, fontMetrics.height)
    implicitHeight: fontMetrics.height * 2
    text: column == 0 ? row + 1 : model.display

    contentItem: Text {
      width: parent.width
      text: btn.text
      elide: Text.ElideRight
      horizontalAlignment: Text.AlignLeft
    }

    // border bottom
    background: Rectangle {
      anchors.bottom: parent.bottom
      height: 1
      color: palette.mid
    }

  }
}
