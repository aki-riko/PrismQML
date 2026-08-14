# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Build manually curated Gallery locale catalogs. 构建人工校订的 Gallery 语言目录。"""

from __future__ import annotations

import json
import re
from pathlib import Path

if __package__:
    from ._manual_gallery_locale_data import LOCALE_DATA
else:
    from _manual_gallery_locale_data import LOCALE_DATA


ROOT = Path(__file__).resolve().parents[3]
I18N_ROOT = ROOT / "prismqml" / "PrismQML" / "i18n"
PROTECTED_TERMS = (
    "PrismQML", "Gallery", "C++", "DRY", "GitHub Releases", "GitHub", "Release",
    "Updater", "UpdateDialog", "ProgressDialog", "Toast", "InfoBar", "Inno Setup",
    "ToolButton", "PushButton", "Button", "PipsPager", "HorizontalPipsPager",
    "VerticalPipsPager", "Carousel", "FlowLayout", "MatrixRain", "TeachingTip",
    "TeachingTour", "StateWidget", "DateTimePicker", "ScrollBar", "ShortcutEditor",
    "AvatarSelector", "Badge", "ContextMenu", "ImageWidget", "Timeline", "ListView",
    "TableView", "TreeView", "BreadcrumbBar", "StackedWidget", "Stepper", "DWM",
    "Windows", "DPI", "Mica", "API", "QML", "ISS",
)
PHRASE_REPLACEMENTS = {
    "de": {
        "Operation successful": "Vorgang erfolgreich", "Operation failed": "Vorgang fehlgeschlagen",
        "Check failed:": "Prüfung fehlgeschlagen:", "Not configured": "Nicht konfiguriert",
        "Auto Update": "Automatische Aktualisierung", "About": "Über", "Help": "Hilfe",
        "All": "Alle", "Name": "Name", "Home": "Startseite", "Profile": "Profil",
        "Data display": "Datenanzeige", "Update pipeline": "Aktualisierungsablauf",
        "Today’s schedule": "Heutiger Zeitplan", "To-do items": "Aufgaben",
        "Sales ranking": "Verkaufsrangliste", "Interface language": "Oberflächensprache",
        "Startup behavior": "Startverhalten", "Minimize to tray": "In den Infobereich minimieren",
        "Follow system": "Systemeinstellung verwenden", "Dark": "Dunkel", "Light": "Hell",
        "Please select": "Bitte auswählen", "Loading components...": "Komponenten werden geladen...",
        "Synchronizing data...": "Daten werden synchronisiert...", "Synchronizing...": "Synchronisieren...",
        "Synchronizing": "Synchronisieren", "Uploading...": "Hochladen...", "Uploading": "Hochladen",
        "Completed": "Abgeschlossen", "Modified": "Geändert", "Selected": "Ausgewählt",
        "Selected:": "Ausgewählt:", "Copyable": "Kopierbar", "Copyable content": "Kopierbarer Inhalt",
    },
    "fr": {
        "Operation successful": "Opération réussie", "Operation failed": "Échec de l’opération",
        "Check failed:": "Échec de la vérification :", "Not configured": "Non configuré",
        "Auto Update": "Mise à jour automatique", "About": "À propos", "Help": "Aide", "All": "Tout",
        "Name": "Nom", "Home": "Accueil", "Profile": "Profil", "Data display": "Affichage des données",
        "Update pipeline": "Processus de mise à jour", "Today’s schedule": "Programme du jour",
        "To-do items": "Tâches", "Sales ranking": "Classement des ventes",
        "Interface language": "Langue de l’interface", "Startup behavior": "Comportement au démarrage",
        "Minimize to tray": "Réduire dans la zone de notification", "Follow system": "Suivre le système",
        "Dark": "Sombre", "Light": "Clair", "Please select": "Veuillez sélectionner",
        "Loading components...": "Chargement des composants...", "Synchronizing data...": "Synchronisation des données...",
        "Synchronizing...": "Synchronisation...", "Synchronizing": "Synchronisation",
        "Uploading...": "Téléversement...", "Uploading": "Téléversement", "Completed": "Terminé",
        "Modified": "Modifié", "Selected": "Sélectionné", "Selected:": "Sélectionné :",
        "Copyable": "Copiable", "Copyable content": "Contenu copiable",
    },
    "es": {
        "Operation successful": "Operación correcta", "Operation failed": "Operación fallida",
        "Check failed:": "Error de comprobación:", "Not configured": "Sin configurar",
        "Auto Update": "Actualización automática", "About": "Acerca de", "Help": "Ayuda", "All": "Todo",
        "Name": "Nombre", "Home": "Inicio", "Profile": "Perfil", "Data display": "Visualización de datos",
        "Update pipeline": "Flujo de actualización", "Today’s schedule": "Agenda de hoy",
        "To-do items": "Tareas pendientes", "Sales ranking": "Clasificación de ventas",
        "Interface language": "Idioma de la interfaz", "Startup behavior": "Comportamiento al iniciar",
        "Minimize to tray": "Minimizar a la bandeja", "Follow system": "Seguir el sistema",
        "Dark": "Oscuro", "Light": "Claro", "Please select": "Seleccione",
        "Loading components...": "Cargando componentes...", "Synchronizing data...": "Sincronizando datos...",
        "Synchronizing...": "Sincronizando...", "Synchronizing": "Sincronizando",
        "Uploading...": "Subiendo...", "Uploading": "Subiendo", "Completed": "Completado",
        "Modified": "Modificado", "Selected": "Seleccionado", "Selected:": "Seleccionado:",
        "Copyable": "Copiable", "Copyable content": "Contenido copiable",
    },
    "it": {
        "Operation successful": "Operazione riuscita", "Operation failed": "Operazione fallita",
        "Check failed:": "Controllo non riuscito:", "Not configured": "Non configurato",
        "Auto Update": "Aggiornamento automatico", "About": "Informazioni", "Help": "Aiuto", "All": "Tutto",
        "Name": "Nome", "Home": "Home", "Profile": "Profilo", "Data display": "Visualizzazione dati",
        "Update pipeline": "Flusso di aggiornamento", "Today’s schedule": "Programma di oggi",
        "To-do items": "Attività", "Sales ranking": "Classifica vendite", "Interface language": "Lingua interfaccia",
        "Startup behavior": "Comportamento all’avvio", "Minimize to tray": "Riduci nell’area di notifica",
        "Follow system": "Segui il sistema", "Dark": "Scuro", "Light": "Chiaro",
        "Please select": "Seleziona", "Loading components...": "Caricamento componenti...",
        "Synchronizing data...": "Sincronizzazione dati...", "Synchronizing...": "Sincronizzazione...",
        "Synchronizing": "Sincronizzazione", "Uploading...": "Caricamento...", "Uploading": "Caricamento",
        "Completed": "Completato", "Modified": "Modificato", "Selected": "Selezionato",
        "Selected:": "Selezionato:", "Copyable": "Copiabile", "Copyable content": "Contenuto copiabile",
    },
    "pt": {
        "Operation successful": "Operação bem-sucedida", "Operation failed": "Falha na operação",
        "Check failed:": "Falha na verificação:", "Not configured": "Não configurado",
        "Auto Update": "Atualização automática", "About": "Sobre", "Help": "Ajuda", "All": "Tudo",
        "Name": "Nome", "Home": "Início", "Profile": "Perfil", "Data display": "Exibição de dados",
        "Update pipeline": "Fluxo de atualização", "Today’s schedule": "Agenda de hoje",
        "To-do items": "Tarefas", "Sales ranking": "Classificação de vendas",
        "Interface language": "Idioma da interface", "Startup behavior": "Comportamento ao iniciar",
        "Minimize to tray": "Minimizar para a bandeja", "Follow system": "Seguir o sistema",
        "Dark": "Escuro", "Light": "Claro", "Please select": "Selecione",
        "Loading components...": "Carregando componentes...", "Synchronizing data...": "Sincronizando dados...",
        "Synchronizing...": "Sincronizando...", "Synchronizing": "Sincronizando",
        "Uploading...": "Enviando...", "Uploading": "Enviando", "Completed": "Concluído",
        "Modified": "Modificado", "Selected": "Selecionado", "Selected:": "Selecionado:",
        "Copyable": "Copiável", "Copyable content": "Conteúdo copiável",
    },
    "nl": {
        "Operation successful": "Bewerking geslaagd", "Operation failed": "Bewerking mislukt",
        "Check failed:": "Controle mislukt:", "Not configured": "Niet geconfigureerd",
        "Auto Update": "Automatisch bijwerken", "About": "Over", "Help": "Help", "All": "Alles",
        "Name": "Naam", "Home": "Start", "Profile": "Profiel", "Data display": "Gegevensweergave",
        "Update pipeline": "Updateproces", "Today’s schedule": "Planning van vandaag", "To-do items": "Taken",
        "Sales ranking": "Verkoopranglijst", "Interface language": "Interfacetaal",
        "Startup behavior": "Opstartgedrag", "Minimize to tray": "Minimaliseren naar systeemvak",
        "Follow system": "Systeem volgen", "Dark": "Donker", "Light": "Licht",
        "Please select": "Selecteer", "Loading components...": "Componenten laden...",
        "Synchronizing data...": "Gegevens synchroniseren...", "Synchronizing...": "Synchroniseren...",
        "Synchronizing": "Synchroniseren", "Uploading...": "Uploaden...", "Uploading": "Uploaden",
        "Completed": "Voltooid", "Modified": "Gewijzigd", "Selected": "Geselecteerd",
        "Selected:": "Geselecteerd:", "Copyable": "Kopieerbaar", "Copyable content": "Kopieerbare inhoud",
    },
    "pl": {
        "Operation successful": "Operacja zakończona powodzeniem", "Operation failed": "Operacja nie powiodła się",
        "Check failed:": "Sprawdzanie nie powiodło się:", "Not configured": "Nie skonfigurowano",
        "Auto Update": "Automatyczna aktualizacja", "About": "Informacje", "Help": "Pomoc", "All": "Wszystko",
        "Name": "Nazwa", "Home": "Strona główna", "Profile": "Profil", "Data display": "Wyświetlanie danych",
        "Update pipeline": "Proces aktualizacji", "Today’s schedule": "Dzisiejszy harmonogram",
        "To-do items": "Zadania", "Sales ranking": "Ranking sprzedaży", "Interface language": "Język interfejsu",
        "Startup behavior": "Zachowanie przy uruchamianiu", "Minimize to tray": "Minimalizuj do zasobnika",
        "Follow system": "Zgodnie z systemem", "Dark": "Ciemny", "Light": "Jasny",
        "Please select": "Wybierz", "Loading components...": "Ładowanie komponentów...",
        "Synchronizing data...": "Synchronizowanie danych...", "Synchronizing...": "Synchronizowanie...",
        "Synchronizing": "Synchronizowanie", "Uploading...": "Wysyłanie...", "Uploading": "Wysyłanie",
        "Completed": "Ukończono", "Modified": "Zmodyfikowano", "Selected": "Wybrano",
        "Selected:": "Wybrano:", "Copyable": "Można skopiować", "Copyable content": "Treść do skopiowania",
    },
    "tr": {
        "Operation successful": "İşlem başarılı", "Operation failed": "İşlem başarısız",
        "Check failed:": "Kontrol başarısız:", "Not configured": "Yapılandırılmadı",
        "Auto Update": "Otomatik güncelleme", "About": "Hakkında", "Help": "Yardım", "All": "Tümü",
        "Name": "Ad", "Home": "Ana sayfa", "Profile": "Profil", "Data display": "Veri görünümü",
        "Update pipeline": "Güncelleme akışı", "Today’s schedule": "Bugünün programı", "To-do items": "Yapılacaklar",
        "Sales ranking": "Satış sıralaması", "Interface language": "Arayüz dili",
        "Startup behavior": "Başlangıç davranışı", "Minimize to tray": "Sistem tepsisine küçült",
        "Follow system": "Sistemi izle", "Dark": "Koyu", "Light": "Açık", "Please select": "Lütfen seçin",
        "Loading components...": "Bileşenler yükleniyor...", "Synchronizing data...": "Veriler eşitleniyor...",
        "Synchronizing...": "Eşitleniyor...", "Synchronizing": "Eşitleniyor", "Uploading...": "Yükleniyor...",
        "Uploading": "Yükleniyor", "Completed": "Tamamlandı", "Modified": "Değiştirildi",
        "Selected": "Seçili", "Selected:": "Seçili:", "Copyable": "Kopyalanabilir",
        "Copyable content": "Kopyalanabilir içerik",
    },
    "id": {
        "Operation successful": "Operasi berhasil", "Operation failed": "Operasi gagal",
        "Check failed:": "Pemeriksaan gagal:", "Not configured": "Belum dikonfigurasi",
        "Auto Update": "Pembaruan otomatis", "About": "Tentang", "Help": "Bantuan", "All": "Semua",
        "Name": "Nama", "Home": "Beranda", "Profile": "Profil", "Data display": "Tampilan data",
        "Update pipeline": "Alur pembaruan", "Today’s schedule": "Jadwal hari ini", "To-do items": "Daftar tugas",
        "Sales ranking": "Peringkat penjualan", "Interface language": "Bahasa antarmuka",
        "Startup behavior": "Perilaku saat mulai", "Minimize to tray": "Minimalkan ke baki sistem",
        "Follow system": "Ikuti sistem", "Dark": "Gelap", "Light": "Terang", "Please select": "Silakan pilih",
        "Loading components...": "Memuat komponen...", "Synchronizing data...": "Menyinkronkan data...",
        "Synchronizing...": "Menyinkronkan...", "Synchronizing": "Menyinkronkan",
        "Uploading...": "Mengunggah...", "Uploading": "Mengunggah", "Completed": "Selesai",
        "Modified": "Diubah", "Selected": "Dipilih", "Selected:": "Dipilih:", "Copyable": "Dapat disalin",
        "Copyable content": "Konten dapat disalin",
    },
    "vi": {
        "Operation successful": "Thao tác thành công", "Operation failed": "Thao tác thất bại",
        "Check failed:": "Kiểm tra thất bại:", "Not configured": "Chưa cấu hình",
        "Auto Update": "Tự động cập nhật", "About": "Giới thiệu", "Help": "Trợ giúp", "All": "Tất cả",
        "Name": "Tên", "Home": "Trang chủ", "Profile": "Hồ sơ", "Data display": "Hiển thị dữ liệu",
        "Update pipeline": "Quy trình cập nhật", "Today’s schedule": "Lịch hôm nay", "To-do items": "Việc cần làm",
        "Sales ranking": "Xếp hạng doanh số", "Interface language": "Ngôn ngữ giao diện",
        "Startup behavior": "Hành vi khi khởi động", "Minimize to tray": "Thu nhỏ vào khay hệ thống",
        "Follow system": "Theo hệ thống", "Dark": "Tối", "Light": "Sáng", "Please select": "Vui lòng chọn",
        "Loading components...": "Đang tải thành phần...", "Synchronizing data...": "Đang đồng bộ dữ liệu...",
        "Synchronizing...": "Đang đồng bộ...", "Synchronizing": "Đang đồng bộ", "Uploading...": "Đang tải lên...",
        "Uploading": "Đang tải lên", "Completed": "Đã hoàn thành", "Modified": "Đã sửa",
        "Selected": "Đã chọn", "Selected:": "Đã chọn:", "Copyable": "Có thể sao chép",
        "Copyable content": "Nội dung có thể sao chép",
    },
    "ru": {
        "Operation successful": "Операция выполнена", "Operation failed": "Операция не удалась",
        "Check failed:": "Ошибка проверки:", "Not configured": "Не настроено", "Auto Update": "Автообновление",
        "About": "О программе", "Help": "Справка", "All": "Все", "Name": "Название", "Home": "Главная",
        "Profile": "Профиль", "Data display": "Отображение данных", "Update pipeline": "Процесс обновления",
        "Today’s schedule": "План на сегодня", "To-do items": "Задачи", "Sales ranking": "Рейтинг продаж",
        "Interface language": "Язык интерфейса", "Startup behavior": "Поведение при запуске",
        "Minimize to tray": "Свернуть в область уведомлений", "Follow system": "Как в системе",
        "Dark": "Тёмная", "Light": "Светлая", "Please select": "Выберите",
        "Loading components...": "Загрузка компонентов...", "Synchronizing data...": "Синхронизация данных...",
        "Synchronizing...": "Синхронизация...", "Synchronizing": "Синхронизация",
        "Uploading...": "Отправка...", "Uploading": "Отправка", "Completed": "Завершено",
        "Modified": "Изменено", "Selected": "Выбрано", "Selected:": "Выбрано:",
        "Copyable": "Можно скопировать", "Copyable content": "Копируемое содержимое",
    },
    "uk": {
        "Operation successful": "Операцію виконано", "Operation failed": "Операція не вдалася",
        "Check failed:": "Помилка перевірки:", "Not configured": "Не налаштовано",
        "Auto Update": "Автоматичне оновлення", "About": "Про програму", "Help": "Довідка", "All": "Усе",
        "Name": "Назва", "Home": "Головна", "Profile": "Профіль", "Data display": "Відображення даних",
        "Update pipeline": "Процес оновлення", "Today’s schedule": "План на сьогодні", "To-do items": "Завдання",
        "Sales ranking": "Рейтинг продажів", "Interface language": "Мова інтерфейсу",
        "Startup behavior": "Поведінка під час запуску", "Minimize to tray": "Згорнути до системного лотка",
        "Follow system": "Як у системі", "Dark": "Темна", "Light": "Світла", "Please select": "Виберіть",
        "Loading components...": "Завантаження компонентів...", "Synchronizing data...": "Синхронізація даних...",
        "Synchronizing...": "Синхронізація...", "Synchronizing": "Синхронізація",
        "Uploading...": "Надсилання...", "Uploading": "Надсилання", "Completed": "Завершено",
        "Modified": "Змінено", "Selected": "Вибрано", "Selected:": "Вибрано:",
        "Copyable": "Можна копіювати", "Copyable content": "Вміст для копіювання",
    },
    "ja": {
        "Operation successful": "操作に成功しました", "Operation failed": "操作に失敗しました",
        "Check failed:": "確認に失敗しました：", "Not configured": "未設定", "Auto Update": "自動更新",
        "About": "概要", "Help": "ヘルプ", "All": "すべて", "Name": "名前", "Home": "ホーム",
        "Profile": "プロフィール", "Data display": "データ表示", "Update pipeline": "更新フロー",
        "Today’s schedule": "今日の予定", "To-do items": "タスク", "Sales ranking": "売上ランキング",
        "Interface language": "表示言語", "Startup behavior": "起動時の動作",
        "Minimize to tray": "システムトレイに最小化", "Follow system": "システムに従う",
        "Dark": "ダーク", "Light": "ライト", "Please select": "選択してください",
        "Loading components...": "コンポーネントを読み込み中...", "Synchronizing data...": "データを同期中...",
        "Synchronizing...": "同期中...", "Synchronizing": "同期中", "Uploading...": "アップロード中...",
        "Uploading": "アップロード中", "Completed": "完了", "Modified": "変更済み", "Selected": "選択済み",
        "Selected:": "選択：", "Copyable": "コピー可能", "Copyable content": "コピー可能な内容",
    },
    "ko": {
        "Operation successful": "작업 성공", "Operation failed": "작업 실패", "Check failed:": "확인 실패:",
        "Not configured": "설정되지 않음", "Auto Update": "자동 업데이트", "About": "정보", "Help": "도움말",
        "All": "모두", "Name": "이름", "Home": "홈", "Profile": "프로필", "Data display": "데이터 표시",
        "Update pipeline": "업데이트 흐름", "Today’s schedule": "오늘 일정", "To-do items": "할 일",
        "Sales ranking": "판매 순위", "Interface language": "인터페이스 언어",
        "Startup behavior": "시작 동작", "Minimize to tray": "시스템 트레이로 최소화",
        "Follow system": "시스템 설정 사용", "Dark": "어둡게", "Light": "밝게", "Please select": "선택하세요",
        "Loading components...": "컴포넌트를 로드하는 중...", "Synchronizing data...": "데이터 동기화 중...",
        "Synchronizing...": "동기화 중...", "Synchronizing": "동기화 중", "Uploading...": "업로드 중...",
        "Uploading": "업로드 중", "Completed": "완료", "Modified": "수정됨", "Selected": "선택됨",
        "Selected:": "선택:", "Copyable": "복사 가능", "Copyable content": "복사 가능한 내용",
    },
    "ar": {
        "Operation successful": "نجحت العملية", "Operation failed": "فشلت العملية", "Check failed:": "فشل التحقق:",
        "Not configured": "غير مهيأ", "Auto Update": "تحديث تلقائي", "About": "حول", "Help": "المساعدة",
        "All": "الكل", "Name": "الاسم", "Home": "الرئيسية", "Profile": "الملف الشخصي",
        "Data display": "عرض البيانات", "Update pipeline": "مسار التحديث", "Today’s schedule": "جدول اليوم",
        "To-do items": "المهام", "Sales ranking": "ترتيب المبيعات", "Interface language": "لغة الواجهة",
        "Startup behavior": "سلوك بدء التشغيل", "Minimize to tray": "تصغير إلى علبة النظام",
        "Follow system": "اتباع النظام", "Dark": "داكن", "Light": "فاتح", "Please select": "يرجى الاختيار",
        "Loading components...": "جارٍ تحميل المكوّنات...", "Synchronizing data...": "جارٍ مزامنة البيانات...",
        "Synchronizing...": "جارٍ المزامنة...", "Synchronizing": "جارٍ المزامنة",
        "Uploading...": "جارٍ الرفع...", "Uploading": "جارٍ الرفع", "Completed": "مكتمل",
        "Modified": "معدّل", "Selected": "محدد", "Selected:": "المحدد:", "Copyable": "قابل للنسخ",
        "Copyable content": "محتوى قابل للنسخ",
    },
    "hi": {
        "Operation successful": "कार्रवाई सफल", "Operation failed": "कार्रवाई विफल", "Check failed:": "जाँच विफल:",
        "Not configured": "कॉन्फ़िगर नहीं है", "Auto Update": "स्वचालित अपडेट", "About": "परिचय",
        "Help": "सहायता", "All": "सभी", "Name": "नाम", "Home": "होम", "Profile": "प्रोफ़ाइल",
        "Data display": "डेटा प्रदर्शन", "Update pipeline": "अपडेट प्रवाह", "Today’s schedule": "आज का कार्यक्रम",
        "To-do items": "कार्य सूची", "Sales ranking": "बिक्री रैंकिंग", "Interface language": "इंटरफ़ेस भाषा",
        "Startup behavior": "स्टार्टअप व्यवहार", "Minimize to tray": "सिस्टम ट्रे में छोटा करें",
        "Follow system": "सिस्टम के अनुसार", "Dark": "गहरा", "Light": "हल्का", "Please select": "कृपया चुनें",
        "Loading components...": "घटक लोड हो रहे हैं...", "Synchronizing data...": "डेटा सिंक हो रहा है...",
        "Synchronizing...": "सिंक हो रहा है...", "Synchronizing": "सिंक हो रहा है",
        "Uploading...": "अपलोड हो रहा है...", "Uploading": "अपलोड हो रहा है", "Completed": "पूर्ण",
        "Modified": "संशोधित", "Selected": "चयनित", "Selected:": "चयनित:", "Copyable": "कॉपी करने योग्य",
        "Copyable content": "कॉपी करने योग्य सामग्री",
    },
    "th": {
        "Operation successful": "ดำเนินการสำเร็จ", "Operation failed": "การดำเนินการล้มเหลว",
        "Check failed:": "ตรวจสอบล้มเหลว:", "Not configured": "ยังไม่ได้กำหนดค่า",
        "Auto Update": "อัปเดตอัตโนมัติ", "About": "เกี่ยวกับ", "Help": "วิธีใช้", "All": "ทั้งหมด",
        "Name": "ชื่อ", "Home": "หน้าแรก", "Profile": "โปรไฟล์", "Data display": "การแสดงข้อมูล",
        "Update pipeline": "ขั้นตอนการอัปเดต", "Today’s schedule": "กำหนดการวันนี้", "To-do items": "งานที่ต้องทำ",
        "Sales ranking": "อันดับยอดขาย", "Interface language": "ภาษาของอินเทอร์เฟซ",
        "Startup behavior": "การทำงานเมื่อเริ่มต้น", "Minimize to tray": "ย่อไปยังถาดระบบ",
        "Follow system": "ตามระบบ", "Dark": "มืด", "Light": "สว่าง", "Please select": "โปรดเลือก",
        "Loading components...": "กำลังโหลดคอมโพเนนต์...", "Synchronizing data...": "กำลังซิงค์ข้อมูล...",
        "Synchronizing...": "กำลังซิงค์...", "Synchronizing": "กำลังซิงค์", "Uploading...": "กำลังอัปโหลด...",
        "Uploading": "กำลังอัปโหลด", "Completed": "เสร็จสมบูรณ์", "Modified": "แก้ไขแล้ว",
        "Selected": "เลือกแล้ว", "Selected:": "เลือกแล้ว:", "Copyable": "คัดลอกได้",
        "Copyable content": "เนื้อหาที่คัดลอกได้",
    },
}


