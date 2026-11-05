# TASK 04 – Stage Demand Model: czas, fizyka jazdy i zapotrzebowanie etapu

**Cel:** oszacować czas jazdy i fizyczne wymagania każdego etapu, aby kolejne moduły mogły policzyć obciążenie, żywienie, nawodnienie i regenerację.

## Warunki rozpoczęcia

Task 1–3 odebrane. Odczytać model referencyjny w `tests/route_stage_planner.py` oraz ograniczenia opisane w README. Wynik prototypu nie jest zwalidowaną prognozą fizjologiczną.

## Wejście

- segmenty RouteAnalysis i przypisanie ich do etapów;
- masa rowerzysty, roweru i bagażu z pochodzeniem;
- CP/FTP lub prędkość referencyjna z kontekstem, jeśli dostępne;
- parametry modelu: Crr, CdA, gęstość powietrza, wiatr, sprawność napędu i gross efficiency;
- nawierzchnia/techniczność tylko wtedy, gdy istnieją wiarygodne dane.

## Wyjście

Dla segmentu i etapu: szacowany czas jazdy, prędkość, wymagania mocy, praca mechaniczna, szacowany koszt metaboliczny, poziom niepewności, parametry użyte do obliczeń i ostrzeżenia o ograniczeniach modelu.

## Wymagania obliczeniowe

1. Zachować model sił: grawitacja, toczenie, aerodynamika; uwzględnić nachylenie, masę całkowitą i prędkość względem powietrza.
2. Rozwiązywać prędkość dla dostępnej mocy metodą numeryczną z ograniczeniami prędkości i stabilnością na zjazdach.
3. Uwzględnić sprawność napędu przy przejściu między mocą na korbie a mocą na kole.
4. Pracę mechaniczną liczyć jako całkę mocy po czasie. Koszt metaboliczny szacować z jawnej gross efficiency; nie przedstawiać go jako pomiaru.
5. CP/FTP nie traktować jako mocy, którą użytkownik może utrzymywać przez wiele godzin. Potrzebny jest model intensywności długotrwałej / krzywa mocy albo konserwatywny współczynnik z wysoką niepewnością.
6. Prędkość typowa jest jedynie kalibracją przybliżoną. Musi być powiązana z profilem referencyjnym (nawierzchnia, nachylenie/teren); bez kontekstu nie wyciągać z niej pozornie precyzyjnej mocy.
7. Nie pozwalać, aby ujemna moc na zjeździe dawała niefizycznie nieograniczoną prędkość. Uwzględnić ograniczenie prędkości/hamowanie jako jawne uproszczenie.
8. Postoje nie są czasem jazdy. Jeśli nie ma danych o postojach, raportować moving time, a czas całkowity pozostawić jako estymację z osobnym założeniem lub unknown.
9. Nie utożsamiać kosztu metabolicznego z ilością jedzenia do spożycia podczas jazdy.

## Niepewność

Nieznana masa bagażu, brak CP/FTP, nieznana nawierzchnia, brak wiatru i niska jakość wysokości muszą zwiększać niepewność. Domyślne parametry fizyczne są wartościami modelu, nie indywidualnymi pomiarami. Zapisać je w wyniku.

## Testy i kryteria odbioru

- testy jednostkowe równania sił i jednostek;
- testy płaskiego terenu, podjazdu, zjazdu, wiatru i różnych mas;
- monotoniczność: większa masa lub stromszy podjazd nie może bez uzasadnienia zmniejszać czasu;
- brak ujemnego czasu, nieskończonych prędkości i NaN;
- test wpływu zmiany kalibracji i niepewności;
- porównanie z Pythonem na identycznych danych i tolerancjach;
- oddzielne raportowanie moving time i ewentualnego czasu całkowitego.

**Odbiór:** StageDemandModel liczy wynik per etap i wyjaśnia, które wartości są założeniami. Model musi ujawniać ograniczenia zamiast udawać dokładność.
