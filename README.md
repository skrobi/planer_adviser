# RideMore Adventure Engine

Centralna baza wiedzy i silnik rekomendacji dla planowania wypraw rowerowych, bikepackingu, gravel, MTB i ultracycling w Ridemore.bike.

> **Główna zasada produktu:** Adventure Engine ma planować wyprawę w granicach założeń użytkownika, a nie dopasowywać użytkownika do arbitralnie wygenerowanej trasy. Silnik nie ma rozstrzygać, czy wyprawa jest „wykonalna”. Ma pokazać, jakiego obciążenia wymaga wybrany plan, jak to obciążenie odnosi się do możliwości rowerzysty i jak się do niego przygotować.

## Status projektu

- Baza wiedzy: `adventure_knowledge.json`, wersja wiedzy **0.9.4-composition**.
- Aktualna gałąź robocza: `fix/data-contracts-0.9.2`.
- PR: [#1 – Audit and test RideMore adventure knowledge pipeline](https://github.com/skrobi/planer_adviser/pull/1) (otwarty, draft; nie scalony).
- Referencyjny interpreter: Python w `tests/adventure_engine_runner.py`.
- Testy GitHub Actions dla aktualnego modelu GPX: [run 41847569952 – success](https://github.com/skrobi/planer_adviser/actions/runs/41847569952).
- **Ważne:** repozytorium nie zawiera jeszcze produkcyjnego silnika PHP ani integracji z runtime Ridemore. Obecne testy sprawdzają kontrakt wiedzy i interpreter referencyjny, a nie działanie produkcyjnej aplikacji.

## 1. Co zostało zrobione

### 1.1. Baza wiedzy i modele

W `adventure_knowledge.json` zbudowano deklaratywną bazę wiedzy obejmującą m.in.:

- profile wypraw: touring, bikepacking, ultra, gravel adventure, MTB adventure, road expedition, brevet i inne;
- schemat profilu rowerzysty oraz słownik danych i jednostek;
- modele liczbowe i jawne formuły, m.in. zapotrzebowanie etapu (`stage_demand`), żywienie, nawodnienie, zmęczenie/tempo i margines czasu;
- ekspertów/reguły dla bezpieczeństwa, żywienia, nawodnienia, logistyki, sprzętu, ultra i strategii;
- drzewo decyzyjne, katalog parametrów, szablony rekomendacji i kontrakt wejścia/wyjścia;
- obsługę brakujących danych: brak wartości nie jest traktowany jako zero ani uzupełniany wymyśloną wartością;
- rozróżnienie danych zadeklarowanych przez użytkownika, wyliczonych i nieznanych.

Baza zawiera również źródła i założenia naukowe/operacyjne. Wartości progowe są opisane jako heurystyki lub zakresy planistyczne tam, gdzie nie są uniwersalnymi granicami fizjologicznymi.

### 1.2. Żywienie i nawodnienie

Przygotowano modele i reguły do:

- szacowania zapotrzebowania na węglowodany podczas wysiłku;
- oceny zadeklarowanego zapasu jedzenia/produktów CHO;
- szacowania potrzeb płynowych i planowania uzupełnień;
- sygnalizowania brakujących danych i niepewności;
- odróżniania nieznanego zapasu od zapasu faktycznie niewystarczającego.

Jeżeli użytkownik nie zadeklarował zapasu jedzenia, silnik nie może twierdzić, że jego plecak jest niewystarczający. Może wskazać orientacyjne zapotrzebowanie i poprosić o dane potrzebne do oceny zapasu.

Punkt POI na mapie nie dowodzi, że jest tam dostępna odpowiednia ilość wody lub jedzenia. Dostępność, ilość i godziny otwarcia wymagają osobnej weryfikacji.

### 1.3. Bezpieczeństwo i rekomendacje

Dodano m.in.:

- krytyczne ostrzeżenie dla bardzo długiego, jednego etapu bez snu u początkującego;
- konkretne kryteria przerwania jazdy z katalogu rekomendacji;
- reguły dotyczące pierwszego bikepackingu, długości etapu względem doświadczenia i długiego wysiłku;
- ostrożniejsze opisy heurystyk snu – próg ostrzegawczy nie jest gwarancją bezpieczeństwa.

### 1.4. Składanie rekomendacji

Wprowadzono deterministyczny kontrakt składania rekomendacji w trzy karty:

1. `safety_and_staging` – bezpieczeństwo i kwestie organizacji etapów;
2. `nutrition` – żywienie;
3. `hydration` – nawodnienie.

Karty łączą uruchomione reguły, zachowują ich źródła i status danych. Nie mogą wymyślać liczby etapów, zadeklarowanego zapasu ani potwierdzonej dostępności POI.

### 1.5. Interpreter i testy

W repozytorium znajdują się:

- `tests/adventure_engine_runner.py` – interpreter wykonujący modele i reguły z JSON;
- `tests/scenarios.json` – 10 scenariuszy regresyjnych;
- `tests/verify_adventure_engine.py` – weryfikator oczekiwanych rezultatów;
- `tests/test_knowledge_contract.py` i `tests/test_adventure_engine_execution.py` – testy kontraktu i wykonania;
- `tests/kotlina400-bikepacking-route.gpx` – rzeczywisty plik GPX do przyszłych testów analizy i podziału trasy;
- `VERIFICATION_REPORT.md` – zakres weryfikacji, korekty, interpretacja naukowa i ograniczenia;
- `.github/workflows/knowledge-tests.yml` – automatyczne testy w GitHub Actions.

Uruchomienie lokalne (Python 3.11+):

```bash
python -m unittest discover -s tests -v
python tests/adventure_engine_runner.py
python tests/verify_adventure_engine.py
```

## 2. Ustalona koncepcja planowania wypraw

### 2.1. Założenia użytkownika są nadrzędne

Liczba dni wskazana przez użytkownika jest wiążącym parametrem planu. Jeśli użytkownik planuje cztery dni, silnik dzieli trasę na cztery dni – nie zmienia samodzielnie planu na pięć, siedem czy dziewięć dni.

Jeżeli liczba dni nie została podana, silnik może zapytać o nią lub zaproponować warianty, ale nie może przedstawiać arbitralnego wyboru jako decyzji użytkownika.

Nie budujemy osobnego werdyktu „wykonalne/niewykonalne”. Każdą trasę można próbować przejechać, ale koszt wysiłku i ryzyko mogą być bardzo różne. Zadaniem silnika jest te konsekwencje wyjaśnić.

### 2.2. Oceniamy obciążenie, nie wydajemy zakazu

Docelowy komunikat powinien być zrozumiały i odnosić się do danych rowerzysty, np.:

> Przy Twoim deklarowanym doświadczeniu czterodniowy przejazd tej trasy będzie bardzo wymagający. Średnio przypada X km i Y m przewyższenia dziennie. W porównaniu z Twoimi typowymi przejazdami oznacza to większy dystans i znaczne obciążenie podjazdami. Poniżej przedstawiamy bilans każdego etapu oraz zalecenia dotyczące tempa, żywienia, nawodnienia i regeneracji.

Ocena powinna rozdzielać:
- **obciążenie zewnętrzne:** dystans, przewyższenie, czas, nawierzchnia i trudność techniczna;
- **reakcję/obciążenie wewnętrzne:** intensywność i odczuwany wysiłek, o ile mamy odpowiednie dane (np. tętno, moc, RPE);
- **dopasowanie do rowerzysty:** porównanie wymagań trasy z jego typowymi dystansami, prędkością, doświadczeniem wielodniowym i wspinaczkowym;
- **kumulację zmęczenia:** narastające obciążenie kolejnych dni, a nie tylko osobną ocenę każdego etapu.

Nie wolno wyciągać precyzyjnych wniosków o obciążeniu fizjologicznym wyłącznie z dystansu i GPX.

## 3. Co trzeba zrobić

Poniższe punkty są planem prac. Nie należy traktować ich jako już zaimplementowanych funkcji.

### Etap A – Route Analyzer (analiza GPX)

<badge color="success">Prototyp Python wykonany</badge>

W `tests/route_stage_planner.py` zaimplementowano referencyjny parser GPX, obliczanie dystansu, profil wysokości, filtrowanie wysokości, nachylenia oraz sumy podjazdów i zjazdów. Wyniki surowe i wygładzone są raportowane oddzielnie. To prototyp do walidacji, nie gotowy moduł produkcyjny.

Do wykonania w PHP i przed produkcyjnym użyciem pozostają: pełna walidacja przerw/duplikatów/segmentów GPX, filtrowanie zależne od odległości zamiast liczby punktów, walidacja wysokości względem DEM/LiDAR, analiza nawierzchni i klasyfikacja trudności technicznej oraz metadane źródła i pewności dla każdego parametru.

### Etap B – Stage Planner (podział na dni)

<badge color="success">Prototyp Python wykonany</badge>

Prototyp dzieli trasę na dokładnie zadaną liczbę dni, optymalizując równomierność szacowanego czasu jazdy. Limit godzin jest miękkim ograniczeniem: przekroczenie jest raportowane, ale silnik nie zmienia liczby dni użytkownika. Zwracane są kilometraże i współrzędne granic etapów.

Do wykonania: przeniesienie algorytmu do PHP, uwzględnienie dokładnych punktów granicznych bez utraty fragmentów trasy, rozszerzenie funkcji celu o przewyższenie/nawierzchnię/techniczne odcinki i ewentualne POI oraz walidacja na większej liczbie rzeczywistych tras.

Wejścia:
- GPX po analizie;
- liczba dni zadana przez użytkownika;
- profil rowerzysty i jego osiągi;
- preferowany dzienny czas jazdy / długość etapu;
- styl wyprawy, rower i bagaż;
- preferencje noclegowe i samowystarczalność;
- dostępne POI, jeżeli zostały dostarczone i zweryfikowane.

Model powinien:
- podzielić trasę na dokładnie zadaną liczbę etapów;
- nie dzielić wyłącznie według równego dystansu;
- równoważyć czas, dystans, przewyższenie i trudność techniczną;
- uwzględniać doświadczenie rowerzysty jako podstawę oceny obciążenia, a nie jako arbitralny zakaz;
- uwzględniać miejsca noclegu, wody i zaopatrzenia, jeśli istnieją wiarygodne dane;
- zwracać kilka możliwych podziałów tylko wtedy, gdy użytkownik chce porównania;
- zachowywać dokładne punkty początku/końca każdego etapu.

Jeśli nie ma danych POI, można zaproponować geograficzne punkty zakończenia etapów, ale trzeba je oznaczyć jako nieweryfikowane pod kątem noclegu i zaopatrzenia. Nie wolno wymyślać noclegów ani punktów uzupełnień.

### Etap C – Stage Demand & Time Model (czas i zapotrzebowanie)

<badge color="warning">Wersja wstępna w Pythonie</badge>

Prototyp szacuje czas jazdy z modelu fizycznego (grawitacja, toczenie, aerodynamika) oraz kalibracji CP/FTP lub prędkością typową. Oblicza też pracę mechaniczną i przybliżony koszt metaboliczny. Nie ma jeszcze zwalidowanego modelu wielodniowego zmęczenia, postojów i czasu całkowitego.

Do wykonania: kalibracja i walidacja na rzeczywistych przejazdach, zakresy niepewności, wpływ nawierzchni/wiatru/techniki i postojów oraz implementacja w PHP.

Dla każdego etapu obliczać:
- czas jazdy na podstawie dystansu, przewyższenia, nawierzchni, nachylenia, trudności i możliwości rowerzysty;
- czas postojów oraz szacowany czas całkowity;
- przedział czasu i poziom pewności, zamiast jednej pozornie precyzyjnej liczby;
- wpływ bagażu i roweru, jeżeli dane są dostępne.

Model czasu musi być spójny z analizą GPX i profilem użytkownika. Nie może zakładać, że średnia prędkość z płaskiej trasy będzie obowiązywać na trudnym gravelu lub w górach.

### Etap D – Load Assessment (obciążenie dzienne i skumulowane)

Dla każdego dnia i całej wyprawy oceniać osobno:
- dystans względem typowych i najdłuższych przejazdów użytkownika;
- przewyższenie i obciążenie wspinaczkowe względem jego doświadczenia;
- przewidywany czas wysiłku;
- trudność nawierzchni i odcinków technicznych;
- obciążenie kolejnych dni i ograniczoną regenerację;
- niepewność wynikającą z brakujących danych.

Wynik ma wyjaśniać **dlaczego** etap może być trudny, np. „dystans jest 2,5 raza większy od Twojego typowego przejazdu” lub „przewyższenie dzienne jest wysokie w zestawieniu z deklarowanym doświadczeniem wspinaczkowym”. Porównania muszą wynikać z rzeczywistych danych użytkownika.

Nie tworzyć jednej magicznej liczby „trudności”, jeśli nie ma zwalidowanego modelu i czytelnej interpretacji. Można używać kategorii opisowych, ale ich progi wymagają uzasadnienia i testów.

### Etap E – Nutrition Planner (żywienie)

Dla każdego etapu, na podstawie szacowanego czasu i intensywności:
- szacować zakres podaży węglowodanów na godzinę;
- obliczać orientacyjną ilość CHO na etap;
- uwzględniać tolerancję przewodu pokarmowego, wytrenowanie żywieniowe i preferowane produkty;
- rozdzielać żywienie podczas jazdy od całkowitego wydatku energetycznego i posiłku regeneracyjnego;
- przeliczać plan na zadeklarowane żele, batony i inne produkty;
- uwzględniać możliwość uzupełnienia zapasów na trasie, ale wyłącznie na podstawie zweryfikowanych POI.

Nie wolno utożsamiać kalorii wydatkowanych z gramami węglowodanów, które należy przyjąć podczas jazdy. Wartości są zaleceniami planistycznymi, nie diagnozą ani indywidualną poradą medyczną.

### Etap F – Hydration Planner (nawodnienie i elektrolity)

Dla każdego etapu:
- szacować zakres płynów na godzinę i na etap;
- uwzględniać temperaturę/warunki, czas wysiłku, masę ciała i indywidualne dane o potliwości, jeżeli dostępne;
- uwzględniać pojemność bidonów i bukłaków;
- planować, kiedy potrzebne jest uzupełnienie;
- wskazywać elektrolity z odpowiednim poziomem ostrożności;
- rozróżniać szacowane zapotrzebowanie od faktycznie dostępnej wody.

Nie traktować stałej wartości L/h jako uniwersalnej recepty. POI bez potwierdzonej dostępności nie może być przedstawiony jako pewne źródło wody.

### Etap G – Recovery Advisor i Safety Advisor

- Ocena regeneracji pomiędzy etapami i narastania zmęczenia.
- Uwzględnienie snu, przerw, pory dnia i jazdy nocnej.
- Wskazówki dotyczące tempa, przerw i ograniczenia intensywności.
- Kryteria przerwania jazdy i sygnały alarmowe.
- Powiązanie ostrzeżeń z konkretnymi danymi etapu i rowerzysty.
- Krytyczne ostrzeżenia mają być widoczne i zachowywać konkretne działania, nie tylko ogólny komunikat.

### Etap H – Integracja i interfejs rekomendacji

Wyniki wszystkich modułów muszą korzystać z jednego wspólnego modelu etapów. Dla każdego dnia UI powinien pokazać:
- dystans, przewyższenie i profil;
- szacowany czas jazdy i całkowity;
- ocenę obciążenia oraz powody tej oceny;
- zapotrzebowanie na CHO i płyny;
- plan uzupełnień i POI ze statusem weryfikacji;
- regenerację, ostrzeżenia i zalecane działania.

Na poziomie całej wyprawy pokazać sumaryczne obciążenie, kumulację zmęczenia, najtrudniejsze etapy i najważniejsze ryzyka.

### Etap I – PHP runtime i testy end-to-end

- Przenieść/zaimplementować interpreter formuł i reguł w produkcyjnym PHP.
- Zapewnić zgodność wyników PHP z interpreterem referencyjnym Python.
- Dodać testy dla GPX, podziału etapów, brakujących danych, POI, żywienia, nawodnienia i kumulacji zmęczenia.
- Testować scenariusze łatwe, trudne, wielodniowe i z niepełnymi danymi.
- Weryfikować nie tylko liczby, ale także to, czy komunikaty nie wyciągają wniosków bez podstaw.
- Zintegrować wynik z Ridemore plannerem i profilem użytkownika.

## 4. Przykładowy plik testowy: Kotlina400

W repozytorium znajduje się `tests/kotlina400-bikepacking-route.gpx`, rzeczywisty ślad trasy w Polsce.

Wstępna analiza pliku wykonana poza silnikiem:
- 11 428 punktów śladu;
- około **412,8 km**;
- około **12 671 m sumy podjazdów** według surowych różnic wysokości.

**Uwaga:** suma podjazdów pochodzi z surowych danych wysokościowych GPX i wymaga wygładzenia oraz walidacji, np. względem wiarygodnego modelu wysokości. Nie jest jeszcze zatwierdzonym wynikiem Route Analyzera.

Wstępne ręczne podziały na 4–7 dni były wyłącznie eksperymentem matematycznym. Nie są funkcją silnika, nie uwzględniają jeszcze rzeczywistych noclegów, POI, czasu ani indywidualnych osiągów i nie powinny być traktowane jako gotowy plan wyprawy.

Kotlina400 powinna stać się głównym testem regresyjnym dla Route Analyzer i Stage Planner. Należy sprawdzić m.in.:
- zachowanie całkowitego dystansu po podziale;
- sumy przewyższeń etapów względem profilu źródłowego;
- dokładne położenie granic etapów;
- zachowanie liczby dni podanej przez użytkownika;
- różne profile rowerzystów przy tej samej trasie i liczbie dni;
- zmianę czasu, CHO, płynów i oceny obciążenia wraz ze zmianą parametrów użytkownika.

## 5. Docelowy przepływ danych

```text
GPX + profil rowerzysty + założenia wyprawy
                    |
                    v
             Route Analyzer
                    |
                    v
              Stage Planner
          (liczba dni od użytkownika)
                    |
                    v
          Stage Demand / Time Model
                    |
          +---------+---------+
          |         |         |
          v         v         v
        Load     Nutrition  Hydration
      Assessment  Planner   Planner
          |         |         |
          +---------+---------+
                    |
                    v
       Recovery Advisor + Safety Advisor
                    |
                    v
       Adventure Recommendation Engine
                    |
                    v
        Plan całej wyprawy + karty etapów
```

## 6. Zasady, których nie wolno naruszyć

1. **Użytkownik określa plan.** Silnik nie zmienia samodzielnie liczby dni ani nie narzuca arbitralnych limitów.
2. **Brak danych nie oznacza zera.** Nieznane wartości pozostają nieznane.
3. **Nie wymyślamy faktów.** Nie tworzymy nieistniejących etapów, noclegów, punktów wody ani zapasów.
4. **Obciążenie musi mieć uzasadnienie.** Każde ostrzeżenie powinno wskazywać konkretne parametry i porównanie z profilem rowerzysty.
5. **Oddzielamy fakty, szacunki i rekomendacje.** Każdy wynik ma status i poziom pewności.
6. **Czas jest podstawą planowania potrzeb.** Żywienie i nawodnienie liczymy dla przewidywanego czasu konkretnego etapu, nie tylko dystansu.
7. **Uwzględniamy kumulację.** Dzień 4 nie jest oceniany tak, jakby był pierwszym dniem wyprawy.
8. **Nie udajemy medycznej precyzji.** Wartości fizjologiczne są zakresami planistycznymi, z uwzględnieniem indywidualnej zmienności.
9. **Jedno źródło prawdy.** Moduły korzystają ze wspólnego kontraktu etapów i tych samych danych wejściowych.
10. **Testujemy zachowanie, nie tylko składnię.** Silnik ma umieć powiedzieć „nie wiem”, gdy dane nie uzasadniają konkretnej rekomendacji.

## 7. Najbliższa kolejność prac

1. Zdefiniować wspólny kontrakt danych `route_analysis` i `stages[]`.
2. Zaimplementować i przetestować Route Analyzer na Kotlina400, w tym korektę profilu wysokości.
3. Zaimplementować Stage Planner, w którym liczba dni jest twardym parametrem użytkownika.
4. Zbudować model czasu dla każdego etapu.
5. Zbudować Load Assessment: porównanie wymagań etapów z osiągami rowerzysty oraz obciążenie skumulowane.
6. Rozszerzyć Nutrition i Hydration z poziomu pojedynczego etapu na wielodniowy plan.
7. Dodać regenerację i powiązać ją z bezpieczeństwem.
8. Zbudować spójne karty całej wyprawy i poszczególnych dni.
9. Wykonać PHP parity i testy end-to-end w Ridemore.

---

**Stan na 2026-11-04:** baza wiedzy, modele i pierwsza warstwa rekomendacji mają działający interpreter referencyjny i zielone testy CI. Największa brakująca część to analiza rzeczywistego GPX, podział na etapy według założeń użytkownika oraz powiązanie każdego etapu z czasem, obciążeniem, żywieniem, nawodnieniem i regeneracją.
## 8. Pierwszy referencyjny model GPX i podziału etapów (Python)

Dodano eksperymentalny, wykonywalny model referencyjny:
- `tests/route_stage_planner.py` – parser GPX, analiza profilu wysokości, model fizyczny jazdy i podział na zadaną liczbę etapów;
- `tests/test_route_stage_planner.py` – testy syntetycznej trasy oraz rzeczywistego pliku Kotlina400.

### Co liczy prototyp

1. Parsuje punkty GPX (lat/lon/elevation) i oblicza dystans geodezyjny.
2. Wygładza profil wysokości filtrem medianowym i średnią kroczącą, następnie agreguje trasę do krótkich odcinków dystansowych.
3. Wylicza nachylenie, podjazdy i zjazdy dla odcinków.
4. Szacuje prędkość na odcinku z równania mocy potrzebnej do pokonania grawitacji, oporów toczenia i oporu aerodynamicznego.
5. Uwzględnia łączną masę rowerzysty, roweru i bagażu, współczynnik toczenia, CdA, gęstość powietrza, wiatr i sprawność napędu.
6. Kalibruje dostępną moc z CP, FTP (z konfigurowalnym współczynnikiem turystycznym) albo typowej prędkości na zadanym profilu referencyjnym.
7. Oblicza mechaniczną pracę i przybliżony koszt metaboliczny, używając jawnego założenia gross efficiency.
8. Dzieli trasę na dokładnie wskazaną liczbę dni, minimalizując różnice szacowanego czasu jazdy. Limit godzin dziennie jest ograniczeniem miękkim: jeśli zostaje przekroczony, etap jest oznaczony, ale liczba dni użytkownika nie jest zmieniana.
9. Zwraca kilometraż początku/końca etapów i współrzędne granic, aby przyszły PHP mógł wyświetlić podział na mapie.

### Przykładowe uruchomienie

```bash
python tests/route_stage_planner.py tests/kotlina400-bikepacking-route.gpx \\
  --days 4 --body-mass-kg 75 --bike-mass-kg 14 --luggage-mass-kg 8 \\
  --typical-speed-kmh 18 --max-hours 12 --output kotlina400-4days.json
```

Można podać `--critical-power-w` albo `--ftp-w` zamiast `--typical-speed-kmh`. CP/FTP jest lepszym wejściem, jeżeli pochodzi z wiarygodnego pomiaru. Średnia prędkość jest tylko kalibracją przybliżoną i wymaga informacji, na jakiej nawierzchni i profilu została osiągnięta.

### Model fizyczny

Dla każdego odcinka szacowana moc na kole wynika z sumy:
- składowej grawitacyjnej: masa całego układu × g × nachylenie × prędkość;
- oporów toczenia: współczynnik toczenia × masa × g × prędkość;
- oporu aerodynamicznego: 0,5 × gęstość powietrza × CdA × prędkość względna do wiatru do kwadratu × prędkość.

Następnie model rozwiązuje prędkość odpowiadającą przyjętej mocy trwałej. Mechaniczna praca jest przeliczana na szacunkowy koszt metaboliczny przez podzielenie przez gross efficiency. Współczynniki są jawne i konfigurowalne; domyślne wartości nie są indywidualną kalibracją sportowca.

### Ograniczenia prototypu – nie traktować jako gotowej prognozy

- Wygładzanie jest obecnie zależne od liczby punktów GPX, a nie od stałego okna odległości; wymaga dalszej walidacji na śladach o różnej gęstości.
- Surowe dane wysokości mogą być zaszumione. Prototyp raportuje surowe i wygładzone przewyższenie osobno; docelowo należy preferować wiarygodny DEM/LiDAR lub zweryfikowany profil wysokości.
- Prędkość typowa nie określa jednoznacznie mocy ani zdolności wspinaczkowych. Wymaga profilu referencyjnego; przy braku CP/FTP wynik ma wysoką niepewność.
- Model nie ma jeszcze zwalidowanego profilu mocy na wielu czasach, mocy progowej na podjazdach, indywidualnego kosztu jazdy na różnych nawierzchniach ani wpływu zmęczenia z poprzednich dni.
- Powierzchnia, trudność techniczna, wiatr, postoje i warunki pogodowe są uwzględniane tylko wtedy, gdy zostaną dostarczone jako dane wejściowe. Domyślne współczynniki są uproszczeniem.
- Koszt metaboliczny nie jest automatycznie ilością kalorii, które należy zjeść, ani gramami węglowodanów do spożycia podczas jazdy.
- Wynik jest prototypem badawczo-inżynierskim, nie poradą treningową ani medyczną.

### Podstawa naukowa i interpretacja

Model opiera się na mechanice jazdy rowerem (grawitacja, toczenie, aerodynamika), ale fizyczny model trasy nie opisuje samodzielnie fizjologii zawodnika.

- Martin et al., *Modeling road-cycling performance* (1995) – model pierwszych zasad, uwzględniający m.in. wiatr, opony, masę i opory: https://pubmed.ncbi.nlm.nih.gov/7615475/
- Millour et al. (2023) – modelowanie jazdy w warunkach terenowych i użycie danych GPS, prędkości oraz nachylenia: https://journals.sagepub.com/doi/full/10.1177/17479541221106386
- Berjisian et al. (2023) – niepewność profili wysokości i nachylenia z GPS; wysokiej jakości LiDAR/DEM jest lepszy, a filtrowanie i czyszczenie danych poprawia wyniki: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0295027
- Ettema & Lorås (2009) – przegląd sprawności energetycznej w kolarstwie: https://pubmed.ncbi.nlm.nih.gov/19229554/
- Chorley & Lamb (2020) – critical power (CP), W' i ograniczenia stosowania modelu do intensywności wysiłku: https://pmc.ncbi.nlm.nih.gov/articles/PMC7552657/
- Poole et al. (2016) – fizjologiczne znaczenie critical power: https://pubmed.ncbi.nlm.nih.gov/27031742/
- MacDougall et al. (2022) – złożoność i ograniczenia interpretacji sprawności w kolarstwie: https://pubmed.ncbi.nlm.nih.gov/35253274/

### Kontrakt do przyszłego PHP

PHP powinien odtworzyć te same kroki i zwracać te same pola, nie kopiować bezrefleksyjnie implementacji Pythona. Minimalne wejście:
- GPX lub znormalizowany profil odcinków;
- `days`, `max_riding_hours_per_day`;
- masa ciała, masa roweru, masa bagażu;
- CP albo FTP, albo prędkość typowa wraz z profilem referencyjnym;
- gross efficiency (lub jawne założenie);
- parametry roweru/trasy: Crr, CdA, wiatr, nawierzchnia i trudność.

Minimalne wyjście:
- analiza trasy z surowym i skorygowanym profilem wysokości;
- dokładnie N etapów;
- dla każdego etapu dystans, podjazdy/zjazdy, czas jazdy, średnia prędkość, praca mechaniczna, szacowany koszt metaboliczny, współrzędne granic i przekroczenie limitu czasu;
- wersja modelu, źródła parametrów, status brakujących danych i poziom niepewności.

**Ważne:** ten prototyp nie zastępuje jeszcze wcześniejszego planu prac dla wielodniowego Load Assessment, żywienia, nawodnienia i regeneracji. Dostarcza im wspólny, policzony profil etapów, który będzie podstawą kolejnych modeli.


## 9. Docelowa architektura komunikacji: Planer → analiza → wyniki

PHP ma być warstwą produkcyjną i jedynym miejscem, z którego Planer Ridemore uruchamia analizę. Moduły nie powinny komunikować się bezpośrednio z interfejsem Planera ani niezależnie pobierać danych użytkownika. Planer przekazuje kompletny, jawny zestaw wejściowy do jednego serwisu Adventure Engine, a serwis zwraca ustandaryzowany wynik.

### Schemat przepływu

```text
┌──────────────────────────────┐
│ RIDEMORE PLANNER (UI)        │
│                              │
│ GPX + dni + limity + profil  │
│ rowerzysty + rower + bagaż   │
└──────────────┬───────────────┘
               │ żądanie analizy
               ▼
┌──────────────────────────────┐
│ PHP: AdventureEngineService  │
│                              │
│ walidacja wejścia            │
│ uzupełnienie danych profilu  │
│ wersjonowanie żądania        │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ RouteAnalyzer                │
│ GPX → profil odcinków        │
│ dystans / wysokość / grade   │
│ segmenty / jakość danych     │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ StagePlanner                 │
│ profil + liczba dni + limity │
│ → granice etapów             │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ StageDemandModel             │
│ czas / prędkość / moc / praca│
│ energia mechaniczna i koszt  │
│ metaboliczny (szacunek)      │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ AdventureEngine              │
│ obciążenie / żywienie / woda │
│ bezpieczeństwo / regeneracja│
└──────────────┬───────────────┘
               │ jeden kontrakt wyniku
               ▼
┌──────────────────────────────┐
│ PHP: AdventurePlanResult     │
│ summary + stages[] + warnings│
│ estimates + provenance      │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ RIDEMORE PLANNER (UI)        │
│ mapa + profil + karty dni    │
│ ostrzeżenia + edycja planu   │
└──────────────────────────────┘
```

### Odpowiedzialności warstw

| Warstwa | Odpowiedzialność | Nie powinna |
|---|---|---|
| Planer UI | Zebrać GPX, liczbę dni, limity i preferencje; pokazać wynik | Samodzielnie liczyć fizyki trasy |
| AdventureEngineService (PHP) | Walidować wejście, wywołać moduły w kolejności, złożyć odpowiedź | Zawierać logiki widoku lub duplikować obliczenia |
| RouteAnalyzer | Przetworzyć GPX na znormalizowane odcinki i profil wysokości | Decydować o liczbie dni |
| StagePlanner | Wyznaczyć dokładnie tyle etapów, ile podał użytkownik | Zmieniać plan użytkownika bez jego zgody |
| StageDemandModel | Oszacować czas, prędkość, moc i koszt energetyczny | Udawać pomiar, gdy wejściem są szacunki |
| Moduły Adventure Engine | Ocenić obciążenie, CHO, płyny, bezpieczeństwo i regenerację | Wymyślać brakujące dane lub potwierdzoną dostępność POI |
| AdventurePlanResult | Zwrócić jeden stabilny kontrakt dla UI | Zawierać formatowanie zależne od konkretnego widoku |

### Kontrakt wejściowy – przykład

```json
{
  "request_id": "uuid",
  "model_version": "gpx-physics-stage-planner-0.1",
  "route": {
    "format": "gpx",
    "content": "<GPX albo identyfikator pliku>"
  },
  "trip": {
    "days": 4,
    "max_riding_hours_per_day": 8,
    "preferred_riding_hours_per_day": 6
  },
  "rider": {
    "body_mass_kg": 75,
    "critical_power_w": null,
    "ftp_w": null,
    "typical_speed_kmh": 18,
    "reference_grade": 0
  },
  "equipment": {
    "bike_mass_kg": 14,
    "luggage_mass_kg": 8
  },
  "model_parameters": {
    "gross_efficiency": 0.22,
    "crr": 0.006,
    "cda": 0.4,
    "air_density": 1.2,
    "headwind_mps": 0
  }
}
```

To jest ilustracyjny kontrakt. W produkcji należy walidować jednostki, zakresy, pochodzenie danych i brakujące pola. Nie wolno wpisywać wartości przykładowych jako domyślnych danych konkretnego użytkownika.

### Kontrakt wyjściowy – przykład

```json
{
  "request_id": "uuid",
  "model_version": "gpx-physics-stage-planner-0.1",
  "status": "completed_with_estimates",
  "route_summary": {
    "distance_km": 412.8,
    "elevation_gain_m": 0,
    "elevation_gain_source": "smoothed_gpx_estimate"
  },
  "trip_summary": {
    "requested_days": 4,
    "actual_days": 4,
    "total_estimated_moving_hours": 0,
    "time_limit_exceeded_days": []
  },
  "stages": [
    {
      "day": 1,
      "distance_km": 0,
      "elevation_gain_m": 0,
      "estimated_moving_hours": 0,
      "estimated_average_speed_kmh": 0,
      "mechanical_work_kj": 0,
      "estimated_metabolic_energy_kcal": 0,
      "start_coordinate": {"lat": 0, "lon": 0},
      "end_coordinate": {"lat": 0, "lon": 0},
      "time_limit_overrun_hours": 0,
      "load_status": "estimated"
    }
  ],
  "warnings": [],
  "data_quality": {
    "elevation": "estimated",
    "surface": "unknown",
    "power_calibration": "typical_speed_proxy",
    "uncertainty": "high"
  }
}
```

Wartości zerowe w powyższym przykładzie są wyłącznie placeholderami schematu, nie wartościami domyślnymi ani prawidłowym wynikiem. W produkcyjnym JSON pola nieznane powinny być `null` lub mieć jawny status `unknown`, a nie zero.

### Zasady komunikacji

1. Planer wysyła jedno żądanie do PHP, nie wywołuje osobno każdego eksperta.
2. PHP waliduje wejście i uruchamia moduły w ustalonej kolejności.
3. Route Analyzer zwraca znormalizowany profil odcinków; Stage Planner i pozostałe moduły pracują na tym samym profilu.
4. Stage Planner zachowuje liczbę dni zadaną przez użytkownika.
5. Każdy wynik liczbowy ma jednostkę, źródło/pochodzenie i status: measured, declared, calculated, estimated lub unknown.
6. PHP zwraca jeden obiekt wyniku. UI tylko go prezentuje; nie przelicza fizyki.
7. Po zmianie liczby dni, limitu lub danych rowerzysty Planer wysyła nowe żądanie analizy. Można później dodać cache po hashu GPX + parametrów.
8. Wersja modelu i parametrów musi być zapisana przy wyniku, aby można było odtworzyć obliczenia.

### Kolejność implementacji PHP

1. Zdefiniować klasy/kontrakty DTO: `AdventurePlanRequest`, `RouteAnalysis`, `RouteSegment`, `StagePlan`, `StageResult`, `AdventurePlanResult`.
2. Zaimplementować `RouteAnalyzer` i testy zgodności z Pythonem na tych samych plikach GPX.
3. Zaimplementować `StagePlanner` i porównać granice etapów oraz sumy z Pythonem.
4. Zaimplementować `StageDemandModel`; porównywać czas, prędkość, pracę i energię z tolerancją numeryczną.
5. Podłączyć istniejący Adventure Engine (reguły JSON) do wspólnego `stages[]`.
6. Udostępnić jedną metodę serwisu PHP, np. `AdventureEngineService::analyze(AdventurePlanRequest $request)`.
7. Dodać endpoint API dla Planera, autoryzację, limity rozmiaru GPX, obsługę błędów i logowanie wersji modelu.
8. Dopiero potem zintegrować UI Planera i widok wyników.

**Granica odpowiedzialności:** Python pozostaje narzędziem referencyjnym i testowym. Docelowo runtime produkcyjny działa w PHP; nie wymagamy uruchamiania Pythona na serwerze Ridemore.


## 3. Etap 4 – uproszczenie wizarda i kontrakt profilu (2026-11-05)

Przygotowano zmianę na gałęzi `feature/stage-4-wizard-simplification`:

- krótki tryb jest domyślny i ograniczony do maksymalnie 8 pól, które mogą wymagać odpowiedzi;
- dane z profilu rowerzysty, historii przejazdów, planera GPX i adaptera POI mają być uzupełniane automatycznie;
- pytania o współczynnik potliwości, masę ciała, tolerancję wysokiego CHO i podobne parametry nie należą do wizarda wyprawy – są odłożone do przyszłego Advanced Trainer;
- nie pytamy ręcznie o kilometry zweryfikowanych punktów wody i jedzenia – dane powinny pochodzić z bazy POI Ridemore;
- szczegółowy wykaz jedzenia i wartości CHO produktów jest opcjonalny w trybie zaawansowanym;
- usunięto arbitralne założenie 10 kg bagażu jako wartości użytkownika; brak masy bagażu pozostaje nieznany;
- dodano klasyfikację pól profilu według pochodzenia: declared, observed, measured, equipment, preferences i trip-specific;
- dodano testy kontraktu UX wizarda.

**Uwaga implementacyjna:** `ask_if_missing`, `required_when_missing` i `prefill_from` są deklaracją kontraktu. Renderer PHP musi je obsłużyć przed pokazaniem pytań. Obecne testy JSON nie potwierdzają jeszcze działania produkcyjnego wizarda.


## Stage 5 contract work

The current knowledge base adds a canonical multi-stage contract: stable stage identity, moving time separated from stops/sleep, trip-level completeness, POI availability/quantity/capacity/freshness/detour semantics, and a transparent stage-load ledger. The contract intentionally does not invent a cumulative fatigue score or claim that POI presence proves resupply.

See `stage5_contracts` in `adventure_knowledge.json`. This is a declarative target contract; the Python reference interpreter and production PHP engine do not yet execute multi-stage inventory carry-forward or POI arrival-time assessment.


### Executable multi-stage inventory reference

The Python reference runner executes `stage5_contracts.inventory_ledger` for water and CHO. Each stage supplies `inventory_need.water_l`, `inventory_need.cho_g` and route-positioned `inventory_events`; initial stock is under `trip.inventory_start`. Only verified, available and quantitatively confirmed resupply changes stock. Demand is allocated linearly by route distance as an explicit approximation. See `tests/test_inventory_ledger.py`. This is not production PHP.
