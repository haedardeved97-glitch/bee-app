from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
import json, os
from datetime import datetime, timedelta

# مسار البيانات
DATA_FILE = os.path.join(os.getcwd(), "hives.json")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"hives": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def toast(msg):
    MDSnackbar(MDSnackbarText(text=msg)).open()

class MainScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.data = load_data()
        self.build_ui()

    def build_ui(self):
        root = MDBoxLayout(orientation="vertical", padding=12, spacing=12)
        # شريط العنوان
        header = MDBoxLayout(size_hint_y=None, height="56dp", spacing=8)
        header.add_widget(MDIconButton(icon="bee", on_release=lambda x: None))
        header.add_widget(MDLabel(text="إدارة المنحل 🐝", font_style="H5", bold=True))
        root.add_widget(header)

        # قائمة الخلايا
        self.list_box = MDBoxLayout(orientation="vertical", spacing=8, adaptive_height=True)
        scroll = MDScrollView()
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)
        self.refresh_list()

        # زر الإضافة
        add_btn = MDButton(MDButtonText(text="➕ إضافة خلية جديدة"), style="filled", size_hint=(1, None), height="50dp")
        add_btn.bind(on_release=self.open_add_dialog)
        root.add_widget(add_btn)
        self.add_widget(root)

    def refresh_list(self):
        self.list_box.clear_widgets()
        if not self.data["hives"]:
            self.list_box.add_widget(MDLabel(text="لا توجد خلايا بعد. أضف واحدة!", halign="center"))
            return
        for h in self.data["hives"]:
            card = MDCard(orientation="vertical", padding=12, spacing=6, size_hint_y=None, height="130dp", ripple_behavior=True)
            card.add_widget(MDLabel(text=f"🐝 {h['name']}", font_style="H6", bold=True))
            card.add_widget(MDLabel(text=f"📍 {h['location']} | 👑 ملكة: {h['queen_year'] or '؟'}"))
            card.add_widget(MDLabel(text=f"📅 الفحص القادم: {h['next_inspection']}"))
            row = MDBoxLayout(spacing=8, size_hint_y=None, height="40dp")
            b1 = MDButton(MDButtonText(text="فحص"), style="tonal")
            b1.bind(on_release=lambda x, hid=h['id']: self.open_inspect_dialog(hid))
            b2 = MDButton(MDButtonText(text="تفاصيل"), style="tonal")
            b2.bind(on_release=lambda x, hid=h['id']: self.show_details(hid))
            row.add_widget(b1); row.add_widget(b2)
            card.add_widget(row)
            self.list_box.add_widget(card)

    def open_add_dialog(self):
        self.name_field = MDTextField(MDTextFieldHintText(text="اسم الخلية"))
        self.loc_field = MDTextField(MDTextFieldHintText(text="الموقع"))
        self.queen_field = MDTextField(MDTextFieldHintText(text="سنة الملكة (اختياري)"))
        content = MDBoxLayout(orientation="vertical", spacing=12, adaptive_height=True)
        for f in (self.name_field, self.loc_field, self.queen_field):
            content.add_widget(f)
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="خلية جديدة"),
            MDDialogSupportingText(text="أدخل بيانات الخلية"),
            content,
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="إلغاء"), on_release=lambda x: self.dialog.dismiss()),
                MDButton(MDButtonText(text="حفظ"), on_release=self.save_hive),
            ),
        )
        self.dialog.open()

    def save_hive(self, *args):
        name = self.name_field.text.strip()
        if not name:
            toast("اسم الخلية مطلوب")
            return
        hive = {
            "id": (max([h["id"] for h in self.data["hives"]], default=0) + 1),
            "name": name,
            "location": self.loc_field.text.strip(),
            "queen_year": self.queen_field.text.strip(),
            "created": str(datetime.now().date()),
            "inspections": [],
            "next_inspection": str((datetime.now() + timedelta(days=10)).date()),
        }
        self.data["hives"].append(hive)
        save_data(self.data)
        self.dialog.dismiss()
        self.refresh_list()
        toast(f"أُضيفت {name} ✅")

    def open_inspect_dialog(self, hid):
        hive = next(h for h in self.data["hives"] if h["id"] == hid)
        self.current_hid = hid
        self.queen_in = MDTextField(MDTextFieldHintText(text="حالة الملكة"))
        self.brood_in = MDTextField(MDTextFieldHintText(text="الحضنة"))
        self.dis_in = MDTextField(MDTextFieldHintText(text="أمراض (لا شيء/فاروا...)"))
        content = MDBoxLayout(orientation="vertical", spacing=12, adaptive_height=True)
        for f in (self.queen_in, self.brood_in, self.dis_in):
            content.add_widget(f)
        self.inspect_dialog = MDDialog(
            MDDialogHeadlineText(text=f"فحص: {hive['name']}"),
            content,
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="إلغاء"), on_release=lambda x: self.inspect_dialog.dismiss()),
                MDButton(MDButtonText(text="حفظ"), on_release=self.save_inspection),
            ),
        )
        self.inspect_dialog.open()

    def save_inspection(self, *args):
        hive = next(h for h in self.data["hives"] if h["id"] == self.current_hid)
        hive["inspections"].append({
            "date": str(datetime.now().date()),
            "queen": self.queen_in.text or "-",
            "brood": self.brood_in.text or "-",
            "disease": self.dis_in.text or "-",
        })
        hive["next_inspection"] = str((datetime.now() + timedelta(days=10)).date())
        save_data(self.data)
        self.inspect_dialog.dismiss()
        self.refresh_list()
        toast("سُجل الفحص ✅")

    def show_details(self, hid):
        hive = next(h for h in self.data["hives"] if h["id"] == hid)
        lines = [f"🐝 {hive['name']}", f"📍 {hive['location']}", f"👑 {hive['queen_year'] or '؟'}", "— الفحوصات —"]
        if not hive["inspections"]:
            lines.append("لا فحوصات.")
        for i, ins in enumerate(hive["inspections"], 1):
            lines.append(f"{i}. {ins['date']} | ملكة:{ins['queen']} | حضنة:{ins['brood']} | {ins['disease']}")
        d = MDDialog(
            MDDialogHeadlineText(text="التفاصيل"),
            MDDialogSupportingText(text="\n".join(lines)),
            MDDialogButtonContainer(MDButton(MDButtonText(text="إغلاق"), on_release=lambda x: d.dismiss())),
        )
        d.open()

class BeeApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Amber"
        self.theme_cls.theme_style = "Light"
        sm = MDScreenManager()
        sm.add_widget(MainScreen(name="main"))
        return sm

if __name__ == "__main__":
    BeeApp().run()
