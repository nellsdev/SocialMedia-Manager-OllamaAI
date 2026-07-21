# Auth & Profile Specification

## Purpose

Define user authentication, profile creation, and strategy configuration.

## Requirements

### R001: User Registration

The system MUST allow a new user to register via email/password or magic link through Supabase Auth.

#### Scenario: Email registration

- GIVEN a new user with a valid email address
- WHEN they submit the registration form with email and password
- THEN an account is created and a verification email is sent

#### Scenario: Duplicate email

- GIVEN an existing user account
- WHEN a registration attempt uses the same email
- THEN the system SHALL return an error: "Email already registered"

### R002: Profile Creation with Strategy

The system SHALL guide the user through profile setup after first login, including archetype selection, voice definition, content pillars, target audience, and goals.

#### Scenario: First-time onboarding

- GIVEN a newly registered user
- WHEN they log in for the first time
- THEN they SHALL be guided through: (1) Creator Archetype selection, (2) Profile naming, (3) Voice/tone definition, (4) Content pillars (min 1, max 5), (5) Target audience description, (6) Primary goals

#### Scenario: Skipping onboarding

- GIVEN a newly registered user
- WHEN they dismiss the onboarding wizard
- THEN a minimal profile SHALL be created with default values
- AND the user MAY complete strategy setup later

### R003: Creator Archetype Selection

The system MUST provide predefined creator archetypes that influence AI behavior and metric focus.

#### Scenario: Selecting an archetype

- GIVEN the user is in onboarding or settings
- WHEN they select an archetype from the predefined list
- THEN the system SHALL store the archetype and apply its tone, metric, and strategy defaults
- AND the user MAY customize any default afterward

#### Scenario: Changing archetype

- GIVEN an existing profile with an archetype
- WHEN the user changes the archetype
- THEN the system SHALL update AI suggestions, metric focus, and strategy recommendations accordingly
- AND existing content SHALL NOT be affected

### R004: Strategy Profile

The system SHALL store a strategy profile per profile, containing: voice description, content pillars, target audience, goals, visual references.

#### Scenario: Viewing strategy profile

- GIVEN a user with a completed profile
- WHEN they visit Settings > Strategy
- THEN they SHALL see all strategy fields with current values

#### Scenario: Updating audience description

- GIVEN an existing strategy profile
- WHEN the user edits the target audience field
- THEN the change SHALL be saved immediately
- AND future AI suggestions SHALL reflect the updated audience

### Available Archetypes (MVP)

| Archetype | Default Tone | Primary Metric | Strategy Focus |
|-----------|-------------|----------------|----------------|
| Aspiring Influencer | Trend-aware, engaging | Follower growth, reach | Viral hooks, collaborations |
| Authority Professional | Expert, educational | Engagement quality | Thought leadership, insights |
| Personal Sharing | Warm, authentic | Comments, interactions | Lifestyle, everyday moments |
| Business Owner | Value-first, CTA-oriented | Clicks, conversions | Product demos, offers |
| Community Builder | Inclusive, conversational | Participation rate | Polls, discussions, UGC |
