# Spec Delta

## Purpose

Selects a disabled-parking spot for a journey by gathering the spots near a destination, narrowing them to those a traveller accepts, and ranking the remainder by how far the traveller still has to travel by wheelchair.

## ADDED Requirements

### Requirement: Parking spots are available with position and attributes

The system SHALL provide the set of known disabled-parking spots, each carrying a stable identifier, a WGS84 latitude/longitude position, and the descriptive attributes recorded for it by the municipality: owner, time restriction, status, and disabled-parking type.

Spots SHALL be obtained through the project's parking-spot store rather than read from source files by the routing logic, so the storage medium can change without affecting callers.

Spots recorded more than once across the source data SHALL appear only once in the provided set.

#### Scenario: Spots are provided with positions and attributes

- **WHEN** the set of parking spots is requested
- **THEN** each spot has an identifier, a latitude between 51.85 and 52.1, a longitude between 7.5 and 7.8, and its owner, time-restriction, status, and type attributes

#### Scenario: Duplicated source records yield one spot

- **WHEN** the same parking spot is present in more than one source data file
- **THEN** it appears exactly once in the provided set

### Requirement: Candidate spots are gathered within a radius of the destination

The system SHALL treat as candidates only those parking spots whose straight-line distance to the destination is at most 500 metres. The radius SHALL be adjustable by the caller.

#### Scenario: Spot inside the radius is a candidate

- **WHEN** a parking spot lies 300 metres from the destination
- **THEN** it is included in the candidate set

#### Scenario: Spot outside the radius is excluded

- **WHEN** a parking spot lies 800 metres from the destination and the radius is 500 metres
- **THEN** it is not included in the candidate set

#### Scenario: No spot within the radius

- **WHEN** no parking spot lies within the radius of the destination
- **THEN** the system reports that no parking spot is available, identifying the destination and the radius used

### Requirement: Filters narrow the candidate spots

The system SHALL accept a set of filters that restrict which candidate spots are eligible. A filter SHALL be able to constrain:

- spot attributes: owner, time restriction, status, and disabled-parking type
- the maximum remaining wheelchair travel distance from the spot to the destination

All supplied filters SHALL apply together: a spot is eligible only if it satisfies every filter. An empty set of filters SHALL leave every candidate eligible.

Attribute constraints SHALL be evaluated before any route is requested, so that ineligible spots cost no routing work.

#### Scenario: Attribute filter excludes a spot

- **WHEN** a filter requires publicly owned spots and a candidate is privately owned
- **THEN** that candidate is not eligible

#### Scenario: Filters combine with AND

- **WHEN** two filters are supplied and a candidate satisfies only one of them
- **THEN** that candidate is not eligible

#### Scenario: No filters supplied

- **WHEN** an empty set of filters is supplied
- **THEN** every candidate within the radius remains eligible

#### Scenario: Maximum wheelchair distance excludes a spot

- **WHEN** a filter sets a maximum remaining wheelchair distance of 200 metres and a candidate's wheelchair route to the destination is 450 metres
- **THEN** that candidate is not eligible

#### Scenario: All candidates filtered out

- **WHEN** candidates exist within the radius but none satisfies the supplied filters
- **THEN** the system reports that no parking spot satisfies the filters, distinguishing this from the case where no spot lies within the radius

### Requirement: The spot with the shortest wheelchair leg is selected

The system SHALL narrow the eligible candidates to the 5 closest by straight-line distance to the destination, then select from that narrowed set the spot whose wheelchair route to the destination is shortest by travelled distance. Straight-line proximity SHALL determine which spots are considered for ranking; it SHALL NOT by itself decide which one is finally selected.

A candidate for which no wheelchair route to the destination can be produced SHALL be skipped rather than aborting the selection, so long as another candidate remains.

#### Scenario: More than 5 eligible candidates

- **WHEN** more than 5 candidates are eligible within the radius
- **THEN** only the 5 closest by straight-line distance to the destination are considered for wheelchair-route ranking

#### Scenario: Nearest by route wins over nearest by straight line

- **WHEN** one candidate is closer in a straight line but its wheelchair route to the destination is longer than another eligible candidate's among the 5 nearest by straight line
- **THEN** the candidate with the shorter wheelchair route is selected

#### Scenario: Unroutable candidate is skipped

- **WHEN** no wheelchair route can be produced from one candidate to the destination and another eligible candidate is routable
- **THEN** the unroutable candidate is skipped and the routable one is selected

#### Scenario: No candidate is routable

- **WHEN** no eligible candidate has a wheelchair route to the destination
- **THEN** the system reports that no reachable parking spot was found
