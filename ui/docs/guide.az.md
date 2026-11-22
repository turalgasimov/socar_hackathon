## İstifadə qaydası

**RizzML** qazlift quyularının sensor məlumatlarından hər quyu üçün gündəlik neft, su və qaz debitini
hesablayır (virtual axın ölçmə, **VFM**) və hər bağlanmanı təzyiqin bərpası kimi təhlil edir
(təzyiqin keçid prosesinin analizi, **PTA**).

1. SOCAR e-poçtunuzla **daxil olun**. Dili burada, sonra isə **Ayarlar**-da dəyişə bilərsiniz.
2. **Məlumat yüklə.** Xam faylları (CSV və ya Excel) yükləyin. Yükləmə sahəsinin altındakı siyahıda
   tanınan hər fayl yaşıl olur. Və ya Ana səhifədə **Nümunə məlumat** düyməsini basın: hakaton yatağı
   işə düşür.
3. **Analizi başlat.** Təmizləmə, debitlərin hesablanması və quyu sınaqlarının analizi 10 quyu və
   9 ay üçün təxminən 30 saniyə çəkir. Sonra tətbiq **Hasilat debitləri** səhifəsində açılır və bütün
   bölmələr aktivləşir.
4. **Nəticələrə baxın.** Hər səhifənin solunda menyu var.
   - **Hasilat debitləri:** hər quyu üzrə gündəlik neft, su və qaz. Nöqtələr ölçülmüş quyu
     sınaqlarıdır (yüklənibsə).
   - **Quyu sınaqları:** hər bağlanma üçün keçiricilik, skin, ΔP skin, Horner meyli və axın
     səmərəliliyi, sadə dildə şərh, Horner, log-log və təzyiq tarixçəsi qrafikləri.
   - **Qrafik qur:** nəticələrdən istənilən qrafik: trend, çarpaz qrafik, paylanma, histoqram və ya
     quyuların müqayisəsi. Məlumatı CSV kimi yüklənir.
   - **Mədən məlumatları:** hər quyu üzrə təmizlənmiş sensor tarixçəsi, bağlanmalar rənglənib.
   - **Məlumat keyfiyyəti:** təmizləmə zamanı nə tapılıb və düzəldilib.
5. **İxrac:** debitlər və PTA nəticələri CSV və ya Excel kimi, hamısı bir Excel kitabında və bütün
   qrafiklərlə HTML hesabat.
6. **Tarixçə** yükləmələrinizi, analizlərinizi və endirdiyiniz faylları saxlayır, onları sonra yenidən
   açmaq və ya endirmək olar. **Çevir** istənilən CSV-ni Excel-ə və əksinə çevirir.

## Məlumatlarınız

| Fayl | Vacibdir | Nə saxlayır |
|---|---|---|
| `high_freq_data` | bəli | Dəqiqəlik sensorlar: `timestamp`, `well_name`, `whp_psia`, `whp_downstream_psia`, `dh_pressure_psia`, `dh_temperature_degf`, `annulus_pressure_psia`, `gas_lift_rate_mscfd` |
| `choke_events` | bəli | Ştuser dəyişiklikləri: `timestamp`, `well_name`, `choke_opening_pct` (0% = quyu bağlıdır) |
| `reservoir_pvt` | bəli | Hər quyuya bir sətir: lay qalınlığı, məsaməlik, sıxılma, quyu radiusu, neftin həcm əmsalı və özlülüyü, doyma təzyiqi, datum, drenaj sahəsi |
| `well_completion` | bəli | Hər quyuya bir sətir: manometrin dərinliyi, qazlift klapanı, NKB ölçüsü, kollektor, həll olmuş qaz amili, toplanmış neft |
| `well_tests` | xeyr | Ölçülmüş sınaq debitləri. Onlara qarşı dəqiqlik yoxlaması əlavə edir, modelin öyrədilmə dövründən sonrakı sınaqlar isə modeli ayba-ay yeniləyir |

- Fayl adına görə tanınır: adında `high`, `choke`, `pvt`, `completion` və ya `test` olması kifayətdir.
- Excel faylları birinci vərəqdən oxunur. Hər fayl 1 GB-a qədər.
- Təmizləmə avtomatikdir: boş dəyər kodu −999.25, təkrar sətirlər və sensor sıçrayışları.
  Məlumat keyfiyyəti hər birinin sayını göstərir.

## Necə işləyir

**Debitlər (VFM).** Qara qutu deyil, fiziki model.

- Maye debiti ştuserdən axın qanununa tabedir: ştuser ölçüsü, ştuserdəki təzyiq düşküsü,
  quyuağzı təzyiq və qaz-maye nisbəti.
- NKB-dəki təzyiq düşküsü onu neft və suya bölür; qaz həll olmuş qaz amilindən hesablanır.
- 85 ölçülmüş quyu sınağına uyğunlaşdırılan model dərslikdəki ştuser qanununu özü tapdı: ştuser
  ölçüsünün 2,06 dərəcəsi və təzyiq düşküsünün 0,47 dərəcəsi (dərslikdə: 2 və 0,5).
- Bu məlumatda maşın öyrənməsini üstələdi. Cəmi 85 ölçülmüş debit olduqda fizika daha yaxşı ümumiləşir.
- Quyu sınaqları adi hasilat günlərinə nisbətən təxminən 2,5% yüksək göstərir (sınaq separatoru daha
  aşağı təzyiqdə işləyir), gündəlik debitlər buna görə düzəldilir.
