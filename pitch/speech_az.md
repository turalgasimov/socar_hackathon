# SOCAR Hakaton 2026: çıxış mətni

Yeddi dəqiqə, canlı demo daxil. Mətni əzbərləməyin. Fikri bilin və öz sözlərinizlə danışın.

| İşarə | Mənası |
|---|---|
| **[KLİK]** | növbəti slayd |
| **[DEMO]** | tətbiqdə edilən hərəkət |
| *(fasilə)* | bir anlıq dayanın |
| **[SPEAKER ?]** | kimin danışacağı hələ təyin olunmayıb |

Texniki terminlər (VFM, PTA, Horner, skin, time-forward) komanda qaydası ilə ingiliscə qalır.
Azərbaycanca variantın vaxtını məşqdə ölçün; ingiliscə variant söz sayına görə təxminən 6:50 çəkir.

## Çıxışdan əvvəl

- Tətbiqi işə salın və daxil olun: `rizzman@socar.az` / `guessme`. Tətbiq birbaşa menyuda açılsın.
- Təqdimatı açın: `pitch/RizzML_pitch.html` faylını iki dəfə klikləyin. Server lazım deyil.
- Demo slaydını (5-ci) bir dəfə açın və orada da daxil olun. Giriş bütün çıxış boyu qalır.
  Sonra 1-ci slayda qayıdın.

---

## 0:00–0:50 · Giriş və problem · slayd 2–3 · [SPEAKER ?]

> **[KLİK]** Boş 1-ci slayddan keçin: sual görünür və sayğac işə düşür.

GL-04 quyusu dünən nə qədər neft hasil edib?

*(fasilə)*

Bunu heç kim bilmir. Nə biz bilirik, nə də bu quyuya cavabdeh olan mühəndis.

Doqquz ay ərzində bu yatağın on quyusu təxminən dörd milyon sensor ölçüsü qeydə alıb. Amma
ölçülmüş hasilat debiti cəmi səksən beşdir. Bu, hər quyu üçün ayda təxminən bir test deməkdir.

API-nin quyu sınağı təcrübəsinə, yəni MPMS 20.5 standartına görə, iki test arasındakı hər debit
ölçülmür, sadəcə bölüşdürülür. Tədqiqatlar da göstərir ki, bu xəta ən çox ayda bir testdən iki
testə keçəndə azalır.

> **[KLİK]**

Deməli, testlər arasında mühəndislər debiti ayrı-ayrı proqramlarda və cədvəllərdə təxmin edir.
Görmədiyiniz şey isə itkiyə çevrilir.

SOCAR neftinin yarıdan çoxu qazlift quyularından gəlir. Ölçülən hər debit ya bir günə qədər çəkən
quyu testi, ya da bahalı avadanlıq tələb edir.

## 0:50–1:05 · Həll · slayd 4

> **[KLİK]**

RizzML SOCAR-ın artıq quraşdırdığı sensorlardan hər quyu üçün gündəlik debit çıxarır. Quyunun hər
bağlanmasını isə lay diaqnozuna çevirir.

Bu, SOCAR-ın öz serverində işləyən bir brauzer tətbiqidir. Heç bir yeni avadanlıq lazım deyil.

## 1:05–3:30 · Canlı demo · slayd 5 (tətbiq)

> **[KLİK]** Tətbiq slaydın içində açılır. Ehtiyat variant: ikinci noutbuk və ya QR kod.

İndi bunu sizin verdiyiniz test datası üzərində göstərim.

Tətbiq mərkəzi serverdə işləyir. Mən sadəcə brauzerdən qoşuluram.

> **[DEMO]** "Məlumat yüklə": xam CSV fayllarını atın və "Analizi başlat" düyməsini basın.

Bunlar xam fayllardır, necə qeydə alınıbsa, eləcə. Analiz bir dəqiqəyə yaxın çəkir. Bu arada
sistemin nəyi yoxladığını deyim, çünki bizə verilən datada heç nə göründüyü kimi deyildi.

Bir faylda guya heç bir boş dəyər yox idi. Əslində isə yeddi mindən çox ölçü sadəcə bir koddur:
mənfi doqquz yüz doxsan doqquz tam yüzdə iyirmi beş.

Bir quyu qaz debitini "min kub fut" başlığı altında kub metrlə yazmışdı. Bu, iyirmi səkkiz dəfəlik
xəta deməkdir.

