# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""FluentQML Models - 高性能数据模型"""

from typing import List, Dict, Any, Optional
from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, QByteArray, Property, Signal


class TableListModel(QAbstractListModel):
    """高性能表格数据模型 - 支持百万级数据
    
    使用 QAbstractListModel 实现按需数据提供，避免一次性序列化全部数据。
    
    用法:
        model = TableListModel()
        model.setData([{"name": "商品1", "count": 10, "price": "¥9.99"}, ...])
        table_widget.setModel(model)
    """
    
    countChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[Dict[str, Any]] = []
        self._roles: Dict[int, str] = {}
        self._role_names: Dict[int, QByteArray] = {}
        self._base_role = Qt.UserRole + 1
    
    def _get_count(self) -> int:
        return len(self._data)
    
    # QML 可访问的 count 属性
    count = Property(int, _get_count, notify=countChanged)
    
    def rowCount(self, parent=QModelIndex()) -> int:
        """返回数据行数"""
        if parent.isValid():
            return 0
        return len(self._data)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """按需返回单元格数据"""
        if not index.isValid() or index.row() >= len(self._data):
            return None
        
        row_data = self._data[index.row()]
        
        # modelData 角色返回整行数据
        if role == Qt.UserRole:
            return row_data
        
        # 返回角色对应的数据
        if role in self._roles:
            key = self._roles[role]
            return row_data.get(key, "")
        
        # DisplayRole 返回第一个字段的值
        if role == Qt.DisplayRole and self._roles:
            first_key = list(self._roles.values())[0] if self._roles else None
            if first_key and first_key != "_rowData":
                return row_data.get(first_key, "")
        
        return None
    
    def roleNames(self) -> Dict[int, QByteArray]:
        """返回角色名映射，供 QML 使用"""
        return self._role_names
    
    def setModelData(self, data: List[Dict[str, Any]]):
        """设置模型数据
        
        Args:
            data: 数据列表，每项为字典
        """
        self.beginResetModel()
        self._data = data
        
        # 自动推断角色（从第一条数据）
        if data:
            self._roles.clear()
            self._role_names.clear()
            role_id = self._base_role
            for key in data[0].keys():
                self._roles[role_id] = key
                self._role_names[role_id] = QByteArray(key.encode())
                role_id += 1
            # 添加 modelData 角色用于整行数据
            self._roles[Qt.UserRole] = "_rowData"
            self._role_names[Qt.UserRole] = QByteArray(b"modelData")
        
        self.endResetModel()
        self.countChanged.emit()
    
    def appendRow(self, row_data: Dict[str, Any]):
        """追加一行数据"""
        row = len(self._data)
        self.beginInsertRows(QModelIndex(), row, row)
        self._data.append(row_data)
        self.endInsertRows()
        self.countChanged.emit()
    
    def removeRow(self, row: int, parent=QModelIndex()) -> bool:
        """删除一行数据"""
        if row < 0 or row >= len(self._data):
            return False
        self.beginRemoveRows(parent, row, row)
        del self._data[row]
        self.endRemoveRows()
        self.countChanged.emit()
        return True
    
    def clear(self):
        """清空所有数据"""
        self.beginResetModel()
        self._data.clear()
        self.endResetModel()
    
    def getRow(self, row: int) -> Optional[Dict[str, Any]]:
        """获取指定行数据"""
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
