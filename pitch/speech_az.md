# SOCAR Hakaton 2026: çıxış mətni

Yeddi dəqiqə, canlı demo daxil. Bunu əzbərləməyin: hər bölmənin **əsas fikrini** yadda saxlayın və
öz sözlərinizlə danışın. Mətn sadəcə nümunədir.

| İşarə | Mənası |
|---|---|
| **[KLİK]** | növbəti slayd |
| **[DEMO]** | tətbiqdə edilən hərəkət |
| *(fasilə)* | bir anlıq dayanın |
| **[SPEAKER ?]** | kimin danışacağı hələ təyin olunmayıb |

## Çıxışdan əvvəl

- Tətbiqi işə salın və daxil olun: `rizzman@socar.az` / `guessme`.
- Təqdimatı açın: `pitch/RizzML_pitch.html` faylını iki dəfə klikləyin.
- Demo slaydını (5-ci) bir dəfə açın və orada da daxil olun. Sonra 1-ci slayda qayıdın.

---

## 0:00–0:50 · Giriş və problem · slayd 2–3 · [SPEAKER ?]

*Əsas fikir: data çoxdur, ölçülmüş debit isə azdır.*

> **[KLİK]** Boş 1-ci slayddan keçin: sual görünür və sayğac işə düşür.

GL-04 quyusu dünən nə qədər neft verib?

*(fasilə)*

Bunu heç kim bilmir. Nə biz, nə də bu quyuya baxan mühəndis.

Doqquz ayda on quyu dörd milyon sensor ölçüsü yazıb. Amma ölçülmüş debit cəmi səksən beşdir. Yəni
hər quyu ayda təxminən bir dəfə ölçülür.

API standartına görə iki ölçmə arasındakı debit ölçülmür, sadəcə hesabla bölüşdürülür. Tədqiqatlar
da göstərir ki, ayda bir ölçmədən ikiyə keçəndə xəta ən çox azalır.

> **[KLİK]**

Yəni ölçmələr arasında mühəndislər debiti cədvəllərdə təxmin edir. Görmədiyin şeyi isə itirirsən.

SOCAR neftinin yarıdan çoxu qazlift quyularından gəlir. Hər ölçmə ya bir günə qədər çəkən test, ya
da bahalı avadanlıq deməkdir.

## 0:50–1:05 · Həll · slayd 4

*Əsas fikir: mövcud sensorlardan hər gün debit, yeni avadanlıq lazım deyil.*

> **[KLİK]**

RizzML SOCAR-ın artıq qoyduğu sensorlardan hər quyunun gündəlik debitini hesablayır. Quyu
bağlananda isə layın vəziyyətini göstərir.

Bu, SOCAR-ın öz serverində işləyən sadə bir brauzer tətbiqidir. Yeni avadanlıq lazım deyil.

## 1:05–3:30 · Canlı demo · slayd 5 (tətbiq)

*Əsas fikir: xam fayl girir, bir dəqiqəyə nəticə çıxır.*

> **[KLİK]** Tətbiq slaydın içində açılır. Ehtiyat: ikinci noutbuk və ya QR kod.

İndi bunu sizin verdiyiniz data üzərində göstərim. Tətbiq serverdə işləyir, mən sadəcə brauzerdən
qoşuluram.

> **[DEMO]** "Məlumat yüklə": xam faylları atın və "Analizi başlat" düyməsini basın.

Bunlar xam fayllardır. Analiz bir dəqiqəyə yaxın çəkir. Bu arada deyim ki, datada heç nə göründüyü
kimi deyildi.

Faylda guya boş dəyər yox idi. Amma yeddi mindən çox ölçü əslində "mənfi doqquz yüz doxsan doqquz"
kodu idi.

Bir quyunun qaz debiti səhv vahidlə yazılmışdı və iyirmi səkkiz dəfə böyük görünürdü.

*(İstəyə bağlı, demo ləngisə buraxın:)* Bir gecə isə on quyunun hamısı eyni anda susmuşdu. Bu,
sensor xətası yox, məlumat sisteminin nasazlığı idi.

Ən maraqlı tapıntımız isə budur: test vaxtı quyu başqa xəttə qoşulur və təzyiq bir az düşür. Buna
görə testlər adi günlərdən təxminən iki yarım faiz yüksək göstərir. Bunu dörd ayrı üsulla
yoxladıq və nəzərə aldıq.

> **[DEMO]** Nəticələr görünür: tətbiq özü "Hasilat debitləri" səhifəsində açılır.

Hazırdır. Hər quyu üçün hər gün neft, su və qaz. Nöqtələr real ölçmələrdir, xətt isə aradakı
günləri dolduran modelimizdir.

> **[DEMO]** Soldakı menyudan "Quyu sınaqları".

İndi quyu bağlanmalarına baxaq. Tətbiq onları özü tapır: bu datada altı quyu bağlanıb. Bu, GL-01
quyusudur, üç gün bağlı qalıb.

Quyu bağlananda təzyiq yavaş-yavaş qalxır. Bu qalxmanın formasından layın keçiriciliyini və quyunun
zədəli olub-olmadığını oxuyuruq.

> **[DEMO]** "Şərh" bölməsini açın.

