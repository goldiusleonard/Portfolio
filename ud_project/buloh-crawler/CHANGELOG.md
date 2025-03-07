# Changelog

All notable changes to Buloh Crawler will be documented in this file.

## [0.13.0] - 2025-02-17

### Added

- Added Date Filtering to Instagram Post Crawler API and Trending Post Search by Hashtag Crawler API.
- Added Instagram Post Search by Username Crawler API.

## [0.12.0] - 2025-02-14

### Added

- Added Twitter/X Post and Profile crawler API using Tweepy.
- Added Twitter/X Post and Profile crawler API using APIfy.

## [0.11.0] - 2025-02-12

### Added

- Added Instagram trending hashtags crawler API.
- Added Instagram trending posts crawler API.

## [0.10.1] - 2025-02-07

### Changed

- Refactored Instagram profile crawler into a separate API.

## [0.10.0] - 2025-02-06

### Added

- Added Twitter tweets and profile scraper using Tweepy.

## [0.9.0] - 2025-02-05

### Added

- Added Instagram profile crawler using Apify and Instaloader to the existing Instagram crawler API.

## [0.8.0] - 2025-02-04

### Added

- Added Instagram posts and comments crawler API.

## [0.7.0] - 2025-01-16

### Added

- Added unit testing for Live TikTok Video Crawler.

## [0.6.0] - 2025-01-15

### Added

- Added APIs to remove all TikTok Live comments and video sessions.

## [0.5.0] - 2025-01-13

### Added

- Added streaming live tiktok video API for display.

## [0.4.1] - 2025-01-10

### Fixed

- Fixed Redis Pub/Sub subscription to reconnect on connection errors.

## [0.4.0] - 2025-01-09

### Added

- Added unit testing for Live TikTok Comment Crawler.

### Changed

- Changed redis methods with Redis Pub/Sub for TikTok Live Recorder.

## [0.3.0] - 2024-12-18

### Added

- Added background task for file removal after video processing
- Added functionality to upload the full recorded live stream video to Blob and return URL link

## [0.2.0] - 2024-12-16

### Added

- Added TikTok live stream comment streaming API
- Added a check alive API for TikTok live streams
- Added video chunk concatenation for TikTok live stream recordings

## [0.1.1] - 2024-12-10

### Added

- Added TikTok live stream recorder and utility functions
- Added stop recording tiktok live stream API function
- Added user_id and save_interval to tiktok live recorder API inputs
- Added TikTok Live recorder integration with Buloh crawler as a single API
- Added changelog and version


### Changed

- Changed multiprocess recording process with direct recording from in-memory stream using FFmpeg 
