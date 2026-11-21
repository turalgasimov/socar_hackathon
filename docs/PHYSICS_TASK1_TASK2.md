# Fizika: Task 1 (VFM + Gas Lift) və Task 2 (PTA)

> Düsturlar LaTeX-dədir: VS Code-da `Ctrl+Shift+V` (Markdown Preview) və ya GitHub-da düzgün görünür.
> Vahidlər **oilfield** sistemindədir: q [stb/d], p [psia], k [md], h [ft], μ [cp], B [rb/stb], c_t [1/psi], r [ft], t [saat]. Başqa vahid olarsa ayrıca qeyd olunur.
> Hər bölmədə **"Bizim datada"** qeydi var: həmin fizika datada yoxlanılıbmı, rəqəmlər nədir.

---

## 0. Böyük şəkil — quyu bir "təzyiq zənciridir"

```
 Rezervuar (p̄r, T_res) ── IPR ──► Perforasiya / datum (p_wf, datum TVD)
                                      │  maye sütunu (yalnız neft + su + həll olmuş qaz)
                                      ▼
                         Downhole gauge (dh_pressure, dh_temperature; gauge TVD)
                                      │  ağır maye qradiyenti ≈ 0.35–0.45 psi/ft
                                      ▼
   Annulus (annulus_pressure) ──► GL valve (valve TVD) ── lift-gas inyeksiyası (gas_lift_rate)
                                      │  aerasiya olunmuş sütun: yüngül qradiyent ≈ 0.1–0.25 psi/ft
                                      ▼
                         Wellhead (whp_psia) ── CHOKE (choke_opening_pct) ──► Flowline (whp_downstream)
                                                                                  │
                                                                     Manifold → separator (test zamanı test separatoru)
```

Debit q **bütün zəncirdə eynidir** (kütlə saxlanır). Hər sensor bu zəncirin bir nöqtəsindəki təzyiq və ya temperaturdur, və hər biri q-dan asılıdır. Deməli hər sensor q üçün ayrıca bir tənlik verir. **VFM = bu tənlikləri q-ya görə tərsinə həll etmək** (inverse problem). Sensor sayı (6) naməlumlardan (q_L, WC, p̄r) çoxdur, ona görə sistem redundant-dır: bir neçə müstəqil estimator qurub onları birləşdirmək olar.

Klassik nodal analizdə debit IPR (inflow) və VLP (outflow, tubing + choke) əyrilərinin kəsişməsidir. Gas lift isə VLP əyrisini aşağı salır.

---

# HİSSƏ A — TASK 1: Virtual Flow Metering və Gas Lift fizikası

## A1. Fluid xassələri (PVT)

### A1.1 Əsas təriflər

| Kəmiyyət | Tərif | Datadakı sütun |
|---|---|---|
| Maye debiti | $q_L = q_o + q_w$ | `liquid_rate_stbd` |
| Water cut | $WC = q_w / q_L$ | `water_cut_pct` |
| GOR (formasiya) | $R_p = 1000\,q_g / q_o$ [scf/stb] | `gor_scf_stb` |
| Formasiya GLR | $GLR_f = 1000\,q_g / q_L$ | — |
| Ümumi GLR | $GLR_t = 1000\,(q_g + q_{gi}) / q_L$ | `glr_scf_stb` |
| Ümumi qaz | $q_{g,tot} = q_g + q_{gi}$ | `total_gas_rate_mscfd` |

$q_{gi}$ = lift qazı (`gas_lift_rate_mscfd`). **Hədəf `gas_rate_mscfd` = formasiya qazıdır, lift qazı daxil deyil.**

### A1.2 Doymamış (undersaturated) neft və GOR

- **Bubble point** $p_b$: bu təzyiqdən yuxarıda bütün qaz neftdə həll olunmuş vəziyyətdədir.
- $p > p_b$ olduqda həll olmuş qaz sabitdir: $R_s = R_{sb}$. Rezervuarda sərbəst qaz yoxdur, ona görə **səthdə ölçülən GOR = $R_{sb}$**.
- $p < p_b$ olduqda sərbəst qaz yaranır və GOR artır:

$$R_p = R_s + \frac{k_{rg}\,\mu_o\,B_o}{k_{ro}\,\mu_g\,B_g}$$

> **Bizim datada:** Minimum axın Pwf = 2273 psia, maksimum $p_b$ = 1595 psia. Deməli hər yerdə $p > p_b$ (undersaturated). Test GOR / $R_s$ = 0.989 ± 0.073.
> **Nəticə:** $q_g = q_o \cdot R_s / 1000$. Qaz üçün ayrıca model lazım deyil. 7%-lik səpələnmə test ölçüsünün küyüdür.

### A1.3 Sıxlıqlar (qradiyentlər üçün)

$$\gamma_o = \frac{141.5}{131.5 + API}, \qquad
\rho_o^{live} = \frac{62.4\,\gamma_o + 0.0136\,R_s\,\gamma_g}{B_o}\ \ [\mathrm{lb/ft^3}]$$

$$\gamma_w \approx 1 + 0.695\times10^{-6}\,C_s[\mathrm{ppm}] \quad\text{(duzluluq)}, \qquad \rho_w = 62.4\,\gamma_w$$

