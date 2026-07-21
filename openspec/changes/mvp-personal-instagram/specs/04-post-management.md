# Post Management Specification

## Purpose

Enable creation, editing, and management of posts across Instagram formats.

## Requirements

### R011: Post Creation with Format Selection

The system MUST allow creating posts in four Instagram formats: Story, Carousel, Reel, and Live.

#### Scenario: Creating a Carousel post

- GIVEN the user clicks "New Post"
- WHEN they select format "Carousel"
- THEN the editor SHALL show: title field, multi-image upload (2-10 images), caption field, first-comment field, hashtag section

#### Scenario: Creating a Reel post

- GIVEN the user clicks "New Post"
- WHEN they select format "Reel"
- THEN the editor SHALL show: video upload (max 90s), cover image selection, caption field, audio/music selection (deferred — API will provide options), hashtag section

#### Scenario: Creating a Story

- GIVEN the user clicks "New Post"
- WHEN they select format "Story"
- THEN the editor SHALL show: image/video upload (9:16), text overlay field, link sticker field (if eligible)

### R012: Post Status Lifecycle

A post SHALL progress through statuses: draft → scheduled → published, or draft → published directly.

#### Scenario: Draft to scheduled

- GIVEN a post in "draft" status
- WHEN the user sets a future date/time and clicks "Schedule"
- THEN the post status SHALL change to "scheduled"
- AND the post SHALL appear in the Content Grid on the scheduled date

#### Scenario: Publishing failure

- GIVEN a scheduled post whose publishing time has arrived
- WHEN the Instagram API returns an error
- THEN the post status SHALL change to "failed"
- AND the user SHALL receive an in-app notification with the error reason
- AND the system SHOULD offer a retry option
