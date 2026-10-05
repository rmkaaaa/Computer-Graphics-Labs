from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor

class MetadataModel(QAbstractTableModel):
    HEADERS=["Файл","Формат","Размер","DPI","Глубина цвета","Сжатие","Статус"]
    def __init__(self,parent=None):
        super().__init__(parent)
        self.items=[]
        self.errors_only=False

    def _visible(self):
        if not self.errors_only:
            return self.items
        return [m for m in self.items if not m.ok or not m.status.startswith("OK")]

    def rowCount(self,parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._visible())

    def columnCount(self,parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def item_at(self,row):
        rows=self._visible()
        return rows[row] if 0<=row<len(rows) else None

    def data(self,index,role=Qt.DisplayRole):
        if not index.isValid(): return None
        m=self.item_at(index.row())
        if not m: return None
        vals=[m.file_name,m.format,m.size,m.dpi,m.depth,m.compression,m.status]
        if role in (Qt.DisplayRole,Qt.ToolTipRole):
            return vals[index.column()]
        if role==Qt.ForegroundRole and (not m.ok or not m.status.startswith("OK")):
            return QBrush(QColor(255, 80, 80))
        return None

    def headerData(self,section,orientation,role=Qt.DisplayRole):
        if role==Qt.DisplayRole and orientation==Qt.Horizontal and 0<=section<len(self.HEADERS):
            return self.HEADERS[section]
        return super().headerData(section,orientation,role)

    def clear(self):
        self.beginResetModel(); self.items.clear(); self.endResetModel()

    def add_batch(self,batch):
        if not batch:return
        self.beginResetModel(); self.items.extend(batch); self.endResetModel()

    def set_errors_only(self,value):
        self.beginResetModel(); self.errors_only=value; self.endResetModel()

    def error_count(self):
        return sum(1 for m in self.items if not m.ok or not m.status.startswith("OK"))