$$\rho_g = \frac{2.7\,\gamma_g\,p}{z\,T},\qquad B_g = 0.02827\,\frac{z\,T}{p}\ [\mathrm{ft^3/scf}],\quad T\ [^\circ R]$$

Maye qradiyenti: $\;G_L = \dfrac{(1-WC)\,\rho_o + WC\,\rho_w}{144}\;$ [psi/ft].

> **GL-01 nümunəsi:** API 34.7 → γo = 0.851, ρo ≈ 48.4 lb/ft³ (0.336 psi/ft). Su 147 600 ppm → γw ≈ 1.103 (0.478 psi/ft). WC 42% olduqda $G_L$ ≈ **0.395 psi/ft**.

### A1.4 Ölçü vahidləri (tələlər)

- 1 Mscf = **28.3168 m³**. GL-06-da qaz testləri m³/d ilə yazılıb.
- Stock-tank şərtləri: 14.7 psia, 60 °F. $B_o$ rezervuar barelini stock-tank bareline çevirir.
- BS&W ≈ WC (fərq ±1.8 faiz bəndi; BS&W-də sediment də var).

---

## A2. Inflow — IPR (rezervuardan quyuya axın)

### A2.1 Darcy, radial pseudo-steady state (PSS)

$$q_o = \frac{0.00708\,k\,h\,(\bar p_r - p_{wf})}{\mu_o\,B_o\left[\ln\!\left(\dfrac{r_e}{r_w}\right) - 0.75 + S\right]}
\qquad\Longrightarrow\qquad q_o = J\,(\bar p_r - p_{wf})$$

$$J = \frac{0.00708\,k\,h}{\mu_o B_o\left[\ln(r_e/r_w) - 0.75 + S\right]},\qquad r_e = \sqrt{\frac{43560\,A}{\pi}}\ \ (A\ \text{acre})$$

- Steady-state (sabit təzyiqli sərhəd) halında $-0.75$ əvəzinə $-0.5$ yazılır.
- $p_{wf} < p_b$ olsaydı Vogel tətbiq olunardı: $\;\dfrac{q}{q_{max}} = 1 - 0.2\dfrac{p_{wf}}{\bar p} - 0.8\left(\dfrac{p_{wf}}{\bar p}\right)^2$. **Bizdə lazım deyil.**

**Fiziki məna:** choke-u bağlasan WHP qalxır, sonra $p_{wf}$ qalxır, drawdown ($\bar p_r - p_{wf}$) azalır və debit düşür. Datada bu açıq görünür (GL-01 iyun, GL-04 mart/aprel).

> **Bizim datada:** PTA-dan alınan k, S ilə hesablanmış $J_{Darcy}$ build-up-dan ölçülən $J = q_o/(p_{end} - p_{wf})$ ilə üst-üstə düşür: GL-01 3.90 vs 3.86, GL-06 5.80 vs 5.79. **Generator IPR-i neft debitinə tətbiq edir.**

### A2.2 Deplesiya: $\bar p_r(t)$ zamanla azalır

Material balance (doymamış, su axını yoxdur):

$$N_p B_o = N B_{oi}\,c_e\,\Delta p,\qquad c_e = \frac{c_o S_o + c_w S_w + c_f}{1 - S_w}$$

Qapalı drenaj sahəsi üçün PSS-də təzyiq düşmə sürəti:

$$\frac{d\bar p}{dt}\ [\mathrm{psi/day}] = -\frac{q_t\,[\mathrm{rb/d}]}{c_t\,V_p},\qquad V_p = 7758\,A\,h\,\phi\ [\mathrm{rb}],\quad q_t = q_o B_o + q_w B_w$$

> ⚠️ **Sintetik data ziddiyyəti (vacib!):** GL-01 üçün $V_p$ = 7758·110·80·0.194 = 13.2 MMrb, $q_t$ ≈ 1976 rb/d, $c_t$ = 1.275e-5. Bu verir **dp̄/dt ≈ 11.7 psi/gün**, yəni 9 ayda ~3200 psi. Datada müşahidə olunan isə ~0.3 psi/gündür (~80 psi / 9 ay). Üstəlik GL-01-in kumulyativ hasilatı (9.96 MMstb) bu pore volume-dan praktiki olaraq çıxa bilməz.
> **Nəticə:** generator $\bar p_r(t)$-ni material balance olmadan, birbaşa təyin edib. İlkin build-up model fiti aquifer deyil, qapalı sərhədə işarə edir. Sərhəd tipi PTA mərhələsində repo skripti ilə təsdiqlənəcək. **Qapalı-tank MB-ni modelə məcburi qoymaq səhv olardı.** $\bar p_r(t)$ datadan (test + build-up) hamar funksiya kimi öyrənilməlidir.

---

## A3. Dərinliklər və təzyiq düzəlişləri

| Dərinlik (completion / PVT) | Rolu | Nümunə GL-01 |
|---|---|---|
| `datum_tvd_ft` | IPR və p* üçün istinad dərinliyi (perforasiya) | 9660 ft |
| `gauge_tvd_ft` | dh_pressure/dh_temperature burada ölçülür | 9380 ft (datumdan 280 ft yuxarı) |
| `gl_valve_tvd_ft` | lift qazının tubing-ə girdiyi nöqtə | 3940 ft |
| tubing ID | sürət → sürtünmə, holdup | 2.992 in |

Gauge-dan datuma düzəliş (gauge ilə perforasiya arasında yalnız maye var):

