import os
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from PySide6.QtCore import QThread, Signal
from format_detector import parse_file

class ScanThread(QThread):
    batch_ready=Signal(list)
    progress=Signal(int,int)
    completed=Signal(int,int)

    def __init__(self, folder, parent=None):
        super().__init__(parent)
        self.folder=os.path.abspath(folder)
        self._stop=False

    def stop(self):
        self._stop=True
        self.requestInterruption()

    def _collect_paths(self):
        paths=[]
        stack=[self.folder]
        while stack and len(paths)<100000:
            if self._stop or self.isInterruptionRequested():
                break
            current=stack.pop()
            try:
                with os.scandir(current) as it:
                    for entry in it:
                        if self._stop or self.isInterruptionRequested() or len(paths)>=100000:
                            break
                        try:
                            if entry.is_dir(follow_symlinks=False):
                                stack.append(entry.path)
                            elif entry.is_file(follow_symlinks=False):
                                paths.append(entry.path)
                        except OSError:
                            pass
            except OSError:
                pass
        return paths

    def _parse(self, path):
        item=parse_file(path)
        try:
            item.file_name=os.path.relpath(path,self.folder)
        except ValueError:
            pass
        return item

    def run(self):
        start=time.perf_counter()
        paths=self._collect_paths()
        total=len(paths)
        self.progress.emit(0,total)

        if not total:
            self.completed.emit(0,int((time.perf_counter()-start)*1000))
            return

        workers=min(8,max(2,(os.cpu_count() or 4)))
        processed=0
        batch=[]
        iterator=iter(paths)
        pending=set()

        with ThreadPoolExecutor(max_workers=workers,thread_name_prefix="metadata") as pool:
            for _ in range(min(workers*2,total)):
                try:
                    pending.add(pool.submit(self._parse,next(iterator)))
                except StopIteration:
                    break

            while pending and not self._stop and not self.isInterruptionRequested():
                done,pending=wait(pending,timeout=0.1,return_when=FIRST_COMPLETED)
                for fut in done:
                    try:
                        batch.append(fut.result())
                    except Exception:
                        pass
                    processed+=1
                    try:
                        pending.add(pool.submit(self._parse,next(iterator)))
                    except StopIteration:
                        pass
                    if len(batch)>=64:
                        self.batch_ready.emit(batch)
                        batch=[]
                if done:
                    self.progress.emit(processed,total)

            for f in pending:
                f.cancel()

        if batch:
            self.batch_ready.emit(batch)

        self.completed.emit(processed,int((time.perf_counter()-start)*1000))
