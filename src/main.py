# import os
#
# wrong_path = os.environ['GST_PLUGIN_PATH']
# right_path = os.getcwd()
# pattern = '{}:'.format(right_path)
# to_replace = '{};'.format(right_path)
#
# fixed_path = wrong_path.replace(pattern, to_replace)
# os.environ['GST_PLUGIN_PATH'] = fixed_path


import set_kivy_config
# import irc.client
# import requests
# import youtube_dl
# import json
# noinspection PyPackageRequirements
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.clock import Clock
from kivy.lang.builder import Builder
from kivy.core.audio import SoundLoader
from kivy.utils import platform

from loginscreen import LoginScreen
from mainscreen import MainScreen
from icon import Icon, IconsLayout
from ooc import OOCWindow, OOCLogLabel
from main_log import LogLabel, LogWindow
from sprite import SpritePreview, SpriteSettings, SpriteWindow
from textbox import MainTextInput, TextBox
from toolbar import Toolbar
from left_tab import LeftTab
from irc_mo import MessageFactory
from keyboard_listener import KeyboardListener
from settings_types import MultiChoiceOptions, SeriesWhitelist, FavCharacterList, FavSFXList

from mopopup import MOPopup
from mopopup import MOPopupYN
from location import location_manager
from os import listdir

from commands import command_processor
from kivy.core.window import Window

KV_DIR = "kv_files/"

for kv_file in listdir(KV_DIR):
    Builder.load_file(KV_DIR + kv_file)


def truth():
    print('Casca is gay')


class MainScreenManager(ScreenManager):
    main_screen = ObjectProperty(None)
    irc_connection = ObjectProperty(None)
    connected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(MainScreenManager, self).__init__(**kwargs)
        self.popup_ = MOPopup("Connection", "Connecting to IRC", "K", False)

    def on_irc_connection(self, *args):
        """Called when the IRC connection is created"""

        self.set_handlers()
        self.main_screen.user = App.get_running_app().get_user()
        Clock.schedule_interval(self.process_irc, 1.0 / 60.0)
        self.popup_.open()

    def set_handlers(self):
        connection_manager = App.get_running_app().get_user_handler().get_connection_manager()
        self.irc_connection.on_join_handler = connection_manager.on_join
        self.irc_connection.on_users_handler = connection_manager.on_join_users
        self.irc_connection.on_disconnect_handler = connection_manager.on_disconnect

    def on_connected(self, *args):
        """Called when MO connects to the IRC channel"""

        self.unset_the_r_flag()
        self.popup_.dismiss()
        del self.popup_
        config = App.get_running_app().config
        sfx = SoundLoader.load('sounds/general/login.mp3')
        v = config.getdefaultint('sound', 'effect_volume', 100)
        sfx.volume = v / 100
        sfx.play()
        self.current = "main"
        self.main_screen.on_ready()
        connection_manager = App.get_running_app().get_user_handler().get_connection_manager()
        Clock.schedule_interval(connection_manager.update_chat, 1.0 / 60.0)

    def unset_the_r_flag(self):
        """Fixes being unable to receive private messages from other users"""

        username = App.get_running_app().get_user().username
        self.irc_connection.send_mode(username, "-R")

    def process_irc(self, dt):
        self.irc_connection.process()
        self.connected = self.irc_connection.is_connected()


