# TASK 06 – PHP AdventureEngineService i API

**Cel:** udostępnić jeden produkcyjny punkt wejścia dla istniejącego Planera Ridemore. UI nie może wywoływać niezależnie poszczególnych ekspertów ani samodzielnie wykonywać obliczeń.

## Warunki rozpoczęcia

Task 1–5 odebrane. Przed implementacją sprawdzić rzeczywistą strukturę PHP Ridemore, standardy autoryzacji, obsługę błędów, PDO, logowanie i routing API. Repozytorium planer_adviser jest repozytorium specyfikacji/referencji i nie zawiera jeszcze produkcyjnego runtime PHP.

## Zakres

1. Utworzyć serwis orkiestrujący, proponowana nazwa `AdventureEngineService`, z jedną metodą wejściową `analyze(AdventurePlanRequest $request)`.
2. Serwis waliduje request i uruchamia w kolejności: RouteAnalyzer → StagePlanner → StageDemandModel → eksperci Adventure Engine → composer wyniku.
3. Zwraca jeden `AdventurePlanResult` w wersjonowanym formacie.
4. Dodać endpoint API zgodny z istniejącym stylem Ridemore, bez tworzenia równoległego routera.
5. Zabezpieczyć endpoint istniejącym mechanizmem autoryzacji i sprawdzeniem właściciela/ dostępu do trasy.
6. Ograniczyć rozmiar GPX, typ pliku, czas wykonania i zużycie pamięci; walidować XML bez niebezpiecznego przetwarzania zewnętrznych encji.
7. Obsłużyć identyfikator requestu, wersję modelu, logowanie błędów i diagnostykę bez zapisywania zbędnych danych wrażliwych.
8. Wprowadzić cache tylko jeśli klucz obejmuje hash GPX, parametry, wersję kontraktu i wersję modelu. Cache nie może zwracać wyniku dla innych ustawień.
9. Nie wymagać uruchamiania Pythona na serwerze. PHP jest runtime produkcyjnym.

## Kontrakt API

- wejście: wersjonowany JSON/identyfikator GPX i parametry opisane w Task 1;
- sukces: jeden AdventurePlanResult;
- błędy: stabilny kod, komunikat dla użytkownika, diagnostyczny kontekst dla logów, request_id;
- walidacja danych użytkownika: błędy pól muszą wskazywać konkretne pole i oczekiwany format;
- błędy analizy GPX, brak danych i niepewność nie mogą być mylone z awarią serwera.

## Proponowane klasy

Nazwy dopasować do istniejącej architektury, nie traktować jako nakazu tworzenia nowych katalogów:
- `AdventureEngineService`;
- `AdventurePlanRequestValidator`;
- DTO z Task 1;
- adaptery istniejących modułów;
- `AdventurePlanResultFormatter` lub serializer;
- kontroler/handler API zgodny z obecnym Ridemore.

## Testy i kryteria odbioru

- testy jednostkowe serwisu i walidatora;
- testy API: poprawne żądanie, błędne dane, brak GPX, niedozwolony dostęp, zbyt duży plik, błąd parsera, brak części danych;
- test, że moduły są wywoływane we właściwej kolejności;
- test, że API zwraca jeden stabilny kontrakt;
- test bezpieczeństwa XML i limitów zasobów;
- test wersjonowania i cache;
- testy integracyjne na Kotlina400;
- test potwierdzający, że produkcyjna ścieżka nie uruchamia Pythona.

**Odbiór:** jeden bezpieczny endpoint PHP zwracający kompletny, wersjonowany plan; brak logiki obliczeniowej w kontrolerze i UI.
