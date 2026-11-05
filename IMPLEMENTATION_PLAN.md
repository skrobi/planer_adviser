# RideMore Adventure Engine – plan implementacji

## Zasady prowadzenia prac

1. Prace muszą rozwijać istniejący Ridemore.bike i rozwiązania już obecne w repozytorium oraz aplikacji. Nie projektujemy nowego produktu od zera.
2. Przed proponowaniem zmian należy zinwentaryzować istniejące ekrany, komponenty, mapę, planer, przepływy, modele danych i możliwości techniczne.
3. Preferowane są ponowne użycie i niewielkie rozszerzenia istniejących rozwiązań. Duże przebudowy, wymiana bibliotek, zmiana architektury lub tworzenie równoległych modułów wymagają uzasadnienia i osobnej zgody właściciela produktu.
4. Nie wolno rozpoczynać kolejnego zadania, jeżeli jego warunek wejścia nie został spełniony.
5. W szczególności Task 1 i dalsze prace implementacyjne mogą rozpocząć się dopiero po wyraźnej akceptacji przez właściciela produktu wszystkich obowiązkowych mockupów z Task 0.

---

# TASK 0 – Audyt istniejącego UX/UI, projekt i akceptacja mockupów

**Priorytet:** obowiązkowy, blokujący dalsze prace  
**Cel:** zaprojektować docelowy przepływ i interfejs Adventure Engine, wykorzystując istniejący planer i interfejs Ridemore.bike.  
**Rezultat:** komplet obowiązkowych mockupów oraz opis zachowania ekranów, zatwierdzony przez właściciela produktu.

## 0.1. Zasada: najpierw audyt, potem projekt

Przed przygotowaniem mockupów wykonawca musi:

- przejrzeć istniejący planer Ridemore.bike i dostępne widoki na desktopie oraz mobile;
- zinwentaryzować istniejące komponenty, style, mapy, profile wysokościowe, karty, formularze, nawigację i wzorce interakcji;
- sprawdzić, które elementy można wykorzystać bez zmian;
- wskazać elementy wymagające jedynie dostosowania;
- wskazać rzeczywiście brakujące elementy.

Należy przygotować krótką tabelę: **element istniejący → sposób ponownego użycia → ewentualna minimalna zmiana**. Jeśli proponowana zmiana jest większa, trzeba opisać jej powód, wpływ na istniejący planer i alternatywę o mniejszym zakresie.

Nie wolno bez uzasadnienia:
- tworzyć nowego, niezależnego planera obok obecnego;
- zmieniać głównej nawigacji lub ogólnego układu Ridemore;
- wymieniać istniejących bibliotek i komponentów;
- przebudowywać istniejących modułów, które mogą obsłużyć wymagany scenariusz po niewielkim rozszerzeniu;
- tworzyć nowych ekranów, jeśli tę samą funkcję można czytelnie dodać do istniejącego widoku.

Mockupy mają pokazywać docelowy sposób rozszerzenia obecnego produktu, a nie oderwaną koncepcję graficzną.

## 0.2. Obowiązkowa lista mockupów

Wykonawca musi przygotować wszystkie poniższe mockupy. Mogą one wykorzystywać istniejące ekrany jako bazę, ale muszą pokazywać kompletny docelowy interfejs i przepływ.

### M0.1 – Wejście do Adventure Engine / rozpoczęcie planowania
- Jak użytkownik uruchamia doradcę z obecnego planera.
- Wybór lub wczytanie trasy GPX oraz obsługa już wybranej trasy.
- Wyraźne rozróżnienie: nowy plan, kontynuacja/edycja istniejącego planu.
- Wykorzystanie istniejącego widoku planera, jeśli to możliwe.

### M0.2 – Analiza trasy
- Mapa trasy i podstawowe dane: dystans, przewyższenie, profil wysokościowy.
- Informacje o charakterze trasy i rozpoznanych wyzwaniach, o ile są dostępne w danych.
- Widoczne rozróżnienie danych zmierzonych, obliczonych, szacunkowych i nieznanych.
- Prezentacja braków danych bez udawania, że zostały zweryfikowane.

### M0.3 – Ustalenie założeń wyprawy
- Liczba dni / termin lub dostępny horyzont wyprawy.
- Preferencje dotyczące długości i charakteru etapów.
- Rodzaj wyprawy i podstawowe informacje o rowerze oraz bagażu.
- Proste pytania o doświadczenie i możliwości rowerzysty.
- Parametry techniczne, których typowy użytkownik nie potrafi podać, mają mieć rozsądne wartości domyślne lub estymacje z oznaczoną niepewnością, zamiast rozbudowanego formularza eksperckiego.