$$p_{wf,datum} = p_{gauge} + G_L\,(D_{datum} - D_{gauge})$$

- Datum − gauge fərqi quyulardan asılı olaraq **150–420 ft**-dir. Ofset ~55–170 psi-dir və **təxminən sabitdir**. Ona görə $J$ və Δp hesablarında sadələşir, **amma p* və p̄ datumda verilməlidir.**
- ⚠️ Real qaz-lift quyusunda shut-in-dən sonra **faza seqreqasiyası** (gauge-in altında su toplanması) qradiyenti zamanla dəyişdirir. Bu, sabit ofsetdən fərqli olaraq k və S-i təhrif edə bilər. Sintetik datadakı build-up əyrilərində belə təhrif görünmür (əyrilər monoton qalxır).
- PTA üçün: m, k, S yalnız Δp-dən asılıdır, ona görə sabit ofset onlara təsir etmir.

---

## A4. Tubing axını və GAS LIFT

### A4.1 Təzyiq qradiyenti tənliyi

$$\frac{dp}{dz} = \underbrace{\frac{\rho_m\,g\cos\theta}{144\,g_c}}_{\text{hidrostatik (≈80–95%)}} + \underbrace{\frac{f\,\rho_m\,v_m^2}{2\,g_c\,d\cdot 144}}_{\text{sürtünmə}} + \underbrace{\frac{\rho_m\,v_m}{144\,g_c}\frac{dv_m}{dz}}_{\text{akselerasiya (≈0)}}$$

Qarışıq sıxlığı holdup ilə hesablanır:

$$\rho_m = H_L\,\rho_L + (1 - H_L)\,\rho_g,\qquad \lambda_L = \frac{q_L^{in\text{-}situ}}{q_L^{in\text{-}situ} + q_g^{in\text{-}situ}}\ \ \text{(no-slip)},\qquad H_L \ge \lambda_L$$

Qaz mayedən sürətli qalxır (slip), ona görə $H_L > \lambda_L$. Holdup korrelyasiyaları: Hagedorn-Brown, Beggs-Brill, Gray (tNavigator / Prosper bunlardan istifadə edir).

Valve-dan yuxarıda in-situ qaz həcmi:

$$q_g^{in\text{-}situ}\,[\mathrm{ft^3/d}] = \left(1000\,q_{gi} + q_o\,(R_p - R_s(p))\right)\,B_g(p)$$

### A4.2 Gas lift niyə işləyir — rəqəmlərlə (GL-01)

- **Gauge-dan valve-a qədər** (5440 ft, ağır maye, ~0.40 psi/ft): $p_{valve}^{tbg} \approx 3240 - 0.40 \times 5440 \approx 1064$ psia.
- **Lift qazı olmasaydı** (valve-dan səthə qədər də 0.40 psi/ft): $p_{wh} \approx 1064 - 0.40 \times 3940 = -512$ psia. Bu mümkün deyil, yəni **quyu təbii axmazdı (ölü quyu)**.
- **Lift qazı ilə:** WHP ≈ 300 psia. Valve-dan yuxarı orta qradiyent = (1064 − 300) / 3940 ≈ **0.19 psi/ft**. Qaz sütunu təxminən 2 dəfə yüngülləşdirib.

### A4.3 Gas-lift performance curve (GLPC)

$q_L$ əvvəlcə $q_{gi}$ artdıqca artır, çünki hidrostatik təzyiq azalır. Müəyyən nöqtədən sonra azalır, çünki sürtünmə ($\propto v_m^2$) dominant olur. Optimum nöqtədə $dq_o/dq_{gi}$ = qazın marjinal dəyəridir. Datada GL rate pilləli dəyişir (operator optimallaşdırması). 06-14-də kompressor trip-i zamanı GL ~50% düşür.

### A4.4 Annulus → valve → tubing (gas-lift valve fizikası)

Annulusda statik qaz sütunu:

$$p_{inj}(D_v) = p_{ann,surf}\;\exp\!\left(\frac{0.01875\,\gamma_g\,D_v}{\bar z\,\bar T}\right)$$

Valve-dan keçən qaz axını orifis kimidir (Thornhill-Craver):

$$q_{gi} = \frac{155.5\,C_d\,A_{port}\,p_{up}\sqrt{\dfrac{2gk}{k-1}\left(r^{2/k} - r^{(k+1)/k}\right)}}{\sqrt{\gamma_g\,T_{up}}},\qquad r = \frac{p_{tbg}}{p_{inj}},\quad r_c \approx 0.55$$

`gl_valve_port_64ths` → $A_{port}$. $r < r_c$ olduqda axın kritikdir və $q_{gi}$ tubing təzyiqindən asılı olmur.

> **GL-01:** $p_{ann}$ = 1166 psia, $\gamma_g$ = 0.65, $D_v$ = 3940 ft, $\bar z\bar T$ ≈ 540 → $p_{inj}$ ≈ 1274 psia. Tubing tərəfində ≈ 1064 psia, deməli valve üzərində ~210 psi düşür.
> **Datada görünən:** choke bağlananda tubing təzyiqi qalxır və annulus təzyiqi də qalxır (GL-04 mart/aprel pillələri). Yəni annulus_pressure tubing təzyiqinin dolayı ölçüsüdür.

---

## A5. CHOKE fizikası (ən güclü estimatorumuz)

