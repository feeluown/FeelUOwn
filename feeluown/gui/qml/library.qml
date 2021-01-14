import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15


Item {
  width: 640

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: 20

    TabBar {
      id: tabbar
      width: parent.width

      Repeater {
        model: ["概览", "歌曲", "歌手", "专辑", "视频"]

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

        Text {
          text: "最近播放"
          font.pointSize: 15
          font.bold: true
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
