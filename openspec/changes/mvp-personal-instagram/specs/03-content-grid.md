# Content Grid Specification

## Purpose

Provide a visual content planning calendar that shows pillar distribution, format mix, and scheduling gaps.

## Requirements

### R008: Content Grid View

The system MUST display a visual calendar showing scheduled and draft posts by day/week/month.

#### Scenario: Monthly grid view

- GIVEN the user has scheduled posts in the current month
- WHEN they navigate to the Content Grid
- THEN a monthly calendar SHALL display each post as a card on its scheduled date
- AND each card SHALL show: title, content pillar (color-coded), format badge, status

#### Scenario: Day view detail

- GIVEN a day with multiple scheduled posts
- WHEN the user clicks on a specific date
- THEN a detailed day view SHALL list all posts for that date with full metadata

### R009: Pillar Distribution Analysis

The system SHALL display a visual breakdown of content pillars and format distribution.

#### Scenario: Pillar balance indicator

- GIVEN the user has posts planned across multiple pillars
- WHEN viewing the Content Grid
- THEN a sidebar or top bar SHALL show a donut chart of pillar distribution

#### Scenario: Format mix warning

- GIVEN one format type (e.g., Reels) represents over 70% of planned content
- WHEN the grid renders
- THEN the system SHOULD show a suggestion: "Your content is heavily skewed toward Reels. Consider adding Carousels for deeper engagement."

### R010: Drag-and-Drop Planning

The system SHALL allow dragging ideas from the Idea Bank into the Content Grid.

#### Scenario: Idea to calendar slot

- GIVEN the user has the Idea Bank sidebar open alongside the Content Grid
- WHEN they drag an idea card onto a date in the calendar
- THEN a new draft post SHALL be created on that date, pre-filled with the idea's data
- AND the original idea SHALL be marked as "converted"
