from pathlib import Path
from PySide6.QtCore import QFile, QObject, QEvent, QSize, Qt
from PySide6.QtGui import QImageReader, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QFileDialog, QHeaderView
from metadata_model import MetadataModel
from worker import ScanThread

class MainWindow(QObject):
    def __init__(self):
        super().__init__()
        loader=QUiLoader()
        file=QFile(str(Path(__file__).with_name("mainwindow.ui")))
        if not file.open(QFile.ReadOnly): raise RuntimeError("Не удалось открыть mainwindow.ui")
        self.window=loader.load(file); file.close()
        if self.window is None: raise RuntimeError(loader.errorString())

        for name in ("chooseButton","stopButton","clearButton","errorsOnlyCheck","tableView","progressBar",
                     "infoLabel","previewLabel","selectedInfoLabel","mainSplitter","foundCard",
                     "processedCard","errorCard","timeCard"):
            setattr(self,name,getattr(self.window,name))

        self.model=MetadataModel(self.window)
        self.tableView.setModel(self.model)
        self.tableView.verticalHeader().setVisible(False)
        h=self.tableView.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Interactive)
        h.setStretchLastSection(True)
        for i,w in enumerate((285,75,95,95,120,120,210)): self.tableView.setColumnWidth(i,w)
        self.mainSplitter.setSizes([950,380])

        self.worker=None
        self._preview_pixmap=None
        self.chooseButton.clicked.connect(self.choose_folder)
        self.stopButton.clicked.connect(self.stop_scan)
        self.clearButton.clicked.connect(self.clear_results)
        self.errorsOnlyCheck.toggled.connect(self.model.set_errors_only)
        self.tableView.clicked.connect(self.show_selected)
        self.stopButton.setEnabled(False)
        self.window.installEventFilter(self)
        self.update_cards(0,0)

    def show(self): self.window.show()

    def eventFilter(self,obj,event):
        if obj is self.window and event.type()==QEvent.Close:
            self.stop_scan(wait=True); self.clear_preview()
        return super().eventFilter(obj,event)

    def choose_folder(self):
        folder=QFileDialog.getExistingDirectory(self.window,"Выберите папку")
        if not folder:return
        self.stop_scan(wait=True)
        self.model.clear(); self.clear_preview()
        self.errorsOnlyCheck.setChecked(False)
        self.progressBar.setRange(0,1); self.progressBar.setValue(0)
        self.infoLabel.setText(f"Сканирование: {folder}")
        self.timeCard.setText("Время\n—")
        self.update_cards(0,0)
        self.chooseButton.setEnabled(False); self.stopButton.setEnabled(True)
        self.clearButton.setEnabled(False)
        worker=ScanThread(folder,self.window); self.worker=worker
        worker.batch_ready.connect(self.on_batch)
        worker.progress.connect(self.on_progress)
        worker.completed.connect(self.on_completed)
        worker.finished.connect(self.on_thread_finished)
        worker.start()

    def on_batch(self,batch):
        self.model.add_batch(batch)
        self.update_cards(len(self.model.items),self.model.error_count())

    def stop_scan(self,wait=False):
        if self.worker and self.worker.isRunning():
            self.infoLabel.setText("Остановка...")
            self.worker.stop()
            if wait:self.worker.wait(5000)

    def clear_results(self):
        if self.worker and self.worker.isRunning(): return
        self.model.clear(); self.clear_preview()
        self.progressBar.setRange(0,1); self.progressBar.setValue(0)
        self.infoLabel.setText("Готово. Выберите папку для анализа.")
        self.timeCard.setText("Время\n—"); self.update_cards(0,0)

    def update_cards(self,processed,errors,total=None):
        if total is None: total=processed
        self.foundCard.setText(f"Найдено\n{total}")
        self.processedCard.setText(f"Обработано\n{processed}")
        self.errorCard.setText(f"Ошибок / повреждённых\n{errors}")

    def on_progress(self,current,total):
        self.progressBar.setRange(0,max(1,total)); self.progressBar.setValue(current)
        self.infoLabel.setText(f"Обработано: {current} / {total}")
        self.update_cards(len(self.model.items),self.model.error_count(),total)

    def on_completed(self,processed,elapsed):
        stopped=processed < self.progressBar.maximum()
        state="Остановлено" if stopped else "Готово"
        self.infoLabel.setText(f"{state}. Обработано: {processed}. Время: {elapsed/1000:.3f} с")
        self.timeCard.setText(f"Время\n{elapsed/1000:.3f} с")
        self.update_cards(len(self.model.items),self.model.error_count(),self.progressBar.maximum())
        self.chooseButton.setEnabled(True); self.stopButton.setEnabled(False); self.clearButton.setEnabled(True)

    def on_thread_finished(self):
        if self.worker:self.worker.deleteLater(); self.worker=None
        self.chooseButton.setEnabled(True); self.stopButton.setEnabled(False); self.clearButton.setEnabled(True)

    def clear_preview(self):
        self.previewLabel.clear(); self.previewLabel.setText("Выберите файл в таблице")
        self.selectedInfoLabel.setText("Информация о выбранном файле"); self._preview_pixmap=None

    def show_selected(self,index):
        item=self.model.item_at(index.row())
        if not item:return
        self._preview_pixmap=None; self.previewLabel.clear()
        target=self.previewLabel.size()-QSize(16,16)
        width,height=self._parse_size(item.size)
        scaled=self._fit_size(width,height,target.width(),target.height())
        reader=QImageReader(item.path); reader.setAutoTransform(True)
        if scaled.isValid():reader.setScaledSize(scaled)
        image=reader.read()
        if image.isNull():self.previewLabel.setText("Предпросмотр недоступен")
        else:
            self._preview_pixmap=QPixmap.fromImage(image)
            self.previewLabel.setPixmap(self._preview_pixmap); self.previewLabel.setAlignment(Qt.AlignCenter)
        self.selectedInfoLabel.setText(
            f"Файл: {item.file_name}\n\nФормат: {item.format}\nРазмер: {item.size}\nDPI: {item.dpi}\n"
            f"Глубина цвета: {item.depth}\nСжатие: {item.compression}\nСтатус: {item.status}\n\n{item.details}"
        )

    @staticmethod
    def _parse_size(text):
        try:
            p=text.lower().replace("x","×").split("×"); return int(p[0].strip()),int(p[1].strip())
        except (ValueError,IndexError):return 0,0

    @staticmethod
    def _fit_size(width,height,max_width,max_height):
        if width<=0 or height<=0 or max_width<=0 or max_height<=0:return QSize()
        scale=min(max_width/width,max_height/height,1.0)
        return QSize(max(1,int(width*scale)),max(1,int(height*scale)))
