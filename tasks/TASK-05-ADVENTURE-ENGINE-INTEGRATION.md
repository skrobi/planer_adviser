# TASK 05 – Integracja z ekspertami Adventure Engine

**Cel:** połączyć obliczone etapy z istniejącą bazą wiedzy i ekspertami tak, aby użytkownik otrzymał spójny plan całej wyprawy oraz rekomendacje per dzień.

## Warunki rozpoczęcia

Task 1–4 odebrane. Wykorzystać istniejące `adventure_knowledge.json`, `wizard_questions.json`, `tests/adventure_engine_runner.py`, scenariusze i testy. Nie przepisywać wiedzy do nowych, rozproszonych plików bez potrzeby.

## Zakres

1. Zmapować wynik RouteAnalyzer, StagePlanner i StageDemandModel na aktualny kontekst wejściowy ekspertów.
2. Rozszerzyć kontekst z pojedynczej wyprawy na tablicę `stages[]`, zachowując rekomendacje globalne i per etap.
3. Zintegrować istniejące obszary: bezpieczeństwo, obciążenie, żywienie, nawodnienie, regeneracja, logistyka i sprzęt – tylko w zakresie faktycznie opisanym w bazie wiedzy.
4. Uwzględnić kumulację zmęczenia w kolejnych dniach. Nie oceniać każdego dnia tak, jakby był pierwszym.
5. Składać rekomendacje w czytelne grupy/karty, zachowując identyfikatory reguł, źródła, priorytet i uzasadnienie.
6. Oddzielić wymagania fizjologiczne od rekomendacji spożycia CHO. Ilość CHO wyznaczać z czasu/intensywności i jawnych zakresów planistycznych, nie przez proste przeliczenie wszystkich kcal na węglowodany.
7. Nawodnienie prezentować jako zakres/estymację, jeśli nie ma indywidualnych danych o poceniu. Nie pytać standardowego użytkownika o współczynnik potliwości.
8. Ocenić zapas żywności tylko wtedy, gdy użytkownik go zadeklarował. Nieznany zapas nie jest niewystarczający.
9. POI traktować jako potencjalne punkty na mapie. Nie deklarować dostępności, ilości wody, jedzenia ani noclegu bez potwierdzonych danych.
10. Każda rekomendacja ma zawierać powód, dane wejściowe, status i ewentualną niepewność.

## Reguły nadrzędne

- Nie zmieniać liczby dni użytkownika.
- Trudny plan nie jest odrzucany; silnik przedstawia skalę wymagań i ostrzeżenia.
- Brak danych nie jest zerem i nie może uruchamiać fałszywej reguły.
- Ostrzeżenia krytyczne muszą zachować konkretne zalecenia bezpieczeństwa z katalogu.
- Nie dodawać diagnoz ani medycznych gwarancji.

## Wyjście

Rozszerzony `AdventurePlanResult`: rekomendacje globalne, rekomendacje przypisane do etapów, wskaźniki obciążenia, CHO, płyny, regeneracja, ostrzeżenia, provenance i uncertainty.

## Testy i kryteria odbioru

- zachować istniejące scenariusze regresyjne i oczekiwane wyniki;
- testy trzech grup rekomendacji już obecnych w interpreterze;
- testy nieznanego i zadeklarowanego zapasu jedzenia;
- testy braku potliwości i estymacji płynów;
- testy kumulacji obciążenia na kolejnych etapach;
- testy ostrzeżeń krytycznych i kryteriów przerwania wysiłku;
- testy braku fikcyjnych POI i dostępności;
- testy, że zmiana liczby dni przez użytkownika zmienia podział i zapotrzebowanie, ale nie jest automatycznie korygowana przez silnik.

**Odbiór:** eksperci działają na wspólnym modelu etapów, zachowują identyfikowalność reguł i nie generują nieuzasadnionych twierdzeń.