### M0.4 – Profil rowerzysty i podsumowanie danych wejściowych
- Czytelne podsumowanie informacji zadeklarowanych przez użytkownika.
- Wskazanie wartości przyjętych automatycznie przez system.
- Możliwość poprawienia danych, które użytkownik zna.
- Informacja, które dane mają największy wpływ na dokładność obliczeń.

### M0.5 – Podział trasy na etapy
- Cała trasa na mapie z granicami etapów.
- Lista/karty etapów z dystansem, przewyższeniem, szacowanym czasem i obciążeniem.
- Możliwość zmiany liczby dni zgodnie z założeniami użytkownika i ponownego przeliczenia.
- Jeżeli plan jest bardzo wymagający, interfejs pokazuje konsekwencje i ostrzeżenia; nie zmienia samodzielnie liczby dni ani nie blokuje planu.

### M0.6 – Szczegóły pojedynczego etapu / dnia
- Dane etapu, profil wysokościowy i mapa.
- Szacowany czas jazdy oraz obciążenie.
- Zapotrzebowanie energetyczne i żywieniowe, w tym węglowodany.
- Szacowane zapotrzebowanie na płyny i plan ich uzupełniania.
- Rekomendacje dotyczące odpoczynku, bezpieczeństwa i przygotowania.
- Jasne wskazanie niepewności oraz danych, których nie udało się ustalić.

### M0.7 – Centrum rekomendacji Adventure Engine
- Zintegrowane rekomendacje dotyczące bezpieczeństwa, etapów, żywienia, nawodnienia, regeneracji, sprzętu i logistyki – w zakresie obsługiwanym przez aktualną bazę wiedzy.
- Priorytety i poziom ważności ostrzeżeń.
- Uzasadnienie: dlaczego system pokazuje daną rekomendację i z jakich danych wynika.
- Rozróżnienie informacji potwierdzonych, szacunkowych, wymagających danych użytkownika i nieznanych.
- Brak fikcyjnych zapewnień o dostępności noclegów, sklepów, wody lub innych POI.

### M0.8 – Końcowe podsumowanie i plan wyprawy
- Widok całej wyprawy oraz wszystkich etapów.
- Najważniejsze parametry i obciążenie poszczególnych dni.
- Zbiorcze rekomendacje, ostrzeżenia i lista przygotowań.
- Możliwość powrotu do edycji założeń i ponownego przeliczenia.
- Czytelne oznaczenie, które elementy planu są szacunkami, a które opierają się na danych potwierdzonych.

## 0.3. Obowiązkowe stany i warianty

Nie wystarczy pokazać wyłącznie idealnego scenariusza. Mockupy muszą pokazywać również:

1. Dane kompletne i wystarczające do obliczeń.
2. Część danych nieznana – system przyjmuje jawne założenia i oznacza niepewność.
3. Brak danych, których nie można wiarygodnie oszacować – użytkownik widzi ograniczenie.
4. Bardzo wymagający plan, np. krótka liczba dni na trudnej trasie – system pokazuje konsekwencje, ale nie odrzuca planu i nie zmienia założeń użytkownika.
5. POI znalezione na mapie, ale bez potwierdzenia dostępności, ilości lub godzin otwarcia.
6. Edycja założeń po wygenerowaniu planu i ponowne przeliczenie etapów.

## 0.4. Wymagania wizualne i interakcyjne

- Zachować istniejący język wizualny Ridemore.bike: jasny, nowoczesny, profesjonalny i spójny z aktualną aplikacją.
- Preferować istniejące komponenty i wzorce interfejsu.
- Mockupy przygotować co najmniej dla desktopu i mobile; nie muszą oznaczać dwóch zupełnie różnych projektów.
- Pokazać najważniejsze interakcje, przejścia między ekranami, edycję danych i reakcję interfejsu na zmianę założeń.
- Nie przeciążać użytkownika technicznymi pytaniami. Szczegóły eksperckie mogą być pokazane jako przyjęte założenia lub wartości rozwijane w szczegółach.
- Używać spójnych, realistycznych danych demonstracyjnych. Preferowany scenariusz bazowy: plik GPX Kotlina400 znajdujący się w repozytorium. Dane przykładowe muszą być oznaczone jako demonstracyjne, jeżeli nie pochodzą z rzeczywistej weryfikacji.

## 0.5. Wymagane materiały przekazywane do akceptacji

Wykonawca przedstawia:

