import os
import json
import threading
import urllib.request
import urllib.parse
import urllib.error
import mimetypes
import uuid

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView


# =========================================================
# Y MESSENGER KIVY
# =========================================================

# روی لپ‌تاپ:
SERVER = "http://127.0.0.1:5000"

# اگر APK روی گوشی باشد، این را بعداً به IP لپ‌تاپ تغییر می‌دهیم.
# مثال:
# SERVER = "http://192.168.1.5:5000"


KV = """

#:import dp kivy.metrics.dp

<BlueButton@Button>:
    size_hint_y: None
    height: dp(48)
    background_normal: ""
    background_color: app.main_color
    color: 1,1,1,1

<YInput@TextInput>:
    size_hint_y: None
    height: dp(48)
    multiline: False
    background_normal: ""
    background_color: app.input_color
    foreground_color: 1,1,1,1
    padding: dp(12),dp(12)


<LoginScreen>:

    BoxLayout:
        orientation: "vertical"
        padding: dp(25)
        spacing: dp(12)

        Widget:
            size_hint_y: .3

        Label:
            text: "Y MESSENGER"
            font_size: dp(30)
            bold: True
            color: app.main_color
            size_hint_y: None
            height: dp(55)

        Label:
            text: "ورود به حساب"
            size_hint_y: None
            height: dp(40)

        YInput:
            id: username
            hint_text: "نام کاربری"

        YInput:
            id: password
            hint_text: "رمز عبور"
            password: True

        BlueButton:
            text: "ورود"
            on_release: root.login()

        Button:
            text: "ثبت‌نام"
            size_hint_y: None
            height: dp(45)
            background_normal: ""
            background_color: 0,0,0,0
            color: app.main_color
            on_release: app.root.current = "register"

        Widget:


<RegisterScreen>:

    BoxLayout:
        orientation: "vertical"
        padding: dp(25)
        spacing: dp(12)

        Widget:
            size_hint_y: .15

        Label:
            text: "ساخت حساب"
            font_size: dp(28)
            bold: True
            color: app.main_color
            size_hint_y: None
            height: dp(55)

        YInput:
            id: username
            hint_text: "نام کاربری"

        YInput:
            id: password
            hint_text: "رمز عبور"
            password: True

        YInput:
            id: bio
            hint_text: "بیوگرافی"

        BlueButton:
            text: "ثبت‌نام"
            on_release: root.register()

        Button:
            text: "بازگشت"
            size_hint_y: None
            height: dp(45)
            background_normal: ""
            background_color: 0,0,0,0
            color: app.main_color
            on_release: app.root.current = "login"

        Widget:


<HomeScreen>:

    BoxLayout:
        orientation: "vertical"

        BoxLayout:
            size_hint_y: None
            height: dp(60)
            padding: dp(7)
            spacing: dp(7)

            Label:
                text: "Y MESSENGER"
                font_size: dp(20)
                bold: True
                color: app.main_color

            Button:
                text: "⚙"
                size_hint_x: None
                width: dp(50)
                background_normal: ""
                background_color: app.main_color
                on_release: root.open_settings()

            Button:
                text: "خروج"
                size_hint_x: None
                width: dp(60)
                background_normal: ""
                background_color: .65,.1,.1,1
                on_release: root.logout()

        YInput:
            id: search
            hint_text: "جستجوی کاربر..."
            on_text: root.search_users(self.text)

        ScrollView:
            do_scroll_x: False

            GridLayout:
                id: users_box
                cols: 1
                spacing: dp(5)
                padding: dp(8)
                size_hint_y: None
                height: self.minimum_height


<ChatScreen>:

    BoxLayout:
        orientation: "vertical"

        BoxLayout:
            size_hint_y: None
            height: dp(58)
            padding: dp(7)
            spacing: dp(7)

            Button:
                text: "‹"
                size_hint_x: None
                width: dp(50)
                background_normal: ""
                background_color: app.main_color
                on_release: root.back_home()

            Label:
                text: root.chat_user
                font_size: dp(19)
                bold: True

        ScrollView:
            id: scroll
            do_scroll_x: False

            GridLayout:
                id: messages_box
                cols: 1
                spacing: dp(5)
                padding: dp(10)
                size_hint_y: None
                height: self.minimum_height

        BoxLayout:
            size_hint_y: None
            height: dp(58)
            padding: dp(6)
            spacing: dp(6)

            TextInput:
                id: message
                multiline: False
                hint_text: "پیام..."
                background_normal: ""
                background_color: app.input_color
                foreground_color: 1,1,1,1
                padding: dp(10),dp(10)

            Button:
                text: "ارسال"
                size_hint_x: None
                width: dp(75)
                background_normal: ""
                background_color: app.main_color
                on_release: root.send_message()


<SettingsScreen>:

    BoxLayout:
        orientation: "vertical"
        padding: dp(15)
        spacing: dp(10)

        BoxLayout:
            size_hint_y: None
            height: dp(55)

            Button:
                text: "‹"
                size_hint_x: None
                width: dp(50)
                background_normal: ""
                background_color: app.main_color
                on_release: root.back()

            Label:
                text: "تنظیمات"
                font_size: dp(22)
                bold: True

        Label:
            text: "رنگ اصلی"

        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(5)

            Button:
                text: "آبی"
                background_normal: ""
                background_color: .1,.4,1,1
                on_release: root.set_color("#2196F3")

            Button:
                text: "بنفش"
                background_normal: ""
                background_color: .5,.1,1,1
                on_release: root.set_color("#8E44AD")

            Button:
                text: "سبز"
                background_normal: ""
                background_color: .1,.7,.3,1
                on_release: root.set_color("#00A884")

            Button:
                text: "قرمز"
                background_normal: ""
                background_color: .8,.1,.1,1
                on_release: root.set_color("#E53935")

        YInput:
            id: custom_color
            hint_text: "#2196F3"

        BlueButton:
            text: "اعمال رنگ سفارشی"
            on_release: root.custom_color()

        Label:
            text: "تاریکی"

        Slider:
            id: darkness
            min: 0
            max: 1
            value: root.darkness
            on_value: root.change_darkness(self.value)

        BlueButton:
            text: "انتخاب تصویر پس‌زمینه"
            on_release: root.choose_background()

        BlueButton:
            text: "حذف پس‌زمینه"
            on_release: root.delete_background()

        Widget:
"""


