# routing Specification

## Purpose

Compute wheelchair-accessible routes and combined shade-optimized, wheelchair-accessible routes for wheelchair users navigating a city.

## Requirements

### Requirement: Wheelchair-accessible routing
The system SHALL compute a route between two geographic coordinates using a wheelchair-accessible routing profile with strict accessibility restrictions, and SHALL return the result as a GeoJSON FeatureCollection.

#### Scenario: Successful accessible route
- **WHEN** a request is made for a route between two coordinates
- **THEN** the system returns a GeoJSON FeatureCollection describing a wheelchair-accessible route

#### Scenario: Accessibility restrictions applied
- **WHEN** computing a wheelchair route
- **THEN** the routing request includes strict accessibility restrictions (maximum incline, maximum sloped kerb, minimum width, smoothness, surface, and track type)

### Requirement: Shade-optimized wheelchair-accessible route
The system SHALL compute a single route that is both shade-optimized and wheelchair-accessible by first requesting a shade-biased foot route and then routing through sampled waypoints of that shade path using the wheelchair profile.

#### Scenario: Combined shade and accessibility route
- **WHEN** a shade-optimized route is requested between two coordinates
- **THEN** the system requests a shade-biased foot route, samples its waypoints, re-routes through those waypoints with the wheelchair profile, and returns a single GeoJSON FeatureCollection

#### Scenario: Shade bias requested
- **WHEN** requesting the shade-biased foot route
- **THEN** the request biases routing toward higher shade values using the shade raster column and a negative weight factor

### Requirement: Fallback to accessible route
The system SHALL return a plain wheelchair-accessible route when the shade-optimized wheelchair route cannot be produced, and SHALL indicate when the fallback is in use.

#### Scenario: Wheelchair route through shade waypoints fails
- **WHEN** the wheelchair route through the shaded waypoints cannot be produced
- **THEN** the system returns a plain wheelchair-accessible route and indicates the fallback mode was used

#### Scenario: Accessible route itself fails
- **WHEN** the plain wheelchair-accessible route also cannot be produced
- **THEN** the system returns an error instead of a route
