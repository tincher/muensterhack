# Spec Delta

## ADDED Requirements

### Requirement: Complete car-then-wheelchair route

The system SHALL compute a single journey from an origin to a destination that is driven by car to a disabled-parking spot near the destination and completed by wheelchair from that spot.

The journey SHALL consist of exactly two legs:

1. a car leg from the origin to the selected parking spot, routed with a driving profile
2. a wheelchair leg from the selected parking spot to the destination, routed with the existing shade-optimized wheelchair-accessible behavior

The parking spot SHALL be the one chosen by the parking-selection behavior, using the filters supplied with the request.

#### Scenario: Successful complete route

- **WHEN** a complete route is requested between an origin and a destination with a set of filters
- **THEN** the system returns a journey containing a car leg that starts at the origin and ends at the selected parking spot, and a wheelchair leg that starts at that same parking spot and ends at the destination

#### Scenario: Wheelchair leg keeps accessibility and shade behavior

- **WHEN** the wheelchair leg of a complete route is computed
- **THEN** it applies the same strict accessibility restrictions and shade optimization as a standalone shade-optimized wheelchair route, including that route's own fallback behavior

#### Scenario: Legs meet at the parking spot

- **WHEN** a complete route is returned
- **THEN** the end position of the car leg and the start position of the wheelchair leg are the selected parking spot

### Requirement: The mode change is visible in the result

The system SHALL return the complete journey as a single GeoJSON FeatureCollection, matching the result shape of the existing routing functions so that existing consumers can render it without special handling.

Within that result the transition from car to wheelchair SHALL be identifiable without inspecting geometry:

- each leg SHALL carry a property naming its travel mode, distinguishing the car leg from the wheelchair leg
- the result SHALL include a distinct point marking the parking spot at which the mode changes, identified as the transfer point and carrying the selected spot's identifier
- the result SHALL indicate that it is a complete multi-modal journey, consistent with how existing routes indicate their mode

#### Scenario: Legs are labelled by mode

- **WHEN** a complete route is returned
- **THEN** the car leg carries a mode property identifying car travel and the wheelchair leg carries a mode property identifying wheelchair travel

#### Scenario: Transfer point is present

- **WHEN** a complete route is returned
- **THEN** the result contains a point feature at the selected parking spot, marked as the transfer point and carrying that spot's identifier

#### Scenario: Result is renderable like other routes

- **WHEN** a complete route is passed to the existing map rendering
- **THEN** it renders without changes to that rendering, because the result is a GeoJSON FeatureCollection like the other routing results

#### Scenario: Journey totals are available

- **WHEN** a complete route is returned
- **THEN** the distance and duration of the car leg and of the wheelchair leg are each available from the result

### Requirement: Complete route fails clearly when no usable parking spot exists

The system SHALL report an error when a complete route cannot be produced because no parking spot is available, none satisfies the supplied filters, or none is reachable by wheelchair.

The system SHALL NOT substitute a single-mode route for a failed complete route: a caller asking for a complete journey SHALL NOT receive a car-only or wheelchair-only result presented as a complete one.

#### Scenario: No usable parking spot

- **WHEN** no parking spot near the destination satisfies the filters and is reachable
- **THEN** the system returns an error identifying why no spot was usable, rather than a route

#### Scenario: Car leg cannot be produced

- **WHEN** the car leg to the selected parking spot cannot be produced
- **THEN** the system returns an error rather than a wheelchair-only route