# =========================================================
# API
# =========================================================

def api_request(
    method,
    endpoint,
    data=None,
    token=None
):

    url = SERVER.rstrip("/") + endpoint

    headers = {
        "User-Agent":
            "Y-MESSENGER-KIVY/1.26.1.7"
    }

    body = None

    if token:
        headers["Authorization"] = (
            "Bearer " + token
        )

    if data is not None:

        body = json.dumps(
            data
        ).encode("utf-8")

        headers[
            "Content-Type"
        ] = "application/json"

    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:

            raw = response.read().decode(
                "utf-8"
            )

            if not raw:
                return {}

            return json.loads(raw)

    except urllib.error.HTTPError as error:

        try:

            raw = error.read().decode(
                "utf-8"
            )

            return json.loads(raw)

        except:

            return {
                "ok": False,
                "error":
                    "HTTP " +
                    str(error.code)
            }

    except Exception as error:

        print(
            "SERVER ERROR:",
            repr(error)
        )

        return {
            "ok": False,
            "error":
                "SERVER ERROR: " +
                repr(error)
        }


# =========================================================
# UPLOAD
# =========================================================

def upload_background(
    filepath,
    token
):

    try:

        boundary = uuid.uuid4().hex

        filename = os.path.basename(
            filepath
        )

        mime = mimetypes.guess_type(
            filename
        )[0]

        if not mime:
            mime = "application/octet-stream"

        with open(
            filepath,
            "rb"
        ) as file:

            file_data = file.read()

        body = []

        body.append(
            (
                "--" +
                boundary +
                "\r\n"
                'Content-Disposition: form-data; '
                'name="background"; '
                'filename="' +
                filename +
                '"\r\n'
                "Content-Type: " +
                mime +
                "\r\n\r\n"
            ).encode()
        )

        body.append(file_data)

        body.append(
            (
                "\r\n--" +
                boundary +
                "--\r\n"
            ).encode()
        )

        body = b"".join(body)

        request = urllib.request.Request(
            SERVER.rstrip("/") +
            "/api/theme/background",
            data=body,
            method="POST"
        )

        request.add_header(
            "Authorization",
            "Bearer " + token
        )

        request.add_header(
            "Content-Type",
            "multipart/form-data; boundary=" +
            boundary
        )

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            raw = response.read().decode(
                "utf-8"
            )

            return json.loads(raw)

    except Exception as error:

        return {
            "ok": False,
            "error": str(error)
        }


