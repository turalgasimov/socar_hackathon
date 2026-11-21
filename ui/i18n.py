"""UI text in Azerbaijani, English and Russian. English is the key and the fallback.

    python ui/i18n.py   # fails if any t("...") string in the app lacks an az or ru entry
"""
from __future__ import annotations

LANGS = {"az": "Azərbaycanca", "en": "English", "ru": "Русский"}

# English: (Azerbaijani, Russian). Placeholders in {} must survive translation unchanged.
TEXT = {
    # launcher
    "Home": ("Ana səhifə", "Главная"),
    "Load Data": ("Məlumat yüklə", "Загрузка данных"),
    "Raw sensor files, CSV or Excel": ("Xam sensor faylları, CSV və ya Excel", "Исходные файлы датчиков, CSV или Excel"),
    "Field Data": ("Mədən məlumatları", "Промысловые данные"),
    "Sensor history per well": ("Hər quyu üzrə sensor tarixçəsi", "История датчиков по скважинам"),
    "Production Rates": ("Hasilat debitləri", "Дебиты"),
    "Daily oil, water and gas (VFM)": ("Gündəlik neft, su və qaz (VFM)", "Суточные нефть, вода и газ (VFM)"),
    "Well Tests": ("Quyu sınaqları", "Исследования скважин"),
    "Build-up analysis (PTA)": ("Təzyiqin bərpası analizi (PTA)", "Анализ КВД (PTA)"),
    "Generate Graph": ("Qrafik qur", "Построить график"),
    "Any chart from the results": ("Nəticələrdən istənilən qrafik", "Любой график по результатам"),
    "Data Quality": ("Məlumat keyfiyyəti", "Качество данных"),
    "Cleaning report": ("Təmizləmə hesabatı", "Отчёт об очистке"),
    "Sample Data": ("Nümunə məlumat", "Демо-данные"),
    "Run on the hackathon field": ("Hakaton yatağı ilə işə sal", "Запуск на данных хакатона"),
    "Convert": ("Çevir", "Конвертер"),
    "CSV and Excel": ("CSV və Excel", "CSV и Excel"),
    "Settings": ("Ayarlar", "Настройки"),
    "Theme and language": ("Mövzu və dil", "Тема и язык"),
    "Export": ("İxrac", "Экспорт"),
    "Results and report": ("Nəticələr və hesabat", "Результаты и отчёт"),
    "Load data first": ("Əvvəlcə məlumat yükləyin", "Сначала загрузите данные"),
    "Sample data not found": ("Nümunə məlumat tapılmadı", "Демо-данные не найдены"),
    "History": ("Tarixçə", "История"),
    "Your uploads and files": ("Yükləmələriniz və fayllarınız", "Ваши загрузки и файлы"),
    "Help": ("Kömək", "Справка"),
    "How to use RizzML": ("RizzML-dən necə istifadə etməli", "Как пользоваться RizzML"),
    "Log out": ("Çıxış", "Выйти"),
    "Daily well rates and well-test analysis": ("Gündəlik quyu debitləri və quyu sınaqlarının analizi",
                                                "Суточные дебиты и анализ исследований скважин"),
    # sign-in
    "Sign in": ("Daxil ol", "Войти"),
    "Email": ("E-poçt", "Эл. почта"),
    "Password": ("Şifrə", "Пароль"),
    "Wrong email or password.": ("E-poçt və ya şifrə yanlışdır.", "Неверная почта или пароль."),
    # history
    "Upload": ("Yükləmə", "Загрузка"),
    "Analysis": ("Analiz", "Анализ"),
    "File": ("Fayl", "Файл"),
    "Open": ("Aç", "Открыть"),
    "Download": ("Endir", "Скачать"),
    "No longer available": ("Artıq mövcud deyil", "Больше недоступно"),
    "Nothing yet. Uploads, analyses and downloaded files appear here.":
        ("Hələ heç nə yoxdur. Yükləmələr, analizlər və endirilən fayllar burada görünəcək.",
         "Пока пусто. Здесь появятся загрузки, анализы и скачанные файлы."),
    "{source}: {wells} wells, {days} well-days, {shutins} build-ups":
        ("{source}: {wells} quyu, {days} quyu-gün, {shutins} bərpa əyrisi",
         "{source}: скважин {wells}, скважино-суток {days}, КВД {shutins}"),
    "Graph data": ("Qrafik məlumatı", "Данные графика"),
    "Converted": ("Çevrilmiş", "Конвертировано"),
    # load
    "Raw files": ("Xam fayllar", "Исходные файлы"),
    "(optional)": ("(istəyə bağlı)", "(необязательно)"),
    "Run analysis": ("Analizi başlat", "Запустить анализ"),
    "Run on sample data": ("Nümunə məlumatla başlat", "Запустить на демо-данных"),
    "Analysing…": ("Analiz edilir…", "Идёт анализ…"),
    "Preparing downloads": ("Yükləmələr hazırlanır", "Подготовка файлов"),
    "Analysis failed": ("Analiz alınmadı", "Анализ не выполнен"),
    "The data could not be analysed: {e}. Check that each file has the expected columns.":
        ("Məlumatı analiz etmək mümkün olmadı: {e}. Hər faylda lazımi sütunların olduğunu yoxlayın.",
         "Не удалось проанализировать данные: {e}. Проверьте, что в каждом файле есть нужные столбцы."),
    "No data analysed yet.": ("Hələ məlumat analiz edilməyib.", "Данные ещё не проанализированы."),
    "Cleaning per-minute sensor data (missing-value codes, duplicates, spikes)":
        ("Dəqiqəlik sensor məlumatları təmizlənir (boş dəyər kodları, təkrarlar, sıçrayışlar)",
         "Очистка поминутных данных датчиков (коды пропусков, дубликаты, выбросы)"),
    "Building daily inputs for every well": ("Hər quyu üçün gündəlik giriş məlumatları qurulur",
                                             "Подготовка суточных входных данных по каждой скважине"),
    "Predicting daily oil, water and gas rates with the trained model":
        ("Öyrədilmiş modellə gündəlik neft, su və qaz debitləri hesablanır",
         "Расчёт суточных дебитов нефти, воды и газа обученной моделью"),
    "Checking accuracy against the measured well tests": ("Dəqiqlik ölçülmüş quyu sınaqları ilə yoxlanılır",
                                                          "Проверка точности по замерам скважин"),
    "Finding shut-ins and interpreting each build-up (PTA)": ("Bağlanmalar tapılır və hər bərpa əyrisi şərh edilir (PTA)",
                                                              "Поиск остановок и интерпретация каждой КВД (PTA)"),
    "Summarising sensors for the charts": ("Qrafiklər üçün sensor məlumatları ümumiləşdirilir",
                                           "Подготовка данных датчиков для графиков"),
    # field data and sensors
    "Well": ("Quyu", "Скважина"),
    "Wells": ("Quyular", "Скважины"),
    "Sensors": ("Sensorlar", "Датчики"),
    "Wellhead pressure (psia)": ("Quyuağzı təzyiq (psia)", "Устьевое давление (psia)"),
    "Wellhead pressure, downstream of choke (psia)": ("Quyuağzı təzyiq, ştuserdən sonra (psia)",
                                                      "Устьевое давление после штуцера (psia)"),
    "Downhole pressure (psia)": ("Quyudibi təzyiq (psia)", "Забойное давление (psia)"),
    "Downhole temperature (°F)": ("Quyudibi temperatur (°F)", "Забойная температура (°F)"),
    "Annulus pressure (psia)": ("Həlqəvi fəza təzyiqi (psia)", "Затрубное давление (psia)"),
    "Gas-lift injection (Mscf/d)": ("Qazlift vurulması (Mscf/d)", "Закачка газлифтного газа (Mscf/d)"),
    # data quality
    "Rows received": ("Alınan sətirlər", "Получено строк"),
    "Rows after cleaning": ("Təmizləmədən sonra sətirlər", "Строк после очистки"),
    "Missing-value codes (-999.25) masked": ("Boş dəyər kodları (-999.25) çıxarıldı", "Скрыто кодов пропусков (-999.25)"),
    "Missing-value codes masked": ("Boş dəyər kodları çıxarıldı", "Скрыто кодов пропусков"),
    "Duplicate rows dropped": ("Təkrar sətirlər silindi", "Удалено дубликатов"),
    "Shut-in minutes": ("Bağlı qalma dəqiqələri", "Минут остановки"),
    "Well-days predicted": ("Hesablanmış quyu-günlər", "Рассчитано скважино-суток"),
    "Days with low sensor coverage (<80%)": ("Sensor örtüyü aşağı olan günlər (<80%)",
                                             "Дней с низким покрытием датчиков (<80%)"),
    "Low-coverage days": ("Aşağı örtüklü günlər", "Дней с низким покрытием"),
    "Check": ("Yoxlama", "Проверка"),
    "Value": ("Dəyər", "Значение"),
    # rates
    "Not in the trained model: {wells}. Rates use the field average.":
        ("Öyrədilmiş modeldə yoxdur: {wells}. Debitlər mədən ortalamasına əsaslanır.",
         "Нет в обученной модели: {wells}. Дебиты по среднему по месторождению."),
    "Well-days": ("Quyu-günlər", "Скважино-сутки"),
    "Field oil, {date}": ("Mədən üzrə neft, {date}", "Нефть месторождения, {date}"),
    "Oil error vs tests": ("Sınaqlara görə neft xətası", "Ошибка по нефти к замерам"),
    "MAPE over {n} measured tests in this data.": ("Bu məlumatdakı {n} ölçülmüş sınaq üzrə MAPE.",
                                                    "MAPE по {n} замерам в этих данных."),
    "Daily rates, {well}": ("Gündəlik debitlər, {well}", "Суточные дебиты, {well}"),
    "Rates, CSV": ("Debitlər, CSV", "Дебиты, CSV"),
    "Rates, Excel": ("Debitlər, Excel", "Дебиты, Excel"),
    "Phase": ("Faza", "Фаза"),
    "Oil": ("Neft", "Нефть"),
    "Water": ("Su", "Вода"),
    "Gas": ("Qaz", "Газ"),
    # PTA
    "Shut-in": ("Bağlanma", "Остановка"),
    "Permeability": ("Keçiricilik", "Проницаемость"),
    "Skin": ("Skin-faktor", "Скин-фактор"),
    "ΔP skin": ("ΔP skin", "ΔP скин"),
    "Horner slope, psi/cycle": ("Horner meyli, psi/dövr", "Наклон Хорнера, psi/цикл"),
    "Flow efficiency": ("Axın səmərəliliyi", "Коэф. совершенства"),
    "Interpretation": ("Şərh", "Интерпретация"),
    "No shut-ins in this data.": ("Bu məlumatda bağlanma yoxdur.", "В этих данных нет остановок."),
    "No shut-in: {wells}": ("Bağlanma yoxdur: {wells}", "Нет остановок: {wells}"),
    "{well}, shut-in {start}: {error}": ("{well}, bağlanma {start}: {error}", "{well}, остановка {start}: {error}"),
    "PTA, CSV": ("PTA, CSV", "PTA, CSV"),
    "PTA, Excel": ("PTA, Excel", "PTA, Excel"),
    "low": ("aşağı", "низкая"),
    "moderate": ("orta", "средняя"),
    "high": ("yüksək", "высокая"),
    "Permeability is about **{k:.0f} md** ({grade}), from a model match of the whole build-up "
    "(fit error {rms:.2f} psi RMS); the implied Horner slope is {m:.1f} psi per log cycle.":
        ("Keçiricilik təxminən **{k:.0f} md**-dir ({grade}); bütün bərpa əyrisinin model uyğunluğundan alınıb "
         "(uyğunluq xətası {rms:.2f} psi RMS); buna uyğun Horner meyli log dövrünə {m:.1f} psi-dir.",
         "Проницаемость около **{k:.0f} мД** ({grade}), по совмещению модели со всей КВД "
         "(ошибка {rms:.2f} psi RMS); соответствующий наклон Хорнера {m:.1f} psi на логарифмический цикл."),
    "The late build-up shows a **closed boundary** at about {re:,.0f} ft (drainage limit reached).":
        ("Bərpanın son hissəsi təxminən {re:,.0f} ft məsafədə **qapalı sərhəd** göstərir (drenaj həddinə çatılıb).",
         "Поздняя часть КВД показывает **закрытую границу** примерно на {re:,.0f} ft (достигнута граница дренирования)."),
    "Skin is **+{S:.1f}**: the near-wellbore zone is **damaged**. About {dps:.0f} psi is lost across it, "
    "and the well flows at roughly {fe:.0%} of its undamaged potential. **Candidate for a stimulation review.**":
        ("Skin **+{S:.1f}**-dir: quyuətrafı zona **zədələnib**. Orada təxminən {dps:.0f} psi itir və quyu "
         "zədəsiz potensialının təxminən {fe:.0%}-i ilə işləyir. **Stimulyasiya baxışı üçün namizəddir.**",
         "Скин **+{S:.1f}**: призабойная зона **загрязнена**. В ней теряется около {dps:.0f} psi, и скважина "
         "работает примерно на {fe:.0%} от потенциала без загрязнения. **Кандидат на интенсификацию.**"),
    "Skin is **{S:.1f}**: the near-wellbore zone is **stimulated** (better than undamaged rock). "
    "No damage to remove; flow efficiency {fe:.0%}.":
        ("Skin **{S:.1f}**-dir: quyuətrafı zona **stimulyasiya olunub** (zədəsiz süxurdan yaxşıdır). "
         "Aradan qaldırılacaq zədə yoxdur; axın səmərəliliyi {fe:.0%}.",
         "Скин **{S:.1f}**: призабойная зона **интенсифицирована** (лучше незагрязнённой породы). "
         "Загрязнения нет; коэффициент совершенства {fe:.0%}."),
    "Skin is **{S:.1f}**, close to zero: **no significant damage**.":
        ("Skin **{S:.1f}**-dir, sıfıra yaxın: **əhəmiyyətli zədə yoxdur**.",
         "Скин **{S:.1f}**, близок к нулю: **значимого загрязнения нет**."),
    "Radial flow did not clearly develop (the derivative never stays flat for 0.3 log cycle). "
    "The model match still uses every point, but treat permeability and skin as **indicative**.":
        ("Radial axın aydın formalaşmayıb (törəmə 0,3 log dövrü boyunca sabit qalmır). Model uyğunluğu yenə "
         "bütün nöqtələrdən istifadə edir, lakin keçiricilik və skin **təxmini** qəbul edilməlidir.",
         "Радиальный приток явно не сформировался (производная не держится ровной 0,3 лог. цикла). Модель "
         "всё равно использует все точки, но проницаемость и скин следует считать **ориентировочными**."),
    "Extrapolated pressure p* is {p:.0f} psia at the gauge ({pd:.0f} psia at datum); "
    "the test investigated about {ri:,.0f} ft into the reservoir.":
        ("Ekstrapolyasiya olunmuş təzyiq p* manometrdə {p:.0f} psia-dır (datumda {pd:.0f} psia); "
         "sınaq laya təxminən {ri:,.0f} ft dərinliyə baxıb.",
         "Экстраполированное давление p* на манометре {p:.0f} psia ({pd:.0f} psia на отметке приведения); "
         "исследование охватило около {ri:,.0f} ft пласта."),
    "Extrapolated pressure p* is {p:.0f} psia at the gauge; the test investigated about {ri:,.0f} ft into the reservoir.":
        ("Ekstrapolyasiya olunmuş təzyiq p* manometrdə {p:.0f} psia-dır; sınaq laya təxminən {ri:,.0f} ft dərinliyə baxıb.",
         "Экстраполированное давление p* на манометре {p:.0f} psia; исследование охватило около {ri:,.0f} ft пласта."),
    "Removing the damage could add up to about **{lost:,.0f} stb/d** of oil at today's drawdown. "
    "An upper bound: it assumes the damage can be removed and the lift system can take the rate.":
        ("Zədəni aradan qaldırmaq bugünkü depressiyada gündə təxminən **{lost:,.0f} stb/d**-ə qədər əlavə neft verə bilər. "
         "Bu yuxarı həddir: zədənin aradan qaldırıla biləcəyi və qazlift sisteminin bu debiti qəbul edəcəyi fərz olunur.",
         "Устранение загрязнения может добавить до **{lost:,.0f} stb/d** нефти при текущей депрессии. "
         "Это верхняя оценка: предполагается, что загрязнение устранимо, а газлифт примет этот дебит."),
    # export
    "Production rates (VFM)": ("Hasilat debitləri (VFM)", "Дебиты (VFM)"),
    "Well tests (PTA)": ("Quyu sınaqları (PTA)", "Исследования скважин (PTA)"),
    "Everything": ("Hamısı", "Всё"),
    "Excel workbook": ("Excel kitabı", "Книга Excel"),
    "Report with charts (HTML)": ("Qrafikli hesabat (HTML)", "Отчёт с графиками (HTML)"),
    # convert
    "CSV or Excel file": ("CSV və ya Excel faylı", "Файл CSV или Excel"),
    "Sheet": ("Vərəq", "Лист"),
    "Download as CSV": ("CSV kimi yüklə", "Скачать как CSV"),
    "Download as Excel": ("Excel kimi yüklə", "Скачать как Excel"),
    "Too many rows for Excel (limit 1,048,576). Keep this one as CSV.":
        ("Excel üçün sətir sayı çoxdur (limit 1 048 576). Bu faylı CSV kimi saxlayın.",
         "Слишком много строк для Excel (лимит 1 048 576). Оставьте этот файл в CSV."),
    "{rows} rows, {cols} columns": ("{rows} sətir, {cols} sütun", "Строк: {rows}, столбцов: {cols}"),
    # settings
    "Theme": ("Mövzu", "Тема"),
    "Dark": ("Tünd", "Тёмная"),
    "Light": ("Açıq", "Светлая"),
    "Language": ("Dil", "Язык"),
    # graph builder
    "Data": ("Məlumat", "Данные"),
    "Chart": ("Qrafik növü", "Тип графика"),
    "Measure": ("Göstərici", "Показатель"),
    "X axis": ("X oxu", "Ось X"),
    "Statistic": ("Statistika", "Статистика"),
    "Daily rates": ("Gündəlik debitlər", "Суточные дебиты"),
    "Sensors, hourly": ("Sensorlar, saatlıq", "Датчики, почасово"),
    "Measured well tests": ("Ölçülmüş quyu sınaqları", "Замеры скважин"),
    "PTA results": ("PTA nəticələri", "Результаты PTA"),
    "Trend over time": ("Zamana görə trend", "Динамика во времени"),
    "Cross-plot": ("Çarpaz qrafik", "Кросс-плот"),
    "Distribution by well": ("Quyular üzrə paylanma", "Распределение по скважинам"),
    "Histogram": ("Histoqram", "Гистограмма"),
    "Compare wells": ("Quyuların müqayisəsi", "Сравнение скважин"),
    "Mean": ("Orta", "Среднее"),
    "Sum": ("Cəm", "Сумма"),
    "Minimum": ("Minimum", "Минимум"),
    "Maximum": ("Maksimum", "Максимум"),
    "Download data (CSV)": ("Məlumatı yüklə (CSV)", "Скачать данные (CSV)"),
    "Select at least one well.": ("Ən azı bir quyu seçin.", "Выберите хотя бы одну скважину."),
    "Oil rate (stb/d)": ("Neft debiti (stb/d)", "Дебит нефти (stb/d)"),
    "Water rate (stb/d)": ("Su debiti (stb/d)", "Дебит воды (stb/d)"),
    "Gas rate (Mscf/d)": ("Qaz debiti (Mscf/d)", "Дебит газа (Mscf/d)"),
    "Water cut (%)": ("Sulaşma (%)", "Обводнённость (%)"),
    "Gas-oil ratio (scf/stb)": ("Qaz amili (scf/stb)", "Газовый фактор (scf/stb)"),
    "Date": ("Tarix", "Дата"),
    "Permeability (md)": ("Keçiricilik (md)", "Проницаемость (мД)"),
    "ΔP skin (psi)": ("ΔP skin (psi)", "ΔP скин (psi)"),
    "Horner slope (psi/cycle)": ("Horner meyli (psi/dövr)", "Наклон Хорнера (psi/цикл)"),
    "Shut-in duration (h)": ("Bağlanma müddəti (saat)", "Длительность остановки (ч)"),
    "p* at gauge (psia)": ("p* manometrdə (psia)", "p* на манометре (psia)"),
    "Investigation radius (ft)": ("Tədqiqat radiusu (ft)", "Радиус исследования (ft)"),
    "Count": ("Say", "Количество"),
    # charts
    "Oil and water (stb/d)": ("Neft və su (stb/d)", "Нефть и вода (stb/d)"),
    "Gas (Mscf/d)": ("Qaz (Mscf/d)", "Газ (Mscf/d)"),
    "{name}, daily estimate": ("{name}, gündəlik qiymət", "{name}, суточная оценка"),
    "{name}, measured test": ("{name}, ölçülmüş sınaq", "{name}, замер"),
    "Downhole pressure": ("Quyudibi təzyiq", "Забойное давление"),
    "shut-in": ("bağlanma", "остановка"),
    "Pressure history": ("Təzyiq tarixçəsi", "История давления"),
    "Pressure change Δp": ("Təzyiq dəyişməsi Δp", "Изменение давления Δp"),
    "Bourdet derivative": ("Bourdet törəməsi", "Производная Бурде"),
    "Model match Δp": ("Model uyğunluğu Δp", "Модель Δp"),
    "Model match derivative": ("Model uyğunluğu, törəmə", "Модель, производная"),
    "radial flow window": ("radial axın pəncərəsi", "окно радиального притока"),
    "Shut-in time Δt (h)": ("Bağlanma vaxtı Δt (saat)", "Время остановки Δt (ч)"),
    "Log-log diagnostic": ("Log-log diaqnostika", "Диагностика log-log"),
    "Build-up pressure": ("Bərpa təzyiqi", "Давление восстановления"),
    "Radial flow points": ("Radial axın nöqtələri", "Точки радиального притока"),
    "Horner line: m = {m:.1f} psi/cycle, p* = {p:.0f} psia":
        ("Horner xətti: m = {m:.1f} psi/dövr, p* = {p:.0f} psia", "Прямая Хорнера: m = {m:.1f} psi/цикл, p* = {p:.0f} psia"),
    "Model match": ("Model uyğunluğu", "Модель"),
    "Horner time (tp + Δt) / Δt": ("Horner vaxtı (tp + Δt) / Δt", "Время Хорнера (tp + Δt) / Δt"),
    "Horner plot": ("Horner qrafiki", "График Хорнера"),
}


def translator(lang: str):
    """t(english) -> text in `lang`; unknown strings and English pass through unchanged."""
    i = {"az": 0, "ru": 1}.get(lang)
    return (lambda s: s) if i is None else (lambda s: TEXT[s][i] if s in TEXT else s)


if __name__ == "__main__":
    import re
    from pathlib import Path
    here = Path(__file__).parent
    used = set()
    for f in ("app.py", "charts.py", "pipeline.py"):
        src = (here / f).read_text()
        # t("...") and N_("..."), including implicitly concatenated literals
        for m in re.finditer(r'''\b(?:t|N_)\(\s*((?:"[^"\n]*"\s*|'[^'\n]*'\s*)+)''', src):
            used.add("".join(a or b for a, b in re.findall(r'''"([^"\n]*)"|'([^'\n]*)\'''', m.group(1))))
    missing = sorted(s for s in used if s not in TEXT)
    assert not missing, f"no translation for: {missing}"
    for en, pair in TEXT.items():
        for tr in pair:
            assert sorted(re.findall(r"\{[^}]*\}", en)) == sorted(re.findall(r"\{[^}]*\}", tr)), (en, tr)
    print(f"OK: {len(used)} strings used, all translated to az and ru; placeholders intact")
