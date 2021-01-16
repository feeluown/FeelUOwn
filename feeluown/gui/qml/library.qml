import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt.labs.qmlmodels 1.0

import 'qml:' as Local


Item {
  width: 640

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: 20

    TabBar {
      id: tabbar
      width: parent.width

      Repeater {
        model: ["歌曲", "歌手", "专辑", "视频"]

        TabButton {
          id: button
          text: modelData
          width: 50
          contentItem: Text {
            text: button.text
            color: palette.text
            horizontalAlignment: Text.AlignHCenter
          }
          // border bottom
          background: Rectangle {
            anchors.bottom: parent.bottom
            height: button.checked ? 3 : 0
            color: palette.mid
          }
        }
      }
    }

    // margin
    Item {
      height: 20
    }

    StackLayout {
      currentIndex: tabbar.currentIndex

      Item {
        id: homeTab

        Local.SongTable {
          id: songTable
          width: parent.width
          height: parent.height
        }
      }
      Item {
        id: discoverTab
      }
      Item {
        id: activityTab
      }
    }
  }
}