# =========================================================
# POPUP
# =========================================================

def popup(
    title,
    message
):

    Popup(
        title=title,
        content=Label(
            text=str(message),
            halign="center"
        ),
        size_hint=(.85, .35)
    ).open()


# =========================================================
# LOGIN
# =========================================================

class LoginScreen(Screen):

    def login(self):

        username = (
            self.ids.username.text.strip()
        )

        password = (
            self.ids.password.text
        )

        if not username or not password:

            popup(
                "خطا",
                "نام کاربری و رمز عبور را وارد کن."
            )

            return

        threading.Thread(
            target=self.do_login,
            args=(
                username,
                password
            ),
            daemon=True
        ).start()

    def do_login(
        self,
        username,
        password
    ):

        result = api_request(
            "POST",
            "/api/login",
            {
                "username": username,
                "password": password
            }
        )

        Clock.schedule_once(
            lambda dt:
                self.finish_login(result)
        )

    def finish_login(self, result):

        if not result.get("ok"):

            popup(
                "ورود ناموفق",
                result.get(
                    "error",
                    "ورود انجام نشد."
                )
            )

            return

        app = App.get_running_app()

        app.token = result.get(
            "token",
            ""
        )

        app.me = result.get(
            "user",
            {}
        )

        app.save_session()

        app.root.current = "home"

        app.root.get_screen(
            "home"
        ).load_users()


# =========================================================
# REGISTER
# =========================================================

class RegisterScreen(Screen):

    def register(self):

        username = (
            self.ids.username.text.strip()
        )

        password = (
            self.ids.password.text
        )

        bio = (
            self.ids.bio.text.strip()
        )

        if not username or not password:

            popup(
                "خطا",
                "نام کاربری و رمز عبور را وارد کن."
            )

            return

        threading.Thread(
            target=self.do_register,
            args=(
                username,
                password,
                bio
            ),
            daemon=True
        ).start()

    def do_register(
        self,
        username,
        password,
        bio
    ):

        result = api_request(
            "POST",
            "/api/register",
            {
                "username": username,
                "password": password,
                "bio": bio
            }
        )

        Clock.schedule_once(
            lambda dt:
                self.finish_register(result)
        )

    def finish_register(self, result):

        if not result.get("ok"):

            popup(
                "ثبت‌نام ناموفق",
                result.get(
                    "error",
                    "ثبت‌نام انجام نشد."
                )
            )

            return

        popup(
            "موفق",
            "حساب با موفقیت ساخته شد."
        )

        self.manager.current = "login"


# =========================================================
# HOME
# =========================================================

class HomeScreen(Screen):

    def on_enter(self):

        app = App.get_running_app()

        if app.token:
            self.load_users()

    def load_users(self):

        threading.Thread(
            target=self.get_users,
            daemon=True
        ).start()

    def get_users(self):

        app = App.get_running_app()

        result = api_request(
            "GET",
            "/api/users",
            token=app.token
        )

        Clock.schedule_once(
            lambda dt:
                self.show_users(result)
        )

    def search_users(self, text):

        text = text.strip()

        if not text:

            self.load_users()

            return

        threading.Thread(
            target=self.do_search,
            args=(text,),
            daemon=True
        ).start()

    def do_search(self, text):

        app = App.get_running_app()

        result = api_request(
            "GET",
            "/api/users/search?q=" +
            urllib.parse.quote(text),
            token=app.token
        )

        Clock.schedule_once(
            lambda dt:
                self.show_users(result)
        )

    def show_users(self, result):

        box = self.ids.users_box

        box.clear_widgets()

        if not result.get("ok"):

            popup(
                "خطا",
                result.get(
                    "error",
                    "کاربران دریافت نشدند."
                )
            )

            return

        users = result.get(
            "users",
            []
        )

        if not users:

            box.add_widget(
                Label(
                    text="کاربری پیدا نشد.",
                    size_hint_y=None,
                    height=50
                )
            )

            return

        for user in users:

            username = user.get(
                "username",
                ""
            )

            button = Button(
                text=username,
                size_hint_y=None,
                height=55,
                background_normal="",
                background_color=
                    App.get_running_app().main_color
            )

            button.bind(
                on_release=
                    lambda btn,
                    name=username:
                    self.open_chat(name)
            )

            box.add_widget(
                button
            )

    def open_chat(
        self,
        username
    ):

        screen = self.manager.get_screen(
            "chat"
        )

        screen.chat_user = username

        self.manager.current = "chat"

        screen.load_messages()

    def open_settings(self):

        self.manager.current = "settings"

    def logout(self):

        app = App.get_running_app()

        try:

            api_request(
                "POST",
                "/api/logout",
                token=app.token
            )

        except:
            pass

        app.token = ""
        app.me = {}

        app.clear_session()

        self.manager.current = "login"


