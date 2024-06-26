"""Define a simple example plugin."""

# ba_meta require api 7

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import _ba
import os
import shutil
import hashlib

if TYPE_CHECKING:
    pass

pack_dir = 'avalanchaData'  # folder
pack_name = 'Avalancha Data'  # name

lang = ba.app.lang.language

if lang == 'Spanish':
    installing = 'Instalando Paquete ' + str(pack_name) + '...'
    success = 'Paquete ' + str(pack_name) + ' instalación finalizada!'
    fail = 'Paquete ' + str(pack_name) + ' instalación fallida'
elif lang == 'Chinese':
    installing = '安裝包 ' + str(pack_name) + ', 请稍候...'
    success = '盒 ' + str(pack_name) + ' 安装完成！'
    fail = '盒 ' + str(pack_name) + ' 安装失败'
else:
    installing = 'Installing pack ' + str(pack_name) + '...'
    success = 'Pack ' + str(pack_name) + ' installation succeeded!'
    fail = 'Pack ' + str(pack_name) + ' installation failed'

class PackInstaller:

    def __init__(self) -> None:
        self.python_user = _ba.env()["python_directory_user"]
        self.cfiles = self.python_user + '/' + pack_dir + '/'
        self.app_dir = _ba.env()["python_directory_app"] + '/'
        self.models_dir = self.app_dir + 'models/'
        self.audio_dir = self.app_dir + 'audio/'
        self.textures_dir = self.app_dir + 'textures/'

        self.audio = []
        self.models = []
        self.textures = []
        self.platform = _ba.app.platform
        self.get_pack()

    def get_pack(self) -> None:
        fls = os.listdir(self.cfiles)
        for fl in fls:
            if fl.endswith('.ogg'): # audio
                self.audio.append(fl)
            if fl.endswith('.bob') or fl.endswith('.cob'): # models
                self.models.append(fl)
            if fl.endswith('.ktx') or fl.endswith('.dds'): # textures
                self.textures.append(fl)

    @staticmethod
    def checkFileSame(f1, f2):
        try:
            md5s = [hashlib.md5(), hashlib.md5()]
            fs = [f1, f2]
            for i in range(2):
                f = open(fs[i], 'rb')
                block_size = 2 ** 20
                while True:
                    data = f.read(block_size)
                    if not data: break
                    md5s[i].update(data)
                f.close()
                md5s[i] = md5s[i].hexdigest()
            return md5s[0] == md5s[1]
        except Exception as e:
            return False

    def _installed(self) -> None:
        installed = True
        for a in self.audio:
            app = 'ba_data/audio/' + a
            user = self.cfiles + a
            if not os.path.isfile(app):
                installed = False
                break
            if not self.checkFileSame(app, user):
                installed = False
                break
        for m in self.models:
            app = 'ba_data/models/' + m
            user = self.cfiles + m
            if not os.path.isfile(app):
                installed = False
                break
            if not self.checkFileSame(app, user):
                installed = False
                break
        for t in self.textures:
            if self.platform == 'android':
                if t.endswith('.dds'):
                    continue
            else:
                if t.endswith('.ktx'):
                    continue
            app = 'ba_data/textures/' + t
            user = self.cfiles + t
            if not os.path.isfile(app):
                installed = False
                break
            if not self.checkFileSame(app, user):
                installed = False
                break
        return installed

    def install_pack(self) -> None:
        if self._installed():
            return

        try:
            ba.timer(1.0, lambda: ba.screenmessage(installing, color=(1, 1, 0)))
            fls = os.listdir(self.cfiles)
            for fl in fls:
                if fl.endswith('.ogg'): # audio
                    shutil.copyfile(self.cfiles + fl, 'ba_data/audio/' + fl)
                if fl.endswith('.bob') or fl.endswith('.cob'): # models
                    shutil.copyfile(self.cfiles + fl, 'ba_data/models/' + fl)
                if fl.endswith('.ktx') or fl.endswith('.dds'): # textures
                    shutil.copyfile(self.cfiles + fl, 'ba_data/textures/' + fl)
            ba.timer(1.0, lambda: ba.screenmessage(success, color=(0, 1, 0)))
        except IOError as e:
            ba.timer(1.0, lambda: ba.screenmessage(fail, color=(1, 0, 0)))
            ba.timer(1.0, lambda: ba.screenmessage(str(e), color=(1, 0, 0)))

# ba_meta export plugin
class NewPack(ba.Plugin):
    """My first ballistica plugin!"""

    def __init__(self) -> None:
        PackInstaller().install_pack()
        exec('import ' + pack_dir + '.banewpack')