def _replace_words(value: str, replacements: dict[str, str]) -> str:
    protected: dict[str, str] = {}
    result = value
    for index, term in enumerate(sorted(PROTECTED_TERMS, key=len, reverse=True)):
        marker = f"@@{index}@@"
        if term in result:
            protected[marker] = term
            result = result.replace(term, marker)
    for source, target in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        result = re.sub(rf"\b{re.escape(source)}\b", target, result, flags=re.IGNORECASE)
    for marker, term in protected.items():
        result = result.replace(marker, term)
    return result


def _localize_patterns(value: str, data: dict[str, object]) -> str:
    patterns = (
        (r"^Multi-select (\d+)$", lambda m: f"{data['multi']} {m.group(1)}"),
        (r"^Option (\d+)$", lambda m: f"{data['option']} {m.group(1)}"),
        (r"^Option ([A-Z])$", lambda m: f"{data['option']} {m.group(1)}"),
        (r"^Tag (\d+)$", lambda m: f"{data['tag']} {m.group(1)}"),
        (r"^Content (\d+)$", lambda m: f"{data['content']} {m.group(1)}"),
        (r"^Help (\d+)$", lambda m: f"{data['help']} {m.group(1)}"),
        (r"^Product ([A-E])$", lambda m: f"{data['product']} {m.group(1)}"),
    )
    for pattern, replacement in patterns:
        match = re.fullmatch(pattern, value)
        if match:
            return replacement(match)
    language = data["language"]
    if value in PHRASE_REPLACEMENTS.get(language, {}):
        return PHRASE_REPLACEMENTS[language][value]
    return _replace_words(value, data["replacements"])


def main() -> int:
    english = json.loads((I18N_ROOT / "en.json").read_text(encoding="utf-8"))
    source = json.loads((I18N_ROOT / "zh_CN.json").read_text(encoding="utf-8"))
    keys = [key for key in source if key.startswith("gallery_")]
    for language, data in LOCALE_DATA.items():
        data["language"] = language
        path = I18N_ROOT / f"{language}.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        existing = {
            key: catalog[key] for key in keys
            if catalog[key] != source[key]
        }
        for key in keys:
            catalog[key] = _localize_patterns(english[key], data)
        catalog.update(existing)
        phrases = PHRASE_REPLACEMENTS.get(language, {})
        for key in keys:
            if english[key] in phrases:
                catalog[key] = phrases[english[key]]
        path.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