GL-01 zədələnib: potensialının cəmi əlli yeddi faizi ilə işləyir. Zədəni təmizləsək, gündə yeddi
yüz əlli barelə qədər əlavə neft verə bilər. Yəni bu quyu təmir üçün ilk namizəddir.

> **[DEMO]** Soldakı menyudan "İxrac".

Bütün nəticələr bir kliklə Excel faylına və hesabata çıxır.

> Yeni quyu çıxsa, deyin: "Bu quyu model üçün yenidir, ona görə tətbiq onu təxmin etmir, ayrıca
> qeyd edir."

## 3:30–5:20 · Metod, nəticələr və quyu sınaqları · slayd 6–8 · [SPEAKER ?]

*Əsas fikir: fizika maşın öyrənməsini uddu, xəta iki-üç faizdir.*

> **[KLİK]**

Buna niyə inanmaq olar? Çünki maşın öyrənməsini də sınadıq və o, uduzdu.

Cəmi səksən beş ölçmə ilə maşın öyrənməsi modeli beş faiz xəta verdi. Bu, keçən ayın ölçməsini
sadəcə təkrarlamaqdan yaxşı deyil.

Bizim fiziki modelin xətası təxminən iki yarım faizdir, yəni iki dəfə dəqiqdir. Hər proqnozu da
yalnız keçmiş məlumatla yoxladıq, gələcəyə baxmadan.

Ən çox sevdiyimiz hissə isə budur: modelin rəqəmlərini biz vermədik, onları datadan özü tapdı. Və
tapdığı rəqəmlər dərslikdəki ştuser qanunu ilə üst-üstə düşür.

> **[KLİK]**

Yekun nəticə belədir: neftdə xəta iki tam onda altı faiz, suda üç tam onda səkkiz, qazda isə beş
tam onda yeddi faizdir.

Model görmədiyi yeni quyuda zəifdir. Ona görə tətbiq belə quyunu ayrıca qeyd edir.

> **[KLİK]**

Bu isə altı bağlanmanın hamısıdır. Nöqtələr ölçülmüş təzyiqdir, xətlər isə bizim modelimizdir. Hər
quyuda model ölçmə ilə demək olar ki, üst-üstə düşür.

Üç quyu zədələnib, üçü isə yaxşı vəziyyətdədir. Modeli yoxlamaq üçün bir sınaq da etdik: GL-01-in
yalnız ilk gününü verdik və model qalan iki günü düzgün proqnozlaşdırdı.

## 5:20–5:55 · Rəqabət və dəyər · slayd 9–10 · [SPEAKER ?]

*Əsas fikir: hamı yarısını edir, biz ikisini birləşdiririk.*

> **[KLİK]**

Otuza yaxın məhsula baxdıq. Biri debit verir, digəri təzyiqi oxuyur, amma heç kim ikisini
birləşdirmir. SOCAR artıq KAPPA işlədir, bizim gündəlik debitlərimiz isə məhz onun ehtiyac
duyduğu məlumatdır.

> **[KLİK]**

Bu nə qazandırır? Hər gün, hər quyu üçün debit. Hər bağlanma zədəli quyunu göstərir: PETRONAS bu
yolla axtarışı iki həftədən bir günə endirib. Burada isə üç zədəli quyu gündə min dörd yüz yetmiş
barelə qədər əlavə neft verə bilər. Hamısı SOCAR-ın içində, bir kompüterdə işləyir.

## 5:55–6:15 · Komanda · slayd 11 · [SPEAKER ?]

*Əsas fikir: hər birimiz üçün bir cümlə.*

> **[KLİK]**

Biz RizzML-ik. Rövşən Ağabəyov fizika olimpiadasının qalibidir və su vurulan quyular haqqında elmi
məqalənin müəllifidir. Tural Qasımov CanSat qlobal finalçısıdır və hərbi səviyyəli simulyasiyalar
hazırlayıb. Faiq Tayıbov iki dəfə ICPC çempionudur və süni intellekti tədris sistemlərinə
inteqrasiya edib.

## 6:15–6:50 · Xərcin azalması · slayd 12 · [SPEAKER ?]

*Əsas fikir: bir gün əvəzinə saniyədən az, avadanlıqsız.*

> **[KLİK]** Sayğac burada dayanır.

Bu yeddi dəqiqədə SOCAR təxminən bir quyu testi apardı. RizzML isə bir kompüterdə [sağdakı rəqəm]
gündəlik debit hesablaya bilərdi.

Bu gün bir ölçmə bir günə qədər çəkir, ayda bir dəfə olur, xəta altı faizdir və hər quyuya iki yüz
əlli min dollara qədər avadanlıq lazımdır. Bizdə isə saniyədən az vaxt, hər gün, iki tam onda altı
faiz xəta və heç bir avadanlıq.

Bu, hər quyuda üç yüz min dollara qədər qənaətdir, bütün SOCAR üzrə isə bir milyard səkkiz yüz
milyon dollara qədər.

Beləliklə, GL-04 dünən nə qədər neft verib?

*(fasilə)*

İndi bilirsiniz. Təşəkkür edirik.

## 6:50–7:00 · Ehtiyat vaxt

On saniyə ehtiyat var. Yükləmə ləngisə, data haqqında danışmağa davam edin. Tətbiq işləməsə,
ehtiyat videoya keçin və eyni mətnlə davam edin.
