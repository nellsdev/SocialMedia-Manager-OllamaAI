# Idea Bank Specification

## Purpose

Allow creators to capture content ideas from multiple channels and manage them until they become posts.

## Requirements

### R005: Idea Capture (In-App)

The system MUST allow users to create text-based content ideas within the application.

#### Scenario: Quick idea creation

- GIVEN the user is on the Idea Bank page
- WHEN they click "New Idea" and enter a title and optional description
- THEN the idea SHALL be saved with status "idea", timestamp, and an optional content pillar tag

#### Scenario: Idea with format suggestion

- GIVEN the user is creating a new idea
- WHEN they submit the form
- THEN they MAY optionally select a suggested format (Story, Carousel, Reel, Live)
- AND the format SHALL be displayed as a badge in the idea card

### R006: Idea Capture (WhatsApp)

The system SHALL allow users to forward messages from WhatsApp to a dedicated number, which auto-creates ideas.

#### Scenario: WhatsApp idea capture

- GIVEN the user has configured their WhatsApp number
- WHEN they forward a text message to the system's WhatsApp number
- THEN a new idea SHALL be created with the message text as the description
- AND the idea SHALL be tagged with source "whatsapp"

#### Scenario: WhatsApp with media

- GIVEN the user forwards a message containing an image
- WHEN the system receives it
- THEN the idea SHALL include the image as a reference
- AND the idea description SHALL default to "Media idea — no text"

### R007: Idea Management

The system SHALL provide browsing, searching, filtering, and converting ideas into draft posts.

#### Scenario: Filtering by pillar

- GIVEN the Idea Bank contains ideas tagged with multiple pillars
- WHEN the user selects a pillar filter
- THEN only ideas with that pillar SHALL be displayed

#### Scenario: Converting idea to post

- GIVEN an existing idea in the Idea Bank
- WHEN the user clicks "Convert to Post"
- THEN a new draft post SHALL be created pre-filled with the idea's title, description, and format
- AND the original idea SHALL be marked as status "converted"
