# Scheduling & Publishing Specification

## Purpose

Schedule posts for automatic publishing to Instagram at specified times.

## Requirements

### R017: Post Scheduling

The system MUST allow users to schedule posts for future automatic publishing.

#### Scenario: Schedule with timezone

- GIVEN a post in "draft" status with published date/time set
- WHEN the user clicks "Schedule"
- THEN the post SHALL be queued for publishing at the specified local time (converted to UTC for scheduling)
- AND the status SHALL change to "scheduled"

#### Scenario: Schedule in the past

- GIVEN a post with a date/time in the past
- WHEN the user attempts to schedule it
- THEN the system SHALL show an error: "Cannot schedule in the past"
- AND MAY offer to publish immediately instead

### R018: Automatic Publishing

The system MUST publish scheduled posts at their scheduled time via the Instagram Graph API.

#### Scenario: Successful publish

- GIVEN a scheduled post at publish time
- WHEN the SchedulerAgent triggers
- THEN the system SHALL call Instagram Graph API with the post content and media
- AND on success, SHALL update post status to "published" with the platform's post ID
- AND SHALL store the published post URL

#### Scenario: API rate limit hit

- GIVEN Instagram API returns a rate limit error
- WHEN the SchedulerAgent attempts to publish
- THEN the system SHALL retry after the rate limit reset period
- AND SHALL NOT change the post status during retry window
- AND SHALL notify the user if rate limiting persists beyond 24 hours

### R019: Calendar View

The system SHALL display scheduled posts in a calendar with visual status indicators.

#### Scenario: Calendar with mixed statuses

- GIVEN the user has draft, scheduled, and published posts
- WHEN viewing the calendar
- THEN each post SHALL display with a color indicator: gray (draft), blue (scheduled), green (published), red (failed)