# =========================================================
# CHAT
# =========================================================

class ChatScreen(Screen):

    chat_user = StringProperty("")

    def load_messages(self):

        if not self.chat_user:
            return

        threading.Thread(
            target=self.get_messages,
            daemon=True
        ).start()

    def get_messages(self):

        app = App.get_running_app()

        result = api_request(
            "GET",
            "/api/messages?username=" +
            urllib.parse.quote(
                self.chat_user
            ),
            token=app.token
        )

        Clock.schedule_once(
            lambda dt:
                self.show_messages(result)
        )

    def show_messages(self, result):

        box = self.ids.messages_box

        box.clear_widgets()

        if not result.get("ok"):

            popup(
                "خطا",
                result.get(
                    "error",
                    "پیام‌ها دریافت نشدند."
                )
            )

            return

        messages = result.get(
            "messages",
            []
        )

        for message in messages:

            sender = message.get(
                "sender",
                ""
            )

            text = message.get(
                "message",
                ""
            )

            label = Label(
                text=
                    sender +
                    ": " +
                    text,
                size_hint_y=None,
                height=45,
                halign="right"
            )

            box.add_widget(
                label
            )

        Clock.schedule_once(
            lambda dt:
                setattr(
                    self.ids.scroll,
                    "scroll_y",
                    0
                )
        )

    def send_message(self):

        text = (
            self.ids.message.text.strip()
        )

        if not text:
            return

        self.ids.message.text = ""

        threading.Thread(
            target=self.do_send,
            args=(text,),
            daemon=True
        ).start()

    def do_send(self, text):

        app = App.get_running_app()

        result = api_request(
            "POST",
            "/api/send",
            {
                "username":
                    self.chat_user,

                "message":
                    text
            },
            token=app.token
        )

        Clock.schedule_once(
            lambda dt:
                self.after_send(result)
        )

    def after_send(self, result):

        if not result.get("ok"):

            popup(
                "خطا",
                result.get(
                    "error",
                    "پیام ارسال نشد."
                )
            )

            return

        self.load_messages()

    def back_home(self):

        self.manager.current = "home"


# =========================================================
# SETTINGS
# =========================================================

