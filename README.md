# RideMore Adventure Engine

Centralna baza wiedzy i silnik rekomendacji dla planowania wypraw rowerowych, bikepackingu, gravel, MTB i ultracycling w Ridemore.bike.

> **Główna zasada produktu:** Adventure Engine ma planować wyprawę w granicach założeń użytkownika, a nie dopasowywać użytkownika do arbitralnie wygenerowanej trasy. Silnik nie ma rozstrzygać, czy wyprawa jest „wykonalna”. Ma pokazać, jakiego obciążenia wymaga wybrany plan, jak to obciążenie odnosi się do możliwości rowerzysty i jak się do niego przygotować.

## Status projektu

- Baza wiedzy: `adventure_knowledge.json`, wersja wiedzy **0.9.4-composition**.
- Aktualna gałąź robocza: `fix/data-contracts-0.9.2`.
- PR: [#1 – Audit and test RideMore adventure knowledge pipeline](https://github.com/skrobi/planer_adviser/pull/1) (otwarty, draft; nie scalony).
- Referencyjny interpreter: Python w `tests/adventure_engine_runner.py`.
- Ostatni workflow dla aktualnego HEAD: [GitHub Actions – success](https://github.com/skrobi/planer_adviser/actions/runs/41843541954).
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

- Wczytywanie GPX i walidacja śladu (punkty, kolejność, przerwy, duplikaty, pętle).
- Obliczanie dystansu, profilu wysokości, sumy podjazdów/zjazdów i nachyleń.
- Wygładzanie profilu wysokości oraz wykrywanie anomalii pomiarowych; przechowywanie wartości surowych i skorygowanych.
- Analiza nawierzchni, jeśli dane są dostępne.
- Wykrywanie i opisywanie odcinków technicznych, stromych podjazdów i zjazdów.
- Zachowanie punktów trasy, aby granice etapów można było wskazać dokładnie na mapie i wyeksportować do GPX.
- Każdy parametr powinien mieć źródło i poziom pewności. Brak danych o nawierzchni nie może oznaczać nawierzchni asfaltowej.

### Etap B – Stage Planner (podział na dni)

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