### A5.1 Kritik və subkritik axın

- **Kritik axın** ($p_{dn}/p_{up} \lesssim 0.5$–$0.6$): debit yalnız upstream təzyiqdən asılıdır. Gilbert tipli korrelyasiyalar bu hal üçündür:

$$p_{wh} = \frac{435\,R^{0.546}\,q_L}{S^{1.89}}\qquad (R\ [\mathrm{Mscf/stb}],\ S\ [1/64\ \mathrm{in}],\ p\ [\mathrm{psig}])$$

  Ros, Baxendell və Achong korrelyasiyaları eyni formadadır, yalnız sabitlər fərqlidir.

- **Subkritik axın:** downstream təzyiq də rol oynayır. Mexanistik orifis tənliyi:

$$\dot m = C_d\,A\,\sqrt{2\,g_c\,\rho_m\,\Delta p_c},\qquad \Delta p_c = p_{wh} - p_{dn},\qquad A = \frac{\pi}{4}\left(\frac{S}{64}\right)^2$$

### A5.2 Bizim düstur haradan gəlir (törəmə)

1. Choke-da qaz həcmcə dominantdır. GL-01: $GLR_t$ = 581 scf/stb, $B_g$(300 psia) ≈ 0.052 ft³/scf → 30 ft³ qaz / 5.6 ft³ maye → **qaz həcm payı ≈ 84%**.
2. Qaz dominant olduqda sıxlıq təxminən $\rho_m \propto p_{wh}/GLR$ olur.
3. Kütlənin əsas hissəsi mayededir, ona görə $q_L \propto \dot m$.
4. Bunları birləşdirəndə:

$$\boxed{\,q_L \;\propto\; S^2\,\sqrt{\frac{p_{wh}\,\Delta p_c}{GLR}}\,}$$

> **Datadan öyrənilən** (`ml/eda/benchmark_vfm.py`): $q_L \propto S^{2.05}\,\Delta p_c^{0.47}\,p_{wh}^{0.46}\,GLR^{-0.61}$. Bu, fiziki törəmə ilə demək olar eynidir (2, 0.5, 0.5, −0.5).
> - Choke opening → bean: $S = \text{opening\%}/100 \times 128$. Burada xətti choke xarakteristikası **fərz edilib**; eksponent qeyri-xəttiliyi qismən udur.
> - Gilbert-in öz sabitləri (435 / 0.546 / 1.89) datada quyular arasında 1.22–1.56 dəfə fərqli nisbət verir. Ona görə **sabitləri sərt kodlamırıq, eksponentləri öyrənirik**.

### A5.3 Test separatoru effekti

Normal rejimdə $p_{dn}/p_{wh}$ ≈ 196/299 = 0.66, test zamanı ≈ 170/281 = 0.60. Axın subkritik və ya kritikə yaxındır, ona görə **downstream təzyiq debitə təsir edir**. Test zamanı downstream −24 psi, $p_{wf}$ −11 psi dəyişir və debit 1–4% artır. Test etiketləri "test rejimindəki" debitdir.

---

## A6. Termal fizika (yeni tapıntı — 3-cü estimator)

### A6.1 Geotermal profil

$$T_{geo}(D) = T_{surf} + g_G\,D$$

Shut-in zamanı gauge temperaturu geotermal dəyərə qayıdır: $T_{gauge}^{shut} = T_{res} - g_G\,(D_{datum} - D_{gauge})$.

> **Bizim datada:** $g_G$ = **1.09–1.44 °F/100ft** (6 shut-in). Məsələn GL-01: 202.2 − 1.39 × 2.80 = 198.3 °F, ölçülən 198.32 °F.

### A6.2 Ramey: axın zamanı temperatur

$$T_f(z) = T_{geo}(z) + g_G\,A\left(1 - e^{-z/A}\right),\qquad A = \frac{\dot m\,c_p\,f(t)}{2\pi\,r_{ti}\,U\,k_e} \;\propto\; q$$

Debit nə qədər böyükdürsə, $A$ o qədər böyük olur və maye yuxarı qalxarkən daha az soyuyur. Gauge perforasiyaya yaxındır (150–420 ft), ona görə $T_f \approx T_{res}$.

### A6.3 Joule-Thomson qızması

Mayelər üçün $\mu_{JT} < 0$-dır, yəni təzyiq düşəndə maye **qızır**:

$$\Delta T_{JT} = -\mu_{JT}\,\Delta p \approx \eta\,(\bar p_r - p_{wf}),\qquad \eta_{oil} \approx 0.003\text{–}0.005\ ^\circ\mathrm{F/psi}$$

Ona görə:

$$T_{gauge} - T_{res} \approx \eta\,(\bar p_r - p_{wf}) = \frac{\eta}{J}\,q_o \quad\Longrightarrow\quad \boxed{\,q_o = \frac{J}{\eta}\,(T_{gauge} - T_{res})\,}$$

> **Bizim datada:** $\eta$ = 3.00, 3.28, 3.40, 2.60, 3.48, 3.02 mF/psi (GL-01/02/04/06/08/10). Bu, real neft üçün tipik intervaldır. GL-04-də drawdown böyükdür (~915 psi), ona görə gauge temperaturu reservoir temperaturundan 3.1 °F yüksəkdir.
> Hər quyu üçün $q_o = a + b\,T$ modeli: **LOO 2.09%**, korrelyasiya 0.95–0.99 (GL-03-də debit dəyişməzdir, ona görə zəifdir).
> ⚠️ Temperatur dəyişikliyi kiçikdir (0.01 °F ~ 3 psi). Sensor küyü vacibdir; **gündəlik ortalama** küyü azaldır.

