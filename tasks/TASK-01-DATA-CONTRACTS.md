# TASK 01 – Kontrakty danych i DTO

**Cel:** ustalić jeden, stabilny kontrakt danych pomiędzy istniejącym planerem, serwisem PHP, analizą GPX, podziałem etapów i ekspertami Adventure Engine.

## Warunek rozpoczęcia

Task 0 musi być wyraźnie zaakceptowany przez właściciela produktu. Wykonawca ma przejrzeć aktualne `adventure_knowledge.json`, `wizard_questions.json`, README oraz testy. Nie wolno definiować równoległego schematu ignorującego istniejące pola.

## Zakres

1. Zmapować istniejące pola bazy wiedzy, wizarda, profilu rowerzysty, danych roweru/bagażu i wejścia GPX.
2. Zdefiniować kontrakty wejściowe i wyjściowe oraz ich wersjonowanie.
3. Zdefiniować DTO (proponowane nazwy): `AdventurePlanRequest`, `RiderProfile`, `EquipmentProfile`, `TripConstraints`, `RouteAnalysis`, `RouteSegment`, `StagePlan`, `StageResult`, `AdventurePlanResult`, `DataQuality`, `Warning`.
4. Zdefiniować słownik jednostek, zakresów i typów: liczby, nullable, enumy, współrzędne, daty, identyfikatory.
5. Dla każdego pola określić pochodzenie: `declared`, `observed`, `measured`, `calculated`, `estimated`, `unknown` (zachować istniejące nazewnictwo bazy, jeśli ma już formalny kontrakt; różnice udokumentować).
6. Określić sposób zapisu niepewności, źródła, wersji modelu i przyjętego założenia.
7. Zdefiniować walidację oraz rozróżnienie: pole wymagane, opcjonalne, automatycznie uzupełniane, nieznane i wymagające decyzji użytkownika.

## Minimalny kontrakt wejściowy

- identyfikator żądania i wersja kontraktu;
- GPX albo bezpieczny identyfikator pliku;
- liczba dni zadana przez użytkownika;
- miękki limit/preferowany czas jazdy, jeśli użytkownik go podał;
- profil rowerzysty z jawnym pochodzeniem pól;
- masa roweru i bagażu, jeśli znana;
- parametry kalibracji (CP/FTP lub prędkość referencyjna) tylko jeśli dostępne;
- opcjonalne preferencje rodzaju wyprawy i nawierzchni;
- dane POI wyłącznie z istniejącego, wskazanego źródła Ridemore.

## Minimalny kontrakt wyniku

- status wykonania i identyfikator żądania;
- podsumowanie trasy;
- dokładnie tyle etapów, ile zażądał użytkownik (jeśli analiza mogła zostać wykonana);
- dla każdego etapu: dystans, przewyższenie, czas, obciążenie i dane żywieniowe/nawodnieniowe, gdy są policzalne;
- rekomendacje i ostrzeżenia z uzasadnieniem;
- status/pochodzenie/niepewność dla liczb;
- lista brakujących danych i ograniczeń;
- wersje bazy wiedzy i modeli.

## Ważne reguły

- Brak danych to `null`/status `unknown`, nigdy automatyczne zero.
- Nie wpisywać demonstracyjnych wartości jako profilu użytkownika.
- Nie wymagać od przeciętnego użytkownika potliwości, CdA, Crr, gross efficiency ani podobnych parametrów. Jeśli model używa wartości domyślnej, zapisać ją jako estymację/założenie.
- Nie utożsamiać kalorii metabolicznych z ilością kalorii/CHO, które użytkownik musi spożyć podczas jazdy.
- Nie dodawać do kontraktu pól bez odbiorcy lub określonego znaczenia.

## Proponowane miejsce implementacji

Dopasować do istniejącej struktury PHP Ridemore. Nie tworzyć nowego frameworka. Przed kodowaniem wskazać docelowe pliki/namespace i uzgodnić je z aktualnym stylem projektu. Repozytorium referencyjne nie zawiera jeszcze produkcyjnego PHP.

## Testy i kryteria odbioru

- testy walidacji typów, jednostek, zakresów, nullable i enumów;
- testy brakujących danych i statusu `unknown`;
- testy wersjonowania kontraktu;
- test round-trip JSON → DTO → JSON;
- test zgodności pól z bazą wiedzy i wizardem;
- dokumentacja przykładowego poprawnego żądania i wyniku;
- brak niejawnych wartości domyślnych i pól o niejasnym znaczeniu.

**Odbiór:** zatwierdzony dokument kontraktu, implementacja DTO/walidatorów i automatyczne testy. Nie przechodzić do Task 2, dopóki kontrakt nie jest stabilny.
