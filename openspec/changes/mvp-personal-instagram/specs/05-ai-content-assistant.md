# AI Content Assistant Specification

## Purpose

Provide AI-powered content suggestions (captions, hashtags, formats) tailored to the creator's archetype, voice, and strategy.

## Requirements

### R013: Real-Time Caption Suggestions

The system SHALL generate caption and hashtag suggestions while the user writes a post, based on the profile's strategy profile and archetype.

#### Scenario: AI suggests caption

- GIVEN the user is editing a post draft with a title/description filled
- WHEN they click "Suggest Caption"
- THEN the system SHALL generate 3 caption options tailored to the profile's archetype, voice, and content pillars
- AND each option SHALL display with a "Use This" button

#### Scenario: Archetype-tailored tone

- GIVEN an Authority Professional archetype profile
- WHEN the AI generates caption suggestions
- THEN the captions SHALL use an expert/educational tone, avoiding slang or overly casual language

#### Scenario: Hashtag suggestions

- GIVEN the user has entered a caption
- WHEN they click "Suggest Hashtags"
- THEN the system SHALL suggest 5-10 hashtags combining: trending tags in the user's niche, pillar-relevant tags, and location tags

### R014: Batch Idea Generation

The system SHALL generate weekly content ideas based on trends and the profile's content pillars.

#### Scenario: Weekly idea batch

- GIVEN a profile with defined content pillars and archetype
- WHEN the user requests "Generate Weekly Ideas"
- THEN the system SHALL produce up to 7 content ideas (one per day)
- AND each idea SHALL include: title, suggested format, brief description, relevance to content pillar

#### Scenario: Empty idea generation

- GIVEN a profile with NO content pillars defined
- WHEN the user requests idea generation
- THEN the system SHOULD prompt: "Define your content pillars first for better suggestions"

### R015: Format Recommendation

The AI SHALL suggest the best Instagram format for each content idea based on the content type and archetype.

#### Scenario: Format for educational content

- GIVEN a content idea about "How to analyze engagement metrics"
- WHEN the AI analyzes it
- THEN it SHOULD recommend "Carousel (step-by-step guide)" or "Reel (quick tip)"
- AND include the reasoning: "Your audience engages more with educational Carousels"

### R016: Persona Memory

The AI MUST persist knowledge of the creator's past content to avoid repeating topics and maintain consistent voice.

#### Scenario: Avoiding repetition

- GIVEN the user has posted about "Instagram algorithm changes" in the last 30 days
- WHEN the AI generates new content ideas
- THEN it SHOULD NOT suggest the same topic again
- AND it MAY suggest: "You covered this recently — how about an update or a different angle?"