class MysteryOnlineApp(App):
    use_kivy_settings = False
    window_handle = None

    def __init__(self, **kwargs):
        super(MysteryOnlineApp, self).__init__(**kwargs)
        self.user = None
        self.main_screen = None
        self.user_handler = None
        self.message_factory = MessageFactory()
        self.keyboard_listener = None
        self.fav_chars = None
        self.fav_sfx = None
        self.cursor = None

    def build(self):
        msm = MainScreenManager()
        self.keyboard_listener = KeyboardListener()
        location_manager.load_locations()
        return msm

    def build_config(self, config):
        config.setdefaults('display', {
            'resolution': '1920x1080',
            'rpg_mode': 0,
        })
        config.setdefaults('sound', {
            'blip_volume': 100,
            'music_volume': 100,
            'effect_volume': 100
        })
        config.setdefaults('other', {
            'ooc_notif_delay': 60,
            'log_scrolling': 1,
            'ooc_scrolling': 1,
            'instant_text': 0,
            'last_username': 'YourUsernameHere',
            'textbox_speed': 60,
            'textbox_transparency': 60,
            'nsfw_mode': 1,
            'spoiler_mode': 1,
            'sprite_tooltips': 1,
            'graceful_exit': 'True',
            'whitelisted_series': [],
            'fav_characters': [],
            'fav_sfx': []
        })
        config.setdefaults('command_shortcuts', {
            '>': "/color green '>"
        })
        config.setdefaults('keybindings', {
            'open_character_select': 'ctrl+p',
            'open_inventory': 'ctrl+i',
            'refresh': 'ctrl+r'
        })

    def build_settings(self, settings):
        settings.register_type('multioptions', MultiChoiceOptions)
        settings.register_type('serieswhitelist', SeriesWhitelist)
        settings.register_type('favcharacterlist', FavCharacterList)
        settings.register_type('favsfxlist', FavSFXList)
        settings.add_json_panel('Display', self.config, 'settings.json')
        settings.add_json_panel('Sound', self.config, 'settings2.json')
        settings.add_json_panel('Other', self.config, 'settings3.json')
        settings.add_json_panel('Favorites', self.config, 'settings4.json')

    def set_user(self, user):
        self.user = user

    def get_user(self):
        return self.user

    def set_fav_chars(self, fav_chars):
        self.fav_chars = fav_chars

    def get_fav_chars(self):
        return self.fav_chars

    def set_fav_sfx(self, fav_sfx):
        self.fav_sfx = fav_sfx

    def get_fav_sfx(self):
        return self.fav_sfx

    def set_main_screen(self, scr):
        self.main_screen = scr

    def get_main_screen(self):
        return self.main_screen

    def set_user_handler(self, user_handler):
        self.user_handler = user_handler

    def get_user_handler(self):
        return self.user_handler

    def get_message_factory(self):
        return self.message_factory

    def on_stop(self):
        config = self.config
        self.set_graceful_flag(True)
        if self.main_screen:
            self.main_screen.on_stop()
        config.write()
        super(MysteryOnlineApp, self).on_stop()

    def on_start(self):
        config = self.config
        self.load_shortcuts()
        self.find_window_handle()
        self.load_cursor()
        self.set_cursor()
        if not self.was_last_exit_graceful():
            self.show_ungraceful_exit_popup()
        else:
            self.set_graceful_flag(False)
            config.write()
        App.get_running_app().open_settings()  # Necessary to not crash upon setting favorites outside settings
        App.get_running_app().close_settings()  # Maybe we'll find a better option one day
        super().on_start()

    def was_last_exit_graceful(self):
        graceful_exit = self.config.getboolean('other', 'graceful_exit')
        if graceful_exit:
            return True
        return False

    def show_ungraceful_exit_popup(self):
        popup = MOPopupYN('Ungraceful Exit', 'It seems MO closed unexpectedly last time.\n'
                                             'Do you wish to send us the error log?', [self.send_error_log, None])
        popup.open()

    def set_graceful_flag(self, boolean):
        self.config.set('other', 'graceful_exit', boolean)

    def send_error_log(self, *args):
        print("Waiting on that bot")

    def load_shortcuts(self):
        command_processor.load_shortcuts()

    def find_window_handle(self):
        if platform == 'win':
            import win32gui

        def callback(hwnd, window_title):
            if platform == 'win':
                if win32gui.GetWindowText(hwnd) == window_title:
                    self.window_handle = hwnd
        if platform == 'win':
            win32gui.EnumWindows(callback, 'MysteryOnline')

    def get_window_handle(self):
        return self.window_handle

    def load_cursor(self):
        if platform == 'win':
            import win32gui
            import win32con
            try:
                self.cursor = win32gui.LoadImage(0, 'cursor.cur', win32con.IMAGE_CURSOR, 0, 0, win32con.LR_LOADFROMFILE)
        # TODO too broad an exception
            except:
                self.cursor = 'default'
        else:
            self.cursor = 'default'

    def reset_cursor(self, *args):
        if platform == 'win':
            import win32gui
            win32gui.SetCursor(self.cursor)

    def set_cursor(self):
        if self.cursor != 'default':
            Window.bind(mouse_pos=self.reset_cursor)
            Window.bind(on_motion=self.reset_cursor)


if __name__ == "__main__":
    MysteryOnlineApp().run()

__all__ = ['set_kivy_config', 'LoginScreen', 'MainScreen', 'Icon', 'IconsLayout', 'OOCWindow', 'OOCLogLabel',
           'LogLabel', 'LogWindow', 'SpriteSettings', 'SpriteWindow', 'SpritePreview', 'TextBox', 'MainTextInput',
           'Toolbar', 'LeftTab']