- komplet mockupów M0.1–M0.8;
- widoki desktop i mobile;
- mapę przepływu użytkownika między ekranami;
- opis najważniejszych interakcji i stanów;
- tabelę ponownego wykorzystania istniejących elementów;
- listę proponowanych zmian w istniejącym interfejsie wraz z uzasadnieniem i oceną ich zakresu;
- listę otwartych decyzji, których nie da się rozstrzygnąć bez właściciela produktu.

## 0.6. Kryteria akceptacji Task 0

Task 0 jest zakończony wyłącznie wtedy, gdy:

- wszystkie mockupy M0.1–M0.8 zostały przygotowane;
- pokazano wymagane stany i warianty z punktu 0.3;
- zaprojektowany przepływ jest spójny i obejmuje pełną ścieżkę użytkownika;
- projekt bazuje na istniejącym Ridemore i nie wprowadza nieuzasadnionej przebudowy;
- każda większa zmiana względem istniejącego interfejsu została wskazana i uzasadniona;
- właściciel produktu zapoznał się z materiałami i wyraźnie zaakceptował komplet mockupów.

### Twarda bramka akceptacyjna – zakaz przejścia dalej

**Bez wyraźnej akceptacji właściciela produktu dla wszystkich obowiązkowych mockupów M0.1–M0.8 nie wolno rozpocząć Task 1 ani żadnych dalszych prac implementacyjnych.**

Wykonawca może wprowadzać poprawki do mockupów na podstawie uwag właściciela produktu. Po każdej istotnej zmianie należy ponownie przedstawić zmienione ekrany do akceptacji. Milczenie, upływ czasu ani wewnętrzna ocena wykonawcy nie oznaczają akceptacji.

Akceptacja Task 0 dotyczy projektu UX/UI i przepływu. Nie oznacza automatycznej zgody na duże zmiany architektury lub zakresu technicznego.

---

# Kolejne zadania – kolejność zależności

Poniższe zadania mogą być rozpoczynane dopiero po zaakceptowaniu Task 0.

| Zadanie | Zakres | Warunek rozpoczęcia |
|---|---|---|
| Task 1 | Kontrakty danych, DTO i statusy pochodzenia danych | Akceptacja Task 0 |
| Task 2 | GPX Analyzer – analiza trasy i profilu wysokościowego | Task 1 |
| Task 3 | Stage Planner – podział trasy na zadaną liczbę etapów | Task 1 i 2 |
| Task 4 | Model fizyczny i model zapotrzebowania etapów | Task 1–3 |
| Task 5 | Integracja modeli z ekspertami Adventure Engine | Task 1–4 |
| Task 6 | API i obsługa procesu planowania | Task 1–5 |
| Task 7 | Integracja z istniejącym planerem Ridemore.bike | Akceptacja UX/UI oraz gotowe API |
| Task 8 | Testy integracyjne, regresyjne i walidacja wyników | Task 1–7 |

Szczegółowe specyfikacje techniczne kolejnych zadań powinny być opracowane z uwzględnieniem zaakceptowanych mockupów i istniejącej architektury. Nie należy implementować funkcji wykraczających poza zatwierdzony zakres bez uzgodnienia z właścicielem produktu.


## Szczegółowe instrukcje wykonawcze

Skrócona tabela powyżej jest tylko mapą kolejności. Pełne opisy zakresu, założeń, wejść/wyjść, zależności, obsługi błędów i kryteriów odbioru znajdują się w katalogu [tasks/](tasks/README.md):

- [Task 0 – audyt istniejącego UI, mockupy i akceptacja](tasks/TASK-00-UX-MOCKUPS.md)
- [Task 1 – kontrakty danych i DTO](tasks/TASK-01-DATA-CONTRACTS.md)
- [Task 2 – GPX Analyzer](tasks/TASK-02-GPX-ANALYZER.md)
- [Task 3 – Stage Planner](tasks/TASK-03-STAGE-PLANNER.md)
- [Task 4 – Stage Demand Model](tasks/TASK-04-STAGE-DEMAND-MODEL.md)
- [Task 5 – integracja Adventure Engine](tasks/TASK-05-ADVENTURE-ENGINE-INTEGRATION.md)
- [Task 6 – PHP Service i API](tasks/TASK-06-PHP-SERVICE-API.md)
- [Task 7 – integracja z istniejącym planerem](tasks/TASK-07-PLANNER-UI-INTEGRATION.md)
- [Task 8 – walidacja i wydanie](tasks/TASK-08-VALIDATION-AND-RELEASE.md)

Każdy task jest osobnym dokumentem wykonawczym. Przed rozpoczęciem zadania należy spełnić jego warunek wejścia i zapoznać się z kryteriami odbioru. Task 0 pozostaje twardą bramką: bez wyraźnej akceptacji mockupów nie wolno rozpocząć Task 1.