---

## A7. Faza bölgüsü: water cut və qaz

- **Fractional flow:** WC su doyumu ilə artır (Buckley-Leverett, su qabağı və ya aquifer):

$$f_w = \frac{1}{1 + \dfrac{k_{ro}\,\mu_w}{k_{rw}\,\mu_o}}$$

  Vaxt şkalası aylar-illərdir, ona görə gündəlik şkalada WC **hamar trenddir**. Datada 9 ayda +4…+8 faiz bəndi artır. Model: hər quyu üçün xətti (və ya kumulyativ mayeyə görə) trend, LOO xətası 0.94 faiz bəndi.
- **Qaz:** $q_g = q_o R_s/1000$ (A1.2).
- **Kütlə balansı avtomatik qorunur:** $q_o + q_w = q_L$, $q_g/q_o = R_s$.

---

## A8. Well test ölçüsünün fizikası (etiketlərin mənbəyi)

- Quyu 12–24 saat test separatoruna yönləndirilir. Neft, su və qaz ayrı ölçülür (neft/su üçün sayğac, qaz üçün orifis sayğacı).
- Tipik qeyri-müəyyənlik: neft ±2–5%, su ±3–5%, qaz ±5–10%. **Bizdə GOR səpələnməsi ~7% → qaz küyü ~5–7%.**
- Test separatoru normal separatordan aşağı təzyiqdədir, bu da test rejimi bias-ı yaradır (A5.3).
- Etiket = test pəncərəsi üzrə orta debit. Gizli "həqiqət" isə gündəlik ortadır.

---

## A9. VFM bir inverse problem kimi və ML-in yeri

| # | Tənlik | Naməlumlar | Sensorlar | Status |
|---|---|---|---|---|
| E1 | Choke: $q_L = C_w\,S^{a}\Delta p_c^{b}p_{wh}^{c}GLR^{d}$ | $q_L$ | choke, WHP, downstream, GL | ✅ LOO 1.82% |
| E2 | IPR: $q_o = J(\bar p_r(t) - p_{wf})$ | $q_o$, $\bar p_r(t)$ | dh_pressure | ✅ LOO 2.10% (q_L) |
| E3 | Termal: $q_o = (J/\eta)(T - T_{res})$ | $q_o$ | dh_temperature | ✅ LOO 2.09% (q_o) |
| E4 | VLP: $p_{gauge} - p_{wh} = \Delta p_{tbg}(q_L, WC, GLR)$ | $q_L$, WC | dh, WHP, GL | ⏳ (WC üçün potensial siqnal) |
| E5 | GL valve: $q_{gi} = f(p_{ann}, p_{tbg})$ | — | annulus, GL | QC |

**Fizika ML-ə necə daxil olur (güclüdən zəifə):**

1. **Struktur (grey-box):** fiziki forma sabitdir, əmsallar öyrənilir (E1-də log-xətti).
2. **Fiziki feature-lər:** $\ln S$, $\sqrt{p\,\Delta p}$, drawdown, $T - T_{res}$, GLR.
3. **Məhdudiyyətlər:** $q \ge 0$; $S = 0 \Rightarrow q = 0$; $\partial q/\partial S > 0$; $q_g = R_s q_o$.
4. **Residual ML:** fizika + ML(residual). 85 nöqtədə yalnız güclü regularizasiya ilə işləyir (RF-residual 2.11% verdi, yəni pisləşdirdi).
5. **Multi-estimator ansambl:** E1 + E2 + E3, çəkilər tərs dispersiyaya görə ($w_i \propto 1/\sigma_i^2$). Sensor küyləri müstəqil olduğu üçün xəta azalır.
6. PINN tipli physics-loss: 85 nöqtə üçün lazımsız mürəkkəblikdir.

---

# HİSSƏ B — TASK 2: Pressure Transient Analysis (Build-up)

## B1. Diffuziya tənliyi

Kütlə saxlanması + Darcy + az sıxılan maye birləşəndə alınır:

$$\frac{1}{r}\frac{\partial}{\partial r}\left(r\,\frac{\partial p}{\partial r}\right) = \frac{\phi\,\mu\,c_t}{0.0002637\,k}\,\frac{\partial p}{\partial t}\qquad (t\ \text{saat})$$

**Fərziyyələr:** tək faza, sabit μ, kiçik və sabit $c_t$, homogen-izotrop lay, üfüqi radial axın, tam penetrasiya, qravitasiya nəzərə alınmır. README "single-phase oil, $Q_o$ ilə" deyir, yəni bu fərziyyələr qəbul edilir.

$\eta = k/(\phi\mu c_t)$ — **hidravlik diffuzivlik**: təzyiq dalğasının nə qədər sürətlə yayıldığını göstərir.

Dimensiyasız dəyişənlər:

$$p_D = \frac{k\,h\,(p_i - p)}{141.2\,q\,B\,\mu},\qquad t_D = \frac{0.0002637\,k\,t}{\phi\,\mu\,c_t\,r_w^2},\qquad r_D = \frac{r}{r_w}$$