- Yeni məlumat modeli aktual saxlayır. Yüklənən məlumatda modelin öyrədilmə dövründən sonrakı quyu
  sınaqları olduqda, model hər ayın əvvəlində həmin aydan əvvəl bitmiş bütün sınaqlarla yenidən
  qurulur. Heç bir gün öz ayının və ya sonrakı ayların sınağı ilə hesablanmır, model faylının özü isə
  dəyişmir. Məlumat keyfiyyəti hansı ayların yenidən qurulduğunu göstərir.
- Öyrədilmə dövründən sonra başlayan məlumat da həmin dövrdən istifadə edir: son məlum ştuser
  vəziyyəti və indiyədək hasil edilmiş neft saxlanılan öyrətmə tarixçəsindən götürülür.

**Quyu sınaqları (PTA).** Bağlanmalar ştuserin 0% olduğu yerdə tapılır. Hər bərpa əyrisi üçün:

- Horner analizi radial axının düz xəttini tapır;
- sonra quyunun modeli (quyu lüləsinin həcmi, skin, radial axın, qapalı və ya sonsuz sərhəd) bərpanın
  hər nöqtəsinə uyğunlaşdırılır və göstərilən keçiricilik və skini verir;
- istifadə olunan neft debiti bağlanmadan əvvəlki hesablanmış gündəlik debitdir.

Quyudibi manometr datumdan yuxarıdadır. Fərq bərpa boyu sabitdir, ona görə keçiricilikdə, skində,
meyldə və ΔP skin-də ixtisar olunur. Yalnız p\* həm manometrdə, həm də datumda göstərilir.

**Dəqiqlik.** Hər ölçülmüş sınaq yalnız əvvəlki məlumatla proqnozlaşdırılıb:

| Faza | Xəta (MAPE) | Həcmə görə (WAPE) | R² |
|---|---|---|---|
| Neft | 2,56% | 2,33% | 0,998 |
| Su | 3,82% | 3,48% | 0,996 |
| Qaz | 5,65% | 4,61% | 0,994 |

PTA modeli hər bərpa əyrisinə 0,03–0,08 psi (RMS) dəqiqliklə uyğun gəlir.

**Məhdudiyyətlər.**

- Modelin öyrədilmədiyi quyu mədən ortalamasını alır və tətbiq onu qeyd edir. Bir neçə quyu sınağı onu
  kalibrləyənə qədər debitləri etibarlı deyil.
- Yalnız bağlanmış quyular üçün quyu sınağı analizi var.
- Bərpa analizi birfazalı neft qəbul edir. Burada bu doğrudur: təzyiq doyma təzyiqindən yuxarı qalır.
- Giriş demo hesabdır, hələ real autentifikasiya deyil.

## Terminlər

| Termin | Mənası |
|---|---|
| VFM | Virtual axın ölçmə: debitlərin sınaq separatoru və ya sayğac əvəzinə sensorlardan qiymətləndirilməsi |
| PTA | Təzyiqin keçid prosesinin analizi: lay xassələrinin təzyiq dəyişməsindən, burada bağlanma zamanı oxunması |
| Bağlanma, bərpa | Ştuser bağlanır, axın dayanır və quyudibi təzyiq artır |
| Keçiricilik (k, md) | Neftin süxurdan nə qədər asan axması |
| Skin (S) | Quyu ətrafında əlavə təzyiq itkisi. Müsbət: zədələnib. Mənfi: stimulyasiya olunub |
| ΔP skin (psi) | Skinə görə itən təzyiq |
| Axın səmərəliliyi | Quyunun zədəsiz potensialının nə qədərini verdiyi |
| Horner qrafiki, meyl m | Təzyiq log((tp + Δt) / Δt)-yə qarşı. Düz hissə m-i verir, m isə k-nı |
| p\* | Sonsuz uzun bağlanmaya ekstrapolyasiya olunmuş təzyiq |
| Log-log, Bourdet törəməsi | Diaqnostik qrafik. Düz törəmə radial axın deməkdir |
| MAPE, WAPE, R² | Orta % xəta, həcmə görə % xəta, izah olunan dəyişkənliyin payı |
| Sulaşma, qaz amili | Mayedə suyun payı; bir barel neftə düşən qaz |
| stb/d, Mscf/d, psia | Gündə stok-tank barel, gündə min standart kub fut, mütləq təzyiq |

## Problemlər

| Nə görürsünüz | Nə etməli |
|---|---|
| Fayl siyahıda boz qalır | Adında `high`, `choke`, `pvt`, `completion` və ya `test` olmalıdır. Adını dəyişin |
| "Məlumatı analiz etmək mümkün olmadı" | Lazımi sütun yoxdur və ya adı dəyişib. **Məlumatlarınız** bölməsi ilə müqayisə edin |
| Nümunə məlumat bağlıdır | Serverdə nümunə sensor faylı yoxdur. Orada `git lfs pull` işlədin |
| Quyunun Quyu sınaqları nəticəsi yoxdur | Quyu heç bağlanmayıb: ştuseri heç 0%-ə çatmayıb |
| "Öyrədilmiş modeldə yoxdur" | Yeni quyu. Debitləri mədən ortalamasına əsaslanır |
| Səhifə əvvəlcə məlumat yükləməyi istəyir | Analizi başladın və ya **Tarixçə**-dən birini yenidən açın |
| Mövzunu dəyişəndə səhifə yenilənir | Normaldır. Eyni səhifəyə nəticələrinizlə qayıdırsınız |
| Yükləmə yavaşdır | Dəqiqəlik fayl təxminən 260 MB-dır. Ofis şəbəkəsi ilə yükləyin |
