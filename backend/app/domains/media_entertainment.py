"""Sports, Music, Movies, OTT, Gaming, and Media domain blueprints (Domains 28, 29, 30, 31, 32, 33, 34)."""
from __future__ import annotations

from app.domains.base import (
    ChartRule,
    ComparisonRule,
    DomainBlueprint,
    EntityRule,
    KpiRule,
    RecommendationRule,
    RiskRule,
    TrendRule,
)

DOMAINS: list[DomainBlueprint] = [
    # 28. Sports
    DomainBlueprint(
        id="sports",
        name="Sports",
        description="Sports matches, league standings, win/loss records, scores, home vs away, tournament stages, and game attendance.",
        keywords=("match", "game", "team", "league", "score", "points", "win", "loss", "tournament", "home_team", "away_team", "stadium", "referee"),
        alternative_domains=("Sports Performance", "Movies and Entertainment"),
        entities=(
            EntityRule("sports_team", "Sports Team / Franchise", ("team_name", "team_id", "club", "franchise")),
            EntityRule("sports_match", "Match / Game", ("match_id", "game_id", "fixture_id")),
        ),
        kpis=(
            KpiRule("team_win_rate", "Team Win Rate", "Percentage of matches won by team", ("numeric", "boolean"), metric_patterns=("is_win", "win", "win_pct"), formula="mean", format="percentage", business_meaning="Competitive sports victory rate"),
            KpiRule("avg_points_scored", "Average Points / Goals Scored", "Mean score per match played", ("numeric",), metric_patterns=("points", "goals", "runs", "score"), formula="mean", format="number", business_meaning="Offensive scoring potency"),
        ),
        charts=(
            ChartRule("points_by_team", "Total Points Scored by Team", "bar", dimension_patterns=("team_name", "club"), metric_patterns=("points", "goals", "score"), aggregation="sum", business_question="Which teams possess the highest scoring output in the league?"),
        ),
        comparisons=(
            ComparisonRule("category", "Home vs Away Win Rates", ("venue_type", "location"), ("is_win", "points")),
        ),
        trends=(
            TrendRule(("points", "goals"), ("match_date", "date"), "Tracking team scoring momentum over the season"),
        ),
        risks=(
            RiskRule("scoring_slump", "Severe Team Scoring Slump", "drop", metric_patterns=("points", "goals"), threshold=0.35, label="Requires investigation", recommended_action="Review tactical formations and offensive possession efficiency."),
        ),
        recommendations=(
            RecommendationRule("performance_improvement", "team_win_rate", "home_advantage", "Exploit tactical pace strategies in away fixtures to mitigate home-team crowd advantage.", "Subject to squad physical fatigue."),
        ),
    ),

    # 29. Sports Performance
    DomainBlueprint(
        id="sports_performance",
        name="Sports Performance",
        description="Individual athlete statistics, speed, distance covered, heart rate, minutes played, sprint volume, and player efficiency.",
        keywords=("athlete", "player", "heart_rate", "speed", "distance_covered", "sprints", "minutes_played", "efficiency", "passing_accuracy", "vo2_max"),
        alternative_domains=("Sports", "Healthcare"),
        entities=(
            EntityRule("athlete", "Athlete / Player", ("player_id", "athlete_name", "jersey_no")),
            EntityRule("training_session", "Training Session / Match Event", ("session_id", "event_id", "fixture_id")),
        ),
        kpis=(
            KpiRule("avg_player_speed", "Average Top Speed (km/h)", "Mean maximum velocity achieved by athlete", ("numeric",), metric_patterns=("top_speed", "max_speed", "velocity"), formula="mean", format="number", business_meaning="Athletic sprint velocity capability"),
            KpiRule("total_distance_covered", "Total Distance Covered (km)", "Sum of physical running distance logged", ("numeric",), metric_patterns=("distance", "distance_km", "meters_covered"), formula="sum", format="number", business_meaning="Player work-rate endurance"),
        ),
        charts=(
            ChartRule("distance_by_player", "Distance Covered by Player", "bar", dimension_patterns=("athlete_name", "player_name"), metric_patterns=("distance", "distance_km"), aggregation="sum", business_question="Which athletes log the highest physical distance in competition?"),
        ),
        comparisons=(
            ComparisonRule("category", "Sprint Volume across Playing Positions", ("position", "role"), ("sprints", "top_speed")),
        ),
        trends=(
            TrendRule(("distance", "heart_rate"), ("date", "session_date"), "Monitoring athlete physical load accumulation over training microcycles"),
        ),
        risks=(
            RiskRule("overtraining_fatigue", "Physical Overtraining Strain", "spike", metric_patterns=("fatigue_index", "strain"), threshold=1.5, label="Requires investigation", recommended_action="Implement recovery protocols and rotate starting minutes to prevent hamstring strains."),
        ),
        recommendations=(
            RecommendationRule("performance_improvement", "total_distance_covered", "high_fatigue", "Individualize training load tapering prior to high-stakes match fixtures.", "Requires sports science staff agreement."),
        ),
    ),

    # 30. Music
    DomainBlueprint(
        id="music",
        name="Music",
        description="Music streaming, song plays, track duration, artists, albums, playlists, genres, acousticness, and royalties.",
        keywords=("music", "track", "song", "artist", "album", "genre", "streams", "plays", "bpm", "tempo", "acousticness", "danceability", "playlist", "royalty"),
        alternative_domains=("OTT and Streaming", "Movies and Entertainment"),
        entities=(
            EntityRule("musical_track", "Track / Song", ("track_id", "song_title", "isrc", "track_name")),
            EntityRule("music_artist", "Music Artist / Band", ("artist_id", "artist_name", "performer")),
        ),
        kpis=(
            KpiRule("total_streams", "Total Music Streams", "Sum of all track plays recorded across listeners", ("numeric",), metric_patterns=("streams", "plays", "play_count", "stream_count"), formula="sum", format="number", business_meaning="Gross music catalog consumption"),
            KpiRule("total_royalties", "Total Royalties Earned", "Gross monetary royalties payable on streamed tracks", ("numeric",), metric_patterns=("royalties", "earnings", "revenue"), formula="sum", format="currency", business_meaning="Music catalog financial return"),
        ),
        charts=(
            ChartRule("streams_by_genre", "Stream Volume by Music Genre", "pie", dimension_patterns=("genre", "subgenre"), metric_patterns=("streams", "plays"), aggregation="sum", business_question="Which musical genres dominate total platform listening?"),
            ChartRule("top_artists", "Top Artists by Stream Volume", "bar", dimension_patterns=("artist_name", "artist"), metric_patterns=("streams", "plays"), aggregation="sum", business_question="Which artists command the largest audience listenership?"),
        ),
        comparisons=(
            ComparisonRule("category", "Track Plays across Playlist Types", ("playlist_type", "editorial"), ("streams", "plays")),
        ),
        trends=(
            TrendRule(("streams", "plays"), ("date", "release_date"), "Tracking viral track streaming curves post-release"),
        ),
        risks=(
            RiskRule("catalog_stream_decay", "Rapid Catalog Stream Decay", "drop", metric_patterns=("streams", "plays"), threshold=0.40, label="Requires investigation", recommended_action="Pitch tracks into algorithmic mood playlists to maintain sustained passive listenership."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "total_streams", "top_tracks", "Bundle popular catalog tracks into curated mood and workout playlist features.", "Subject to publisher licensing agreements."),
        ),
    ),

    # 31. Movies and Entertainment
    DomainBlueprint(
        id="movies_entertainment",
        name="Movies and Entertainment",
        description="Film box office, cinema screens, movie releases, production budgets, ticket sales, Rotten Tomatoes ratings, and runtime.",
        keywords=("movie", "film", "box_office", "cinema", "theatrical", "director", "cast", "runtime", "rating", "rotten_tomatoes", "imdb", "budget", "gross_revenue"),
        alternative_domains=("OTT and Streaming", "Media and Publishing"),
        entities=(
            EntityRule("film", "Movie / Motion Picture", ("movie_id", "film_title", "title")),
            EntityRule("director", "Film Director", ("director", "director_name")),
        ),
        kpis=(
            KpiRule("total_box_office", "Total Box Office Gross", "Gross theatrical ticket revenue generated by films", ("numeric",), metric_patterns=("box_office", "gross", "domestic_gross", "worldwide_gross"), formula="sum", format="currency", business_meaning="Theatrical commercial performance"),
            KpiRule("avg_critics_score", "Average Critic / Audience Rating", "Mean review score across film rating aggregators", ("numeric",), metric_patterns=("rating", "score", "imdb_score", "tomatometer"), formula="mean", format="number", business_meaning="Artistic and entertainment reception"),
        ),
        charts=(
            ChartRule("box_office_by_genre", "Box Office Gross by Movie Genre", "bar", dimension_patterns=("genre", "category"), metric_patterns=("box_office", "gross"), aggregation="sum", business_question="Which cinematic genres generate the highest box office returns?"),
            ChartRule("budget_vs_gross", "Production Budget vs Box Office Gross", "scatter", metric_patterns=("box_office", "gross"), dimension_patterns=(), aggregation="sum", business_question="Does high production budget consistently yield high box office returns?"),
        ),
        comparisons=(
            ComparisonRule("category", "Box Office Returns by Studio / Distributor", ("studio", "distributor"), ("box_office", "gross")),
        ),
        trends=(
            TrendRule(("box_office", "gross"), ("release_date", "weekend"), "Tracking opening weekend theatrical decay curves"),
        ),
        risks=(
            RiskRule("theatrical_flop_anomaly", "Severe Box Office Deficit", "drop", metric_patterns=("gross", "box_office"), threshold=0.50, label="Requires investigation", recommended_action="Shorten theatrical exclusivity window and accelerate digital PVOD release."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "total_box_office", "high_roi_genres", "Prioritize greenlighting mid-budget horror and animated family film concepts with historically superior ROI.", "Requires script and talent acquisition."),
        ),
    ),

    # 32. OTT and Streaming
    DomainBlueprint(
        id="ott_streaming",
        name="OTT and Streaming",
        description="Video-on-demand streaming, watch hours, completion rates, subscriber viewing habits, bitrates, buffering, and CDN delivery.",
        keywords=("ott", "streaming", "watch_time", "video_streams", "completion_rate", "buffering", "bitrate", "cdn", "series", "episode", "binge", "viewer"),
        alternative_domains=("Movies and Entertainment", "Music", "SaaS and Subscription"),
        entities=(
            EntityRule("video_content", "Video Title / Episode", ("video_id", "content_id", "series_id", "episode_id")),
            EntityRule("viewer", "Subscriber / Viewer", ("viewer_id", "user_id", "profile_id")),
        ),
        kpis=(
            KpiRule("total_watch_hours", "Total Hours Streamed", "Sum of all video playback hours consumed", ("numeric",), metric_patterns=("watch_time", "hours_streamed", "duration_minutes"), formula="sum", format="duration", business_meaning="Platform audience viewing engagement"),
            KpiRule("video_completion_rate", "Episode Completion Rate", "Percentage of video stream events viewed past 90% runtime", ("numeric", "boolean"), metric_patterns=("is_completed", "completion_rate"), formula="mean", format="percentage", business_meaning="Content narrative stickiness"),
        ),
        charts=(
            ChartRule("watch_time_by_title", "Watch Hours by Content Title", "bar", dimension_patterns=("title", "series_name", "genre"), metric_patterns=("watch_time", "hours_streamed"), aggregation="sum", business_question="Which marquee titles drive the majority of streaming hours?"),
        ),
        comparisons=(
            ComparisonRule("category", "Buffering Rates across CDN Providers", ("cdn_provider", "device_type"), ("buffering_ratio", "rebuffer_time")),
        ),
        trends=(
            TrendRule(("watch_time", "hours_streamed"), ("date", "time"), "Analyzing weekend binge viewing surges"),
        ),
        risks=(
            RiskRule("buffering_spike", "Playback Buffering Ratio Surge", "spike", metric_patterns=("buffering_ratio", "buffering_time"), threshold=0.03, label="Requires investigation", recommended_action="Reroute streaming traffic away from congested CDN edge nodes."),
        ),
        recommendations=(
            RecommendationRule("customer_retention", "total_watch_hours", "popular_series", "Commission second-season renewals for original series exceeding 70% completion rates.", "Subject to production studio budgets."),
        ),
    ),

    # 33. Gaming
    DomainBlueprint(
        id="gaming",
        name="Gaming",
        description="Video games, player sessions, in-app purchases (IAP), levels completed, battle passes, virtual currency, and player retention.",
        keywords=("gaming", "game", "player", "session_length", "level_completed", "iap", "microtransaction", "virtual_currency", "battle_pass", "guild", "leaderboard", "quest"),
        alternative_domains=("Product Analytics", "SaaS and Subscription", "OTT and Streaming"),
        entities=(
            EntityRule("player", "Player / Gamer", ("player_id", "gamer_tag", "user_id")),
            EntityRule("game_level", "Game Level / Mission", ("level_id", "quest_id", "mission_id")),
        ),
        kpis=(
            KpiRule("arppu", "Average Revenue Per Paying User (ARPPU)", "Mean monetary spend among players who make in-game purchases", ("numeric",), metric_patterns=("iap_spend", "revenue", "arppu"), formula="mean", format="currency", business_meaning="Monetization depth among paying gamer segment"),
            KpiRule("avg_session_minutes", "Average Gameplay Session (mins)", "Mean continuous time players spend in game client", ("numeric",), metric_patterns=("session_minutes", "session_length", "playtime"), formula="mean", format="duration", business_meaning="Game immersion and core loop stickiness"),
        ),
        charts=(
            ChartRule("iap_by_item", "In-App Purchases by Virtual Item", "bar", dimension_patterns=("item_name", "item_category", "sku"), metric_patterns=("iap_spend", "amount"), aggregation="sum", business_question="Which virtual cosmetic or power items generate the highest IAP revenue?"),
        ),
        comparisons=(
            ComparisonRule("category", "Player Churn across Game Levels", ("level_id", "level_number"), ("churn_rate", "quit_rate")),
        ),
        trends=(
            TrendRule(("player_id", "dau"), ("date", "day"), "Monitoring player base surge post-major game patch update"),
        ),
        risks=(
            RiskRule("level_difficulty_wall", "Player Level Churn Wall", "spike", metric_patterns=("fail_rate", "quit_rate"), threshold=0.70, label="Requires investigation", recommended_action="Re-tune enemy difficulty and resource drops on levels exhibiting abnormal quit rates."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "arppu", "monetization", "Introduce time-limited seasonal battle passes with exclusive cosmetic rewards.", "Must maintain gameplay fairness to avoid pay-to-win backlash."),
        ),
    ),

    # 34. Media and Publishing
    DomainBlueprint(
        id="media_publishing",
        name="Media and Publishing",
        description="News publications, digital magazines, article reads, author performance, paywall conversions, and reader scroll depth.",
        keywords=("article", "publisher", "author", "news", "editorial", "paywall", "subscriber", "read_time", "scroll_depth", "byline", "syndication"),
        alternative_domains=("Web Analytics", "Social Media", "SaaS and Subscription"),
        entities=(
            EntityRule("article", "Editorial Article / Story", ("article_id", "story_id", "headline", "url")),
            EntityRule("author", "Journalist / Author", ("author", "byline", "writer_id")),
        ),
        kpis=(
            KpiRule("total_reads", "Total Article Reads", "Sum of completed article reads across audience", ("numeric",), metric_patterns=("reads", "pageviews", "read_count"), formula="sum", format="number", business_meaning="Journalistic audience reach"),
            KpiRule("avg_read_time", "Average Dwell / Read Time", "Mean minutes readers spend engaged on story text", ("numeric",), metric_patterns=("read_time", "dwell_time", "time_on_page"), formula="mean", format="duration", business_meaning="Editorial content engagement depth"),
        ),
        charts=(
            ChartRule("reads_by_section", "Article Reads by Editorial Section", "pie", dimension_patterns=("section", "desk", "category"), metric_patterns=("reads", "pageviews"), aggregation="sum", business_question="Which editorial desks drive the largest reading audience?"),
        ),
        comparisons=(
            ComparisonRule("category", "Paywall Conversions across Editorial Desks", ("section", "desk"), ("paywall_conversions", "subscriptions")),
        ),
        trends=(
            TrendRule(("reads", "pageviews"), ("publish_date", "date"), "Tracking breaking news traffic spikes and tail readership"),
        ),
        risks=(
            RiskRule("reader_bounce_spike", "Low Editorial Engagement Spike", "drop", metric_patterns=("scroll_depth", "read_time"), threshold=0.30, label="Requires investigation", recommended_action="Review article headline clickbait alignment and inline media placements."),
        ),
        recommendations=(
            RecommendationRule("revenue_improvement", "total_reads", "high_dwell_topics", "Repurpose high-dwell investigative articles into subscriber-exclusive newsletter series.", "Requires editorial writer bandwidth."),
        ),
    ),
]