## B2. Sonsuz lay həlli (line source)

$$p_i - p(r,t) = -70.6\,\frac{qB\mu}{kh}\;\mathrm{Ei}\!\left(-\frac{948\,\phi\,\mu\,c_t\,r^2}{k\,t}\right)$$

Kiçik arqumentdə ($x < 0.01$) $-\mathrm{Ei}(-x) \approx -\ln(1.781\,x)$. Quyuda ($r = r_w$) bu verir:

$$p_{wf}(t) = p_i - \frac{162.6\,qB\mu}{kh}\left[\log t + \log\frac{k}{\phi\mu c_t r_w^2} - 3.2275 + 0.8686\,S\right]$$

**Nəticə:** $p_{wf}$ $\log t$-yə qarşı düz xəttdir və slope-u $m = 162.6\,qB\mu/(kh)$-dır. Bütün semi-log analizin əsası budur.

## B3. Skin

Hawkins: quyu ətrafında $r_s$ radiuslu, $k_s$ keçiricilikli zona var.

$$S = \left(\frac{k}{k_s} - 1\right)\ln\frac{r_s}{r_w},\qquad \Delta p_{skin} = \frac{141.2\,qB\mu}{kh}\,S = 0.869\,m\,S,\qquad r_{w,eff} = r_w\,e^{-S}$$

- $S > 0$: zədələnmə (damage — qazma məhlulu, fines, scale).
- $S < 0$: stimulyasiya (turşu, frac).
- Axın səmərəliliyi və zədələnmə nisbəti:

$$FE = \frac{\bar p - p_{wf} - \Delta p_{skin}}{\bar p - p_{wf}},\qquad DR = 1/FE$$

## B4. Wellbore storage (WBS)

Quyu bağlanandan sonra lay quyuya axmağa davam edir (afterflow), çünki quyu həcmi sıxılır və ya maye səviyyəsi qalxır:

$$C = c_{wb}\,V_{wb}\ \ \text{(dolu quyu)}\qquad \text{və ya}\qquad C = \frac{144\,A_{wb}}{5.615\,\rho}\ \ \text{(qalxan səviyyə)}\quad [\mathrm{bbl/psi}]$$

Erkən dövrdə **unit slope** olur:

$$\Delta p = \frac{q\,B}{24\,C}\,\Delta t,\qquad C_D = \frac{0.8936\,C}{\phi\,c_t\,h\,r_w^2}$$

WBS-in bitmə vaxtı:

$$t_{wbs} \approx \frac{(200000 + 12000\,S)\,C\,\mu}{k\,h}\ \ [\text{saat}]$$

**Fiziki məna:** $kh/\mu$ nə qədər kiçikdirsə, WBS o qədər uzun çəkir.

> **Bizim datada:** GL-04-də $kh/\mu$ ən kiçikdir (56·32/1.725 ≈ 1040 md·ft/cp). Ona görə WBS hump-ı böyükdür və radial axın yalnız ~14 saatdan başlayır. Qaz-lift quyularında annulus qazı storage-i böyüdə bilər.

## B5. Superposition → Horner tənliyi

Build-up iki həllin cəmi kimi göstərilir: $t_p + \Delta t$ müddət +q ilə hasilat və $\Delta t$ müddət −q ilə "inyeksiya". Loqarifmik yaxınlaşma ilə:

$$\boxed{\,p_{ws}(\Delta t) = p^{*} - m\,\log\frac{t_p + \Delta t}{\Delta t}\,},\qquad m = \frac{162.6\,q_o\,B_o\,\mu_o}{k\,h}$$

**Horner pseudo-producing time:** $\;t_p = \dfrac{24\,N_p}{q_o}$ [saat]. Bu, eyni kumulyativ hasilatı verən ekvivalent sabit-debit müddətidir. $N_p$ = `cum_oil_at_2025_01_01` + Σ(VFM gündəlik neft). Burada VFM **iki dəfə** istifadə olunur: həm $q_o$, həm də $N_p$ üçün.

**MDH:** $t_p \gg \Delta t$ olduqda $\log\frac{t_p+\Delta t}{\Delta t} \approx \log t_p - \log\Delta t$, yəni $p_{ws} = p_{1hr} + m\log\Delta t$. Bizdə $t_p$ = 91 000–233 000 saatdır, Δt isə ≤ 72 saat, ona görə Horner və MDH praktiki olaraq eynidir.

## B6. Horner analizi — addım-addım (bütün tələb olunan parametrlər)

| # | Parametr | Düstur |
|---|---|---|
| 1 | **Horner slope m** [psi/cycle] | $p_{ws}$ vs $\log\frac{t_p+\Delta t}{\Delta t}$ qrafikində radial axın hissəsinə xətti fit, mütləq slope |
| 2 | **Permeability k** [md] | $k = \dfrac{162.6\,q_o\,B_o\,\mu_o}{m\,h}$ |
| 3 | $p_{1hr}$ | Düz xəttin $\Delta t$ = 1 saatdakı qiyməti (**ölçülmüş nöqtə deyil, xəttin özü!**) |
| 4 | **Skin S** | $S = 1.151\left[\dfrac{p_{1hr} - p_{wf}(\Delta t{=}0)}{m} - \log\dfrac{k}{\phi\,\mu_o\,c_t\,r_w^2} + 3.2275\right]$ |
| 5 | **ΔP skin** [psi] | $\Delta p_{skin} = 0.869\,m\,S$ |
| 6 | p* | Xəttin $\frac{t_p+\Delta t}{\Delta t} = 1$ (yəni $\log = 0$) nöqtəsinə ekstrapolyasiyası |
| 7 | FE, $r_i$, C | B3, B8, B4 |

