# WhatsApp Integration Specification (Idea Capture)

## Purpose

Enable idea capture through WhatsApp message forwarding.

## Requirements

### R023: WhatsApp Number Configuration

The system MUST allow the user to link a WhatsApp phone number for receiving forwarded ideas.

#### Scenario: Linking WhatsApp

- GIVEN the user is in Settings > Integrations
- WHEN they click "Connect WhatsApp"
- THEN the system SHALL display a QR code or link to initiate WhatsApp connection
- AND on successful connection, SHALL display the configured number

### R024: Inbound Message Processing

The system SHALL receive forwarded messages from WhatsApp and create ideas.

#### Scenario: Text message forwarded

- GIVEN the user forwards a text message to the configured WhatsApp number
- WHEN the system receives it
- THEN a new idea SHALL be created with the message text
- AND the source SHALL be marked as "WhatsApp"

#### Scenario: Multiple messages in one forward

- GIVEN the user forwards a message containing text and multiple images
- WHEN the system receives it
- THEN a single idea SHALL be created linking all media
- AND the description SHALL contain the text with attached media references