class SettingsScreen(Screen):

    darkness = NumericProperty(0)

    def on_enter(self):

        self.load_theme()

    def load_theme(self):

        threading.Thread(
            target=self.get_theme,
            daemon=True
        ).start()

    def get_theme(self):

        app = App.get_running_app()

        result = api_request(
            "GET",
            "/api/theme",
            token=app.token
        )

        Clock.schedule_once(
            lambda dt:
                self.apply_theme(result)
        )

    def apply_theme(self, result):

        if not result.get("ok"):
            return

        theme = result.get(
            "theme",
            {}
        )

        color = theme.get(
            "main_color"
        )

        if color:
            App.get_running_app().set_color(
                color
            )

        self.darkness = float(
            theme.get(
                "darkness",
                0
            )
        )

    def set_color(self, color):

        app = App.get_running_app()

        app.set_color(color)

        threading.Thread(
            target=lambda:
                api_request(
                    "POST",
                    "/api/theme",
                    {
                        "main_color":
                            color
                    },
                    token=app.token
                ),
            daemon=True
        ).start()

    def custom_color(self):

        color = (
            self.ids.custom_color.text
            .strip()
        )

        if not color.startswith("#"):
            color = "#" + color

        if len(color) != 7:

            popup(
                "خطا",
                "مثال صحیح: #2196F3"
            )

            return

        try:

            int(color[1:], 16)

        except:

            popup(
                "خطا",
                "کد رنگ صحیح نیست."
            )

            return

        self.set_color(
            color
        )

    def change_darkness(
        self,
        value
    ):

        self.darkness = value

        app = App.get_running_app()

        threading.Thread(
            target=lambda:
                api_request(
                    "POST",
                    "/api/theme",
                    {
                        "darkness":
                            value
                    },
                    token=app.token
                ),
            daemon=True
        ).start()

    def choose_background(self):

        chooser = FileChooserListView(
            path=os.path.expanduser("~"),
            filters=[
                "*.png",
                "*.jpg",
                "*.jpeg",
                "*.webp"
            ]
        )

        popup_window = Popup(
            title="انتخاب تصویر",
            content=chooser,
            size_hint=(.95, .9)
        )

        def selected(
            instance,
            selection
        ):

            if not selection:
                return

            popup_window.dismiss()

            self.upload_background(
                selection[0]
            )

        chooser.bind(
            on_submit=selected
        )

        popup_window.open()

    def upload_background(
        self,
        filepath
    ):

        app = App.get_running_app()

        threading.Thread(
            target=lambda:
                upload_background(
                    filepath,
                    app.token
                ),
            daemon=True
        ).start()

        popup(
            "در حال ارسال",
            "تصویر در حال آپلود است..."
        )

    def delete_background(self):

        app = App.get_running_app()

        threading.Thread(
            target=lambda:
                api_request(
                    "DELETE",
                    "/api/theme/background",
                    token=app.token
                ),
            daemon=True
        ).start()

        popup(
            "انجام شد",
            "درخواست حذف پس‌زمینه ارسال شد."
        )

    def back(self):

        self.manager.current = "home"


# =========================================================
# APP
# =========================================================

class YMessengerApp(App):

    title = "Y MESSENGER"

    main_color = (
        0.129,
        0.588,
        0.953,
        1
    )

    input_color = (
        0.08,
        0.10,
        0.14,
        1
    )

    token = ""
    me = {}

    session_file = "ymessenger_session.json"

    def build(self):

        Builder.load_string(KV)

        from kivy.uix.screenmanager import ScreenManager

        manager = ScreenManager()

        manager.add_widget(
            LoginScreen(
                name="login"
            )
        )

        manager.add_widget(
            RegisterScreen(
                name="register"
            )
        )

        manager.add_widget(
            HomeScreen(
                name="home"
            )
        )

        manager.add_widget(
            ChatScreen(
                name="chat"
            )
        )

        manager.add_widget(
            SettingsScreen(
                name="settings"
            )
        )

        self.load_session()

        if self.token:
            manager.current = "home"
        else:
            manager.current = "login"

        return manager

    def set_color(
        self,
        color
    ):

        color = color.replace(
            "#",
            ""
        )

        try:

            r = int(
                color[0:2],
                16
            ) / 255

            g = int(
                color[2:4],
                16
            ) / 255

            b = int(
                color[4:6],
                16
            ) / 255

            self.main_color = (
                r,
                g,
                b,
                1
            )

        except:
            pass

    def session_path(self):

        return os.path.join(
            self.user_data_dir,
            self.session_file
        )

    def save_session(self):

        try:

            os.makedirs(
                self.user_data_dir,
                exist_ok=True
            )

            with open(
                self.session_path(),
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    {
                        "token":
                            self.token,

                        "me":
                            self.me
                    },
                    file,
                    ensure_ascii=False
                )

        except Exception as error:

            print(
                "SESSION SAVE ERROR:",
                error
            )

    def load_session(self):

        try:

            path = self.session_path()

            if not os.path.exists(path):
                return

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            self.token = data.get(
                "token",
                ""
            )

            self.me = data.get(
                "me",
                {}
            )

        except:

            self.token = ""
            self.me = {}

    def clear_session(self):

        try:

            path = self.session_path()

            if os.path.exists(path):
                os.remove(path)

        except:
            pass