$p_{1hr}$-in tam Horner forması $\log\frac{t_p+1}{t_p}$ düzəlişini də ehtiva edir, amma bizdə $t_p$ çox böyük olduğu üçün bu düzəliş ≈ 0-dır.

## B7. Bourdet derivative — rejimləri tanımaq

$$\Delta p' = \frac{d\,\Delta p}{d\ln\Delta t_e},\qquad \Delta t_e = \frac{t_p\,\Delta t}{t_p + \Delta t}\ \ \text{(Agarwal ekvivalent vaxtı)}$$

Radial axında derivative sabitdir: $\;\Delta p' = \dfrac{m}{2.303} = 70.6\,\dfrac{qB\mu}{kh}$.

| Rejim | Δp (log-log) | Δp' (log-log) |
|---|---|---|
| Wellbore storage | unit slope | unit slope (Δp ilə üst-üstə) |
| WBS → radial keçidi | — | hump (S > 0 olduqda böyük) |
| **Radial (infinite-acting)** | yavaş artır | **düz xətt** → buradan m alınır |
| Qapalı sərhəd (build-up) | plato | sürətlə düşür |
| Sabit təzyiqli sərhəd (aquifer) | plato | kəskin düşür |
| Tək fault | — | 2 dəfə qalxır |

Hamarlaşdırma: $L$ = 0.1–0.2 log-dövr.

> **Bizim datada:** GL-08 ideal haldır (radial 1–72 saat). GL-01-də derivative 10 saatdan sonra sıfıra düşür, Pws 3511.5 psia-da plato edir. GL-10 qısadır və sonda derivative düşür.
> ⚠️ **Düzəliş:** əvvəlki versiyada burada "aquifer / sabit təzyiqli sərhəd" hipotezi yazılmışdı. Bu hipotez **geri götürülür**: ilkin analitik model fiti (WBS + skin + radial + sərhəd) qapalı sərhədə işarə edir. Sərhəd tipi PTA mərhələsində repo skripti ilə təsdiqlənəcək.

## B8. Tədqiqat radiusu və orta təzyiq

$$r_i = \sqrt{\frac{k\,\Delta t}{948\,\phi\,\mu\,c_t}} \approx 0.0325\sqrt{\frac{k\,\Delta t}{\phi\mu c_t}}$$

Bəzi mənbələr 0.029 sabitindən istifadə edir (Lee). $r_i < r_e$ şərti radial pəncərənin fiziki yoxlamasıdır.

**MBH ilə orta təzyiq:**

$$\bar p = p^{*} - \frac{m}{2.303}\,p_{DMBH}(t_{pDA}),\qquad t_{DA} = \frac{0.0002637\,k\,t_p}{\phi\,\mu\,c_t\,A},\quad C_A = 31.62\ \text{(dairə)}$$

> **Bizdə:** $t_p$ = $N_p/q$ çox böyükdür, ona görə p* > p̄ (GL-01: p* = 3606 psia, ölçülmüş plato 3511.5 psia). Hesabatda p*-i və p̄-ni ayrıca göstərmək lazımdır.

## B9. Tələlər və nüanslar

1. **Tək faza vs neft + su:** Perrine yanaşmasında ümumi mobillik $\lambda_t = k_o/\mu_o + k_w/\mu_w$ istifadə olunur. README yalnız $Q_o$ istəyir, ona görə alınan k **effektiv neft keçiriciliyidir**. Generator da neft istifadə edir (J uyğunluğu bunu göstərir).
2. **Gauge dərinliyi:** Δp-yə təsir etmir. Real qaz-lift quyularında shut-in-dən sonra **faza ayrılması (phase segregation)** "hump" yarada bilər; sintetik datada bu yoxdur.
3. **Radial pəncərənin seçimi** ən böyük xəta mənbəyidir. Avtomatik seçim üçün qaydalar:
   - WBS bitdikdən sonra (unit-slope-dan ≥ 1–1.5 log-dövr sonra) başlasın;
   - derivative sabit olsun (CV minimal);
   - $r_i < r_e$ olsun.
4. **Rate history:** shut-in-dən əvvəl choke pillələri var. Superposition time ilə derivative daha düzgündür. Horner yenə də tələb olunan əsas çıxışdır.

## B10. VFM xətasının PTA-ya keçməsi

VFM-də nisbi xəta $\varepsilon = \delta q/q$ olsun. m təzyiqdən alınır, ona görə dəyişmir. Onda:

$$\frac{\delta k}{k} = \varepsilon,\qquad \delta S = -1.151\log_{10}(1+\varepsilon) \approx -0.5\,\varepsilon,\qquad \delta(\Delta p_{skin}) = 0.869\,m\,\delta S$$

> **Nəticə:** VFM-də 2% xəta k-da 2% xəta verir, skin-də isə yalnız −0.01. **k-nın dəqiqliyi birbaşa VFM-in dəqiqliyidir.**

## B11. VFM ↔ PTA əlaqəsi — nəyi yoxlayır, nəyi yoxlamır

