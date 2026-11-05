# TASK 02 – GPX Analyzer

**Cel:** przekształcić GPX w wiarygodny, znormalizowany profil trasy, który będzie wspólnym wejściem dla Stage Planner i modeli zapotrzebowania.

## Warunki rozpoczęcia

Task 1 odebrany. Przed implementacją przeczytać i uruchomić `tests/route_stage_planner.py` oraz `tests/test_route_stage_planner.py`. Python jest referencją zachowania, nie runtime produkcyjnym.

## Zakres funkcjonalny

1. Walidować GPX: poprawność XML, obecność tracków/punktów, współrzędne, kolejność, elewacja, rozmiar i limity pliku.
2. Parsować track points i obliczać odległości geodezyjne między kolejnymi punktami.
3. Normalizować trasę do segmentów o określonej długości/strategii próbkowania; nie uzależniać zachowania filtra wyłącznie od liczby punktów w pliku.
4. Analizować profil wysokości, nachylenie, podjazdy i zjazdy. Zachować oddzielnie wartości surowe i skorygowane/wygładzone.
5. Wykrywać luki i anomalie: brak elewacji, duplikaty punktów, skoki GPS, nienaturalne wysokości, przerwy i nieciągłości.
6. Zachować geometrię i współrzędne, aby granice etapów można było później odtworzyć na mapie.
7. Zwrócić ocenę jakości danych i źródło wysokości. Nie twierdzić, że GPX elevation jest pomiarem terenowym o znanej dokładności.
8. Jeśli Ridemore ma dostęp do lepszego DEM, zaprojektować adapter jako osobny, jawny etap; nie dodawać zewnętrznego źródła bez uzgodnienia i testów.

## Wejście

`AdventurePlanRequest.route`: treść GPX lub bezpieczny identyfikator pliku oraz opcjonalne ustawienia jakości/źródła danych.

## Wyjście

`RouteAnalysis`: całkowity dystans, surowe i wygładzone przewyższenie, min/max wysokość, profil segmentów, nachylenia, współrzędne, ostrzeżenia jakości oraz pochodzenie danych.

Każdy segment powinien mieć stabilny indeks/ID, początek/koniec, dystans, różnicę wysokości, nachylenie i status jakości.

## Algorytm i założenia

- Dystans liczony geodezyjnie na podstawie współrzędnych.
- Nachylenie liczone z różnicy wysokości i dystansu poziomego.
- Filtr wysokości musi operować na stałym oknie odległości lub jawnie udokumentowanej metodzie niezależnej od gęstości punktów.
- Nie usuwać rzeczywistych podjazdów i zjazdów przez nadmierne wygładzanie.
- Surowe i skorygowane przewyższenie raportować oddzielnie.
- Brak elewacji nie może być uzupełniany zerem. Można użyć zatwierdzonego DEM, a jeśli go nie ma – zwrócić brak/niepewność.
- Nie scalać pętli ani nie zamykać trasy automatycznie, jeśli GPX tego nie uzasadnia.

## Obsługa błędów

Rozróżnić: plik niepoprawny, pusty, nieobsługiwany, zbyt duży, brak punktów, brak wysokości, częściowa wysokość, nieciągła geometria oraz błąd źródła DEM. Błąd ma mieć kod i czytelny opis; nie zwracać pozornie poprawnego profilu.

## Testy i kryteria odbioru

- syntetyczne trasy: płaska, stały podjazd, zjazd, profil falisty, pętla, brak wysokości, szum i duplikaty;
- testy GPX Kotlina400;
- ten sam ślad zapisany z różną gęstością punktów daje zbliżony dystans i przewyższenie w ustalonej tolerancji;
- sumy odcinków zgadzają się z podsumowaniem;
- współrzędne i kolejność punktów są zachowane;
- wyniki PHP porównane z Pythonem, z udokumentowanymi tolerancjami numerycznymi;
- testy odporności na błędne i nadmiernie duże pliki.

**Odbiór:** RouteAnalyzer zwraca stabilny `RouteAnalysis` i przechodzi testy; Stage Planner nie powinien sam parsować GPX.