*(İstəyə bağlı, demo ləngisə buraxın:)* Bundan başqa, iki min yarım təkrarlanan sətir, işarəsi tərsinə dönmüş dəyərlər və bir gecə var ki,
on quyunun hamısı eyni anda susub. Bu, on sensorun birdən xarab olması deyil, data sisteminin
nasazlığıdır.

Bir tələni tutduğumuz üçün isə xüsusilə fəxr edirik. Quyu testi zamanı axın test separatoruna
yönəlir və quyuağzı təzyiq adi gündən otuz psi-yə qədər aşağı olur. Bu effekti dörd müstəqil üsulla
ölçdük və hamısı eyni nəticəni verdi: iki yarım faiz.

> **[DEMO]** Nəticələr görünür: tətbiq özü "Hasilat debitləri" səhifəsində açılır.

Hazırdır. Hər quyu üçün, hər gün neft, su və qaz debiti var. Nöqtələr real quyu testləridir, xətt
isə aradakı günləri dolduran modelimizdir.

> **[DEMO]** Soldakı menyudan "Quyu sınaqları" bölməsinə keçin.

İndi laya keçək. Quyunun hər bağlanması avtomatik tapılır: bu datada altı quyu bağlanıb. Bu,
GL-01 quyusudur, aprel ayında üç gün bağlı qalıb.

> **[DEMO]** Horner qrafikini göstərin.

Əvvəlcə Horner qrafiki qurulur, sonra quyunun modeli bütün nöqtələrə uyğunlaşdırılır. Nəticə
belədir: keçiricilik yüz beş millidarsi, skin üstəgəl beş tam onda yeddi, skinə görə itən təzyiq
isə yüz on yeddi psi.

> **[DEMO]** "Şərh" bölməsini açın.

Skinin müsbət olması o deməkdir ki, quyu zədələnib və potensialının cəmi əlli yeddi faizi ilə
işləyir. Zədəni aradan qaldırsaq, quyu gündə yeddi yüz əlli barelə qədər əlavə neft verə bilər.
Yəni bu quyu stimulyasiya üçün namizəddir.

> **[DEMO]** Soldakı menyudan "İxrac" bölməsinə keçin.

Bir kliklə hər iki hissənin nəticələrini Excel faylına və hesabata çıxarmaq olur.

> Test datasında model üçün yeni bir quyu olarsa, belə deyin: "Bu quyu model üçün yenidir, ona görə
> tətbiq təxmin etmək əvəzinə onu ayrıca qeyd edir."

## 3:30–5:20 · Metodologiya, nəticələr və quyu sınaqları · slayd 6–8 · [SPEAKER ?]

> **[KLİK]**

Bu nəticələrə niyə inanmaq olar? Çünki maşın öyrənməsinə ədalətli şans verdik və o, uduzdu.

Cəmi səksən beş ölçülmüş debitlə əlli səkkiz əlamətli reqressiya modeli beş faiz xəta verdi.
Statistik baxımdan bu, keçən ayın testini sadəcə təkrarlamaqdan yaxşı deyil.

Bizim fiziki modelimizin xətası isə təxminən iki yarım faizdir. Yəni o, iki dəfə daha dəqiqdir və
bu fərq statistik cəhətdən etibarlıdır.

Bütün nəticələr time-forward üsulu ilə alınıb: hər proqnoz yalnız keçmiş məlumata əsaslanır.

Ən çox sevdiyimiz hissə isə budur: modelə heç bir fizika öyrətməmişdik. O, ştuser ölçüsü üçün iki
tam yüzdə altı, təzyiq düşküsü üçün isə sıfır tam yüzdə qırx yeddi dərəcəsini özü tapdı. Dərslikdə
bu rəqəmlər iki və yarımdır. Yəni model ştuserdən axın qanununu datadan özü yenidən kəşf etdi.

> **[KLİK]**

Yekun nəticələr belədir: neftdə xəta iki tam onda altı faiz, suda üç tam onda səkkiz faiz, qazda
isə beş tam onda yeddi faizdir. Hər üç fazada R-kvadrat sıfır tam yüzdə doxsan doqquzdan yüksəkdir.