$$J_{Darcy} = \frac{0.00708\,kh}{\mu B(\ln\frac{r_e}{r_w} - 0.75 + S)},\qquad k = \frac{162.6\,qB\mu}{mh}\ \Rightarrow\ J_{Darcy} \propto q,\qquad J_{BU} = \frac{q}{p_{end} - p_{wf}} \propto q$$

> ⚠️ **Düzəliş:** hər iki J q-ya mütənasibdir, ona görə $J_{Darcy}/J_{BU}$ nisbəti q-dan asılı deyil. Qapalı dairədə PSS-də isə $J_{Darcy} \equiv q/(\bar p - p_{wf})$.
> **Nəticə:** bu dövrə **VFM-i təsdiqləmir**. O, yalnız PTA-nın daxili konsistentliyini yoxlayır: radial pəncərə, sərhəd, p̄-yə çatma. PTA-dan VFM-ə faydalı ötürülə bilən yeganə şey **p̄ (orta lay təzyiqi) ankerləridir**.

---

# HİSSƏ C — "Fizikaya nə qədər çox əsaslansaq, o qədər yaxşı?" — sintetik data riski

Qısa cavab: **yoxlanılmış fizika — bəli; yoxlanılmamış fizika — təhlükəlidir.** Generator real fizikanın sadələşdirilmiş versiyasıdır. Ona görə hər qanunu datada test edib sonra istifadə edirik.

| Hipotez | Test | Nəticə | Qərar |
|---|---|---|---|
| GOR = $R_s$ | test GOR / $R_s$ | 0.989 ± 0.073 | ✅ istifadə |
| Undersaturated | min $p_{wf}$ vs max $p_b$ | 2273 > 1595 | ✅ xətti PI |
| Build-up Darcy radial axınla konsistentdir | $J_{Darcy}$ vs $J_{BU}$ | 3.90/3.86, 5.80/5.79 | ✅ yalnız PTA QC (nisbət q-dan asılı deyil, B11) |
| Sabit gauge→datum ofseti k, S-ə təsir edir | riyazi: ofset m-də və $(p_{1hr}-p_{wf})$-də sadələşir | — | ❌ yalnız p*, p̄ datuma keçirilir |
| Fizika (choke, termal) ML-dən yaxşıdır — time-forward-da da | `benchmark_vfm.py --tf-only`, neft, 55 hədəf | 2.67–3.10% vs Ridge 5.11%, persistence 6.00% | ✅ |
| Choke orifis forması | öyrənilmiş eksponentlər | 2.05 / 0.47 / 0.46 / −0.61 | ✅ grey-box |
| Gilbert sabitləri (435/0.546/1.89) | nisbətin quyular arası səpələnməsi | 1.22–1.56× fərq | ❌ sərt kodlama yox, eksponentlər öyrənilir |
| Joule-Thomson | $(T-T_{res})/DD$ | 2.6–3.5 mF/psi | ✅ E3 estimatoru |
| Geotermal | $T_{shut}$ vs $T_{res} - g\Delta z$ | 1.1–1.44 °F/100ft | ✅ QC |
| Qapalı-tank material balance | proqnoz 11.7 psi/gün vs müşahidə ~0.3 | ❌ **rədd** | $\bar p_r(t)$ datadan |
| Choke % → bean xətti | — | yoxlanmayıb | eksponent udur |

**Sintetik datanın riskləri:**

1. **Generator sadədir** — real dünyada doğru olan qanun burada olmaya bilər. MB nümunəsi: tətbiq etsəydik, 3000 psi səhv düşmə alardıq.
2. **Generator tam bir düsturdursa**, onu "tapmaq" dəqiqliyi artırır. Amma münsiflər metodologiyanı da qiymətləndirir. Ona görə fizikanı **real mühəndislik əsaslandırması** ilə təqdim etmək lazımdır, "reverse engineering" kimi yox.
3. **Gizli həqiqətdə sensorlarda olmayan küy** ola bilər. Bu, azaldıla bilməyən xəta mərtəbəsidir; ona qarşı overfit etməyin.
4. **Domain shift:** etiketlər test rejimindədir, gündəlik proqnoz isə normal rejimdə. Fizika ekstrapolyasiyada ML-dən etibarlıdır. QC üçün: **test olmayan günlərdə E1/E2/E3-ün bir-biri ilə uyğunluğunu** yoxlayın; uyğunsuzluq xəbərdarlıq siqnalıdır.
5. **Tək estimatora güvənməyin** — ansambl riskləri bölüşdürür.

**Strategiya:** fizika = **struktur**, əmsallar = **datadan**. Hər fiziki komponentin töhfəsini ablation ilə göstərin (məs. "label fix olmadan +X%", "test-mode düzəlişi olmadan +Y%"). Bu, metodologiya balı üçündür.

---

## İstinadlar (klassik)

- Ahmed, *Reservoir Engineering Handbook* (IPR, MB, PTA) — Research-ML qovluğunda var.
- Lee, *Well Testing* (SPE Textbook); Bourdet, *Well Test Analysis: The Use of Advanced Interpretation Models*.
- Brown, *The Technology of Artificial Lift Methods* (gas lift, Thornhill-Craver).
- Gilbert (1954) choke korrelyasiyası; Ramey (1962) wellbore heat transmission.
