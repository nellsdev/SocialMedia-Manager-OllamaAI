# Dashboard & Metrics Specification

## Purpose

Display social media performance metrics with archetype-adaptive KPIs.

## Requirements

### R020: KPI Dashboard

The system MUST display key performance indicators for the connected Instagram account.

#### Scenario: Dashboard loads with data

- GIVEN the user has an active Instagram connection with published posts
- WHEN they navigate to the Dashboard
- THEN the dashboard SHALL show: follower count, total likes, total comments, reach, engagement rate
- AND each metric SHALL show: current value, trend arrow (up/down), percentage change from previous period

#### Scenario: Dashboard with no data

- GIVEN a newly connected Instagram account with no published posts
- WHEN the user views the Dashboard
- THEN the dashboard SHALL show empty state with message: "Publish your first post to see metrics"
- AND SHALL NOT show error states

### R021: Metrics Over Time

The system SHALL display line charts for each KPI over selectable time ranges.

#### Scenario: 30-day engagement chart

- GIVEN the user has 30+ days of metrics data
- WHEN they select "Last 30 Days" on the engagement chart
- THEN a line chart SHALL display daily engagement rate with labeled axis and tooltip on hover

#### Scenario: Sparse data (under 7 days)

- GIVEN the account has fewer than 7 days of metrics
- WHEN the user views any time-series chart
- THEN the chart SHALL display available data points
- AND SHALL show a note: "Collecting more data for trends"

### R022: Archetype-Adaptive Metrics

The dashboard SHALL prioritize metrics based on the selected creator archetype.

#### Scenario: Aspiring Influencer dashboard

- GIVEN a profile with "Aspiring Influencer" archetype
- WHEN the dashboard loads
- THEN follower growth rate and reach SHALL be displayed prominently at the top

#### Scenario: Authority Professional dashboard

- GIVEN a profile with "Authority Professional" archetype
- WHEN the dashboard loads
- THEN engagement quality signals (saves, shares, comment depth) SHALL be emphasized
- AND follower count SHOULD NOT be the primary metric