Məhdudiyyətlərimizi də açıq deyirik: model heç görmədiyi quyuda dəqiqliyini itirir. Ona görə
tətbiq belə quyunu təxmin etmək əvəzinə ayrıca qeyd edir.

> **[KLİK]**

İndi quyu sınaqlarına baxaq. Bu, datadakı altı bərpa əyrisinin hamısıdır, log-log diaqnostik
qrafikdə. Nöqtələr ölçülmüş təzyiq və onun törəməsidir, xətlər isə hər quyunun bütün nöqtələrə
uyğunlaşdırılmış modelidir. Uyğunluq xətası psi-nin onda birindən azdır, bu da ölçmə küyünə yaxındır.

Keçiricilik qırx üç ilə iki yüz doxsan beş millidarsi arasındadır. Üç quyu stimulyasiya olunub,
üçü zədələnib, GL-01 və GL-10 isə qapalı sərhədə çatır. Modeli görmədiyi data üzərində də
yoxladıq: GL-01-in ilk gününə uyğunlaşdırılan model sonrakı iki günü ölçmə küyü səviyyəsində
proqnozlaşdırır.

## 5:20–5:55 · Rəqabət və dəyər · slayd 9–10 · [SPEAKER ?]

> **[KLİK]**

Təxminən otuz məhsulu yoxladıq. Debit və quyu testi proqramları var, amma ayrı-ayrılıqda. Heç kim
onları qazlift quyuları üçün, sizdə artıq olan sensorlar üzərində birləşdirmir. SOCAR isə artıq
KAPPA-dan istifadə edir və bizim gündəlik debitlərimiz məhz onun ehtiyac duyduğu məlumatdır.

> **[KLİK]**

Bu, nə qazandırır? Hər gün, hər quyu üçün debit. Quyunun hər bağlanması skin rəqəminə çevrilir:
PETRONAS bu yolla zədələnmiş quyuların axtarışını iki həftədən bir günə endirib. Burada isə
zədələnmiş üç quyu gündə min dörd yüz yetmiş barelə qədər əlavə neft verə bilər, bu yuxarı
həddir. Hamısı SOCAR şəbəkəsinin içində bir kompüterdə işləyir.

## 5:55–6:15 · Komanda · slayd 11 · [SPEAKER ?]

> **[KLİK]**

Biz RizzML komandasıyıq. Rövşən Ağabəyov fizika olimpiadasının qalibidir və "PI-ML and Physical
Type Curves for Water-Injection Wells" məqaləsinin müəllifidir. Tural Qasımov CanSat qlobal
finalçısıdır, hərbi səviyyəli simulyasiyalar və proqram təminatı hazırlayıb. Faiq Tayıbov iki dəfə
ICPC çempionudur, maşın öyrənməsi və kompüter görməsini tədris idarəetmə sistemlərinə (LMS)
inteqrasiya edib.

## 6:15–6:50 · Xərclərin azalması · slayd 12 · [SPEAKER ?]

> **[KLİK]** Sayğac burada dayanır.

Bu yeddi dəqiqədə SOCAR təxminən bir quyu testi apardı. RizzML isə bir kompüterdə
[sağdakı rəqəm] gündəlik quyu debiti hesablaya bilərdi.

Bu gün bir debit üçün bir günə qədər çəkən test lazımdır. Bu, ayda bir dəfə olur, xəta altı faizdir
və hər quyuya iki yüz əlli min dollara qədər avadanlıq tələb olunur. RizzML ilə debit saniyənin
yüzdə ikisində hesablanır, hər gün yenilənir, xəta iki tam onda altı faizdir və heç bir avadanlıq
lazım deyil.

Bu, hər quyuda üç yüz min dollara qədər qənaət deməkdir. SOCAR-ın bütün quyularında isə bu qənaət
bir milyard səkkiz yüz milyon dollara çatır.

Beləliklə, GL-04 quyusu dünən nə qədər neft hasil edib?

*(fasilə)*

İndi bunu bilirsiniz. Təşəkkür edirik.

## 6:50–7:00 · Ehtiyat vaxt

Canlı demo üçün on saniyə ehtiyat vaxt var, üstəlik yuxarıdakı istəyə bağlı cümlə. Yükləmə ləngisə, data keyfiyyəti haqqında danışmağa
davam edin. Tətbiq işləməsə, ehtiyat videoya keçin və eyni mətnlə davam edin.
