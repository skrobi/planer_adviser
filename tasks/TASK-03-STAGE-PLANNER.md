# TASK 03 – Stage Planner: podział trasy na etapy

**Cel:** podzielić analizowaną trasę na dokładnie taką liczbę dni, jaką podał użytkownik, przy możliwie rozsądnym rozkładzie obciążenia.

## Warunki rozpoczęcia

Task 1 i Task 2 odebrane. Użyć istniejącego prototypu `tests/route_stage_planner.py` i jego testów jako punktu odniesienia. Nie kopiować ślepo algorytmu bez sprawdzenia ograniczeń.

## Wejście

- `RouteAnalysis` z uporządkowanymi segmentami i geometrią;
- wymagana liczba dni;
- preferowany i maksymalny czas jazdy dziennie, jeśli podane;
- opcjonalne preferencje długości etapów lub punktów końcowych, jeśli istnieją w zaakceptowanym UX.

## Wyjście

`StagePlan` zawierający dokładnie N etapów, kolejność, zakres indeksów/odległości, współrzędne początku/końca, dystans, przewyższenie, zjazdy, szacowany czas (jeśli dostępny), wskaźniki nierównomierności i ostrzeżenia.

## Wymagane zachowanie

1. Liczba etapów ma być równa liczbie dni zadanej przez użytkownika.
2. Limit godzin dziennie jest miękki: przekroczenie jest raportowane, ale algorytm nie dodaje dni i nie odrzuca planu.
3. Preferować zbalansowanie czasu jazdy, a nie samego dystansu. Gdy czas nie jest jeszcze dostępny, zastosować jawny fallback i oznaczyć niższą jakość podziału.
4. Nie rozcinać geometrii ani nie gubić odcinków. Każdy segment trasy należy przypisać dokładnie do jednego etapu.
5. Zachować kolejność trasy i ciągłość granic. Dla pętli nie zakładać automatycznie, że punkt końcowy jest miejscem noclegu.
6. Jeżeli liczba dni jest większa niż liczba sensownych punktów podziału lub segmentów, zwrócić czytelny status/ostrzeżenie i nie generować pustych etapów bez jawnej reguły.
7. W przyszłości można uwzględnić ograniczenia użytkownika (np. wymuszony punkt postoju), ale nie tworzyć fikcyjnych miejsc noclegowych.

## Algorytm

- Wyznaczać granice wyłącznie na granicach segmentów albo interpolować je w sposób zachowujący geometrię.
- Minimalizować nierównomierność sumy czasu etapów; dodatkowe kryteria (przewyższenie, trudność) muszą mieć jawne wagi i testy.
- Nie optymalizować przez zmianę N.
- Raportować jakość kompromisu, np. rozrzut czasu/dystansu/przewyższenia między etapami.

## Testy i kryteria odbioru

- dokładnie N etapów dla scenariuszy z różną liczbą dni;
- suma dystansu i przewyższenia etapów odpowiada analizie trasy w tolerancji;
- brak luk i nakładania się odcinków;
- zachowana kolejność i współrzędne granic;
- limit czasu przekroczony → ostrzeżenie, nie zmiana liczby dni;
- zmiana parametrów rowerzysty może zmienić granice, ale nie N;
- test Kotlina400 oraz syntetyczne trasy płaskie, górskie i z nierównomiernym profilem;
- testy porównawcze z Pythonem z określonymi tolerancjami.

**Odbiór:** stabilny StagePlanner zwracający StagePlan zgodny z żądanym N i bez utraty geometrii.
